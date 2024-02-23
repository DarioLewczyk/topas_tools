# Authorship: {{{
# Written By: Dario Lewczyk
# Date: 02-20-2024
#}}}
# Imports: {{{
import re
import numpy as np
#}}}
# FileModifier: {{{
class FileModifier():
    '''
    This class holds all of the functions needed to modify TOPAS 
    input files from output file results.

    It works with the OUT_Parser quite heavily.
    '''
    # __init__: {{{
    def __init__(self,):
        self._out_file_monitor = {}
    #}}}
    # out_file_monitor: {{{
    @property
    def out_file_monitor(self):
        return self._out_file_monitor
    @out_file_monitor.setter
    def out_file_monitor(self,new_out_file_monitor):
        if not isinstance(new_out_file_monitor, dict):
            raise ValueError('out_file_monitor needs to be a dictionary!')
        self._out_file_monitor = new_out_file_monitor
    #}}}
    # _modify_out_for_monitoring: {{{
    def _modify_out_for_monitoring(self,
            out:str = None,
            on_phases:list = None, 
            off_phases:list = None, 
            threshold_for_on:float = None, 
            threshold_for_off:float = None, 
            current_idx:int = None,
            off_sf_value:float = 1.0e-100,
            on_sf_value:float = 1.0e-6,
            on_method:str = None,
            current_time:float = None,
            debug:bool = False,
            time_error:float = 1.1,
        ):
        '''
        This function handles the actual runtime modifications of output files 
        It uses thresholds provided by the user to determine when to add or remove phases (it does this by
        making scale factors either reasonable e.g. 1.5e-5 or extremely low e.g. 1e-100) to turn phases on or off.

        on_phases = list of phases you want to monitor the Rwp to turn on
        off_phases = list of phases you want to monitor the scale factor to turn off

        The threshold for on should be a percent deviation from the initial Rwp
        The threshold for off should be a percentage of the max value of a scale factor.
        
        current_idx: this is the current index of patterns you have refined.        

        out: this is the output file's filename.

        This needs to be able to also take into account, things written after the tag for the formula. e.g. Ta2O5_HT

        on_method can be either time or rwp. If it is time, you need to give a time. 

        time_error is the amount of +/- that the time can be off to trigger the phase on or off
        '''
        # get the relevant lines: {{{
        relevant_lines = self._get_relevant_lines_for_monitoring(out, off_phases,on_phases,threshold_for_off,threshold_for_on,debug)
        #}}} 
        # check to see if the index is zero or not: {{{
        if current_idx == 0:
            for i, key in enumerate(relevant_lines):
                entry = relevant_lines[key]
                value = entry['value']
                name = entry['name']
                entry_type = entry['type']
                if entry_type == 'on': 
                    rwp = entry['rwp']
                else:
                    rwp = None
                self.out_file_monitor[i] = {
                        'values': [value],
                        'name':name,
                        'type': entry_type,
                        'rwps':[rwp],
                        'stopped':False,
                }
        #}}}
        # For all other indices: {{{
        else:
            # Loop through the out file monitor: {{{
            for i, key in enumerate(self.out_file_monitor):
                entry = self.out_file_monitor[key] # this is the current substance entry for the history
                current_entry = relevant_lines[key] # This is the current substance entry
                line_idx = current_entry['linenumber'] # This gives us the linenumber for the scale factor.
                str_num = current_entry['string_number'] # This is the current string for the scale factor.
                threshold = current_entry['threshold'] # This is the appropriate threshold for the given phase

                values = entry['values'] # List of the scale factors.
                name = entry['name'] # should contain the substance name with some other things like "sf_"
                entry_type = entry['type'] # Either 'off' or 'on'
                rwps = entry['rwps'] # Will be either a float for the Rwp or 'None'
                stopped = entry['stopped'] # Either True or False

                max_value = max(values) # This gets us the largest value present.
                current_value = current_entry['value'] # This gives the current value
                norm_val = current_value/max_value # This gives us the normalized value relative to the max.
                # Handle Phase ON Cases: {{{ 
                if entry_type == 'on' and on_method == 'rwp':
                    try:
                        min_rwp = min(rwps) # This will give us the min Rwp value (remember that low Rwp is good, high Rwp is bad)
                        current_rwp = current_entry['rwp'] # This gives us the current Rwp
                        rwp_pct_diff = (current_rwp - min_rwp)/min_rwp # If this is positive, that could trigger the turning on of a phase. we are not dealing with a percentage 
                        if rwp_pct_diff >= threshold and not stopped:
                            entry['stopped'] = True # We are adding the phase so we can stop monitoring
                            # IF this is the case, we have yet to enable the phase. 
                            self._modify_sf_line(out=out,line_idx=line_idx,str_num=str_num,replacement_value=on_sf_value,debug=debug) 
                            print(f'ENABLED {name}')
                        elif rwp_pct_diff < threshold:
                            # No need to add the phase
                            self.out_file_monitor[key]['rwps'].append(current_rwp) # Add the newest Rwp
                    except:
                        # This case does not need to deal with Rwps. 
                        pass
                elif entry_type == 'on' and on_method == 'time':
                    try:
                        if np.abs(current_time - threshold_for_on) <= time_error and not stopped: 
                            # This ensures that whether you are running forward or reverse direction, you can trigger at an appropriate time. 
                            entry['stopped'] = True # We are adding the phase and can stop monitoring. 
                            self._modify_sf_line(out=out,line_idx=line_idx,str_num=str_num,replacement_value=on_sf_value,debug=debug) 
                            print(f'ENABLED {name}')
                    except:
                        pass
                #}}}
                # Handle the Phase OFF Case: {{{
                elif entry_type == 'off':
                    if norm_val > threshold:
                        # This means we keep going. The scale factor hasnt fallen far enough
                        entry['values'].append(current_value)
                    elif norm_val <= threshold and not stopped:
                        entry['stopped'] = True # We are removing the phase, so stop monitoring it. 
                        # Now, DISABLE the phase: {{{
                        self._modify_sf_line(out=out,line_idx=line_idx,str_num=str_num,replacement_value=off_sf_value,debug=debug)
                        print(f'DISABLED {name}')
                        #}}} 

                #}}}

            #}}} 
        #}}} 
    #}}}
    # _parse_scale_factor_line: {{{
    def _parse_scale_factor_line(self,line:str = None, debug:bool = False):
        '''
        This function allows us to quickly parse the text in the scale factor keyword line. 
        It will find values in the form: 
        1.2233e-2
        or 
        1e-100
        '''
        number =re.findall(r'(\d+?\.\d+e?\-?\+?\d+)',line) # This will find any value that could possibly show up.
        if len(number) == 0:
            if debug:
                print(line)
            number = re.findall(r'\d?\.?\d+?',line)
        number = number[0]
        return float(number)

    #}}}
    # _modify_sf_line: {{{
    def _modify_sf_line(self, out:str = None, line_idx:int = None, str_num:str = None, replacement_value:float = None, debug:bool = False,):
        '''
        The purpose of this function is to make modifications to the scale factor line
        of an output file to either turn on or off a phase. 
        '''
        with open(out,'r') as f:
            lines = f.readlines() 
            f.close()
                        
        relevant_line = lines[line_idx] # Recall the line we stored 
                        
        relevant_line = relevant_line.replace(str_num, str(replacement_value)) # Replace the value with zero must be like this to not mess up other things.
        if 'min 0' not in relevant_line:
            relevant_line = f'{relevant_line} min 0' #this makes sure that the phase actually is disabled. 
        #relevant_line = relevant_line.replace(name, f'!{name}') # Replace the variable name with the variable name plus ! which will fix the value to zero 
        lines[line_idx] = relevant_line
        #line.replace(name,f'!{name}') # This locks the phase to 0
        if debug:
            print(f'relevant_line: {line_idx}, line to be written: {relevant_line}, TEST: {lines[line_idx]}')
        with open(out,'w') as f:
            f.writelines(lines) # Just rewrite the lines to the file 
            f.close()

    #}}}
    # _get_relevant_lines_for_monitoring: {{{ 
    def _get_relevant_lines_for_monitoring(self,out:str = None,  off_phases:list = None, on_phases:list = None, threshold_for_off:float = None, threshold_for_on:float = None, debug:bool = False):
        '''
        Since we are adding more kinds of monitoring than simply scale factor to remove a phase, 
        it seems fitting that we should create some kind of framework to make the task of accomplishing this easier.

        turning off phases is accomplished by looking at the scale factors. 
        turning on phases is accomplished by looking at the Rwp as a guide then changing scale factor.
        '''
        relevant_lines = {}
        rwp = None # This will store the Rwp for those phases we want to turn on. 
        # Open the Output File: {{{
        with open(out,'r') as f:
            lines = f.readlines()
            # Go through each of the lines: {{{
            for i, line in enumerate(lines):
                scale_kwd = re.findall(r'^\s*scale',line) # Search the output for the line pertaining to scale factor
                rwp_kwd = re.findall('r_wp\s+\d+\.\d+',line) # Search the ouput for the line pertaining to the Rwp
                if rwp_kwd:
                    rwp = float(rwp_kwd[0].split(' ')[-1]) # This should give me the rwp value
                if scale_kwd:
                    line_prms = re.findall(r'\S+',line) # This will split the line into only words and values.
                    prm_name = line_prms[1] # The second word should always be a parameter name for the scale factor.
                    str_value = line_prms[2] # The third item is the value (may include an error oo.)
                    # Handle cases where you want to turn a phase off: {{{
                    for j, off in enumerate(off_phases):
                        # assign its threshold: {{{
                        try:
                            threshold = threshold_for_off[j] # If the user gave a list of thresholds for each phase...
                        except:
                            threshold = threshold_for_off
                        #}}}
                        #define the index for the dict: {{{ 
                        if j == 0 and len(relevant_lines) == 0:
                            # This is the first entry
                            k = j
                        else:
                            k = len(relevant_lines)
                        #}}}
                        if debug: 
                            print(off.lower()) 
                            print(prm_name.lower())
                        if  off.lower() in prm_name.lower():
                            if debug:
                                print('%s Inside'%off.lower()) 
                                print('%s Inside'%prm_name.lower())
                            value = self._parse_scale_factor_line(line,debug=debug)
                            relevant_lines[k] = {
                                    'linenumber': i,
                                    'line': line,
                                    'value': value, 
                                    'name': prm_name, 
                                    'string_number':str_value,
                                    'type': 'off',
                                    'threshold': threshold,
                            }# Record the line 
                            
                            if j == len(off_phases):
                                break # If you reach the end, no point in reading more lines.
                    #}}}
                    # Handle the cases where you want to turn on a phase: {{{
                    if on_phases != None:
                        for j, on in enumerate(on_phases):
                            # Assign its threshold: {{{
                            try:
                                threshold = threshold_for_on[j]  # IF the user gave a list of thresholds
                            except:
                                threshold = threshold_for_on
                            #}}}
                            if j == 0 and len(relevant_lines) == 0:
                                k = j
                            else:
                                k = len(relevant_lines)
                            if on.lower() in prm_name.lower():
                                value = self._parse_scale_factor_line(line,debug)
                                relevant_lines[k] = {
                                    'linenumber': i, 
                                    'line': line, 
                                    'value': value, 
                                    'name':prm_name, 
                                    'string_number': str_value,
                                    'type': 'on',
                                    'threshold':threshold,
                                    'rwp':rwp,
                                } # record the line 
                                if j == len(off_phases)-1:
                                    break # IF you reach the end, stop reading
    
                    #}}}
            #}}}
            f.close()
        #}}}
        return relevant_lines
    #}}} 
#}}}
