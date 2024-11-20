# Authorship: {{{
# Written by: Dario Lewczyk
# Date: 02-20-2024
#}}}
# Imports: {{{
import re
import sys
import numpy as np

#}}}
# ResultParser: {{{
class ResultParser:
    '''

    This class is used to parse the results of Rietveld
    refinement including: 
    .xy
    .csv
    .hkli 
    '''
    # __init__: {{{
    def __init__(self,):
        pass
    #}}}
    # _replace_nan_with_previous: {{{
    def _replace_nan_with_previous(self,):
        '''
        This function is designed to replace the 1.QNAN0 values
        with the last valid value for parse_xy
        '''
        last_valid = [None]*4 # Assumes 4 column data are being imported
        def converter(val, col):
            nonlocal last_valid
            try:
                float_val = float(val)
                last_valid[col] = float_val
                return float_val
            except ValueError:
                return last_valid[col] if last_valid[col] is not None else 0
        return converter
    #}}}
    # _parse_xy: {{{
    def _parse_xy(self,xy_file:str = None,delimiter:str = ',', skiprows:int = 0):
        '''
        This function returns a tuple of all of the information your xy file should have

        Sometimes TOPAS may output a string called "1.#QNAN0" which will essentially break this function. 
        By default, this function will replace it with the last valid value.
        '''
        try:
            xy_data = np.loadtxt(xy_file, delimiter=delimiter, skiprows=skiprows) # imports the xy data to an array 
        except:
            converters = {i: lambda val, col=i: self._replace_nan_with_previous()(val,col) for i in range(4)}
            xy_data = np.genfromtxt(xy_file, delimiter=delimiter, converters=converters, autostrip=True, invalid_raise=False, skip_header = skiprows) # imports the xy data to an array 
        tth = xy_data[:,0]
        yobs = xy_data[:,1]
        try:
            ycalc = xy_data[:,2]
            ydiff = xy_data[:,3]
        except:
            ycalc = None
            ydiff = None
           
        return (tth, yobs, ycalc, ydiff)

    #}}}
    # _parse_c_matrix: {{{
    def _parse_c_matrix(self, 
            out_file:str = None,
            correlation_threshold:int = None, 
            ):
        '''
        The purpose of this function is to automatically generate a dictionary
        for the user to quickly view the c matrices for any of the refined patterns.  
        We want to also have each of the correlations be clearly labeled.
        '''
        c_matrix = {} # This is the matrix object we create
        c_matrix_lines = []
        c_matrix_var_names = [] # We want to correlate the variable names with the correlation values
        # Get the rows of the matrix: {{{
        with open(out_file,'r') as out:
            lines = out.readlines()
            c_mat_line = None
            for i, line in enumerate(lines):
                if 'C_matrix_normalized' in line: 
                    c_mat_line = i
                if c_mat_line:
                    if i > c_mat_line:
                        # At this point, we have passed the point of introduction of the matrix. 
                        splitline = line.split(' ') # The vars and numbers are separated by whitespace
                        corrected_line = [] # We need to do some post-processing before we pass the lines onward.
                        if len(splitline) > 1 and '\n' not in splitline:
                            # This check ensures we do not get unimportant lines.
                            for l in splitline:
                                if l != '':
                                    corrected_line.append(l) # Add only non-blank entries
                            c_matrix_lines.append(corrected_line)
                            #print(i,corrected_line)
            out.close() # We are done with the file now. 
        #}}}
        # Generate the C matrix Object: {{{
        if c_matrix_lines:
            for i, row in enumerate(c_matrix_lines):
                if i == 0:
                    # The first entry should be the top row of the matrix with variable indices.
                    ints = np.loadtxt(row)
                    #print(ints)
                    #print(len(ints))
                    for num in ints:
                        c_matrix[int(num)] = {} # Initialize the entry
                else:
                    # Get the Var names and Numbers: {{{
                    var_name = row[0]
                    c_matrix_var_names.append(var_name) # Store the name
                    var_num = int(row[1].strip(':')) # The number correlated to the variable name is recorded next
                    # Update the C Matrix: 
                    c_matrix[var_num].update({
                        'name': var_name,
                        'correlations':{},
                    })
                    #}}}
                    # GET Correlations: {{{
                    numbers = row[2:]
                    fixed_numbers = []
                    for v in numbers: 
                        combined_num = re.findall(r'\D?\d+',v) # This gets any digit (either positive or negative) and can split combined numbers
                        if combined_num:
                            fixed_numbers.extend(combined_num) # This adds the positive and negative numbers
                    correlations = np.loadtxt(fixed_numbers)
                    #print(len(correlations))
                    #}}}
                    # UPDATE THE MATRIX: {{{
                    for j, v in enumerate(correlations):
                        j = j+1 # This brings the variable numbers in line with the correlations
                        c_matrix[var_num]['correlations'].update({
                            j:v
                        })
                    #}}}
        #}}}
        # Update the correlations with the names of the variables: {{{ 
        for i in c_matrix:
            entry = c_matrix[i]
            correlations = entry['correlations']
            for j in correlations:
                correlation = correlations[j]
                # Get correlation Flags: {{{
                if correlation_threshold:
                    if correlation > correlation_threshold or correlation < -1*correlation_threshold:
                        flag = 'CHECK'
                    else:
                        flag = 'OK'
                else:
                    flag = 'N/A'

                #}}}
                correlations[j] = {
                        'name': c_matrix_var_names[j-1], # Need the index, so j-1
                        'correlation': correlation,
                        'flag':flag,
                }

        #}}}
        return c_matrix
    #}}}
    # _get_correlations: {{{
    def _get_correlations(self, c_matrix:dict = None, flag_search:str = 'CHECK',debug:bool = False):
        '''
        pattern_idx: This is the pattern number you want to investigate
        flag_search: This is the flag to find under the correlations dictionary.

        corr_dict: This is a clearer filtered dictionary of correlations
        '''
        corr_dict = {} 
        if type(c_matrix) == None:
            print('No C Matrix Present.')
            sys.exit() 
        else:
            # Find the correlations matching your search flag: {{{ 
            for i in c_matrix:
                cent = c_matrix[i]
                name1 = cent['name']
                corr_dict.update({
                    i: {name1: {}},
                })
                correlations = cent['correlations']
                if debug:
                    print(f'{i}: {name1}')
                for j in correlations:
                    corrent = correlations[j]
                    correlation = corrent['correlation']
                    name2 = corrent['name']
                    flag = corrent['flag']
                    if flag == flag_search and name1!= name2:
                        corr_dict[i][name1].update({
                            j:{name2:correlation} 
                        })
                        if debug:
                            print(f'\t{j} ({name2}): {correlation}')
                if corr_dict[i][name1] == {}:
                    corr_dict.pop(i) # If there is only one value, it is the value itself. 
            #}}} 
        return corr_dict
    #}}}
    # _parse_hkli: {{{
    def _parse_hkli(self,hkli_file:str = None,sort_hkli:bool = False):
        '''
        This allows us to parse files created by TOPAS6 using the: Create_hklm_d_Th2_Ip_file() macro
        format of data: 
            0: h
            1: k
            2: l
            3: multiplicity
            4: d-spacing
            5: 2 theta
            6: Intensity
        This will create a tuple from hkl

        If you want to have the hkli sorted by tth, you can but it significantly slows processing.
        ''' 
        try:
            hkli_data = np.loadtxt(hkli_file) # This gives us our data in an array. Now just need to parse it.  
            # assign the columns to variables: {{{
            h = hkli_data[:,0]
            k = hkli_data[:,1]
            l = hkli_data[:,2]
            m = hkli_data[:,3]
            d = hkli_data[:,4]
            tth = hkli_data[:,5]
            intensity = hkli_data[:,6]
            #}}}
            # Group hkl into a tuple: (h,k,l):{{{
            hkl = [(int(h[i]), int(k[i]), int(l[i])) for i, v in enumerate(hkli_data)]
            #}}}
            # Sort by 2theta: {{{
            if sort_hkli:
                sorted_tth = sorted(tth) # This creates a separate list that is sorted from low to hi tth
                j = list(tth) # Cast tth as a list so we can use the index functionality to sort the other arrays
                sorted_hkl = []
                sorted_m = []
                sorted_d = []
                sorted_i = []
                for val in sorted_tth:
                    sorted_hkl.append(hkl[j.index(val)])
                    sorted_m.append(m[j.index(val)])
                    sorted_d.append(d[j.index(val)])
                    sorted_i.append(intensity[j.index(val)])
            
                tth = sorted_tth
                hkl = sorted_hkl
                m = sorted_m
                d = sorted_d
                intensity = sorted_i
            #}}}
            # update the hkli out: {{{
            hkli_out = {
                'hkl':hkl,
                'm': m,
                'd':d,
                'tth':tth,
                'i':intensity,
            }
            #}}} 
        except:
            print(f'There was a problem with the hkli file: {hkli_file}')
            hkli_out = {
                    'hkl': [0],
                    'm': [0],
                    'd': [0],
                    'tth':[0],
                    'i': [0],
            }
        return hkli_out

    #}}} 
#}}}
