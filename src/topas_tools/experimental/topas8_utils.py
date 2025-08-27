# Authorship: {{{
''' 
Written by: Dario C. Lewczyk
Date: 01-22-25
Purpose: Parse Peter's output and ingest and process data from TOPAS8 through python

Since TOPAS8 is not fully released at this time and these things are subject to change, they will remain in the experimental 
module of topas_tools
'''
#}}}
# imports: {{{
from topas_tools.plotting.plotting_utils import GenericPlotter as gp
import os
from glob import glob
import numpy as np
import plotly.graph_objects as go
import pandas as pd
from scipy.optimize import minimize
plt = gp()
#}}}
# Basic functions{{{ 
# parse_xy: {{{
def parse_xy(fn):
    xy = np.loadtxt(fn,delimiter=',')
    tth = xy[:,0]
    yobs = xy[:,1]
    ycalc = xy[:,2]
    ydiff = xy[:,3]
    return tth, yobs, ycalc, ydiff
#}}}
#go_to_dir: {{{
def go_to_dir(base_folder, subfolder_idx, subfolders:list = ['IPS', 'xPS', 'xPx', 'IPx']):
    
    new_dir = os.path.join(base_folder, subfolders[subfolder_idx])
    if os.path.exists(new_dir):
        os.chdir(new_dir)
    else:
        print(f'No path: {new_dir}')
#}}}
# make_hovertemplate: {{{
def make_hovertemplate(xs, ys, yerrs, hs, ks, ls,  labels = ['s (nm^-1)', 'IZTF IB']):
    hts = []
    for i, y in enumerate(ys):
        x = np.around(xs[i],4)
        yerr = np.around(yerrs[i], 4)
        y = np.around(y, 4)
        h = int(hs[i])
        k = int(ks[i])
        l = int(ls[i])
        hts.append(f'hkl: ({h},{k},{l})<br>{labels[0]}: {x}<br>{labels[1]}: {y} ± {yerr}<br>'+'y: %{y}')
    return hts
#}}}
# go_to_dir_and_get_xy: {{{
def go_to_dir_and_get_xy(base_folder, subfolder_idx, subfolders:list = ['IPS', 'xPS', 'xPx', 'IPx']):
    go_to_dir(base_folder, subfolder_idx, subfolders)
    xy_file = glob('*.xy')[0] # Get the xy file
    return parse_xy(xy_file)
#}}}
# get_profile_data: {{{
def get_profile_data(directories:list = None, num_subdirs:int = 4, subdirs:list = ['IPS', 'xPS', 'xPx', 'IPx']):
    ''' 
    This function gives a dictionary with nice labels 
    to separate each of the files nicely for you.

    It also automatically calculates the error for IBs by using the 
    TOPAS calculated error for IBd
    '''
    profile_data = {} # This will house the profile data. 
    # Import the data from the file as is: {{{
    for base_dir in directories:
        previous_dir = os.getcwd()
        for idx in range(num_subdirs):
            try:
                go_to_dir(base_dir, idx, subdirs)
                if os.getcwd() != previous_dir:
                    previous_dir = os.getcwd()
                else:
                    break

                method = os.path.basename(os.getcwd())
                base = os.path.basename(base_dir)
                identifier = '_'.join([base,method]) # This is the identifier that gets added to the name of the file and the column headers.
             
                profile_data[identifier] = {} # Initialize a dictionary for the specific identifier.
     
                out_files = glob('*.out')
                profile = [f for f in out_files if '_profiles.out' in f][0] # This specifies the unmodified file. 
                with open(profile, 'r') as f:
                    header_line = f.readlines()[0].strip('\n').strip('').strip(' ').split(',') # This makes a list of just the header words.
                    loaded_data = np.loadtxt(profile, skiprows=1, delimiter=',') # Should load the numerical data
                    for i, header in enumerate(header_line):
                        profile_data[identifier][header.strip(' ')] = loaded_data[:,i]
                f.close()
            except:
                break
    #}}} 
    # Calculate the errors + Get Hovertemplates: {{{
    for identifier, entry in profile_data.items():
        for key, arr in entry.items():
            if key == 'IZTF_IBs_e':
                IZTF_IBs_e = (entry['IZTF_IBd_e']/entry['IZTF_IBd']) * entry['IZTF_IBs'] # Calculate a scale factor for calculating the IBs errors
                profile_data[identifier][key] = IZTF_IBs_e
            if key == 'hkl':
                hkls = []
                for i, v in enumerate(arr):
                    h = int(entry['H'][i])
                    k = int(entry['K'][i])
                    l = int(entry['L'][i])
                    hkls.append(f'{h}_{k}_{l}')
                profile_data[identifier][key] =np.array( hkls) # This fixes the hkls to be strings again
        # Make hovertemplates: {{{ 
        hs = entry['H']
        ks = entry['K']
        ls = entry['L']
        s = entry['s_nm']
        iztf = entry['IZTF_IBs']
        iztf_e = entry['IZTF_IBs_e']
        ht = make_hovertemplate(s, iztf, iztf_e, hs, ks, ls) # Gives a full list of hovertemplates
        profile_data[identifier]['hovertemplate'] = np.array(ht)
        #}}} 
    #}}}
    return profile_data
#}}}
# filter_by_duplicate_s: {{{ 
def filter_by_duplicate_s(data_dict:dict):
    '''
    This function will search the data dictionary for 
    duplicates in the s_nm array. If it finds one, then it will remove the data
    associated with that point since having two or more peaks overlapped will necessarily lead
    to errors (in an unconstrained model).

    uses profile_data to do all the filtering at once.
    '''
    filtered_dict = {}
    for name, entry in data_dict.items():
        
        s_nm = entry['s_nm']
        # Find the unique values
        unique_vals, counts = np.unique(s_nm, return_counts=True)
        duplicate_vals = unique_vals[counts>1]
        duplicate_mask = np.isin(s_nm, duplicate_vals)
        

        # Filter out the values at the duplicate indices
        filtered_dict[name] = {key:val[~duplicate_mask] for key, val in entry.items()}
    return filtered_dict

#}}}
# filter_by_pct_error: {{{
def filter_by_pct_error(data_dict:dict, threshold:float = 10,base_ib_key:str = 'IZTF_IBs'):
    '''
    This function filters by the error in the IZTF (s)
    If the error is below the threshold percentage of the point, it is included
    otherwise, it is excluded

    We should also think about the fact that when peaks are right on top of each other, they are unreliable even if 
    perceived errors are low. 
    '''
    filter_key = f'filtered_{threshold}'
    data_dict[filter_key] = {}
    for identifier, entry in data_dict.items():
        try:
            IZTF_s = entry[base_ib_key]
            IZTF_s_e = entry[f'{base_ib_key}_e']
            pct_e = (IZTF_s_e/IZTF_s)*100 # These are a list of all the percent errors
            data_dict[filter_key][identifier] = {} 
            for label, arr in entry.items():
                data_dict[filter_key][identifier][label] = []
                for i, val in enumerate(arr):
                    pct_e_at_idx = pct_e[i] # This is the current error for the entry. 
                    if pct_e_at_idx < threshold:
                        data_dict[filter_key][identifier][label].append(val)
        except:
            pass
    for identifier, entry in data_dict[filter_key].items():
        try:
            s = entry['s_nm']
            h = entry['H']
            k =entry['K']
            l =entry['L']
            iztf = entry[base_ib_key]
            iztf_e = np.around(np.array(entry[f'{base_ib_key}_e'][i],4))
            hts = make_hovertemplate(s, iztf, iztf_e, h, k, l, labels = ['s (nm^-1)', base_ib_key])

            data_dict[filter_key][identifier]['hovertemplate'] = hts
        except:
            pass
    return data_dict

#}}}
# fit_to_line: {{{
def fit_to_line(x, y,  artificial_x = None):
    ''' 
    This performs a fast fit to data you provide.
    If you want to modify the xaxis you are fitting, pass np.linspace to artificial_x

    returns m, x, fit
    '''
    if type(artificial_x ) == type(None):
        artificial_x = np.linspace(0, 20, 20)
    try:
        m, b = np.polyfit(x, y, 1)
        fit = [m*s + b for s in artificial_x]
    except:
        m, b = (0,0)
        fit = np.zeros_like(artificial_x)
    return m, b, fit
#}}}
# get_datasets: {{{
def get_datasets(profile_data:dict = None, colors:list = ['blue'], 
        base_ib_key:str = 'IZTF_IBs'):
    '''
    This function takes a profile_data dictionary
    The first layer keys must be the identifier (e.g. not filtered_x)
    
    colors: a list of colors for each entry of profile_data
    
    returns:
        a list of dictionaries with entries: [x, y, yerr, name, hovertemplate, color]
    '''
    datasets = []
    for i, (key, entry) in enumerate(profile_data.items()):
        name = key
        x = np.array(entry['s_nm'])
        y = np.array(entry[base_ib_key])
        yerr = np.array(entry[f'{base_ib_key}_e']) 
        h = entry['H']
        k = entry['K']
        l = entry['L']
        color = colors[i]
        datasets.append({
            'x': x,
            'y': y,
            'yerr': yerr,
            'H': h,
            'K': k,
            'L': l,
            'name':name,
            'hovertemplate':make_hovertemplate(x, y, yerr, h, k, l, labels = ['s (nm^-1)', base_ib_key]),
            'color':color,
        })
    return datasets
#}}}
# calculate_size_error: {{{
def calculate_size_error(size_arr, beta_size, beta_err):
    '''
    Since the size error is not as simple as rescaling 
    or copy/pasting, here is a function
    to get the error associated with a IB -> size conversion

    Takes: 
        array of sizes (in units of nm)
        array of beta_size (strain corrected IB in s (nm^-1))
        array of beta errors (units of s (nm^-1))
    '''
    size_err = np.array(size_arr) - 1/(np.array(beta_size) + np.array(beta_err))  # Calculate the size error in appropriate units
    return size_err
#}}}
# calculate_size: {{{ 
def calculate_size(s_arr, beta_arr, beta_err, epsilon, scale_factor = None, mode:int = 0):
    ''' 
    This function uses 3 arrays (s, beta, and beta_error) along with an epsilon (strain)
    and optional scaling factor to convert IB data to size data

    mode: 0 = returns the strain corrected IBs (beta_size)
    mode: 1 = returns the hkl-dependent MCL sizes

    returns: (array, error_array)
    '''
    s_arr = np.array(s_arr)
    beta_arr = np.array(beta_arr)
    beta_err = np.array(beta_err)

    # Calculations for Beta_size: {{{
    unscaled_beta_size_arr = (beta_arr - epsilon * s_arr) 
    if not isinstance(scale_factor,type(None)):
        scaled_beta_size_arr = (beta_arr - epsilon * s_arr) * scale_factor
        scaled_beta_err = beta_err * scale_factor # Error is just a rescaling
        if mode == 0:
            return (scaled_beta_size_arr, scaled_beta_err) 
    if mode == 0: 
        # This means that we would then just return the unscaled beta sizes
        return(unscaled_beta_size_arr, beta_err)
    #}}}
    # Size Calculations: {{{
    if mode == 1:
        unscaled_size = 1/unscaled_beta_size_arr # The size is just the inversion of the IB in s
        unscaled_size_err = calculate_size_error(unscaled_size, unscaled_beta_size_arr, beta_err) # This gives us the correct strain
        if not isinstance(scale_factor, type(None)):
            scaled_size = unscaled_size * scale_factor
            scaled_size_err = unscaled_size_err * scale_factor
            return (scaled_size, scaled_size_err)
        return (unscaled_size, unscaled_size_err)

    #}}} 
        
#}}}
# get_size_dataset: {{{
def get_size_dataset(datasets:list = None, params:list = None, unscaled_idx:int = 1, 
        guess_for_unscaled_beta:float = None,
        mode:int = 0, apply_scale:bool = True):
    ''' 
    This takes datasets and will automatically size correct them 

    mode: 
        0 - This simply returns the strain corrected IB dataset
        1 - This will return the inverted IBs for size calculations
    '''
    num_datasets = len(datasets)
    num_params = len(params)
    # get epsilons: {{{
    if num_datasets == num_params:
        epsilons = params[0]
        scale_factors = params[1:]
    else:
        epsilons = params[:num_datasets-1] # The first half are epsilons
        scale_factors = params[num_datasets-1:] # The second half are scale factors
    #}}}
    size_datasets = []
    # Generate new datasets: {{{
    for i, dataset in enumerate(datasets): 
        # Get the prms: {{{
        s = dataset['x']
        b = dataset['y']
        berr = dataset['yerr']
        color = dataset['color']
        ht = dataset['hovertemplate']
        name = dataset['name']
        h = dataset['H']
        k = dataset['K']
        l = dataset['L']
        #}}}
        # scale factor: {{{
        if i < unscaled_idx:
            try:
                epsilon = epsilons[i]
            except:
                epsilon = epsilons
            scale_factor = scale_factors[i]
        elif i > unscaled_idx:
            try:
                epsilon = epsilons[i-1]
            except:
                epsilon = epsilons
            scale_factor = scale_factors[i-1]
        else:
            if guess_for_unscaled_beta:
                epsilon = guess_for_unscaled_beta
            else:
                epsilon = epsilons
            scale_factor = 1

        #}}}
        if apply_scale:
            sc_ib, sc_ib_err = calculate_size(s, b, berr, epsilon, scale_factor,mode) # This gives the associated Beta_size array
        else:
            sc_ib, sc_ib_err = calculate_size(s, b, berr, epsilon, mode=mode) # This gives unscaled Beta_size arrays
        if mode == 1:
            size, size_err = calculate_size(s,b, berr, epsilon, mode=mode)
            recorded_y = size
            recorded_yerr = size_err
            label = 'Size (nm)'
        else:
            recorded_y = sc_ib
            recorded_yerr = sc_ib_err
            label = 'Strain Corrected IB (s, nm)'
        size_datasets.append({
            'x': s,
            'y': recorded_y,
            'yerr': recorded_yerr,
            'H': h,
            'K': k,
            'L': l,
            'name': f'{name}_epsilon = {np.around(epsilon, 6)}',
            'color': color,
            'hovertemplate': make_hovertemplate(s, recorded_y,recorded_yerr,  h, k, l, labels = ['s (nm^-1)', label]),
            'mode': mode,
            'rescaled': apply_scale,
        })
    #}}}
    return size_datasets

#}}}
# subtract_datasets: {{{
def subtract_datasets(datasets1, datasets2, tolerance):
    """
    Subtract y values of dataset2 from dataset1 based on x values with a given tolerance.
    
    Parameters:
    dataset1 (list of dict): First dataset with 'x', 'y', 'yerr' keys, each containing arrays of the same length.
    dataset2 (list of dict): Second dataset with 'x', 'y', 'yerr' keys, each containing arrays of the same length.
    tolerance (float): Tolerance for matching x values.
    
    Returns:
    list of dict: Resulting dataset with subtracted y values.
    """
    result = []
    
    for dataset1 in datasets1:
        x1, y1, yerr1 = dataset1['x'], dataset1['y'], dataset1['yerr']
        color, name, h, k, l = dataset1['color'], dataset1['name'], dataset1['H'], dataset1['K'], dataset1['L']
        result_x = []
        result_y = []
        result_yerr = []
        
        used_indices = set()
        
        for i in range(len(x1)):
            for dataset2 in datasets2:
                x2, y2, yerr2 = dataset2['x'], dataset2['y'], dataset2['yerr']
                for j in range(len(x2)):
                    if abs(x1[i] - x2[j]) <= tolerance and j not in used_indices:
                        result_x.append(x1[i])
                        result_y.append(y1[i] - y2[j])
                        result_yerr.append(np.sqrt(yerr1[i]**2 + yerr2[j]**2))
                        used_indices.add(j)
                        break
        
        if result_x:
            result.append({
                'x': np.array(result_x), 
                'y': np.array(result_y), 
                'yerr': np.array(result_yerr),
                'H': h,
                'K': k,
                'L': l,
                'color': color,
                'name': name,
                'hovertemplate': make_hovertemplate(result_x, result_y, result_yerr, h, k, l, ['s (nm^-1)','ZTF IBs (corrected)'])
            })
    
    return result       
        
#}}}
# get_profile_output: {{{
def get_profile_output(
        profile_data:dict = None, 
        filter_key:str = None, 
        epsilon = None, 
        scale_factors:list = None, 
        unscaled_idx:int = 1,
        compositions:list = [80, 70, 50, 30],
        ):
    ''' 
    Function purpose: 
        Return a dataset for a given set of data (e.g. 600 mm S2D with compositions 80%, 70%, 50%, 30%) where relevant data to 
        the composition is stored as well as relevant data to the distance is stored.
    Contains entries: 
    {distance}
        {composition}
            1) s_nm # 1/d in nm
            2) I_scale # Intensity scaling
            3) I_scale_e # error in intensity scaling
            4) beta_total # IZTF_IBs
            5) beta_total_e # IZTF_IBs_e (error in the IB)
            6) beta_size # Strain-corrected IZTF_IBs
            7) beta_size_e # Strain-corrected IZTF_IBs_e (error in beta_size)
            8) size_mcl # This is the set of hkl-dependent MCLs
            9) size_mcl_e # This is the set of hkl-dependent MCLs errors
            10) hkl_label # This is the set of hkl labels for the reflections 
            11) avg_mcl_size # This is a single value representing the average MCL for the composition
            12) avg_mcl_size_e # This is the average error associated with the avg MCL
            13) beta_size_scaled # SC IZTF_IBs with scale factor
            14) beta_size_scaled_e # SC IZTF_IBs_e with scale factor
        ...
        compositions: # This is a list of the compositions (numerical)
        avg_mcl_sizes: # This is a list of the average MCL sizes for all the compositions
        avg_mcl_sizes_e # This is a list of all the average MCL size errors for all the compositions

    The output here will allow for figures to be made easily in an outside program like IGOR.

    Inputs: 
        1) profile_data: profile_data made by the code
        2) filter_key: optional key if using filtered profile_data
        3) epsilon: refined epsilon value(s) for your data
        4) scale_factors: scale factors for your data
        5) unscaled_idx: The index of your data that is not affected by a scale factor (it was the reference during fitting)
        6) compositions: A list of composition numbers e.g. [80, 70, 50, 30]
    '''
    profile_output = {} # This is the profile output
    avg_mcl_sizes = []
    avg_mcl_sizes_e = []

    if filter_key:
        profile_data = profile_data[filter_key]
    # Loop through the profile data: {{{
    for i, (key, entry) in enumerate(profile_data.items()):
        if 'filtered' in key:
            break # Skip these entries if they exist
        # Make the entry label for the output: {{{
        try:
            comp_label = f'{key}_{filter_key}'
        except:
            comp_label = key
        #}}}  
        # gather the profile data we need: {{{
        s = entry['s_nm']
        b = entry['IZTF_IBs'] # beta (IB, size + strain)
        berr = entry['IZTF_IBs_e'] # beta error
        hkl = entry['hkl']
        i_scale = entry['I_scale']
        i_scale_err = entry['I_scale_e']
        #}}}
        # get curr_epsilon : {{{
        try:
            curr_epsilon = epsilon[i] 
        except:
            curr_epsilon = epsilon
        #}}}
        # get curr_sf: {{{
        if type(scale_factors) != type(None):
            if i < unscaled_idx:
                curr_sf = scale_factors[i] # There is no modification to the index necessary
            elif i > unscaled_idx:
                curr_sf = scale_factors[i-1] # We now need to subtract one from the index to be on the correct scale factor
            else:
                curr_sf = 1 # We just set the SF to one since we skipped this one from scaling.

            scaled_beta_size, scaled_beta_size_e = calculate_size(s, b, berr, curr_epsilon, curr_sf, mode=0) # Returns scaled beta size
        else:
            scaled_beta_size, scaled_beta_size_e = (None,None)
        #}}}
        # Calculate the Beta_size (unscaled): {{{
        unscaled_beta_size, unscaled_beta_size_e = calculate_size(s, b, berr, curr_epsilon, mode=0) # Returns unscaled beta size
        #}}}
        # Calculate the MCL sizes: {{{
        mcl_size, mcl_size_e = calculate_size(s, b, berr, curr_epsilon, mode = 1) # Returns the MCLs for each hkl along with their errors
        #}}}
        # Calculate the average MCL and MCL error: {{{
        avg_mcl = np.average(mcl_size)
        avg_mcl_e = np.average(mcl_size_e)

        avg_mcl_sizes.append(avg_mcl)
        avg_mcl_sizes_e.append(avg_mcl_e)
        #}}}
        # Update the output dictionary entry: {{{
        profile_output[comp_label] = {
            's_nm': s,# 1/d in nm
            'i_scale': i_scale, # Intensity scaling
            'i_scale_e': i_scale_err, # Error in intensity scaling
            'beta_total': b,# IZTF_IBs
            'beta_total_e':berr,# IZTF_IBs_e (error in the IB)
            'beta_size': unscaled_beta_size, # Strain-corrected IZTF_IBs
            'beta_size_e': unscaled_beta_size_e, # Strain-corrected IZTF_IBs_e (error in beta_size)
            'size_mcl': mcl_size,# This is the set of hkl-dependent MCLs
            'size_mcl_e': mcl_size_e,# This is the set of hkl-dependent MCLs errors
            'hkl_label':hkl,# This is the set of hkl labels for the reflections 
            'avg_mcl_size': avg_mcl,# This is a single value representing the average MCL for the composition
            'avg_mcl_size_e': avg_mcl_e,# This is the average error associated with the avg MCL
        } 
        if type(scaled_beta_size) != type(None):
            profile_output[comp_label].update({
                'beta_size_scaled':scaled_beta_size, # SC IZTF_IBs with scale factor
                'beta_size_scaled_e':scaled_beta_size_e,# SC IZTF_IBs_e with scale factor
            })
        #}}}
    #}}}
    # Finally, add the list of avg MCLs and compositions: {{{
    profile_output.update({
        'compositions': compositions,
        'avg_mcl_sizes': avg_mcl_sizes,
        'avg_mcl_sizes_e': avg_mcl_sizes_e,
    })
    #}}}
    return profile_output
#}}}
#}}}
# Optimization Functions: {{{
# williamson_hall_optimization:{{{ 
def williamson_hall_optimization(
        params:list = None, 
        datasets:list = None,
        unscaled_idx:int = 1,  
        guess_for_unscaled_beta:float = None,
        **kwargs   
    ):
    ''' 
    This function seeks to return scale factors and
    epsilon values for datasets provided
    
    params: a list of initial values to optimize. Order -> epsilons -> scale factors
        - If you give as many parameters as datasets, then you are choosing to optimize 
        a single epsilon value for all your datasets with the remaining values being 
        scale factors for all datasets but one
        - If you choose to give the total number of datasets * 2 - 1 parameters 
        then each of the first parameters will be epsilons and the rest will be scale factors
        for all the datasets but one
    datasets: list of dictionaries with the data
    unscaled_idx: Index of the dataset that does not have a scale factor applied
    
    **kwargs: 
        legend_x
        legend_y
        yaxis_range
    '''
    # kwargs: {{{
    legend_x = kwargs.get('legend_x', 0.95)
    legend_y = kwargs.get('legend_y', 0.95)
    yaxis_range = kwargs.get('yaxis_range', None)
    #}}}
    # Objective function: {{{
    def objective(params):
        num_datasets = len(datasets) -1
        num_prms = len(params) # If we know how many parameters are passed, we can deduce intent (single epsilon or one for each dataset)
        # Single epsilon case: {{{
        if num_prms == num_datasets+1:
            epsilons = params[0] # A single epsilon
            scale_factors = params[1:]
        #}}}
        # Multiple epsilon case: {{{
        elif num_prms == 2*(num_datasets+1) - 2:
            epsilons = params[:num_datasets] # a list of epsilons for each dataset should be 1 less than all datasets
            scale_factors = params[num_datasets:] # list of scale factors  should be 1 less than all datasets
        #}}} 
        # fail case: {{{
        else:
            raise ValueError(f'You gave the wrong number of parameters for {num_datasets} datasets')
        #}}}  
        sizes = []
        # Calculate sizes: {{{
        for i, dataset in enumerate(datasets):
            s = dataset['x']
            b = dataset['y']
            # choose scale factor: {{{
            if i < unscaled_idx:
                try:
                    epsilon = epsilons[i]
                except:
                    epsilon = epsilons
                # In this case, we can just use the i'th scale factor
                scale_factor = scale_factors[i]
            elif i > unscaled_idx:
                try:
                    epsilon = epsilons[i-1]
                except:
                    epsilon = epsilons
                # If this is the case, we have already passed the idx to skip
                scale_factor = scale_factors[i - 1] 
            #}}} 
            # calculate the size: {{{ 
            if i != unscaled_idx:
                size = scale_factor * (b - epsilon * s)  # Since the scale factor that is 1 isnt refined it's okay to write like this
            else:
                #size = (b-epsilon * s)
                if guess_for_unscaled_beta:
                    size = (b - guess_for_unscaled_beta * s)
                else:
                    size = (b - epsilon * s) # Dont refine the unscaled beta
            #}}}
            sizes.append(size)
        #}}}
        avg_size = np.average([np.average(size) for size in sizes]) 
        rmses = []
        # Calculate RMSEs: {{{
        for i, dataset in enumerate(datasets):
            s = dataset['x']
            b = dataset['y']
            berr = dataset['yerr']
            size = sizes[i]
            # choose scale factor: {{{
            if i < unscaled_idx:
                scale_factor = scale_factors[i]
            elif i > unscaled_idx:
                scale_factor = scale_factors[i-1]
            #}}} 
            if i != unscaled_idx:  
                rmse = np.sqrt(np.mean(((size - avg_size)/ (berr * scale_factor))**2)) 
            else:
                rmse = np.sqrt(np.mean(((size - avg_size)/ berr)**2)) 
            rmses.append(rmse) 
        #}}}
        return sum(rmses)
    #}}}
    # Plot the data you are optimizing: 
    plot_datasets_with_error(datasets, legend_x=legend_x, legend_y=legend_y, yaxis_range=yaxis_range) # This just plots the raw data
    result = minimize(objective, params)
    # plot the result of fitting: {{{
    size_dataset = get_size_dataset(datasets, result.x, unscaled_idx, guess_for_unscaled_beta)
    plot_datasets_with_error(size_dataset, title_text='Strain corrected IBs', yaxis_title='IZF IB (s, nm)', legend_x = legend_x, legend_y = legend_y, yaxis_range=yaxis_range)
    #}}}
    print(result)
    print(f'Final error: {result.fun}') 
    return result.x

#}}}
#}}}
# Plotting functions: {{{
# basic_xy_file_plot: {{{
def basic_xy_file_plot(tth, yobs, ycalc, ydiff, title = ''):
    # initial plot: {{{
    plt.plot_data(
        tth, 
        yobs, 
        title_text=title,
        xaxis_title= f'2{plt._theta}{plt._degree}',
        yaxis_title='Intensity',
        mode = 'lines',
        color = 'blue',
        name = 'yobs',
        height = 450
    )
    #}}}
    # ycalc: {{{
    plt.add_data_to_plot(
        tth, 
        ycalc,
        mode = 'lines',
        color = 'red',
        name = 'ycalc',
    )
    #}}}
    # diff: {{{
    plt.add_data_to_plot(
        tth, 
        ydiff, 
        mode = 'lines',
        color = 'grey', 
        name = 'ydiff',
    )
    #}}}
    plt.show_figure()
#}}}
# plot_ib_data: {{{
def plot_datasets_with_error(
        datasets:list= None, 
        title_text:str = 'Williamson-Hall Plot',
        xaxis_title = 's (nm^-1)',
        yaxis_title = 'IZTF IB (s, nm)',
        yaxis_range = None,
        height = 400,
        width = 800,
        marker_size = 5,
        legend_x = 0.95,
        legend_y = 0.95,
        x_for_fit = np.linspace(0,20,20)
    ):
    ''' 
    This function will take a dictionary of the data you want to plot
    Expected entries are: 
        x, y, yerr, name, hovertemplate, color
    '''
    print('#'*45)
    fig = go.Figure()
    # Loop through the datasets: {{{
    for dataset in datasets:
        x = dataset['x']
        y = dataset['y']
        yerr = dataset['yerr']
        color = dataset['color']
        name = dataset['name']
        ht = dataset['hovertemplate']
        m, b, fit = fit_to_line(x, y, artificial_x=x_for_fit)
        # Plot the base data: {{{
        fig.add_scatter(
            x = x,
            y = y,
            error_y = dict(
                type = 'data',
                array = yerr,
                visible = True,
            ),
            marker = dict(color = color),
            name = name,
            mode = 'markers',
            hovertemplate = ht,
            marker_size = marker_size,

        )
        #}}}
        # Plot the fit to the data: {{{
        fig.add_scatter(
            x = x_for_fit,
            y = fit,
            line = dict(color = color),
            name = f'{name}_fit',
            hovertemplate = f'm= {m}* x + {b}',
            mode = 'lines',
        )
        #}}}
        # Print Useful info: {{{
        print(f'slope ({name}): {np.around(m, 6)}, intercept ({name}): {np.around(b, 6)}')
        #}}}
    #}}}
    print('#'*45)
    fig.update_layout(
        title = title_text,
        xaxis_title = xaxis_title,
        yaxis_title = yaxis_title,
        template = 'simple_white',
        legend = dict(
            x = legend_x,
            y = legend_y,
        ),
        yaxis = dict(range = yaxis_range),
        height = height,
        width = width
    )
    fig.show()
#}}}
#}}}
# IO functions: {{{
# get_igor_compatible_out_files:{{{ 
def get_igor_compatible_out_files(directories:list = None, profile_data:dict=None, num_subdirs:int = 4,subdirs:list = ['IPS', 'xPS', 'xPx', 'IPx']):
    ''' 
    This function will rename the columns of one of the 
    "..._profiles.out" files so that there are no duplicates
    This ensures that when loaded into IGOR, the columns are distinguishable

    make sure the directories are absolute paths
    '''
    for base_dir in directories:
        for idx in range(num_subdirs):
            try:
                go_to_dir(base_dir, idx, subdirs)
            except:
                break
            method = os.path.basename(os.getcwd())
            base = os.path.basename(base_dir)
            identifier = '_'.join([base,method]) # This is the identifier that gets added to the name of the file and the column headers. 

    
            out_files = glob('*.out')
            profile = [f for f in out_files if '_profiles.out' in f][0]
            with open(profile, 'r') as f:
                lines = f.readlines()
                with open(f'{profile.strip(".out")}_{identifier}.out', 'w') as f2:
                    for i, line in enumerate(lines):
                        if i == 0:
                            label_line = lines[0].split(',')
                            updated_label_list = []
                            for j, label in enumerate(label_line):
                                stripped_label = label.strip("\n").strip("").strip(" ")
                                if j < len(label_line)-1:
                                    new_label = f'{stripped_label}_{identifier}'
                                else:
                                    new_label = f'{stripped_label}_{identifier}\n'
                                updated_label_list.append(new_label)
                            updated_label_line = ','.join(updated_label_list)
                            f2.write(updated_label_line)
                        else:
                            lne = []
                            entry = profile_data[identifier]
                            for key, arr in entry.items():
                                lne.append(str(arr[i-1])) # Because the first line is 0, we need to do i-1
                            newline = ','.join(lne)
                            if i+1 < len(lines):
                                newline = newline+'\n'
                            f2.write(newline)
                            #f2.write(line)
                    f2.close()
                f.close()


#}}}
# write_profile_data_to_excel: {{{
def write_profile_data_to_excel(
        profile_data:dict = None, 
        filter_key:str = 'filtered_10',
        excel_fn_prefix:str = 'IrBCN',
        output_dir:str = None,
        include_entries = None,
        modify_keys = True,
    ):
    '''  

    ''' 
    # Write to an excel file
    home = os.getcwd()
    dataframes = [] # these are the dataframes generated from profile_data
    identifiers = [] # The list of identifiers from each profile data entry
    
    try:
        filtered_dict = profile_data[filter_key]
    except:
        filtered_dict = profile_data # This is in the case where you don't need a filter
    for identifier, entry in filtered_dict.items():
        keys = list(entry.keys())
        if len(keys) >1:
            identifiers.append(identifier)
            new_keys = []
            arrs = []
            for key, arr in entry.items():
                include = True
                #  If you want only certain entries: {{{
                if type(include_entries) != type(None):
                    if key in include_entries:
                        include = True
                    else:
                        include = False 
                #}}}
                if include:
                    if modify_keys:
                        new_keys.append(f'{key}_{filter_key}_{identifier}') 
                    else:
                        new_keys.append(key)
                    arrs.append(arr) # add the array data to a list
            df = pd.DataFrame(arrs,index=new_keys).T # Create the dataframe. Must be created like this to have the custom header labels
            dataframes.append(df)
    excel_file = f'{excel_fn_prefix}_{filter_key}.xlsx'
    if os.path.exists(output_dir):
        os.chdir(output_dir)
    else:
        os.mkdir(output_dir)
        os.chdir(output_dir)
    with pd.ExcelWriter(excel_file) as writer:
        for i, df in enumerate(dataframes):
            df.to_excel(writer, sheet_name = identifiers[i], index = False)
    os.chdir(home)
    print(f'Wrote {excel_file} to:\n{output_dir}')
#}}}
# write_output_data_to_excel: {{{
def write_output_data_to_excel(
        all_output_pd:list = None,
        all_epsilons:list = None,
        capillaries:list = ['kapton', 'glass'],
        distances:list = [220, 600, 900, 1200],
        excel_dir:str = os.getcwd(),
    ):
    ''' 
    This function allows you to quickly output large amounts of data to excel
    using the "profile_output" dictionary created by this code in a sequential fashion. 

    all_output_pd: list of profile_output dictionaries
    all_epsilons: list of the epsilon values you want to use in order
    capillaries: list of the unique capillary types in your output. Must be in order of the repeat.
        ex: capillaries = ["kapton", "glass"]
        data: [220_kap, 220_glass, 500_kap, 500_glass]
    distances: list of distances as above
    '''
    if not os.path.exists(excel_dir):
        os.mkdir(excel_dir)
    # Loop through each profile_output: {{{
    for i, pd_out in enumerate(all_output_pd):
        # Make useful string arguments: {{{
        if len(capillaries) == 2:
            curr_capillary = capillaries[i%2]
            dist_idx = (i//2)%len(distances)
            curr_dist = distances[dist_idx]
        else:
            curr_capillary = capillaries[0]
            curr_dist = distances[i]
        curr_epsilon = all_epsilons[i]
        curr_epsilon = str(np.format_float_scientific(curr_epsilon,2)).replace('.','p')
        excel_file = f'{curr_capillary}_{curr_dist}mm_eps_{curr_epsilon}.xlsx'


        cap_letter_id = curr_capillary[0] # Gives either a k or a g for labeling
        dist_id = f'{curr_dist}{cap_letter_id}'
        #}}} 
        dfs = []
        special_entries = ['compositions', 'avg_mcl_sizes', 'avg_mcl_sizes_e'] # These are specifically defined in the profile_output
        # Loop through the dictionary: {{{
        for comp, pd_entry in pd_out.items():
            if comp not in special_entries:
                key_prefix = f'{dist_id}_{comp}'
                new_keys = []
                keys = list(pd_entry.keys())
                for key in keys: 
                    new_keys.append(f'{key_prefix}_{key}_eps_{curr_epsilon}')
                updated_entry = {new_keys[i]:value for i, (key, value) in enumerate(pd_entry.items())}
                df = pd.DataFrame(updated_entry)
                dfs.append(df)
        
        df = pd.DataFrame([pd_out[special_entries[0]], pd_out[special_entries[1]], pd_out[special_entries[2]]], index=[f'{dist_id}_{df_lbl}' for df_lbl in special_entries]).T
        dfs.append(df)
        #}}} 
        # Now we want to write the file
        with pd.ExcelWriter(os.path.join(excel_dir,excel_file)) as writer:
            start_col = 0
            for df in dfs:
                df.to_excel(writer, sheet_name=dist_id, startcol=start_col, index=False)
                start_col+=len(df.T)
    #}}}
#}}}
#}}}
