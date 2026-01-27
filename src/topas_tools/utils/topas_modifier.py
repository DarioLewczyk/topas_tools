# Authorship: {{{
''' 
Written by: Dario C. Lewczyk
Date: 01/16/2026
'''
#}}}
# imports: {{{
from topas_tools.utils.topas_parser import TOPAS_Parser
import re
import logging
#}}}
# TOPAS_Modifier: {{{
class TOPAS_Modifier(TOPAS_Parser):
    '''
    Class used to modify input files for TOPAS
    This is specifically meant to work hand-in-hand 
    with the TOPAS_Parser class which does a better job of parsing 
    the inp files than some of my previous attempts. 
    '''
    logger = logging.getLogger(__name__) # Make a logger for this
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
        if debug: 
            print('MODIFYING THE PRM ENTRIES')
        self.logger.debug('MODIFYING PRM ENTRIES')
        for ph, var_entry in out_dict.items():
            # For each of the phase parts, fix the LPs: {{{
            if 'Ph' in ph:
                self.logger.debug(f'FOUND {ph}')
                relevant_keys = ['lp_a', 'lp_b', 'lp_c', 'lp_al', 'lp_be', 'lp_ga'] 
                for key, entry in var_entry.items(): 
                    idx = entry.get('linenumber')
                    val = entry.get('value')
                    err = entry.get('error')
                    fixed = entry.get('fixed')
                    if debug:
                        print(f'\tCurrent values for {ph} {key}: IDX: {idx}, VAL: {val}, ERR: {err}, FIXED: {fixed}')
                    self.logger.debug(f'Current values for {ph} {key}: IDX: {idx}, VAL: {val}, ERR: {err}, FIXED: {fixed}')
                    # try to replace lines in the INP: {{{
                    self.logger.debug('Trying to find for the old lines:')
                    old = lines[idx]
                    old_parsed_prms = self.parse_phase_prm_line(old) # We are just parsing a line here.
                    self.logger.debug(f'Old Parsed Prms: {old_parsed_prms}')
                    varname = old_parsed_prms.get('var')
                    if old_parsed_prms and varname != 'keepS': 
                        old_val = old_parsed_prms.get('value')
                        old_err = old_parsed_prms.get('error')
                        
                        if debug:
                            print(f'\tOLD LINE: {old}\n\tVARNAME: {varname}, VAL: {old_val}, ERR: {old_err}')
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
                                self.logger.debug(f'Updating old values: {varname}')
                                new = old.replace(str(old_val), str(val)).replace(str(old_err),str(err))
                            elif old_val:
                                self.logger.debug('Neglecting errors...')
                                new = old.replace(str(old_val), str(val)) # This neglects errors if they arent there.
                            else:
                                self.logger.debug('Triggered the case where we do not update')
                                continue # In these cases, not an issue. no need to update. 
                        lines[idx] = new                  
                        self.logger.debug(f'Updated {varname} line {idx}')
                    
                    else:
                        self.logger.debug(f'DID NOT UPDATE {key} in INP')
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
        if specimen_displacement is not None: 
            idx = specimen_displacement.get('linenumber')
            val = specimen_displacement.get('value')
            err = specimen_displacement.get('error')
            fixed = specimen_displacement.get('fixed')
            if debug:
                print(f'Current values for Specimen_Displacement: IDX: {idx}, VAL: {val}, ERR: {err}, FIXED: {fixed}')
         
            if not fixed:
                old = lines[idx]
                sd = self.parse_specimen_displacement_line(old)
                old_val = sd.get('value')
                old_err = sd.get('error') 
                if P == 'x':
                    new = old.replace(f'{old_val}', f'{val}').replace(f'{old_err}', f'{err}').replace('@', '') # Replace the values and turn off the refinement
                else:
                    new = old.replace(f'{old_val}', f'{val}').replace(f'{old_err}', f'{err}')
                lines[idx] = new 
        else:
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

        Returns: 
            lines 
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
                
                ph_num = int(re.search(r'(\d+)', ph).group(1)) # This will be used for making the WPF macros
                wpf_macro = f'WPF_{I}{P}{S}_{ph_num}()\n' # write the macro
                lines.insert(insert_idx, wpf_macro) # Write the macro
                insert_idx += 1 # Advance by 1
                lines.insert(insert_idx, '\n')
                insert_idx += 1 
                added_lines += 2 
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
        # Freeze the updates to the output_xy after it is updated: {{{
        if "output_xy" in out_dict and out_dict.get('output_xy') is not None:
            self.apply_line_offset(out_dict['output_xy'], added_lines) # This offsets the lines by the number necessary
            self.freeze_updates(out_dict['output_xy']) # This applies a freeze to the updates for the lifetime of this input file
        #}}} 
        return lines
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
    # modify_out_dict_linenumber: {{{
    def modify_out_dict_linenumber(self, entry:dict = None, added_lines:int = 0, modified_linenumber:bool = False):
        ''' 
        Allows you to modify the linenumber of an entry in a dictionary

        entry: The entry in your dictionary that contains the keyword: "linenumber"
        added_lines: The number of lines to be added (or subtracted) from the linenumber
        modified_linenumber: An external variable that you probably will be tracking that tells if this code should run or not

        returns a tuple, 
            (entry, modified_linenumber)
        '''
        if not modified_linenumber:
            linenumber = entry['linenumber']
            linenumber += added_lines
            self.logger.debug(f'Original Line Number: {linenumber}')
            self.logger.debug(f'Adding {added_lines} Lines')
            self.logger.debug(f'Modified Line Number: {linenumber}')

            entry['linenumber'] = linenumber 
            modified_linenumber = True
            
        return entry, modified_linenumber
    #}}}
    # modify_bkg: {{{
    def modify_bkg(self,lines, out_dict):
        '''
        Replaces the background with whatever was refined before. 
        Should give a better starting point for refinement
        ''' 
        
        bkg_entry = out_dict['bkg']
        bkg_line = bkg_entry.get('line')
        bkg_idx = bkg_entry.get('linenumber')
        lines[bkg_idx] = f'{bkg_line}\n'
        return lines

    #}}}
    # modify_inp_lines: {{{
    def modify_inp_lines(self, 
            lines = None,
            out_dict:dict = None,
            I:str = 'I',
            P:str = 'P',
            S:str = 'S', 
            cry_files:list = None,
            modify_ph:bool = True, 
            modify_specimen_displacement:bool = True, 
            modify_bkg:bool = True,
            write_ixpxsx_lines:bool = True,
            update_output_xy_line:bool = True,
            new_suffix:str = None,
        ):
        ''' 
        This function wraps all the line modification lines
        This has the advantage that if the input file changes 
        in a fundamental way during the refinement 
        (e.g. your template is not the same throughout)
        this is able to capture that change and work with it.

        This function returns the following: 
            1. lines
            2. new_name
        ''' 
        # 1.  Re-parse the INP to detect drift: {{{ 
        inp_dict = self.get_inp_out_dict(
                lines, 
                record_fit_metrics = False, 
                record_xdd = False
        ) # This gives us the INP dictionary 
        #}}}
        # 2. Refresh out_dict to match INP: {{{
        self.refresh_out_dict(out_dict, inp_dict) # IF there are differences, this will resolve them
        #}}}
        # 3. Modify_ph: {{{
        if modify_ph:
            lines = self.modify_ph_lines(lines=lines, out_dict=out_dict, I=I,P=P,S=S)
        #}}} 
        # 4. Modify_specimen_displacement_lines: {{{
        if modify_specimen_displacement:
            lines = self.modify_specimen_displacement_lines(lines=lines, out_dict=out_dict,P=P)
        #}}}
        # 5. Modify background: {{{
        if modify_bkg:
            lines = self.modify_bkg(lines, out_dict)
        #}}}
        # 7. Write_ixpxsx_lines: {{{
        if write_ixpxsx_lines:
            macro_blocks = self.find_ixpxsx_macro_blocks(lines) # This returns a dict. Keys == phase num, vals == (start, end)
            lines = self.write_ixpxsx_lines(
                    lines=lines, 
                    cry_files=cry_files,
                    out_dict=out_dict,
                    macro_blocks=macro_blocks
            ) 
        #}}}
        # 7. Update outuput_xy filename: {{{
        if update_output_xy_line:
            lines, new_name = self.update_output_xy_line(lines = lines, inp_dict = out_dict, new_suffix = new_suffix)
        else:
            new_name = None
        #}}}

        return (lines, new_name)

    #}}}
#}}}
