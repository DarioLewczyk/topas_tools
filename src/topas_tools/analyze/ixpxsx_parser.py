#  Authorship: {{{ 
""" 
Written by: Dario C. Lewczyk
Date: 01/28/26
"""
#}}}
#  imports: {{{ 
import os
import numpy as np
from glob import glob
import pandas as pd

from topas_tools.utils import ixpxsx_calculator as calculator
from topas_tools.plotting import ixpxsx_plotting
#}}}
##########################
# Profile Data
##########################
# parse_ixpxsx_directory: {{{ 
def parse_ixpxsx_dir(directory:str):
    """ 
    Parse all the *_profiles.out in a single 
    IxPxSx directory. 

    returns: 
        {substance_name: {column_name: np.array()}}
    """
    parsed = {}
    
    # Directly grab only profiles.out files
    profile_files = glob(os.path.join(directory, "*_profiles.out"))
    #  Loop through the profile files: {{{ 
    for f in profile_files:
        substance = os.path.basename(f).replace("_profiles.out",'')
        parsed[substance] = {}
        df = pd.read_csv(f, delimiter=',', index_col=False)
        df.columns = df.columns.str.strip() # Clean column names

        for key, col in df.items():
            try:
                parsed[substance][key] = np.array(col)
            except Exception:
                parsed[substance][key] = list(col)
    #}}}
    return parsed
    
#}}}
# collect_profile_data: {{{ 
def collect_profile_data(base_dir:str, subdirs:str):
    """ 
    Walk through each subdir under base_dir,
    parse its profile data, and return a combined dictionary

    Returns: 
        { identifier: parsed_substance_dict }
    """
    profile_data = {}

    # Loop through subdirs: {{{ 
    for sub in subdirs:
        directory = os.path.join(base_dir, sub)
        if not os.path.exists(directory):
            continue
        identifier = f'{os.path.basename(base_dir)}_{sub}'
        parsed = parse_ixpxsx_dir(directory) 
        
        if parsed:
            profile_data[identifier] = parsed
    #}}}
    return profile_data
#}}}
#  get_profile_data: {{{ 
def get_profile_data(
        directories: list,
        subdirs: list = ['IPS', 'xPS', 'xPx', 'IPx'],
        debug: bool = False
    ):
    """
    High-level function that:
    - walks directories
    - parses profile data
    - computes errors
    - builds hovertemplates
    """
    profile_data = {}

    # Parse all directories
    for base_dir in directories:
        parsed = collect_profile_data(base_dir, subdirs)
        profile_data.update(parsed)

    if debug:
        return profile_data

    # Post-processing (your existing logic)
    for identifier, substances in profile_data.items():
        for substance, entry in substances.items():

            # Compute IBs error
            if 'IZTF_IBs_e' in entry:
                entry['IZTF_IBs_e'] = (
                    entry['IZTF_IBd_e'] / entry['IZTF_IBd']
                ) * entry['IZTF_IBs']

            # Fix HKL strings
            if 'hkl' in entry:
                hkls = [
                    f"{int(entry['H'][i])}_{int(entry['K'][i])}_{int(entry['L'][i])}"
                    for i in range(len(entry['hkl']))
                ]
                entry['hkl'] = np.array(hkls)

            # Hovertemplates
            hs = entry['H']
            ks = entry['K']
            ls = entry['L']
            s = entry['s_nm']
            iztf = entry['IZTF_IBs']
            iztf_e = entry['IZTF_IBs_e']

            entry['hovertemplate'] = np.array(
                ixpxsx_plotting.make_hovertemplate(s, iztf, iztf_e, hs, ks, ls)
            )

    return profile_data

#}}}
##########################
# Dataset generation
##########################
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
            'hovertemplate':ixpxsx_plotting.make_hovertemplate(x, y, yerr, h, k, l, labels = ['s (nm^-1)', base_ib_key]),
            'color':color,
        })
    return datasets
#}}}
# interpret_size_params: {{{ 
def interpret_size_params(params, num_datasets, unscaled_idx):
    """
    Given a flat parameter list, return:
        epsilons: list of length num_datasets
        scale_factors: list of length num_datasets
    """
    n = len(params)

    # Case 1: single epsilon + scale factors
    if n == num_datasets:
        epsilons = [params[0]] * num_datasets
        scale_factors = params[1:]

    # Case 2: epsilon per dataset + scale factors
    elif n == 2 * num_datasets - 1:
        epsilons = params[:num_datasets]
        scale_factors = params[num_datasets:]

    else:
        raise ValueError(
            f"Incorrect number of parameters for {num_datasets} datasets."
        )

    # Insert scale factor = 1 at unscaled index
    scale_factors = (
        scale_factors[:unscaled_idx]
        + [1]
        + scale_factors[unscaled_idx:]
    )

    return epsilons, scale_factors

#}}}
# build_size_dataset: {{{ 
def build_size_dataset(
        dataset,
        y,
        yerr,
        epsilon,
        label,
        color
    ):
    s = dataset['x']
    h = dataset['H']
    k = dataset['K']
    l = dataset['L']

    return {
        'x': s,
        'y': y,
        'yerr': yerr,
        'H': h,
        'K': k,
        'L': l,
        'name': f"{dataset['name']}_epsilon={np.around(epsilon, 6)}",
        'color': color,
        'hovertemplate': ixpxsx_plotting.make_hovertemplate(
            s, y, yerr, h, k, l,
            labels=['s (nm^-1)', label]
        ),
    }

#}}}
# get_size_dataset: {{{  
def get_size_dataset(
        datasets,
        params,
        unscaled_idx=1,
        mode=0,
        apply_scale=True
    ):
    """
    mode:
        0 = strain-corrected IBs
        1 = size (1/beta_size)
    """
    num_datasets = len(datasets)

    # 1. Interpret parameters
    epsilons, scale_factors = interpret_size_params(
        params, num_datasets, unscaled_idx
    )

    size_datasets = []

    # 2. Loop datasets
    for i, ds in enumerate(datasets):
        s = ds['x']
        b = ds['y']
        berr = ds['yerr']
        epsilon = epsilons[i]
        scale_factor = scale_factors[i] if apply_scale else None

        # 3. Compute beta_size
        beta_size, beta_size_err = calculator.compute_beta_size(
            s, b, berr, epsilon, scale_factor
        )

        # 4. Mode selection
        if mode == 0:
            y = beta_size
            yerr = beta_size_err
            label = 'Strain Corrected IB (s, nm)'
        else:
            y, yerr = calculator.compute_size_from_beta(beta_size, beta_size_err)
            label = 'Size (nm)'

        # 5. Build dataset
        size_datasets.append(
            build_size_dataset(
                ds, y, yerr, epsilon, label, ds['color']
            )
        )

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
                'hovertemplate': ixpxsx_plotting.make_hovertemplate(
                    result_x, 
                    result_y, 
                    result_yerr, h, k, l, 
                    ['s (nm^-1)','ZTF IBs (corrected)']
                )
            })
    
    return result       
        
#}}}
##########################
# Filtering and processing
##########################
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
    try:
        for name, entry in data_dict.items():
        
            s_nm = entry['s_nm']
            # Find the unique values
            unique_vals, counts = np.unique(s_nm, return_counts=True)
            duplicate_vals = unique_vals[counts>1]
            duplicate_mask = np.isin(s_nm, duplicate_vals)
        

            # Filter out the values at the duplicate indices
            filtered_dict[name] = {key:val[~duplicate_mask] for key, val in entry.items()}
        return filtered_dict
    except:
        for name, s_dict in data_dict.items():
            filtered_dict[name] = {}
            for substance, entry in s_dict.items():
                s_nm = entry['s_nm']
                unique_vals, counts = np.unique(s_nm, return_counts=True)
                duplicate_vals = unique_vals[counts>1]
                duplicate_mask = np.isin(s_nm, duplicate_vals)
                # Filter the values at the duplicate indices
                filtered_dict[name][substance] = {key:val[~duplicate_mask] for key, val in entry.items()}
        return filtered_dict

#}}}
# filter_by_pct_error: {{{
def filter_by_pct_error(data_dict:dict, threshold:float = 10, mode = 0, base_ib_key:str = 'IZTF_IBs'):
    '''
    This function filters by the error in the IZTF (s)
    If the error is below the threshold percentage of the point, it is included
    otherwise, it is excluded

    We should also think about the fact that when peaks are right on top of each other, they are unreliable even if 
    perceived errors are low. 

    mode = 0:  "pct" - Percent error
    mode = 1:  "abs" - Absolute numerical error
    '''
    filter_key = f'filtered_{threshold}'
    data_dict[filter_key] = {}
    for identifier, entry in data_dict.items():
        try:
            IZTF_s = entry[base_ib_key]
            IZTF_s_e = entry[f'{base_ib_key}_e'] # This is the error numerically 
            pct_e = (IZTF_s_e/IZTF_s)*100 # These are a list of all the percent errors
            data_dict[filter_key][identifier] = {} 
            for label, arr in entry.items():
                data_dict[filter_key][identifier][label] = []
                for i, val in enumerate(arr):
                    pct_e_at_idx = pct_e[i] # This is the current error for the entry. 
                    err_at_idx = IZTF_s_e[i] # This is absolute error at an index
                    # % error mode: {{{
                    if mode == 0:
                        if pct_e_at_idx < threshold:
                            data_dict[filter_key][identifier][label].append(val)
                    #}}}
                    #  numerical error mode: {{{ 
                    elif mode == 1: 
                        if err_at_idx < threshold:
                            data_dict[filter_key][identifier][label].append(val)
                    #}}}

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
# get_reflection_harmonics: {{{
def get_reflection_harmonics(parsed_data:dict, additional_keys:list = None):
    ''' 
    This function takes parsed data produced elsewhere by this code. 
    The function will automatically categorize harmonics within a dictionary along with
    their s-value and beta value. Also includes 2theta and whatever else you would like to store. 
    '''
    basic_keys_to_save = [
            'hkl','IZTF_IBs', 'IZTF_IBs_e',
            's_nm','tth_deg'
            ]
    try:
        basic_keys_to_save.extend(additional_keys)
        keys_to_save = basic_keys_to_save
    except:
        keys_to_save = basic_keys_to_save
    

    harmonics = {}
    # Loop through all recorded HKL: {{{
    for i, hkl_str in enumerate(parsed_data['hkl']):
        hkl = convert_str_hkl_to_tuple(hkl_str)
        norm = normalize_hkl(hkl) # This gets the base family for the reflection
        ht = f'hkl: {str(hkl)}<br>'+ '%{x}<br>%{y}' 
        # Create entries for the harmonics: {{{
        if norm not in harmonics:
            harmonics[norm] = {}
            for key in keys_to_save:
                harmonics[norm][key] = [] # Initialize the entries with lists
                harmonics[norm]['ht'] = [] # Initialize a list for the hover templates
        #}}}
        # Loop through the keys of interest: {{{
        for j, key in enumerate(keys_to_save):
            value = parsed_data[key][i]
            harmonics[norm][key].append(value)
        #}}} 
        harmonics[norm]['ht'].append(ht) # Add the hovertemplate last
    #}}}
    return harmonics
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
        Return a dataset for a given set of data 
        (e.g. 600 mm S2D with compositions 80%, 70%, 50%, 30%) 
        where relevant data to the composition is stored as well 
        as relevant data to the distance is stored.

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
            11) avg_mcl_size # This is a single value representing the 
                average MCL for the composition
            12) avg_mcl_size_e # This is the average error associated 
                with the avg MCL
            13) beta_size_scaled # SC IZTF_IBs with scale factor
            14) beta_size_scaled_e # SC IZTF_IBs_e with scale factor
        ...
        compositions: # This is a list of the compositions (numerical)
        avg_mcl_sizes: # This is a list of the average MCL 
                        sizes for all the compositions
        avg_mcl_sizes_e # This is a list of all the average MCL 
                            size errors for all the compositions

    The output here will allow for figures to be made easily in 
    an outside program like IGOR.

    Inputs: 
        1) profile_data: profile_data made by the code
        2) filter_key: optional key if using filtered profile_data
        3) epsilon: refined epsilon value(s) for your data
        4) scale_factors: scale factors for your data
        5) unscaled_idx: The index of your data that is not affected by a 
            scale factor (it was the reference during fitting)
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
# ProfileDataManager: {{{ 
class ProfileDataManager:
    """
    Central manager for all TOPAS profile data operations.
    Wraps parsing, filtering, dataset generation, sizing, and output formatting.
    """
    def __init__(self, profile_data: dict):
        self.raw = profile_data                      # Unmodified parsed data
        self.filtered = {}                           # Filtered versions
        self.datasets = None                         # get_datasets()
        self.size_datasets = None                    # get_size_dataset()
        self.profile_output = None                   # get_profile_output()

    # ---------------------------------------------------------
    # Filtering
    # ---------------------------------------------------------
    # filter_duplicates: {{{ 
    def filter_duplicates(self):
        """Remove entries with duplicate s_nm values."""
        self.filtered['no_duplicates'] = filter_by_duplicate_s(self.raw)
        return self.filtered['no_duplicates']
    #}}}
    #  filter_by_error: {{{ 
    def filter_by_error(self, threshold=10, mode=0, base_ib_key='IZTF_IBs'):
        """Filter by percent or absolute error."""
        self.filtered[f'err_{threshold}'] = filter_by_pct_error(
            self.raw, threshold, mode, base_ib_key
        )
        return self.filtered[f'err_{threshold}']
    #}}}
    # ---------------------------------------------------------
    # Dataset generation
    # ---------------------------------------------------------
    # make_datasets: {{{ 
    def make_datasets(self, base_ib_key='IZTF_IBs', colors=None):
        """Generate datasets for plotting or fitting."""
        if colors is None:
            colors = ['blue'] * len(self.raw)

        self.datasets = get_datasets(self.raw, colors, base_ib_key)
        return self.datasets
    #}}}
    # ---------------------------------------------------------
    # Size / strain correction
    # ---------------------------------------------------------
    #  make_size_datasets: {{{ 
    def make_size_datasets(
        self,
        params,
        unscaled_idx=1,
        guess_for_unscaled_beta=None,
        mode=0,
        apply_scale=True
    ):
        """Generate strain-corrected or size datasets."""
        if self.datasets is None:
            raise ValueError("Call make_datasets() first.")

        self.size_datasets = get_size_dataset(
            datasets=self.datasets,
            params=params,
            unscaled_idx=unscaled_idx,
            guess_for_unscaled_beta=guess_for_unscaled_beta,
            mode=mode,
            apply_scale=apply_scale
        )
        return self.size_datasets

    #}}}
    # ---------------------------------------------------------
    # Profile output (IGOR-ready)
    # ---------------------------------------------------------
    # make_profile_output: {{{ 
    def make_profile_output(
        self,
        filter_key=None,
        epsilon=None,
        scale_factors=None,
        unscaled_idx=1,
        compositions=[80, 70, 50, 30],
    ):
        """Generate the full profile output dictionary."""

        data = self.raw if filter_key is None else self.filtered[filter_key]

        self.profile_output = get_profile_output(
            profile_data=data,
            filter_key=filter_key,
            epsilon=epsilon,
            scale_factors=scale_factors,
            unscaled_idx=unscaled_idx,
            compositions=compositions
        )
        return self.profile_output
    #}}}

    # ---------------------------------------------------------
    # Harmonics
    # ---------------------------------------------------------
    #  get_harmonics: {{{ 
    def get_harmonics(self, entry_key, additional_keys=None):
        """Return harmonic families for a given profile entry."""
        entry = self.raw[entry_key]
        return get_reflection_harmonics(entry, additional_keys)
    #}}}

    # ---------------------------------------------------------
    # Convenience
    # ---------------------------------------------------------
    #  summary: {{{ 
    def summary(self):
        """Quick overview of what’s available."""
        return {
            "raw_keys": list(self.raw.keys()),
            "filtered_keys": list(self.filtered.keys()),
            "has_datasets": self.datasets is not None,
            "has_size_datasets": self.size_datasets is not None,
            "has_profile_output": self.profile_output is not None,
        }
    #}}}

#}}}
