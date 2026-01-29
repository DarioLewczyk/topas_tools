# Authorship: {{{ 
"""  
Written by: Dario C. Lewczyk
Date: 01/28/26
"""
#}}}
# imports: {{{ 
import numpy as np
from scipy.optimize import minimize
from functools import reduce
from math import gcd
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
        # Error is just a rescaling
        scaled_beta_err = beta_err * scale_factor 
        if mode == 0:
            return (scaled_beta_size_arr, scaled_beta_err) 
    if mode == 0: 
        # This means that we would then just return the unscaled beta sizes
        return(unscaled_beta_size_arr, beta_err)
    #}}}
    # Size Calculations: {{{
    if mode == 1:
        # The size is just the inversion of the IB in s
        unscaled_size = 1/unscaled_beta_size_arr 
        # This gives us the correct strain
        unscaled_size_err = calculate_size_error(
                unscaled_size, 
                unscaled_beta_size_arr, 
                beta_err
        ) 
        if not isinstance(scale_factor, type(None)):
            scaled_size = unscaled_size * scale_factor
            scaled_size_err = unscaled_size_err * scale_factor
            return (scaled_size, scaled_size_err)
        return (unscaled_size, unscaled_size_err)

    #}}}  
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
    # Calculate the size error in appropriate units
    size_err = np.array(size_arr) - 1/(np.array(beta_size) + np.array(beta_err))  
    return size_err
#}}}
# normalize_hkl: {{{
def normalize_hkl(hkl:tuple):
    h,k,l = hkl
    g = reduce(gcd, (abs(h), abs(k), abs(l)))
    return (h//g, k//g, l//g) # returns the GCD reduced hkl
#}}}
# interpret_params: {{{ 
def interpret_params(params, num_datasets, unscaled_idx):
    """
    Given a flat parameter list, return:
        epsilons: list of length num_datasets
        scale_factors: list of length num_datasets-1
    #################################################
    Usage:
        - If you give as many parameters as datasets, 
          then you are choosing to optimize 

        a single epsilon value for all your datasets 
        with the remaining values being scale factors 
        for all datasets but one

        - If you choose to give the total number of 
          datasets * 2 - 1 parameters 
          then each of the first parameters will be epsilons 
          and the rest will be scale factors for all 
          the datasets but one
    #################################################
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
#  compute_beta_size: {{{ 
def compute_beta_size(s, b, berr, epsilon, scale_factor):
    beta_size = (b - epsilon * s)
    beta_size_err = berr

    if scale_factor is not None:
        beta_size *= scale_factor
        beta_size_err *= scale_factor

    return beta_size, beta_size_err

#}}}
# compute_size_from_beta: {{{ 
def compute_size_from_beta(beta_size, beta_size_err):
    size = 1 / beta_size
    size_err = size - 1 / (beta_size + beta_size_err)
    return size, size_err

#}}}
# williamson_hall_objective: {{{ 
def williamson_hall_objective(params, datasets, unscaled_idx):
    """
    Williamson–Hall objective using the new canonical calculators.
    Minimizes variance of strain-corrected IBs across datasets.
    """
    num_datasets = len(datasets)

    # 1. Interpret epsilons + scale factors
    epsilons, scale_factors = interpret_params(
        params, num_datasets, unscaled_idx
    )

    # 2. Compute strain-corrected IBs for each dataset
    beta_sizes = []
    for ds, eps, sf in zip(datasets, epsilons, scale_factors):
        s = ds['x']
        b = ds['y']
        berr = ds['yerr']

        beta_size, _ = compute_beta_size(
            s, b, berr,
            epsilon=eps,
            scale_factor=sf
        )
        beta_sizes.append(beta_size)

    # 3. Stack and compute variance
    stacked = np.vstack(beta_sizes)
    return np.var(stacked, axis=0).sum()

#}}}
# optimize_williamson_hall: {{{ 
def optimize_williamson_hall(
        datasets,
        initial_params,
        unscaled_idx=1,
        **kwargs
    ):
    """
    Clean public API for WH optimization.
    """
    return minimize(
        williamson_hall_objective,
        initial_params,
        args=(datasets, unscaled_idx),
        **kwargs
    )
    
#}}}

