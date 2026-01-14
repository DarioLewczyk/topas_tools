# Authorship: {{{
# Written by: Dario Lewczyk
# Date: 02/20/2024
#}}}
# Imports: {{{
import re
#}}}
# OUT_Parser: {{{
class OUT_Parser:
    '''
    This class has all of the tools necessary to find relevant 
    information to Rietveld refinement inside of TOPAS .out files
    '''
    # __init__:{{{ 
    def __init__(self):
        pass
    #}}} 
    #_get_ints_floats_words: {{{
    def _get_ints_floats_words(self,txt:str = None): 
        '''
        This function just returns 3 lists after doing a re search for
        integers
        floats
        words
        Returns a 3 tuple of the lists
     
        Use the lambda function to pre-screen the returns to exclude blanks
        '''
        ints = list(filter(lambda x: len(x) >0,re.findall(r'\d+', txt)))
        floats = list(filter(lambda x: len(x) >0,re.findall(r'\d+\.\d+e?\-?\d+',txt)))
        words = list(filter(lambda x: len(x) >0,re.findall(r'\w+[_\w+]?',txt)))
        return(ints,floats,words)
    #}}}
    # _extract_site_name {{{
    def _extract_site_name(self, site_string:str = None):
        '''
        This function will get the name of the site
        '''
        match = re.search(r"\bsite\s+(\w+)", site_string)
        return match.group(1) if match else None

    #}}}
    # _extract_site_kw_vals: {{{
    def _extract_site_kw_vals(self, site_string:str = None):
        ''' 
        This function takes a TOPAS style site string and 
        will return the values for each of the keywords: 
            x, y, z, occ, beq
        '''
        keywords = {"x", "y", "z", "occ", "beq"}
        tokens = site_string.split()
        result = {}
        i = 0
        # Step 1: Get a dict with all the matches for the values: {{{
        while i < len(tokens):
            token = tokens[i]
            if token in keywords:
                i += 1
                while i < len(tokens):
                    current = tokens[i]
                    # Skip equations, symbols, and variable names
                    if any(c in current for c in "=@*;:") or not any(char.isdigit() for char in current):
                        i += 1
                        continue
                    # Match float integer or composite value
                    if re.match(r"\d+(?:\.\d+)?(?:'_?\d+(?:\.\d+)?)?", current):
                        result.setdefault(token, []).append(current)
                        break
                    i += 1
            else:
                i += 1
        #}}}
        # Step 2: Return the dict with the values: {{{
        final_result = {}
        for key, value in result.items():
            ints, floats, _ = self._get_ints_floats_words(value[0]) # This takes the match and feeds it into this parser which will find all the ints floats and so on.
            # Get the value or refined value: {{{
            try:
                final_result[key] = float(floats[0])
            except:
                final_result[key] = float(ints[0]) # If the user passes a single integer for something like "occ"
            #}}} 
            # Get the errors (if any): {{{
            try:
                final_result[f'{key}_err'] = float(floats[1])
            except:
                final_result[f'{key}_err'] = None
            #}}}
        #}}}
        return final_result
    #}}}
    # _parse_out_phases: {{{
    def _parse_out_phases(self,out_file:str = None, idx:int = None):
        '''
        This function is able to read in output files in a general manner and update a dictionary 
        called "out_phase_dict" as an attribute. 
        The function takes an output file to read. 
        

        The way that the dictionary produced is formatted is as follows: 
        
        '''
        out_phase_dict = {} # Initialize the current pattern output file dictionary
        with open(out_file,'r') as out:
            lattice_macros = ['Cubic', 'Tetragonal', 'Hexagonal', 'Rhombohedral']
            lattice_macro_keys = [
                ['a'], # Cubic
                ['a', 'c'], # Tetragonal
                ['a', 'c'], # Hexagonal
                ['a', 'ga'], # Rhombohedral
            ]
            lines = out.readlines()
            phase = None
            comment_block = False # This tracks if the program sees a comment block to ignore all text between the two lines. 
            phase_num = 0 # This counts all of the str, hkl_Is, xo_Is
            last_phase_type = None # This will keep track of the 
            end_of_out = False # This will change to True when it finds "C_matrix_normalized"
            for i, line in enumerate(lines):
                skipline = False # This is to skip over the end of comment blocks and str, hkl_Is, xo_I lines.
                # Check for early items like Rwp: {{{
                if 'r_wp' in line:
                    items = re.findall(r'r_wp\s+\d+\.\d+',line)
                    if items:
                        line = items[0] #This gives us the R_wp separated by whitespace
                        rwp = float(line.split(' ')[-1])
                        out_phase_dict['rwp'] = rwp
                #}}}
                # Check for Comments: {{{
                if '\'' in line: # Search for comment indicator
                    splitline = line.split("'")# splits the line based on the presence of a single quote.
                    if len(splitline) >1: 
                        line = splitline[0] # This redefines the line as the line without the comment. 
                elif "/*" in line: # Look for start comment block
                    comment_block = True # This marks the start of a comment block
                elif "*/" in line:# Look for end comment block
                    comment_block = False # This marks the end of a comment block
                    skipline = True
                #}}}
                # Start by finding a structure: {{{
                bareline = line.strip()
                if bareline.startswith('str') and not comment_block and not skipline: # Look for the start of a structure object that is not inside of a comment block 
                    if last_phase_type != None:
                        phase_num += 1
                    last_phase_type = 'str'
                    out_phase_dict[phase_num] = {'phase_type': last_phase_type}
                    skipline = True
                 
                elif bareline.startswith('hkl_Is') and not comment_block and not skipline: # Check for the hkl_Is flag for an hkl phase. Also make sure that the phase is not inside of a comment block
                    if last_phase_type != None:
                        phase_num += 1
                    last_phase_type = 'hkl_Is'
                    out_phase_dict[phase_num] = {'phase_type': last_phase_type}
                    skipline = True
                elif bareline.startswith('xo_Is') and not comment_block and not skipline: # Check for the xo_Is flag for peaks phases. 
                    if last_phase_type != None:
                        phase_num += 1
                    last_phase_type = 'xo_Is'
                    out_phase_dict[phase_num] = {'phase_type': last_phase_type}
                    skipline = True
                elif bareline.startswith('C_matrix_normalized') or 'out' in line:
                    end_of_out = True # This stops recording
                 
                #}}}
                # Add the phase data: {{{
                if not comment_block and last_phase_type != None and not end_of_out and not skipline: # This will record values ONLY if we have not reached the C_matrix, are not in a comment block, or are inside of a phase.
                    
                    ints,floats,words = self._get_ints_floats_words(line) # This is used a lot, so let's just use it here. 
                    # Phase Name: {{{
                    if 'phase_name' in line:
                        split = re.findall(r'\w+',line)
                        key = split[0] # This is the label
                        value = '_'.join(split[1:]) # This is the phase name
                        out_phase_dict[phase_num].update({key:value})
                    #}}}
                    # Phase MAC: {{{
                    elif 'phase_MAC' in line:
                        split = re.findall(r'\d+\.\d+',line)[0]
                        key = 'phase_MAC'
                        value = float(split)
                        out_phase_dict[phase_num].update({key:value})
                    #}}}
                    # LVol FWHM CS G L: {{{
                    elif 'LVol_FWHM_CS_G_L' in line:
                        #key = 'LVol_FWHM_CS_G_L'
                        #out_phase_dict[phase_num][key] = {}
                        split = line.split(',')
                        macro_vars = ['k', 'lvol', 'kf', 'lvolf', 'csgc', 'csgv', 'cslc', 'cslv'] # These are the parameters that are separated by commas for this macro. 
                        # Find what value to record: {{{
                        for j, value in enumerate(split):
                            macro_var = macro_vars[j] # This tells the program what to look for
                            rec = None # This is the default value to record for the macro var key
                            ints,floats,words = self._get_ints_floats_words(value)
                         
                            if macro_var == 'k' or macro_var == 'kf' or macro_var == 'lvol' or macro_var == 'lvolf' or macro_var == 'csgv' or macro_var == 'cslv': # Numerical variables
                                if ints and not floats:
                                    rec = int(ints[0])
                                elif floats:
                                    rec = float(floats[0])
                            elif macro_var == 'csgc' or macro_var == 'cslc': # String variables
                                if words:
                                    rec = words[0] # This takes the string
                            out_phase_dict[phase_num].update({macro_var: rec})
                        #}}}    
                    #}}}
                    # e0_from_Strain: {{{
                    elif 'e0_from_Strain' in line:
                        #key = 'e0_from_Strain'
                        pattern = r'=\s*If\([^)]*\);\:' # This will match an if statement if you use one. 
                        if_stmt = re.search(pattern, line) 
                        
                        if if_stmt:
                            clean_line = re.sub(pattern, '', line)
                            line = clean_line # replace the line to get rid of the if
                        split = line.split(',')
                        macro_vars = ['e0', 'sgc', 'sgv','slc', 'slv'] # These are the parameters separated by commas for this macro
                        # Figure Out what needs to be recorded: {{{
                        for j, value in enumerate(split):
                            macro_var = macro_vars[j] # Tells the program what to look for. 
                            rec = None
                            ints,floats,words = self._get_ints_floats_words(value)
                            if macro_var == 'e0' or macro_var == 'sgv' or macro_var == 'slv': 
                                if ints and not floats:
                                    rec = int(ints[0])
                                elif floats:
                                    rec = float(floats[0])
                            elif macro_var == 'sgc' or macro_var == 'slc': 
                                try:
                                    rec = words[0]
                                except:
                                    rec = None

                            out_phase_dict[phase_num].update({macro_var:rec})
                        #}}}
                    #}}}
                    # Get lattice parameters if not in a macro: {{{
                        
                    elif re.findall(r'^\s*a\b|^\s*b\b|^\s*c\b|^\s*al\b|^\s*be\b|^\s*ga\b',line):
                        try:
                            words = re.findall(r'a|b|c|al|be|ga',line)
                            out_phase_dict[phase_num][words[0]] = float(floats[0])
                        except:
                            print(f'{i}: {line}')
                            print(f'Failed at getting {words} to have a value! for {phase}')
                    #}}}
                    # MVW: {{{
                    elif 'MVW' in line:
                        split = line.split(',')
                        macro_vars = ['m_v','v_v','w_v'] # This is the mass value, volume value, weight value.
                        for j, value in enumerate(split):
                            ints,floats,words = self._get_ints_floats_words(value)
                            macro_var = macro_vars[j] # This is the current macro variable to look for. 
                            rec = None
                            if floats:
                                rec = float(floats[0]) # This should give me the calculated value
                            out_phase_dict[phase_num].update({macro_var:rec}) # This records the macro value

                    #}}}
                    # Getting Peter's strain correction (lorentzian): {{{  
                    elif 'strain_isoL' in line:  
                        ints, floats, words = self._get_ints_floats_words(line)
                        if floats:
                            rec = float(floats[0]) # This is the calculated value
                            #rec_err = float(floats[1]) # This should be the error
                        out_phase_dict[phase_num].update({'strain_isoL':rec})
                    #}}}
                    # Getting Peter's strain correction (gaussian): {{{ 
                    elif 'strain_isoG' in line: 
                        ints, floats, words = self._get_ints_floats_words(line)
                        if floats:
                            rec = float(floats[0]) # This is the calculated value
                            #rec_err = float(floats[1]) # This should be the error
                        out_phase_dict[phase_num].update({'strain_isoG':rec})
                    #}}}

                    # Get the cell mass: {{{
                    elif 'cell_mass' in line: 
                        out_phase_dict[phase_num]['cell_mass'] = float(floats[0])
                    #}}}
                    # Get the volume: {{{
                    elif 'volume' in line:
                        out_phase_dict[phase_num]['volume'] = float(floats[0])
                    #}}}
                    # Get the weight percent: {{{
                    elif 'weight_percent' in line: 
                        out_phase_dict[phase_num]['weight_percent'] = float(floats[0])
                    #}}}
                    # Get R_Bragg: {{{
                    elif 'r_bragg' in line:
                        out_phase_dict[phase_num]['r_bragg'] = float(floats[0])
                    #}}}
                    # Get space_group: {{{
                    elif 'space_group' in line:
                        sg = re.findall(r'\w+\d?\/?\w+',line)
                        out_phase_dict[phase_num]['space_group'] = sg[-1]
                    #}}}
                    # Parse Sites: {{{
                    elif 'site' in line.lower(): 
                        if 'sites' not in list(out_phase_dict[phase_num].keys()):
                            out_phase_dict[phase_num]['sites'] = {} # Initialize a bin to hold these data.
                        # step 1: Find out what the site name is: {{{
                        site_name = self._extract_site_name(line) # This will get the site name (e.g. Ti or Ti1)
                        _ , _, words = self._get_ints_floats_words(site_name)
                        try:
                            atom_name = words[0] # This is the atom for the site
                        except:
                            atom_name = None
                        #}}} 
                        # step 2: Get the values for the kwargs: {{{
                        site_val_dict = self._extract_site_kw_vals(line) # This returns a dict with keys of the kwargs 
                        #}}}
                        # Update the site dictionary: {{{
                        out_phase_dict[phase_num]['sites'][site_name] = {'atom_name': atom_name} # Initialize the sub dictionary for the site
                        for key, value in site_val_dict.items():
                            out_phase_dict[phase_num]['sites'][site_name].update({key: value})
                        #}}}

                    #}}}
                    # Parse TOPAS Scale: {{{
                    elif 'scale ' in line: 
                        #If the e isnt in the float, that means that we are dealing with a replacement that doesnt have a decimal point before the e so it isnt matching. 
                        # This has been thoroughly validated
                        floats = re.findall(r'\d+\.?\d+?e\-?\d+|\d+\.?e\-?\d+',line)  
                        out_phase_dict[phase_num][words[1]] = float(floats[0]) # The scale factor will be the first item in the list of floats here.
                 
                    #}}}
                    # Parse user-defined Scale Factors: {{{
                    elif 'scale_factor' in line: 
                        # It is possible that this will be 0.0000 which may not match nicely. Regardless since this is calculated by TOPAS, it should have more 
                        # than 1 digit past the decimal. 
                        # The line below will only default to looking for something like 0.0000 if it is unable to find something matching the format: 
                        
                        floats = re.findall(r'\d+\.\d+e\-?\d+|\d+\.\d+',line) 
                        if words[0] == 'prm':
                            words[0] = words[1]
                        out_phase_dict[phase_num]['scale_factor'] = float(floats[0]) # We are using the second match here because I am dividing by 1e-7 everytime and that is going to be the first match.
                        out_phase_dict[phase_num]['usr_sf_name'] = words[0]
                 
                    #}}}
                    # Parse Phase_LAC_1_on_cm and Phase_Density_g_on_cm3: {{{
                    elif 'Phase_LAC_1_on_cm' in line or 'Phase_Density_g_on_cm3' in line:
                        floats = list(float(x) for x in floats)
                        out_phase_dict[phase_num][words[0]] = floats
                    #}}}
                    # If you Need anything else, UNCOMMENT PRINT HERE TO FIGURE OUT HOW TO ADD IT: {{{
                    else:
                        #print(i,line)
                        pass
                    #}}} 
                    # Check for lattice parameters: {{{
                    for j, latt in enumerate(lattice_macros):
                        if latt in line:
                            splitline = line.split(',')
                            for k, value in enumerate(splitline):
                                ints,floats,words = self._get_ints_floats_words(value)
                                out_phase_dict[phase_num][lattice_macro_keys[j][k]] = float(floats[0])
                     
                    #}}}
                #}}}
        return out_phase_dict
    #}}}
#}}}
