# Authorship: {{{
''' 
Written by: Dario C. Lewczyk
Date: 01/16/2026
'''
#}}}
# imports: {{{
from topas_tools.utils.topas_parser import TOPAS_Parser
import re
#}}}
# TOPAS_Modifier: {{{
class TOPAS_Modifier(TOPAS_Parser):
    '''
    Class used to modify input files for TOPAS
    This is specifically meant to work hand-in-hand 
    with the TOPAS_Parser class which does a better job of parsing 
    the inp files than some of my previous attempts. 
    '''
    # match_shape_parameters: {{{
    def match_shape_parameters(self, s:str = None):
        '''
        The purpose of this function is to see if a given entry in something like the 
        out_dict is a shape parameter or not

        As a reminder, here are the shape parameters from a typical 
        IxPxSx input file: 

            gauss_fwhm_fault
            lor_fwhm_fault
            size_isoG_fwhm_s_nm
            size_isoL_fwhm_s_nm
            gauss_fwhm_strain
            lor_fwhm_strain

        If it is a shape parameter, then it returns the key, if not, it returns None
        '''
        pattern = re.compile(
            r'([A-za-z._]+_fwhm_[A-Za-z._]+)'
        )
        
        m = pattern.match(s)
        if m:
            p_parameter = m.group(1)
            return p_parameter
        else:
            return None
        
    #}}}
    # modify_ph_lines: {{{
    def modify_ph_lines(self,lines:list = None, out_dict:dict = None, I:str = "I", P:str = "P", S:str = "S", debug:bool = False):
        ''' 
        This function serves the purpose to neatly edit the lines of an INP 
        related to Ph# for IxPxSx type refinements. 
    
        It specifically edits the prm definitions
        '''
        # Loop through the out_dict: {{{
        for ph, var_entry in out_dict.items():
            # For each of the phase parts, fix the LPs: {{{
            if 'Ph' in ph:
                relevant_keys = ['lp_a', 'lp_b', 'lp_c', 'lp_al', 'lp_be', 'lp_ga'] 
                for key, entry in var_entry.items(): 
                    idx = entry.get('linenumber')
                    val = entry.get('value')
                    err = entry.get('error')
                    fixed = entry.get('fixed')
                    if debug:
                        print(f'Current values for {ph} {key}: IDX: {idx}, VAL: {val}, ERR: {err}, FIXED: {fixed}')
                    # try to replace lines in the INP: {{{
                    try:
                        old = lines[idx]
                        varname, old_val, old_err = self.parse_phase_prms(old) # in this form, it returns "variable name, value, error"
                        if debug:
                            print(f'OLD LINE: {old}\n\tVARNAME: {varname}, VAL: {old_val}, ERR: {old_err}')
                        # Conditional for the P being x: {{{
                        if P == 'x' and key in relevant_keys and not fixed:
                            new = old.replace(varname, f'!{varname}').replace(str(old_val), str(val)).replace(str(old_err),str(err))
                        #}}} 
                        # Conditional for the S being x: {{{
                        #elif S == 'x' and not fixed and self.match_shape_parameters(key):
                        #    # In this case, the parameter has been flagged as being a shape parameter
                        #    new = old.replace(varname, f'!{varname}').replace(str(old_val), str(val)).replace(str(old_err), str(err)) 
                        #}}}
                        else:
                            if old_val and old_err:
                                new = old.replace(str(old_val), str(val)).replace(str(old_err),str(err))
                            elif old_val:
                                new = old.replace(str(old_val), str(val)) # This neglects errors if they arent there.
                            else:
                                continue # In these cases, not an issue. no need to update. 
                        lines[idx] = new                  
                    
                    except:
                        if debug:
                            print(f'KEY: {key} NOT UPDATED in INP')
                    #}}}
                    # print(f'OLD: {old}\nNEW: {new}') 
                 
            #}}}
            continue
        #}}}
        return lines 
    #}}}
    # modify_specimen_displacement_lines: {{{
    def modify_specimen_displacement_lines(self, lines:list = None, out_dict:dict = None, P:str = 'P', debug:bool = False):
        '''
        lines: Lines of an inp file
        out_dict: a dictionary containing relevant information from the previous cycle
        P: This is a parameter that tells whether or not the peak positions will be refined next cycle
            If P == 'x': fix the specimen displacement since these cant be refined together 

        '''
        specimen_displacement = out_dict.get('Specimen_Displacement') # This is the only relevant entry
        # Try modifying lines: {{{
        try:
            idx = var_entry.get('linenumber')
            val = var_entry.get('value')
            err = var_entry.get('error')
            fixed = var_entry.get('fixed')
            if debug:
                print(f'Current values for {ph}: IDX: {idx}, VAL: {val}, ERR: {err}, FIXED: {fixed}')
         
            if not fixed:
                old = lines[idx]
                old_val, old_err = self.parse_specimen_displacement(old)
                if P == 'x':
                    new = old.replace(f'{old_val}', f'{val}').replace(f'{old_err}', f'{err}').replace('@', '') # Replace the values and turn off the refinement
                else:
                    new = old.replace(f'{old_val}', f'{val}').replace(f'{old_err}', f'{err}')
                lines[idx] = new 
        except:
            if debug:
                print('No lines altered for Specimen_Displacement in your INP')
            pass
        #}}} 
        return lines
   
    #}}}
    # write_ixpxsx_lines: {{{
    def write_ixpxsx_lines(self,lines:list = None, cry_files:list = None,out_dict:dict = None, macro_blocks:dict = None, I="I", P = "P", S = "S"):
        '''
        This writes the lines necessary for running IxPxSx type refinements 
        and ensures that the added lines are all accounted for so that 
        future refinements can still find an output XY line if it exists.

        lines: read from an INP file
        cry_files: list of files for the IxPxSx technique
        out_dict: output file dictionary generated by TOPAS_Parser
        macro_blocks: macro_blocks dictionary generated by TOPAS_Parser
        I: designation of I
        P: designation of P
        S: designation of S

        returns: 
            A tuple with the lines of the file (modified) first and the number of lines added second
            (lines, added_lines)
        '''
        added_lines = 0 # Keep track of the lines added so that the linenumber for how many lines were added to add the IxPxSx 
        # Now, write the WPF IxPxSx stuff: {{{ 
        insert_idx = macro_blocks[max(list(macro_blocks.keys()))][1] + 2 # This gives us the index where we can insert new lines
        for ph, entry in out_dict.items():
            lines.insert(insert_idx, '\n') # Insert a break
            insert_idx +=1
            added_lines += 1
            # Something important to remember is that the positioning of the WPF_IxPxSx stuff does matter
            # Write a macro for each phase: {{{
            if 'Ph' in ph:
                try:
                    ph_num = int(re.search(r'(\d+)', ph).group(1)) # This will be used for making the WPF macros
                    wpf_macro = f'WPF_{I}{P}{S}_{ph_num}()\n' # write the macro
                    lines.insert(insert_idx, wpf_macro) # Write the macro
                    insert_idx += 1 # Advance by 1
                    lines.insert(insert_idx, '\n')
                    insert_idx += 1 
                    added_lines += 2 
                except:
                    continue
            #}}} 
        #}}}
        # Add the include statements for the CRY: {{{
        for cry in cry_files:
            cry = cry.removesuffix('.out')
            lne = f'#include {cry}.inp'

            lines.insert(insert_idx,lne)
            insert_idx += 1
            lines.insert(insert_idx,'\n')
            insert_idx += 1
            added_lines += 2
        #}}}    
        return lines, added_lines
    #}}}    
    # update_output_xy_line: {{{
    def update_output_xy_line(self, lines:list = None, new_suffix:str = None,  inp_dict:dict = None, debug:bool = False):
        '''
        This allows you to quickly update the lines of an INP file to change the 
        filename of the XY file output by TOPAS.

        new_suffix: This will generally be: {temp}_{ixpxsx_mode}

        returns the lines of the file and the new name created (does not contain the extension)
        '''
        out_xy = inp_dict.get('output_xy') # This should be a dictionary with all necessary information on the output xy line
        #  modify the line: {{{ 
        if out_xy:
            idx = out_xy.get('linenumber')  
            prefix = out_xy.get('prefix')
            old_temp = out_xy.get('temp')
            old_method = out_xy.get('method')
                 
            old_name = f'{prefix}_{old_temp}_{old_method}'
            new_name = f'{prefix}_{new_suffix}'
            if debug:
                print(f'Renaming:\n\t{old_name} -> {new_name}')
                
            old = lines[idx]
            new = old.replace(old_name, new_name)
            lines[idx] = new
        else:
            new_name = None
        #}}}
        return lines, new_name
    #}}}
#}}}
