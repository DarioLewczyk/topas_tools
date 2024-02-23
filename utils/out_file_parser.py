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
        words = list(filter(lambda x: len(x) >0,re.findall(r'\w+_?\w+',txt)))
        return(ints,floats,words)
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
                if 'str' in line and not comment_block and not skipline: # Look for the start of a structure object that is not inside of a comment block 
                    if last_phase_type != None:
                        phase_num += 1
                    last_phase_type = 'str'
                    out_phase_dict[phase_num] = {'phase_type': last_phase_type}
                    skipline = True
                 
                elif 'hkl_Is' in line and not comment_block and not skipline: # Check for the hkl_Is flag for an hkl phase. Also make sure that the phase is not inside of a comment block
                    if last_phase_type != None:
                        phase_num += 1
                    last_phase_type = 'hkl_Is'
                    out_phase_dict[phase_num] = {'phase_type': last_phase_type}
                    skipline = True
                elif 'xo_Is' in line and not comment_block and not skipline: # Check for the xo_Is flag for peaks phases. 
                    if last_phase_type != None:
                        phase_num += 1
                    last_phase_type = 'xo_Is'
                    out_phase_dict[phase_num] = {'phase_type': last_phase_type}
                    skipline = True
                elif 'C_matrix_normalized' in line or 'out' in line:
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
                    elif re.findall(r'^\s+a|^\s+b|^\s+c|^\s+al|^\s+be|^\s+ga',line):
                        #print(line)
                        words = re.findall(r'a|b|c|al|be|ga',line)
                        out_phase_dict[phase_num][words[0]] = float(floats[0])
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
                        site_args = [
                            'site', # Not important
                            'element_label', # This is the element plus an index, typically. 
                            'x', # This is the label "x"
                            'xval', # This is the value for x
                            'y', # This may not be the next value (if you have mins and maxes, they will come before this)
                            'yval', # Value for y
                            'z', # This may not be next, if mins and maxes exist,they will be before this. 
                            'zval', # value for z
                            'element', # This should be the actual element name (e.g. no number)
                            'occ', #This will be a float for the occupancy. 
                            'beq', # This may or may not be present. but is the key to look for b values
                            'beq_label', # If the next entry is a string, it is the B-value label
                            'bval', # The next thing should be the actual B value
                         
                        ]
                        #split = list(filter(lambda x: len(x) > 0, line.split(' '))) # Don't record any blank strings
                        #split = list(filter(lambda x: len(x)>1 , re.findall(r'\S+', line)))
                        split = re.findall(r'\S+',line) # This should only give strings that are not whitespace
                        x_idx = None
                        y_idx = None
                        z_idx = None
                        occ_idx = None
                        occ = None
                        beq_idx = None
                        bval_recorded = False
                        site = None 
                        #print(split)
                        for j, val in enumerate(split): 
                            #ints,floats,words = self._get_ints_floats_words(val) # This gets these quantities for the current entry.
                            if j == 1:
                                site = val # This should be the site label
                                out_phase_dict[phase_num]['sites'][site] = {}
                            if j > 1:
                                # Find KWDS: {{{
                                #val = val.strip('\t') # Get rid of tabs
                                #val = val.strip(' ') # Get rid of spaces 
                                if val == 'x':
                                    x_idx = j
                                elif val == 'y':
                                    y_idx = j
                                elif val == 'z':
                                    z_idx = j
                                elif val == 'beq':
                                    beq_idx = j
                                if val == 'occ':
                                    occ_idx = j # This is where occ is called. This means that the atom will be next then the float.
                                #}}}
                                # Record Vals: {{{
                                if x_idx:
                                    if j == x_idx+1:
                                        coord = re.findall(r'\d+\.\d+|\d+',val) # This gets the coordinate
                                        out_phase_dict[phase_num]['sites'][site].update({'x': float(coord[0])})
                                if y_idx:
                                    if j == y_idx+1:
                                        coord = re.findall(r'\d+\.\d+|\d+',val) # This gets the coordinate
                                        out_phase_dict[phase_num]['sites'][site].update({'y': float(coord[0])})
                                if z_idx:
                                    if j == z_idx+1:
                                        coord = re.findall(r'\d+\.\d+|\d+',val) # This gets the coordinate
                                        out_phase_dict[phase_num]['sites'][site].update({'z': float(coord[0])})
                                if beq_idx and not bval_recorded:
                                    # Get the variable name: {{{
                                    if j == beq_idx +1: 
                                        try:
                                            b_val_keyword = re.findall(r'\w+_\w+',val)[0] # This should find any keyword for bvals 
                                            out_phase_dict[phase_num]['sites'][site].update({'b_val_prm':b_val_keyword}) # This will record the variable. 
                                        except:
                                            out_phase_dict[phase_num]['sites'][site].update({'b_val_prm':None}) # If the previous criteria are not met, record nothing.
                                            try:
                                                bval = float(re.findall(r'\d+\.\d+|\d+',val)[0])
                                                out_phase_dict[phase_num]['sites'][site].update({'bval': bval})
                                                bval_recorded = True
                                            except:
                                                out_phase_dict[phase_num]['sites'][site].update({'bval': None})

                                    #}}}
                                    # Get the variable value: {{{
                                    elif j == beq_idx+2: 
                                        try:
                                            bval = float(re.findall(r'\d+\.\d+|\d+',val)[0]) 
                                            out_phase_dict[phase_num]['sites'][site].update({'bval': bval})
                                            bval_recorded = True
                                        except:
                                            out_phase_dict[phase_num]['sites'][site].update({'bval':None})
                                    #}}}
                                if occ_idx:
                                    if j == occ_idx+1:
                                        occ = val # This should be the atom name for the occupancy
                                    elif j == occ_idx+2:
                                        occupancy = re.findall(r'\d+\.\d+|\d+',val)
                                        out_phase_dict[phase_num]['sites'][site].update({f'{occ}_occ':float(occupancy[0])})
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
