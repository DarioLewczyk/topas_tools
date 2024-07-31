# Authorship: {{{
'''
Written by: Dario C. Lewczyk
Date: 05-16-24

Purpose:
    Assist with some of the general tasks that 
    the bkg_sub.py file inside of background_subtraction
    handles.
'''
#}}}
# Imports: {{{
import os, sys
import numpy as np
import re
import copy
from tqdm import tqdm
from scipy.signal import find_peaks

from topas_tools.utils.topas_utils import Utils
#}}}
# BkgsubUtils: {{{
class BkgsubUtils:
    # __init__: {{{
    def __init__(self,
        glass_dir:str = None,
        air_dir:str = None,
        data_dir:str = None, 
        glass_file:str = None,
        air_file:str = None,
        data_files:list = None,
        ):
        '''
        This can be run independent of the Bkgsub class
        but is mainly meant to work within its framework.
        '''
        # Get attrs: {{{
        self._glass_dir = glass_dir
        self._air_dir = air_dir
        self._data_dir = data_dir
        self.glass_file = glass_file
        self.air_file = air_file
        self.data_files = data_files
        #}}}
    #}}}
    # _get_default_bkgsub_data:{{{
    def _get_default_bkgsub_data(self, data_entries):
        '''
        This function simply serves to allow the user to 
        do chebychev subtraction without having subtracted 
        glass or air or another reference first.
        '''
        bkgsub_data = {}
        for i, entry in data_entries.items():
            data = entry['data'] # This is the originally loaded np data
            fn = entry['fn']
            bkgsub_data[i] = {
                'data': data,
                'tth': data[:,0],
                'yobs': data[:,1],
                'fn':fn,
                'scale_factor': 0,
                'tth_offset': 0,
                'ref_peak': 0,
                'data_peak': 0,
                'interpolated': False,
                'uninterpolated':data,
            }
        return bkgsub_data
    #}}}
    # _import_bkgsub_data: {{{
    def _import_bkgsub_data(self,skiprows:int = 1,len_of_time:int = 6):
        '''
        This function is built to get all of the data
        from the directories you define in Bkgsub
        '''
        data_dict = {}
        # Data Imports: {{{
        dirs = tqdm([self._glass_dir, self._air_dir, self._data_dir]) # Directories with data
        files = [self.glass_file, self.air_file, self.data_files] # File names
        entries = ['glass', 'air', 'data'] # Entry categories
        for i, path in enumerate(dirs):
            if type(path) == str:
                os.chdir(path) # Go to the path where the data are first
                skip_iter = False
            else:
                skip_iter = True
            entry = entries[i]
            fn = files[i] # Will either be a singular file or a list of files.
            data_dict[entry] = {} # Initialize the entry
            dirs.set_description_str(f'Collecting {entry}')
            # If Skip over Air: {{{
            if type(fn) == None:
                data_dict[entry] = None
                    
            #}}}
            #  Get the data: {{{
            elif type(fn) != str and type(fn) != type(None):
                for j, (time,f) in enumerate(fn.items()):
                    try:
                        data = np.loadtxt(f, skiprows= skiprows)
                    except: 
                        print(f'Warning: {f} has a formatting error')
                        new_f = []
                        with open(f, 'r') as open_f:
                            lines = open_f.readlines()
                            for line in lines:
                                cols = re.findall(r'\w+\.?\w*', line)
                                if len(cols) >=2:
                                    new_f.append(line)
                        data = np.loadtxt(new_f,skiprows=skiprows) 
                    tth = data[:,0]
                    yobs = data[:,1]
                    data_dict[entry][j] = {
                            'data': data,
                            'tth':tth,
                            'yobs':yobs,
                            'fn':f,
                            'time': str(time).zfill(len_of_time),
                            
                    }
            #}}}
            # Get background data: {{{
            else:
                if not skip_iter:
                    data = np.loadtxt(fn, skiprows=skiprows)
                    tth = data[:,0]
                    yobs = data[:,1]
                    data_dict[entry].update({
                        'data':data,
                        'tth':tth,
                        'yobs':yobs,
                        'fn':fn,
                    })
            #}}}
        #}}}
        return data_dict
    #}}}
    # scale_reference:  {{{
    def scale_reference(self,reference_data:np.ndarray = None, reference_peak = None, data_peak = None, scale_modifier:float = 1.0):
        '''
        reference_data: the x,y data for the reference
        reference_peak: the intensity observed for the reference peak
        data_peak: the intensity observed for the data peak

        scale_modifier: This parameter is the scaling of the scale factor. If you find that the background is being over or under fit, you can adjust this to modify the amount of scale factor applied. 

        This function returns a dictionary for the scaled reference.
        ''' 
        scale_factor = (data_peak/reference_peak) * scale_modifier

        scaled = reference_data.copy() 
        scaled[:,1] = reference_data[:,1] * scale_factor # This scales the data by the scale factor
        # make output dict: {{{
        scaled_ref = {
                'data': scaled,
                'tth': scaled[:,0],
                'yobs': scaled[:,1],
                'fn': 'Scaled bkg',
                'scale_factor':scale_factor,
        }
        #}}}
        return scaled_ref
    #}}}
    # subtract_patterns: {{{
    def subtract_patterns(self, d1, d2, tolerance:float = 0.001):
        '''
        Both d1 and d2 should be given in the form of datasets as when you use 
        np.loadtxt(). 

        d2 will be subtracted from d1

        tolerance: This is the difference allowed for 2theta from one dataset to another to be considered equivalent.
        
        Note: This function will work regardless of if the spacing is the same or not. 
        if the spacing is not the same, the function will return an interpolated result. 
        '''
        
        differences = [] 
        differences_interp = []
        interpolated = False
        # Perform the subtraction: {{{
        for xa, ya in d1:
            # Find the index of the closest x value in the other dataset.
            idx = (np.abs(d2[:,0] - xa) <= tolerance).nonzero()[0]
            # If a matching x is found within the tolerance, subtract the y
            if idx.size >0:
                for i in idx:
                    differences.append(ya- d2[i, 1])
            else:
                # In the event where there is not a matching x, append nan so that we retain the same length of list.
                differences.append(np.nan)
        differences = np.array(differences) # Convert to an array
        diff_mask = np.isnan(differences) # Make a mask to check if nan vals present
        #}}}
        # interpolate if necessary: {{{
        if True in diff_mask: 
            interpolated = True 
            non_nan_indices = np.where(~np.isnan(differences))[0]
            differences_interp = np.interp(d1[:,0], d1[non_nan_indices,0], differences[non_nan_indices]) 
        else:
            differences_interp = differences
        #}}}
        differences = np.array(list(zip(d1[:,0], differences))) # Return the result in a dataset form.
        differences_interp = np.array(list(zip(d1[:,0], differences_interp))) # Return the result of interpolation
        output = {
                'bkgsub': differences,
                'bkgsub_interpolated': differences_interp,
                'interpolated':interpolated,
        }
        return output
    #}}}
    # find_peak_positions: {{{
    def find_peak_positions(self,
            x,
            y, 
            ignore_below:float = 1,
            ignore_above:float = None,
            height=[950, 1800], 
            threshold = None, 
            distance = None, 
            prominence = None,
            width =[0,100],
            wlen = None,
            rel_height = 0.5,
            plateau_size = None,
            ):
        '''
        x is the 2theta degrees positions
        y is the intensities
        ignore_below: tells the program to ignore peaks at 2theta below this value

        This algorithm uses the scipy peak finding algorithm
        The default values should be restrictive enough to isolate the glass peak but 
        it may be necessary to play with the parameters to ensure that you get the glass peak
        only or at least, that the glass peak is listed first. 
        '''
        # define the range: {{{
        if ignore_below == None:
            ignore_below = min(x)
        if ignore_above == None:
            ignore_above = max(x)
        passing_x = np.where((x >= ignore_below) & (x<= ignore_above))  
        x = x[passing_x] # Redefine the array of x values
        y = y[passing_x] # Redefine the array of y values
        #}}}
        
        peaks, peak_info = find_peaks(y,
                height=height, 
                threshold=threshold, 
                distance= distance, 
                prominence=prominence, 
                width = width, 
                wlen = wlen, 
                rel_height = rel_height, 
                plateau_size = plateau_size
        ) 
        peak_dict = {
                'peak_idx': peaks,
                'peak_info': peak_info,
                'tth': [x[i] for i in peaks],
                'yobs': [y[i] for i in peaks],
        }
        return peak_dict
    #}}}
    # chebychev_bakground: {{{
    def chebychev_bakground(self,
            idx:int = 0, 
            bkgsub_data:dict = None,
            order:int = 8,
            height_offset = 40,
            bkg_offset = 10, 
            regions_to_eval:list = [(1, None)],
            **kwargs
            ):
        '''
        This function enables the performance of 
        all background subtraction functionality 
        using a chebychev polynomial and can be automated
        in the function chebychev_subtraction

        idx: index of the pattern
        bkgsub_data: dictionary of background subtracted data to work with.
        order: Chebychev polynomial order
        height_offset: tolerance below max intensity of the inverted pattern.
        bkg_offset: This is the amount that the background points will be moved to not over-subtract background
        multiple_regions: Use if you want to combine multiple chebychev backgrounds to one
        '''
        output = {} 
        x = bkgsub_data[idx]['tth']
        y = bkgsub_data[idx]['yobs']
        self._cheb_ranges = self._premap_data_for_chebychev_fitting(
                tth=x, 
                yobs=y, 
                regions_to_eval=regions_to_eval,
                height_offset = height_offset,
                bkg_offset = bkg_offset,
                order = order,
        )
        fn = bkgsub_data[idx]['fn']
        
        # Defaults: {{{ 
        threshold = kwargs.get('threshold',None)
        distance = kwargs.get('distance',None)
        prominence =kwargs.get('prominence',None)
        width = kwargs.get('width',[0,400])
        wlen = kwargs.get('wlen', None)
        rel_height = kwargs.get('rel_height', 1.5)
        plateau_size = kwargs.get('plateau_size',None) 
        #}}}
        # Map the baseline with peaks: {{{
        bkgsub = []  
        for i, entry in self._cheb_ranges.items(): 
            tth_rng = entry['tth'] # 2theta values within the specified range
            yobs_rng = entry['yobs']
            fit_bkg = entry['fit'] # Tells whether or not to chebychev fit
            yinv = yobs_rng * -1 # invert the data so the peak finding gets the baseline peaks
            cur_height_offset = entry['height_offset']
            cur_bkg_offset = entry['bkg_offset']
            cur_order = entry['order']
            
            height = kwargs.get('height',max(yinv) - cur_height_offset) # Get the current height 
            peaks = self.find_peak_positions( 
                tth_rng,
                yinv, 
                ignore_below=None,
                ignore_above=None,
                height=height, 
                threshold = threshold, 
                prominence=prominence, 
                distance=distance,
                width = width,
                wlen = wlen,
                rel_height = rel_height,
                plateau_size = plateau_size,
            ) 
            peak_x = peaks['tth']
            peak_y = peaks['yobs']

            # Modify Peak Y Positions: {{{
            mod_peak_y = []
            for curr_y in peak_y:
                mod_peak_y.append(curr_y + cur_bkg_offset)
            mod_peak_y = np.array(mod_peak_y) # convert to an array
            #}}}
            # If the range is to be fit, fit it: {{{
            if fit_bkg:
                fit = np.polynomial.chebyshev.chebfit(peak_x, mod_peak_y, deg = cur_order, full = False)  
                bkg_curve = np.polynomial.chebyshev.chebval(tth_rng, fit) * -1 # This re-inverts the fit so it can be subtracted from the positive curve  
                tmp_bkg = yobs_rng - bkg_curve # Give the background subtracted curve 
                for v in tmp_bkg:
                    bkgsub.append(v) # Add the background subtracted area to the data.
            #}}}
            # If the range is ignored: {{{
            else:
                tmp_bkg = []
                bkg_curve = []
                for v in yobs_rng:
                    tmp_bkg.append(0) # We arent subtracting anything. so make this go to zero
                    bkg_curve.append(0) # We arent subtracting anything. so make this go to zero
                    bkgsub.append(v)
                tmp_bkg = np.array(tmp_bkg)
                bkg_curve = np.array(bkg_curve)
            #}}}
            #}}}
            # update the output: {{{ 
            data = np.array(list(zip(tth_rng,tmp_bkg)))
            output.update({
                f'intermediate_{i}':
                    {
                        'data':data, 
                        'tth':tth_rng,
                        'yobs':tmp_bkg,
                        'fn':fn,
                        'peak_x':peak_x,
                        'peak_y':peak_y, 
                        'orig_y':yobs_rng,
                        'yinv':yinv,
                        'bkg_curve':bkg_curve,
                        'lower_lim':min(tth_rng),
                        'upper_lim':max(tth_rng),
                    }
            })
            #}}}
        
        data = np.array(list(zip(x, bkgsub)))
        composite_bkg_curve = []
        composite_peak_x = []
        composite_peak_y = []
        for i, v in enumerate(regions_to_eval):
            entry = output[f'intermediate_{i}']
            composite_bkg_curve.extend(list(entry['bkg_curve']))
            composite_peak_x.extend(list(entry['peak_x']))
            composite_peak_y.extend(list(entry['peak_y']))
        composite_bkg_curve = np.array(composite_bkg_curve)
        composite_peak_x = np.array(composite_peak_x)
        composite_peak_y = np.array(composite_peak_y)
        output .update( {
                'data': data, 
                'tth':x,
                'yobs':bkgsub,
                'fn':fn,
                'peak_x':composite_peak_x,
                'peak_y':composite_peak_y,  
                'orig_y':y, 
                'yinv':y*-1,
                'bkg_curve':composite_bkg_curve,
        })
        self.chebychev_output = output
        return output
    #}}}
    # _premap_data_for_chebychev_fitting: {{{ 
    def _premap_data_for_chebychev_fitting(self,tth = None,yobs = None, regions_to_eval:list = None, height_offset:list = None, bkg_offset:list = None, order:list = None):
        '''
        This function will map out the regions in your data to tag regions for fitting or exclusion. 

        regions_to_eval: list of tuples with form: (min, max)

        returns a dictionary with entries: 
        region_{i}: {
                'tth': 2theta positions within the region,
                'fit': bool (True if fitting should happen, False if ignore) 
                    }
        '''
        output = {}
        output_idx = 0
        # Loop through the regions to evaluate: {{{
        for i, (curr_region_min, curr_region_max) in enumerate(regions_to_eval):
            # Get current offsets and order: {{{
            try:
                curr_height_offset = height_offset[i] # Should get the current height offset
            except: 
                curr_height_offset = height_offset
            try: 
                curr_bkg_offset = bkg_offset[i]
            except:
                curr_bkg_offset = bkg_offset
            try: 
                curr_order = order[i]
            except:
                curr_order = order
            #}}}
            if curr_region_max == None:
                curr_region_max = max(tth)
            # Check if there are previous regions to test for gaps: {{{
            try:
                prev_region_min, prev_region_max = regions_to_eval[i-1]
            except:
                prev_region_min, prev_region_max = (None, None)
            #}}}
            # first iteration: {{{
            if i == 0:
                first_rng = np.where(tth<curr_region_min) # Get the indices below the first minimum
                second_rng = np.where((tth>curr_region_min) & (tth <= curr_region_max)) # Get indices between start and end
                if len(first_rng[0]) != 0:
                    output[output_idx] = {'tth':tth[first_rng], 'yobs':yobs[first_rng], 'fit': False, 'height_offset': 0, 'bkg_offset': 0, 'order': 0}
                    output_idx += 1
                output[output_idx] = {'tth':tth[second_rng], 'yobs':yobs[second_rng], 'fit':True, 'height_offset':curr_height_offset, 'bkg_offset':curr_bkg_offset, 'order':curr_order}
                output_idx += 1
            #}}}
            # other iterations: {{{
            else:
                # If we are continuing where we left off: {{{
                if curr_region_min == prev_region_max:
                    # This means that we havent skipped a region
                    rng = np.where((tth>curr_region_min)&(tth<=curr_region_max))
                    output[output_idx] = {'tth':tth[rng],'yobs':yobs[rng],'fit':True, 'height_offset': curr_height_offset, 'bkg_offset': curr_bkg_offset, 'order': curr_order}
                    output_idx+=1
                #}}}
                # If there is a gap:{{{ 
                else: 
                    first_rng = np.where((tth>prev_region_max) & (tth<curr_region_min)) # Get indices below the first minimum
                    second_rng = np.where((tth>curr_region_min)&(tth<=curr_region_max))
             
                    output[output_idx] = {'tth':tth[first_rng],'yobs':yobs[first_rng],'fit':False}
                    output_idx+=1
                    output[output_idx] = {'tth':tth[second_rng],'yobs':yobs[second_rng],'fit':True, 'height_offset': curr_height_offset, 'bkg_offset': curr_bkg_offset, 'order': curr_order}
                    output_idx+=1
                #}}} 

            #}}}
            # If the user doesn't give something covering the maximum of the range
            end_rng = np.where(tth>curr_region_max) # Get indices to the end of tth range
            if len(end_rng[0]) !=0 and i == len(regions_to_eval) -1:
                output[output_idx] = {'tth':tth[end_rng],'yobs':yobs[end_rng],'fit':False, 'height_offset':0, 'bkg_offset':0, 'order': 0}

        #}}}
        # test if the code succeeded: {{{
        test_tth = []
        for i, entry in output.items():
            test_tth.extend(list(entry['tth']))
        if list(test_tth) != list(tth):
            print(f'Generated tth:\n\t{test_tth}')
            print(f'Original tth: \n\t{tth}') 
            raise(Exception('Generated 2theta list not the same as input'))
        #}}}
        return output
    #}}}
    # print_bkgsub_results: {{{
    def print_bkgsub_results(self, bkgsub_data:dict = None):
        '''
        This function prints statistical information on the results of background subtraction
        '''
        scale_factors = []
        ref_peaks = []
        data_peaks = []
        tth_offsets = []
        # get data: {{{
        for i, entry in bkgsub_data.items():
            scale_factors.append(entry['scale_factor'])
            ref_peaks.append(entry['ref_peak'])
            data_peaks.append(entry['data_peak'])
            tth_offsets.append(entry['tth_offset'])
        #}}}
        # get stats: {{{
        sf_sd, sf_min, sf_max, sf_avg = (np.std(scale_factors), min(scale_factors), max(scale_factors), np.average(scale_factors))
        ref_sd, ref_min, ref_max, ref_avg  = (np.std(ref_peaks), min(ref_peaks), max(ref_peaks), np.average(ref_peaks))
        data_sd, data_min, data_max, data_avg = (np.std(data_peaks), min(data_peaks), max(data_peaks), np.average(data_peaks))
        tth_offset_sd, tth_offset_min, tth_offset_max, tth_offset_avg  = (np.std(tth_offsets), min(tth_offsets), max(tth_offsets), np.average(tth_offsets))
        #}}}
        # printouts: {{{ 
        labels = ['scale factor', 'reference peak positions', 'data peak positions', '2theta positions']
        data_labels = ['average','min','max','standard deviation']
        data = [
            [sf_avg, sf_min, sf_max, sf_sd],
            [ref_avg, ref_min, ref_max, ref_sd],
            [data_avg, data_min, data_max, data_sd],
            [tth_offset_avg, tth_offset_min, tth_offset_max, tth_offset_sd],
        ]
        for i, entries in enumerate(data):
            label = labels[i]
            print(f'{label}')
            for j, v in enumerate(entries):
                qty = data_labels[j] # Defines what v is
                print(f'\t{qty}: {np.around(v,4)}')
        #}}}
    #}}}
    #print_kwargs_for_peak_finding: {{{ 
    def print_kwargs_for_peak_finding(self):
        '''
        This function is made to allow you to quickly and easily recall what the 
        keyword arguments are for peak finding. 
        '''
        print(
            'Peak finding kwargs: \n'+
            '\tthreshold: None\n'+
            '\tdistance: None\n'+
            '\tprominence: None\n'+
            '\twidth: [0,400]\n'+
            '\twlen: None\n'+
            '\trel_height: 1.5\n'+
            '\tplateau_size: None\n'
        )
    #}}}
    # print_chebychev_manual: {{{
    def print_chebychev_manual(self):
        '''
        This function prints out a description for how to use chebychev subtration
        If you are confused about how to implement multiple region fitting, this will help
        '''
        print('To perform chebychev subtraction, you need to run "self.chebychev_subtraction"\n'+
            'This function can be run either one at a time or in an automated fashion.'+
            'If you want to run only one pattern at a time, give an index. This is useful for testing how the algorithm is working.'
                )
        print(
            'Several kewyord arguments may be used including:\n'+
            '\tlegend_x = 0.99\n'+
            '\tlegend_y = 0.99\n'+
            '\tplot_width = 1200\n'+
            '\tplot_height = 800\n'
        )
        self.print_kwargs_for_peak_finding()

        print(
            'For defining multiple regions, you can make the height_offset, bkg_offset, order, and regions_to_eval as lists.'+
            'An example is given: \n'+
            'height_offset = [90, 70]\n'+
            '\tThis means that the peak finding algorithm will have a range 90 counts below the inverted maximum to find the baseline for the first region and 70 for the second'+
            'bkg_offset = [10, 25]\n'+
            '\tThis means that the first region background curve is offset from the pattern by 10 before subtraction and the second region by 25.\n'+
            'order = [5, 8]\n'+
            '\tThis means that the first region uses a 5 term Chebychev polynomial and the second uses an 8 term polynomial.\n'+
            'regions_to_eval = [(0, 2.3), (2.3, None)]\n'+
            '\tThis means that the first region spans from 0 to 2.3 degrees. The second region extends from 2.3 degrees to the maximum observed angle. If you want to, you can also leave gaps e.g. [(0, 2.3), 4, None)] where the middle is not subtracted.\n'
            
        )
    #}}}
#}}}
