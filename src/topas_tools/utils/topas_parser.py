# Authorship: {{{
'''
Written by Dario C. Lewczyk
Date: 01/16/2026
'''
#}}}
# Imports: {{{
import os
import re
#}}}
# TOPAS_Parser: {{{
# Do not want to have an initializer because 
class TOPAS_Parser:
    # get_lines_visible_to_topas: {{{
    def get_lines_visible_to_topas(self,lines:list = None):
        '''
        This function's purpose is to remove all comments and comment blocks from the input file
        This way we just are searching on things that are actually visible to TOPAS.
     
        it creates a dictionary so that all of the line numbers from the original file are preserved
        '''
        # we are going to remove all of the comment blocks and lines starting with comments: 
        block = False
        skip = False
        topas_lines = {} # dictionary where the keys are the original line numbers and the values are the lines 
        for i, line in enumerate(lines): 
            cleanline = line.strip()
            if cleanline.startswith('/*'):
                block = True
            if cleanline.startswith('*/'):
                block = False
            if cleanline.startswith('\''):
                skip = True
            else:
                skip = False
            if not skip and not block:
                topas_lines[i] = cleanline
        return topas_lines
    #}}}
    # parse_phase_prms: {{{
    def parse_phase_prms(self,topas_lines:dict = None, debug:bool = False):
        '''
        If run with just a single line, it returns the variable name, value, error in a tuple form. 
     
        This function takes the topas_lines dictionary: 
            This contains only lines visible to TOPAS
            The keys are the line numbers in the original file
         
        This function will search the lines of a file for the tags: 
        prm Ph1(varname) # It will be able to pull out the Ph1 and the varname 
        separately so that they can be used in building a dictionary
     
        It will also grab the values and errors for the definitions if given
        It will also grab min and max limits
     
        The code will also be aware of if the variable is fixed or not. 
     
        Along with all of this inormation, it will keep track of the line number 
        '''
        result = {}
        # RE Expressions and Patterns: {{{
        re_tag = re.compile(r"prm\s*(Ph\d+)\(\s*!?(\w+)\s*\)")
        float_re = r"[+-]?\d+(?:\.\d+)?(?:[eE][+-]?\d+)?"
    
        re_val_err = re.compile(rf"({float_re})`_({float_re})")
        re_value   = re.compile(rf"({float_re})")
        re_min     = re.compile(rf"min\s+({float_re})")
        re_max     = re.compile(rf"max\s+({float_re})")
     
        #}}}    
        # If the input data are in the form of a dictionary: {{{
        try:
            for linenumber, line in topas_lines.items():
                # Find a line for a parameter definition of Ph#: {{{
                m = re_tag.search(line)
                if not m:
                    continue
    
                phase = m.group(1)     # e.g. "Ph1"
                var   = m.group(2)     # e.g. "lp_a"
    
                if '!' in line:
                    fixed = True
                else:
                    fixed = False
    
                #}}}
                # Skip assignment lines like "= Ph1(lp_a)": {{{
                if "=" in line and "`_" not in line and "min" not in line:
                    continue
    
                if phase not in result:
                    result[phase] = {}
                #}}}
                entry = {"linenumber":linenumber, "value": None, "error": None, "min": None, "max": None, "fixed": fixed}
                # Value + Error: {{{
                ve = re_val_err.search(line)
                if ve:
                    entry["value"] = float(ve.group(1))
                    entry["error"] = float(ve.group(2))
                else:
                    # Standalone value (first float after the tag)
                    after = line[m.end():]
                    v = re_value.search(after)
                    if v:
                        entry["value"] = float(v.group(1))
                #}}} 
                # Min/ Max: {{{ 
                mn = re_min.search(line)
                if mn:
                    entry["min"] = float(mn.group(1))
    
                mx = re_max.search(line)
                if mx:
                    entry["max"] = float(mx.group(1))
                #}}}
                result[phase][var] = entry
        #}}}
        # If the input data are just a string: {{{
        except:
            m = re_tag.search(topas_lines)
         
            var = None
            value = None
            error = None
            # Find the Ph and its variable name: {{{
            if not m:
                return None
    
            phase = m.group(1)     # e.g. "Ph1"
            var   = m.group(2)     # e.g. "lp_a" 
            #}}}
            # Value + Error: {{{
            ve = re_val_err.search(topas_lines)
            if ve:
                value = float(ve.group(1))
                error = float(ve.group(2))
            else:
                # Standalone value (first float after the tag)
                after = topas_lines[m.end():]
                v = re_value.search(after)
                if v:
                    value = float(v.group(1))
            #}}}
            result = (var, value, error)
    
        #}}}
        return result
    #}}}
    # parse_specimen_displacement: {{{
    def parse_specimen_displacement(self,topas_lines:dict = None):
        '''
        Can also pass a single line if you need to. 
     
        If only a single line: returns a tuple (value, error)
     
        If a dictionary, then it returns a dictionary
        '''
        # RE Pattern: {{{
    
        float_re = r"[+-]?\d+(?:\.\d+)?(?:[eE][+-]?\d+)?"
        pattern = re.compile(
            rf"Specimen_Displacement\(\s*(@)?\s*,\s*({float_re})`_({float_re})\s*\)"
        )
        #}}}
        # If passing a dictionary: {{{
        try:
            for linenumber, line in topas_lines.items():
                m = pattern.search(line)
                if not m:
                    continue
    
                has_at = m.group(1) is not None
                value = float(m.group(2))
                error = float(m.group(3))
    
                return {
                    "linenumber": linenumber,
                    "value": value,
                    "error": error,
                    "fixed": not has_at # This reverses the bool of has_at
                }
            return None
        #}}}
        # If passing a string: {{{
        except:
            m = pattern.search(topas_lines)
            if m:
                value = float(m.group(2))
                error = float(m.group(3))
                return value, error
        #}}}
    #}}}
    # parse_output_xy: {{{
    def parse_output_xy(self,topas_lines:dict = None):
        '''
        This will parse the output xy lines so that you can make new filenames easily
     
        It will return the linenumber of the line as well as the prefix for the filename
        '''
        pattern = re.compile(
        r'Out_X_Yobs_Ycalc_Ydiff\("([A-Za-z0-9_]+)_(\d+C)_([A-Za-z0-9]+)\.xy"\)'
        )
        for linenumber, line in topas_lines.items():
            m = pattern.search(line)
            if m:
    
                return {
                    "linenumber": linenumber,
                    "line": m.group(0),
                    "prefix": m.group(1),
                    "temp": m.group(2),
                    "method": m.group(3)
                }
            else:
                continue
        return None
    #}}}
    # extract_temp_from_string: {{{
    def extract_temp_from_string(self,s:str = None):
        m = re.search(r"(\d+)C", s)
        return int(m.group(1)) if m else None
    
    #}}}
    # get_closest_entry_in_out_dict: {{{
    def get_closest_entry_in_out_dict(self, s:str = None, out_dicts:dict = None):
        '''
        s = the string temperature
        out_dicts = This is the dictionary that contains out_dicts based on the folder name
    
        This allows you to find the closest entry in the out dictionary generated by the 
        run_auto_ixpxsx_refinements() command
        '''
    
        # Build numeric temp list + mapping
        temps = sorted(extract_temp_from_string(k) for k in out_dicts.keys())
        temp_to_key = {extract_temp_from_string(k): k for k in out_dicts.keys()}
     
        # Current T
        current = extract_temp_from_string(s) # This is the current temperature
     
        # Find closest lower
        idx = bisect.bisect_left(temps, current)
        if idx == 0:
            target_temp = temps[idx]
        else:
            target_temp = temps[idx - 1] 
        return out_dicts[temp_to_key[target_temp]]
    #}}}
    # find_ixpxsx_macro_blocks: {{{
    def find_ixpxsx_macro_blocks(self, lines):
        '''
        This function is important because it matters that the WPF_IxPxSx() calls happen before the definition of the skip cases
        For this reason, we need to map out inside of the INP, where are the macros that define WPF_IxPxSx 
    
        This function will return a dictionary where the indices of the phases are the keys
    
        the entries of the dictionary are tuples: (start_idx, end_idx)
        '''
        wpf_re = re.compile(r"^\s*macro\s+WPF_[A-Za-z0-9]+_(\d+)\s*\(")
        blocks = {}
        inside = False
        start_line = None
        phase = None
    
        for i, line in enumerate(lines):
            m = wpf_re.match(line)
    
            if m:
                # This line is a WPF macro line
                p = int(m.group(1))
    
                if not inside:
                    # Start a new block
                    inside = True
                    start_line = i
                    phase = p
                else:
                    # Already inside a block
                    # If phase changes, still treat as same block
                    pass
    
            else:
                # This line is NOT a WPF macro line
                if inside:
                    # Close the block
                    blocks[phase] = (start_line, i-1)
                    inside = False
                    start_line = None
                    phase = None
    
        # If file ends while inside a block
        if inside:
            blocks[phase] = (start_line, len(lines)-1)
    
        return blocks 
    #}}}
    # parse_fit_metrics_line: {{{
    def parse_fit_metrics_line(self, topas_lines:dict):
        '''
        topas_lines:
            A dictionary of all the lines visible to TOPAS where keys are the linenumbers
    
        ALTERNATE USAGE: 
            can pass a single line if you choose
    
        This will find all of the fit metrics normally used in TOPAS and 
        throw them into a dictionary so you have them for later.
    
        '''
        result = {}
    
        pattern = re.compile(
            r'([A-Za-z_]+)\s+(-?\d+(?:\.\d+)?(?:e[+-]?\d+)?)'
        )
        # If passing topas_lines dictionary: {{{
        if type(topas_lines) == dict:
            for linenumber, line in topas_lines.items():
                if 'r_wp' in line:
                    result = {'linenumber': linenumber}
                    matches = pattern.finditer(line)
                    for m in matches:
                        key = m.group(1)
                        try:
                            value = float(m.group(2))
                            result.update({key:value})
                        except:
                            # If the value cant be a float, the loop should skip
                            continue
                     
                    return result
        #}}}
        # If just passing a single line: {{{
        else:
            matches = pattern.finditer(line)
            for m in matches:
                key = m.group(1)
                try:
                    value = float(m.group(2))
                    result.update({key:value})
                except:
                    continue
            return result
        #}}}
    #}}}
    # parse_xdd_line:{{{ 
    def parse_xdd_line(self, topas_lines:dict = None, fileextension:str = 'xy'):
        ''' 
        This function may be used on a dictionary of lines visible to TOPAS or 
        may be used on a single line
    
        This matches the call to load a pattern by TOPAS and gives the filename 
    
        returns: 
            if topas_lines == dict: 
                returns a dict where the key is 'xdd' and the entry is: {'linenumber': linenumber, 'filename', 'filename'}
    
            if topas_lines == str:
                returns the filename
        '''
        if not fileextension.startswith('.'):
            fileextension = f'.{fileextension}'
        ext = re.escape(fileextension)

        pattern = re.compile(
                rf'^\s*xdd\s+"?(?:[^"\s]*?([A-Za-z0-9._-]+{ext}))"?\s*$'
        ) 
        # if topas_lines dictionary: {{{
        if type(topas_lines) ==dict:
            for linenumber, line in topas_lines.items():
                m = pattern.match(line)
                if m:
                    filename = m.group(1) # This gives just the filename
                    return {'xdd': {'linenumber': linenumber, 'filename':filename}}
    
        #}}}
        # if topas_lines not a dictionary: {{{
        else: 
            m = pattern.match(line)
            if m:
                filename = m.group(1)
                return filename
        #}}}
    #}}} 
    # get_inp_out_dict: {{{
    def get_inp_out_dict(self, 
            lines:list = None,  
            record_phase_prms:bool = True, 
            record_xdd:bool = True,
            fileextension:str = 'xy',
            record_displacement:bool = True, 
            record_fit_metrics:bool = True,
            record_output_xy:bool = True,
            record_lines:bool = False,
            debug:bool = False):
        ''' 
        Wrapper function that returns a dictionary full of relevant information 
        for automated refinements

        This function works for BOTH INP and OUT files

        You just specify the things that you would like in the dictionary and it will return a dictionary with
        those items if you would like to customize the output 

        This function will gather all of the prms for a given phase and throw them into a dictionary 
        All linenumbers for the original .out file will also be preserved
        '''
        out_dict = {} # This is the default state for the dictionary
        
        topas_lines = self.get_lines_visible_to_topas(lines) # dictionary with keys as linenumbers and entries as lines
        # phase_prms: {{{
        if record_phase_prms:
            out_dict = self.parse_phase_prms(topas_lines, debug) # Contains all phases, variable names, and values along with linenumber and if var is refining
        #}}}
        # record_lines: {{{
        if record_lines:
            out_dict.update({'topas_lines': topas_lines}) # Record the lines 
        #}}}
        # record_displacement: {{{
        if record_displacement:
            displacement_entry = self.parse_specimen_displacement(topas_lines) # This gives us all the information for the displacement
            out_dict['Specimen_Displacement'] = displacement_entry
        #}}}  
        # record_fit_metrics: {{{
        if record_fit_metrics:
            fit_metrics = self.parse_fit_metrics_line(topas_lines) # Gets all the relevant information on the fit quality
            out_dict['fit_metrics'] = fit_metrics # Store the fit metrics
        #}}}
        # record_output_xy: {{{
        if record_output_xy:
            output_xy = self.parse_output_xy(topas_lines) # This parses the line that handles the output to XY format
            out_dict['output_xy'] = output_xy
        #}}}
        # record_xdd: {{{
        if record_xdd:
            xdd = self.parse_xdd_line(topas_lines, fileextension)
            out_dict['xdd'] = xdd
        #}}}

        return out_dict
    #}}}
    # modify_linenumber: {{{
    def modify_linenumber(self, entry:dict = None, added_lines:int = 0, modified_linenumber:bool = False, debug:bool = False):
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
            new_linenumber = linenumber += added_lines

            if debug:
                print(f'Original Line Number: {linenumber}')
                print(f'Adding {added_lines} Lines')
                print(f'Modified Line Number: {new_linenumber}')
            entry['linenumber'] = new_linenumber
            modified_linenumber = True
            
        return entry, modified_linenumber
    #}}}
#}}}
