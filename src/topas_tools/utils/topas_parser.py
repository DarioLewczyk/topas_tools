# Authorship: {{{
'''
Written by Dario C. Lewczyk
Date: 01/16/2026
'''
#}}}
# Imports: {{{
import os
import re
import bisect
#}}}
# line_parser: {{{
def line_parser(pattern, flags=0):
    regex = re.compile(pattern, flags)
    def decorator(func):
        def wrapper(self, line):
            m = regex.match(line.strip())
            if not m:
                return None
            return func(self,m)
        return wrapper
    return decorator
#}}}
# xdd_pattern: {{{ 
def xdd_pattern(ext):
    if not ext.startswith('.'):
        ext = '.' + ext
    ext = re.escape(ext)
    return rf'^\s*xdd\s+"?(?:[^"\s]*?([A-Za-z0-9._-]+{ext}))"?\s*$'
#}}}
float_re = r"[+-]?\d+(?:\.\d+)?(?:[eE][+-]?\d+)?" # Important for the specimen_displacement

# LineNumberManager:  {{{
class LineNumberManager: 
    # _inp_file_version: {{{
    _inp_file_version = 0 # This tracks when the inp file changes
    #}}}
    # _default_meta: {{{
    def _default_meta(self):
        if not hasattr(self, "_inp_file_version"):
            self._inp_file_version = 0
        return {
            "file_version": self._inp_file_version,
            "auto_update": True,
            "last_offset_applied": 0,
            "dirty": False,
        }

    #}}}
    # bump_inp_file_version: {{{
    def bump_inp_file_version(self):
        '''
        This function causes the inp file version to increase by 1
        '''
        if not hasattr(self, "_inp_file_version"):
            self._inp_file_version = 0
        self._inp_file_version += 1
    #}}}
    # walk_entries: {{{
    def walk_entries(self, out_dict):
        '''
        The purpose of this function is to be able to 
        go through a nested dictionary like my INP/OUT
        dictionaries to iterate over all the entries without 
        having to worry about nesting
        '''
        for key, val in out_dict.items():
            if isinstance(val, dict):
                # Phase dictionary
                if all(isinstance(v, dict) for v in val.values()):
                    for entry in val.values():
                        yield entry
                else:
                    # Single entry (Specimen_Displacement, output_xy, bkg, xdd)
                    yield val
    #}}}
    # apply_line_offset: {{{
    def apply_line_offset(self, entry, delta):
        '''
        This function handles updating the lines of any entry
        in the INP/OUT dictionaries
        '''
        meta = entry["_meta"]
    
        if not meta["auto_update"]:
            return
    
        # Prevent double-application
        if meta["last_offset_applied"] == delta:
            return
    
        entry["linenumber"] += delta
        meta["last_offset_applied"] = delta
        meta["dirty"] = True

    #}}}
    # resync_entry:{{{
    def resync_entry(self, entry, new_linenumber):
        '''
        Sometimes you re‑parse the file and get new line numbers.
        You want to overwrite the old ones only if auto_update is True.
        '''
        meta = entry["_meta"]
    
        if not meta["auto_update"]:
            return
    
        entry["linenumber"] = new_linenumber
        meta["file_version"] = self._inp_file_version
        meta["dirty"] = False
        meta["last_offset_applied"] = 0

    #}}}
    # freeze_updates: {{{
    def freeze_updates(self, entry):
        ''' 
        Makes sure that linenumbers are not changed
        '''
        entry['_meta']['auto_update'] = False
    #}}}
    # unfreeze_updates: {{{
    def unfreeze_updates(self, entry):
        '''
        Toggles the ability of linenumbers to be changed
        '''
        entry['_meta']['auto_update'] = True
    #}}}
    # is_stale: {{{
    def is_stale(self, entry):
        meta = entry['_meta']
        return(
            meta['file_version'] != self._inp_file_version
            or meta["dirty"]
            or meta['last_offset_applied'] != 0
        )
    #}}}
    # stale_entries: {{{
    def stale_entries(self, out_dict):
        for entry in self.walk_entries(out_dict):
            if self.is_stale(entry):
                yield entry
    #}}}
    # build_line_map: {{{
    def build_line_map(self, inp_dict):
        '''
        Gives a fast lookup for re-syncing 
        Uses dictionary keys because that is more stable.

        Build a mapping from dictionary keys to linenumbers.
        Keys are tuples like ('Ph1', 'lp_a') or ('Specimen_Displacement', None)
        '''
    
        line_map = {}
    
        for key, val in inp_dict.items():
    
            # Phase dictionary
            if key.startswith("Ph") and isinstance(val, dict):
                for var, entry in val.items():
                    line_map[(key, var)] = entry["linenumber"]
    
            # Single-entry blocks (Specimen_Displacement, bkg, xdd, output_xy)
            elif isinstance(val, dict) and "linenumber" in val:
                line_map[(key, None)] = val["linenumber"]
    
        return line_map

    
    #}}}
    # refresh_out_dict: {{{
    def refresh_out_dict(self, out_dict, inp_dict):
        '''
        This handles any drift detection for the 
        when an INP file is modified
        '''

        new_line_map = self.build_line_map(inp_dict)
    
        for key, val in out_dict.items():
    
            # Skip output_xy entirely
            if key == "output_xy" and val is not None:
                new_ln = new_line_map.get((key, None))
                if new_ln is not None and new_ln != val['linenumber']:
                    was_frozen = not val['_meta']['auto_update']
                    if was_frozen:
                        self.unfreeze_updates(val)
                    self.resync_entry(val, new_ln) # Because the inp changed, we need to update it
                    # DO NOT REFREEZE. 
                continue
    
            # Phase entries
            if key.startswith("Ph") and isinstance(val, dict):
                for var, entry in val.items():
                    new_ln = new_line_map.get((key, var))
                    if new_ln is not None and new_ln != entry["linenumber"]:
                        self.resync_entry(entry, new_ln)

            # Single-entry blocks
            elif isinstance(val, dict) and "linenumber" in val:
                new_ln = new_line_map.get((key, None))
                if new_ln is not None and new_ln != val["linenumber"]:
                    self.resync_entry(val, new_ln)
    
    
    #}}}
    # apply_added_lines: {{{
    def apply_added_lines(self, out_dict, added_lines):
        ''' 
        This replaces any linenumber += added lines logic
        '''
        for entry in self.walk_entries(out_dict):
            self.apply_line_offset(entry, added_lines)
    
    #}}}
    # _inp_fundamentally_changed: {{{
    def _inp_fundamentally_changed(self, old, new):
        '''
        This compares the template input files
        If they are different, it will return True
        and advance the counter
        '''
        for key, old_entry in old.items():
            if key == "output_xy":
                continue # Ignore this because IxPxSx can shift this. 

            new_entry = new.get(key) 

            #  We dont really care if one dictionary has more or less entries because entries are semi mutable anyway
            if old_entry is None or new_entry is None:
                continue

            # Compare the linenumbers This is the only MEANINGFUL change that we should see
            if 'Ph' in key:
                for prm, prm_entry in old_entry.items():
                    if prm_entry['linenumber'] != new_entry[prm]['linenumber']:
                        return True
                
            elif old_entry['linenumber'] != new_entry['linenumber']:
                return True

        return False

    #}}}
    # propagate_inp_file_version: {{{
    def propagate_inp_file_version(self, inp_dict):
        for entry in self.walk_entries(inp_dict):
            entry["_meta"]["file_version"] = self._inp_file_version
    #}}}
#}}}
# TOPAS_Parser: {{{
# Do not want to have an initializer because 
class TOPAS_Parser(LineNumberManager):
    # global_regex: {{{
    float_re = r"[+-]?\d+(?:\.\d+)?(?:[eE][+-]?\d+)?"
    term_re  = re.compile(rf"({float_re})(?:`_({float_re}))?")
    #}}}
    # apply_parser_over_topas_lines: {{{
    def apply_parser_over_topas_lines(self, topas_lines, parser_func):
        for lineno, line in topas_lines.items():
            result = parser_func(line)
            if result is not None:
                result['linenumber'] = lineno
                result['line'] = line
                result["_meta"] = self._default_meta()
                return result
        return None
    #}}}
    # extract_terms: {{{
    def extract_terms(self, text):
        return [
                {'value': float(v), 'error': float(e) if e else None} 
                for v, e in self.term_re.findall(text)
        ]
    #}}}
    # extract_first_float: {{{
    def extract_first_float(self, text):
        m = re.search(self.float_re, text)
        return float(m.group(0)) if m else None
    #}}}
    # extract_first_float_after_keyword: {{{
    def extract_first_float_after_keyword(self, text, keyword):
        m = re.search(rf"{keyword}\s+({self.float_re})", text)
        return float(m.group(1)) if m else None

    #}}}
    # extract_val_err: {{{
    def extract_val_err(self, text):
        m = re.search(rf'({self.float_re})`?_({self.float_re})', text)
        if m:
            return float(m.group(1)), float(m.group(2))
        return None, None
    #}}}
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
    # parse_phase_prm_line: {{{
    @line_parser(
        rf"prm\s*(?P<phase>Ph\d+)\(\s*!?(?P<var>\w+)\s*\)(?P<body>.*)$"
    )
    def parse_phase_prm_line(self, m):
        '''
        This parses a line for any phase parameters 
        If found, it will return: 
            "phase": phase,
            "var": var,
            "value": val,
            "error": err,
            "min": mn,
            "max": mx,
            "fixed": fixed,
            "is_assignment": False

        in a dictionary format
        '''
        phase = m.group("phase")
        var   = m.group("var")
        body  = m.group("body").strip()
    
        # Skip assignment lines like "=Ph1(lp_a);"
        if body.startswith("="):
            return None
    
        fixed = "!" in m.group(0)
    
        val, err = self.extract_val_err(body)
        if val is None:
            val = self.extract_first_float(body)
    
        mn = self.extract_first_float_after_keyword(body, "min")
        mx = self.extract_first_float_after_keyword(body, "max")
    
        return {
            "phase": phase,
            "var": var,
            "value": val,
            "error": err,
            "min": mn,
            "max": mx,
            "fixed": fixed,
            "is_assignment": False
        }

    #}}}
    # parse_phase_prms: {{{
    def parse_phase_prms(self, topas_lines):
        ''' 
        Simple wrapper to create a nested dictionary of 
        phases with their parameters. 
        '''
        result = {}
    
        for lineno, line in topas_lines.items():
            entry = self.parse_phase_prm_line(line)
            if entry is None:
                continue
    
            phase = entry.pop("phase")
            var   = entry.pop("var")
    
            entry["linenumber"] = lineno
            entry["line"] = line
            entry["_meta"] = self._default_meta()

            if phase not in result:
                result[phase] = {}
    
            result[phase][var] = entry
    
        return result

    #}}}
    # parse_specimen_displacement_line: {{{
    @line_parser(
        rf"""
        Specimen_Displacement
        \(
            \s*(?P<at>@)?\s*,\s*                     # optional @
            (?P<value>{float_re})                       # value
            (?:[_`]_?(?P<error>{float_re}))?            # optional error, with _ or `_ separator
            (?:\s+min\s+(?P<min>{float_re}))?         # optional min keyword + value
            (?:\s+max\s+(?P<max>{float_re}))?         # optional max keyword + value
        \)
        """,
        flags = re.VERBOSE,
    ) 
    def parse_specimen_displacement_line(self,m):
        '''
        This parser works to parse an individual line and get the parameters for specimen displacement
        '''
        value = float(m.group("value"))
        error = float(m.group("error")) if m.group("error") else None
        mn = float(m.group("min")) if m.group("min") else None
        mx = float(m.group("max")) if m.group("max") else None

        fixed = m.group("at") is None # Returns false if being refined
    
        return { 
            "value": value,
            "error": error, 
            "min": mn, 
            "max": mx,
            "fixed": fixed, # This will give us True if the @ is not present and False if it is
        } 
    #}}}
    # parse_specimen_displacement: {{{
    def parse_specimen_displacement(self,topas_lines):
        '''
        This wraps the line parser and gives us the output we want

        The linenumber and line are always included
        '''
        # loop through the topas_lines: {{{
        for lineno, line in topas_lines.items():
           entry = self.parse_specimen_displacement_line(line)
           if entry:
               entry['linenumber'] = lineno
               entry['line'] = line 
               entry['_meta'] = self._default_meta()
               return entry
        return None 
        #}}} 
    #}}}
    # parse_output_xy_line: {{{
    @line_parser(
        r'Out_X_Yobs_Ycalc_Ydiff\("(?P<prefix>[A-Za-z0-9_]+)_(?P<temp>\d+C)_(?P<method>[A-Za-z0-9]+)\.xy"\)' 
    )
    def parse_output_xy_line(self, m):
        '''
        This parses a line from an input file and finds the filename you wish to write to
        '''
        prefix = m.group('prefix')
        temp = m.group('temp')
        method = m.group('method')
        return {
                'prefix':prefix,
                'temp':temp,
                'method':method,
        }
    #}}}
    # parse_output_xy: {{{
    def parse_output_xy(self,topas_lines):
        '''
        This function will use the topas_lines dictionary and return a dictionary 
        which contains the information necessary to change the filename as well as 
        the linenumbers and line itself
        '''
        for lineno, line in topas_lines.items():
            entry = self.parse_output_xy_line(line)
            if entry:
                entry['linenumber'] = lineno
                entry['line'] = line
                entry['_meta'] = self._default_meta()
                return entry
        return None
    #}}}
    # parse_fit_metrics_line: {{{
    def parse_fit_metrics_line(self, line):
        '''
        Use the signature of the fit metrics line to get 
        all the fit metrics
        ''' 
        result = {}
        pattern = re.compile(
            r'([A-Za-z_]+)\s+(-?\d+(?:\.\d+)?(?:e[+-]?\d+)?)'
        )
        if 'r_wp' in line:
            matches = pattern.findall(line)
            if not matches:
                return None
            for key, value in matches:
                result[key] = float(value)
            return result

        else:
            return None
        #}}} 
    # parse_bkg_line: {{{
    @line_parser(rf"^bkg\s*(?P<at>@)?\s*(?P<body>.*)$", flags=re.IGNORECASE) # Throw the match criteria to the wrapper
    def parse_bkg_line(self, m):
        ''' 
        Takes the m output of the line_parser. 

        This matches the bkg pattern in TOPAS and will return a dictionary containing the following: 
            linenumber: linenumber in the inp where the lines are
            line: the full line that can be dropped into a new refinement
            val_#: The value for each item in the bkg
            err_#: The error for each item in the bkg
        '''
        # get the information from the match: {{{
        has_at = m.group('at') is not None
        body = m.group('body') # This gives all the individual values and errors

        terms = self.extract_terms(body)
        #}}}
        return {
                'fixed': not has_at,
                'terms': terms,
        }
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
                    return {
                        'linenumber': linenumber, 
                        'filename':filename, 
                        'line': line,
                        '_meta': self._default_meta()
                    }
    
        #}}}
        # if topas_lines not a dictionary: {{{
        else: 
            m = pattern.match(line)
            if m:
                filename = m.group(1)
                return filename
        #}}}
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
        temps = sorted(self.extract_temp_from_string(k) for k in out_dicts.keys())
        temp_to_key = {self.extract_temp_from_string(k): k for k in out_dicts.keys()}
     
        # Current T
        current = self.extract_temp_from_string(s) # This is the current temperature
     
        # Find closest lower
        idx = bisect.bisect_left(temps, current)
        if idx < len(temps) and temps[idx] == current:
            target_temp = temps[idx] # exact match
        elif idx == 0:
            target_temp = temps[0] # match the zeroth
        else:
            # If this is the case, it matches the closest one to the left
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
    # get_inp_out_dict: {{{
    def get_inp_out_dict(self, 
            lines:list = None,  
            record_phase_prms:bool = True, 
            record_xdd:bool = True,
            record_bkg:bool = True,
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
            phase_prms = self.parse_phase_prms(topas_lines)
            for key, entry in phase_prms.items():
                out_dict.update({key:entry}) # Contains all phases, variable names, and values along with linenumber and if var is refining
            #if debug:
            #    print(f'Phase Prms: {phase_prms}')
        #}}}
        # record_displacement: {{{
        if record_displacement:
            displacement_entry = self.apply_parser_over_topas_lines(topas_lines, self.parse_specimen_displacement_line)
            out_dict['Specimen_Displacement'] = displacement_entry
            #if debug:
            #    print(f'Displacement Entry: {displacement_entry}')
        #}}}  
        # record_fit_metrics: {{{
        if record_fit_metrics:
            fit_metrics = self.apply_parser_over_topas_lines(topas_lines, self.parse_fit_metrics_line)
            out_dict['fit_metrics'] = fit_metrics # Store the fit metrics
            #if debug:
            #    print(f'Fit Metrics: {fit_metrics}')
        #}}}
        # record_output_xy: {{{
        if record_output_xy:
            output_xy = self.apply_parser_over_topas_lines(topas_lines, self.parse_output_xy_line)
            out_dict['output_xy'] = output_xy
            #if debug:
            #    print(f'Output XY: {output_xy}')
        #}}}
        # record_xdd: {{{
        if record_xdd:
            xdd = self.parse_xdd_line(topas_lines, fileextension)
            out_dict['xdd'] = xdd
            #if debug:
            #    print(f'XDD: {xdd}')
        #}}}
        # record bkg: {{{
        if record_bkg:
            bkg = self.apply_parser_over_topas_lines(topas_lines, self.parse_bkg_line)
            out_dict['bkg'] = bkg
            #if debug:
            #    print(f'BKG: {bkg}')
        #}}}
        # record_lines: {{{
        if record_lines:
            out_dict.update({'topas_lines': topas_lines}) # Record the lines 
        #}}}

        return out_dict
    #}}}
#}}}
