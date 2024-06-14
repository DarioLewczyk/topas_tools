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
            os.chdir(path) # Go to the path where the data are first
            entry = entries[i]
            fn = files[i] # Will either be a singular file or a list of files.
            data_dict[entry] = {} # Initialize the entry
            dirs.set_description_str(f'Collecting {entry}')
            # If Skip over Air: {{{
            if type(fn) == None:
                data_dict[entry] = None
                    
            #}}}
            #  Get the data: {{{
            elif type(fn) != str:
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
                        data = np.loadtxt(new_f,skiprows=1) 
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
            ignore_below = 1,
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
        # ignore below: {{{
        passing_x = np.where(x>ignore_below) # Gives the indices above the set threshold
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
        '''
        
        x = bkgsub_data[idx]['tth']
        y = bkgsub_data[idx]['yobs']
        fn = bkgsub_data[idx]['fn']
        yinv = y * -1 # Invert the data so peak finding gets baseline peaks
        # Defaults: {{{
        height = kwargs.get('height',max(yinv) - height_offset)
        threshold = kwargs.get('threshold',None)
        distance = kwargs.get('distance',None)
        prominence =kwargs.get('prominence',None)
        width = kwargs.get('width',[0,400])
        wlen = kwargs.get('wlen', None)
        rel_height = kwargs.get('rel_height', 1.5)
        plateau_size = kwargs.get('plateau_size',None)
        ignore_below = kwargs.get('ignore_below', 1)
        #}}}
        # Map the baselinge with peaks: {{{
        peaks = self.find_peak_positions(
                x, 
                yinv, 
                ignore_below=ignore_below,
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
        #}}}
        # Modify Peak Y Positions: {{{
        mod_peak_y = []
        for i, curr_y in enumerate(peak_y):
            mod_peak_y.append(curr_y + bkg_offset)
        mod_peak_y = np.array(mod_peak_y) # convert to an array
        #}}}
        # Fit the background using the modified peak positions: {{{
        if ignore_below:
            new_x = []
            for tth in x:
                if tth < ignore_below:
                    new_x.append(max(x))
                else:
                    new_x.append(tth)
        else:
            new_x = x
        new_x = np.array(new_x)

        fit = np.polynomial.chebyshev.chebfit(peak_x, mod_peak_y, deg = order, full = False) 
        bkg_curve = np.polynomial.chebyshev.chebval(new_x, fit) * -1 # This re-inverts the fit so it can be subtracted from the positive curve
        bkgsub = y - bkg_curve # Give the background subtracted curve
        #}}}
        data = np.array(list(zip(x,bkgsub )))
        output = {
                'data': data,
                'tth': x,
                'yobs':bkgsub,
                'fn':fn,
                'peak_x':peak_x,
                'peak_y':peak_y,
                'orig_y':y,
                'yinv':yinv, 
                'bkg_curve':bkg_curve,
        }
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
#}}}
