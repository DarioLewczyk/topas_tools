# Authorship: {{{
'''
Written by: Dario C. Lewczyk
Date: 05-16-24
Purpose:
    This code is written to allow a user to 
    background subtract synchrotron data with known 
    background components. 

    Generally speaking, it is best if you have separate diffraction patterns
    for all of the components individually to perform the subtraction
    If you are dealing with glass, you should have the following: 

    1. air scatter
    2. glass
    3. your data
'''
#}}}
# Imports: {{{
import os, sys
import copy
import re
import numpy as np
from tqdm import tqdm
import shutil

from topas_tools.utils.topas_utils import Utils, DataCollector, UsefulUnicode
from topas_tools.utils.bkgsub_utils import BkgsubUtils
from topas_tools.plotting.bkgsub_plotting import BkgSubPlotter
#}}}
# Bkg_Sub: {{{
class Bkgsub(Utils, BkgsubUtils, BkgSubPlotter):
    '''
    Class to enable background subtraction of 
    glass backgrounds. 

    Note: you will get the best results if you 
    background subtract with both an air and glass 
    diffraction pattern.
    '''
    # __init__: {{{
    def __init__(self,
            glass_dir:str = None,
            air_dir:str = None,
            data_dir:str = None,
            fileextension:str = 'xy',
            position_of_time = 1,
            len_of_time = 6,  
            skiprows = 1,  
            tolerance = 0.001,
        ):
        '''
        glass_dir: directory where your reference glass is
        air_dir: directory where your air scatter is
        data_dir: directory to perform background subtraction on

        fileextension: the extension to look for for data collection
        mode: This refers to the mode parameter of DataCollector.
        position_of_time: refer to DataCollector
        len_of_time: refer to DataCollector
        skiprows: refer to DataCollector
        tolerance: refers to the maximum difference for pattern file spacing to be equivalent
        
        Peak finding parameters (SiO2)
            height
            threshold 
            distance 
            prominence
            width
            wlen
            rel_height
            plateau_size
        '''
        # Default values for peak finding{{{ 
        '''
        The reason these are saved is for use later.
        '''
        self._height = [950, 1800]
        self._threshold = None
        self._distance = None
        self._prominence = None
        self._width = [0,100]
        self._wlen = None
        self._rel_height = 0.5
        self._plateau_size = None
        #}}}
        glass_file = None
        air_file = None
        data_files = None
        UsefulUnicode.__init__(self)
        
        # Configuration: {{{ 
        # Get Glass Data: {{{
        # If NO Glass Dir: {{{
        if not glass_dir:
            print('Please navigate to your GLASS reference folder.')
            glass_dir = self.navigate_filesystem()
        #}}}
        # If the glass dir is not valid: {{{
        if not os.path.isdir(glass_dir):
            print(f'{glass_dir} is invalid!')
            print('Please navigate to your GLASS reference folder.')
            glass_dir = self.navigate_filesystem()
        #}}}
        # Normal operation: {{{
        os.chdir(glass_dir)
        glass_files = DataCollector(
                fileextension = fileextension,
                position_of_time = position_of_time,
                len_of_time = len_of_time,
                skiprows = skiprows,
            )
        glass_files.scrape_files()
        glass_files = list(glass_files.file_dict.values())
        if len(glass_files) > 1:
            print('Please select the index of the GLASS file')
            glass_file = self.prompt_user(glass_files) # Show the user all the files found
        elif len(glass_files) == 1:
            glass_file = glass_files[0]
        else:
            raise(ValueError('There were no files in this directory!'))
        #}}}
        #}}}
        # Handle the Air Case: {{{
        # Get air Data: {{{
        if not air_dir:
            response = self.prompt_user(['yes'])
            if response:
                print('Please navigate to your air scatter reference folder.')
                air_dir =  self.navigate_filesystem()
        #}}}
        # IF You want to do air sub: {{{
        if air_dir:
            # Handle the case where the air directory is invalid: {{{ 
            if not os.path.isdir(air_dir):
                print(f'{air_dir} is invalid!')
                print('Please navigate to your AIR reference folder.')
                air_dir = self.navigate_filesystem()
            #}}}
            os.chdir(air_dir)
            air_files = DataCollector(
                    fileextension = fileextension,
                    position_of_time = position_of_time,
                    len_of_time = len_of_time,
                    skiprows = skiprows,
                )
            air_files.scrape_files()
            air_files = list(air_files.file_dict.values())
            if len(air_files) > 1:
                print('Please select the index of the AIR file')
                air_file = self.prompt_user(air_files) # Show the user all the files found
            elif len(air_files) == 1:
                air_file = air_files[0]
            else:
                raise(ValueError('There were no files in this directory!'))   
        #}}}
        #}}}
        # Handle the Data directory: {{{
        # If NO Data Dir: {{{
        if not data_dir:
            print('Please navigate to your DATA folder.')
            data_dir = self.navigate_filesystem()
        #}}}
        # If the Data Dir is not valid: {{{
        if not os.path.isdir(data_dir):
            print(f'{data_dir} is invalid!')
            print('Please navigate to your DATA folder.')
            data_dir = self.navigate_filesystem()
        #}}}
        # Normal operation: {{{
        os.chdir(data_dir)
        data_files = DataCollector(
                fileextension = fileextension,
                position_of_time = position_of_time,
                len_of_time = len_of_time,
                skiprows = skiprows,
            )
        data_files.scrape_files()
        data_files= data_files.file_dict # Make this one the full data dict
        if len(data_files) >= 1:
            pass
        else:
            raise(ValueError('There were no files in this directory!'))
        #}}}
        #}}}
        # Now, initialize internal variables: {{{
        self.glass_file = glass_file # This is the filename for the glass
        self.air_file = air_file # This is the filename for the air if there is one
        self.data_files = data_files # These will be all the data files 
        self._glass_dir = glass_dir
        self._air_dir = air_dir
        self._data_dir = data_dir
        # Get the new path for output: {{{
        # prefix: {{{
        if not air_file:
            prefix = 'glass_sub'
        else:
            prefix = 'air_and_glass_sub'
        #}}}
        #  New Dir Name: {{{
        basename = os.path.basename(self._data_dir)
        if basename == '':
            basename = os.path.dirname(self._data_dir)
            basename = os.path.basename(basename) # This makes sure we get the text from the data folder
        new_dir_name = f'{prefix}_{basename}'
        #}}}
        # Dirname: {{{
        dirname = os.path.dirname(self._data_dir)
        if os.path.basename(dirname) == basename:
            dirname = os.path.dirname(dirname) # Go back another directory. 
        self.output_dir = os.path.join(dirname, new_dir_name)
        #}}}
        #  Make the directory: {{{ 
        if not os.path.exists(self.output_dir):
            os.mkdir(self.output_dir)
        #}}}
        #}}} 
        #}}} 
        #}}}
        # Import data: {{{
        self.patterns = self._import_bkgsub_data(skiprows=skiprows, len_of_time = len_of_time) 
        #}}}
        # If an air file was loaded, subtract it from the glass pattern: {{{
        if air_file:
            air_sub_data = self.subtract_patterns(self.patterns['glass']['data'], self.patterns['air']['data'], tolerance = tolerance)
            self.patterns.update({
                'air_sub_glass':  {
                    'data': air_sub_data,
                    'tth': air_sub_data[:,0],
                    'yobs':air_sub_data[:,1],
                    'fn':'air_sub_glass',
                    }
                })
        else:
            self.patterns.update({
                'air_sub_glass':None
                })
        #}}}

    #}}} 
    # get_glass_ref_peak: {{{
    def get_glass_ref_peak(self, 
            plot_result:bool = True,
            print_results:bool = True, 
           **kwargs, 
        ):
        '''
        kwargs: 
            height
            threshold
            distance
            prominence
            width
            wlen
            rel_height
            plateau_size

            plot_height
            plot_width
            legend_x
            legend_y
        This function is used to assign the glass peak. 
        It uses printouts and plots to give real-time feedback on how well the fitting algorithm is working. 
        '''
        # Set defaults: {{{
        height= kwargs.get('height',self._height) 
        threshold = kwargs.get('threshold',self._threshold) 
        distance = kwargs.get('distance',self._distance)
        prominence = kwargs.get('prominence',self._prominence)
        width =kwargs.get('width', self._width)
        wlen = kwargs.get('wlen',self._wlen)
        rel_height = kwargs.get('rel_height', self._rel_height)
        plateau_size = kwargs.get('plateau_size',self._plateau_size)
        # update defaults: {{{
        self._height = height
        self._threshold = threshold
        self._distance = distance
        self._prominence = prominence
        self._width = width
        self._wlen = wlen
        self._rel_height = rel_height
        self._plateau_size = plateau_size
        #}}}

        plot_height = kwargs.get('plot_height', 800)
        plot_width  = kwargs.get('plot_width', 1000)
        legend_x  = kwargs.get('legend_x', 0.99)
        legend_y = kwargs.get('legend_y', 0.99)
        #}}} 
        # Assign x,y based on air sub or not: {{{
        if self.patterns['air_sub_glass']:
            air_sub = self.patterns['air_sub_glass']
            x = air_sub['tth']
            y = air_sub['yobs']
            name = air_sub['fn']
        else:
            glass = self.patterns['glass']
            x = glass['tth']
            y = glass['yobs']
            name = glass['fn']
        #}}}
        # self.glass_ref_peaks: {{{
        self.glass_ref_peaks = self.find_peak_positions(
            x = x,
            y = y,
            height = height,
            threshold = threshold,
            distance=distance,
            prominence = prominence,
            width = width,
            wlen = wlen,
            rel_height=rel_height,
            plateau_size = plateau_size,
        )
        #}}}
        gp = self.glass_ref_peaks
        # Print information about the glass peaks: {{{
        if print_results:      
            print(f'{gp["peak_info"]}\n')
            for i, idx in enumerate(gp['peak_idx']): 
                tth = gp['tth'][i]
                intensity = gp['yobs'][i]
                print(f'Peak_IDX: {idx}\n\ttth: {tth}\n\tIntensity: {intensity}')
        #}}}
        # Plot the result: {{{
        if plot_result:
            self.plot_pattern_with_peaks(
                pattern_tth = x,
                pattern_yobs = y,
                pattern_name = name,
                peaks_tth= gp['tth'],
                peaks_yobs=gp['yobs'],
                peaks_name = 'Glass Peaks',
                height = plot_height,
                width = plot_width,
                legend_x = legend_x,
                legend_y = legend_y,
            )
        #}}}
    #}}}
    # get_data_glass_peak: {{{ 
    def get_data_glass_peak(self,
            idx:int = 0,
            run_in_loop:bool = False,
            glass_peak_idx:int = 0,
            tolerance_for_bkgsub:float = 0.001,
            plot_result:bool = True,
            print_results:bool = True, 
            **kwargs):
        '''
        Uses the same kwargs as the glass peak finder.

        idx: the index of pattern from your dataset you want to test on
        run_in_loop: if true, this creates a dictionary of all glass peak positions
        glass_peak_idx: this is the index of the peak used to align your ref pattern
        tolerance_for_bkgsub: This is the tolerance for 2theta positions to be equal.
        '''
        # defaults/kwargs: {{{
        height = kwargs.get('height', self._height)
        threshold= kwargs.get('threshold',self._threshold)
        distance = kwargs.get('distance',self._distance)
        prominence = kwargs.get('prominence',self._prominence)
        width = kwargs.get('width', self._width)
        wlen = kwargs.get('wlen',self._wlen)
        rel_height = kwargs.get('rel_height', self._rel_height)
        plateau_size = kwargs.get('plateau_size', self._plateau_size)

        plot_height = kwargs.get('plot_height', 800)
        plot_width  = kwargs.get('plot_width', 1000)
        legend_x  = kwargs.get('legend_x', 0.99)
        legend_y = kwargs.get('legend_y', 0.99)
        #}}}
        data = self.patterns['data'] # Get the data that were loaded
        # If not run in loop: {{{
        if not run_in_loop:
            data = data[idx] 
            x = data['tth']
            y = data['yobs']
            name = data['fn'] # Used in the plots if you show them
            # Find peak positions and update dict: {{{
            res = self.find_peak_positions(
                x = x,
                y = y,
                height=height,
                threshold = threshold,
                distance = distance,
                prominence = prominence,
                width = width,
                wlen = wlen,
                rel_height = rel_height,
                plateau_size = plateau_size,
            )
            #}}}
        #}}}
        # if run in loop: {{{
        else:
            # Define output attributes: {{{
            self.data_peaks = {}
            self.bkgsub_data = {}
            #}}}
            loop_failures = [] # This keeps track of the indices where no peaks were obtained
            loop_warnings = [] # This keeps track of the indices where there are more than one peak.
            plot_result = False # This would be too much for looping
            print_results = False # This would be too much for looping
            d = tqdm(data) # Make a progress bar for the peak finding.
            for i, idx in enumerate(d): 
                entry = data[idx] # Get the current entry
                x = entry['tth']
                y = entry['yobs']
                # Find the peak positions & Update dict: {{{
                self.data_peaks[idx] = self.find_peak_positions(
                    x = x,
                    y = y,
                    height = height,
                    threshold = threshold,
                    distance = distance,
                    prominence = prominence,
                    width = width,
                    wlen = wlen,
                    rel_height = rel_height,
                    plateau_size = plateau_size,
                )
                if len(self.data_peaks[idx]['peak_idx']) == 0:
                    loop_failures.append(idx)
                elif len(self.data_peaks[idx]['peak_idx']) >1:
                    loop_warnings.append(idx)

                #}}}
            # Printout for failures: {{{
            if loop_failures:
                print(f'The following indices failed to obtain a glass peak: \n\t{loop_failures}')
                print(f'You should change your parameters: \n\theight: {height}\n\tthreshold: {threshold}'+
                        f'\n\tdistance: {distance}\n\tprominence: {prominence}\n\twidth: {width}\n\twlen: {wlen}'+
                        f'\n\trel_height: {rel_height}\n\tplateau_size: {plateau_size}'
                        )
            #}}}
            # Printout for warnings: {{{
            if loop_warnings:
                if loop_failures:
                    print('\n')
                print(f'The following indices returned more than one peak... be sure that the glass idx is consistent\n\t {loop_warnings}')
                print(f'You may want to change your parameters: \n\theight: {height}\n\tthreshold: {threshold}'+
                        f'\n\tdistance: {distance}\n\tprominence: {prominence}\n\twidth: {width}\n\twlen: {wlen}'+
                        f'\n\trel_height: {rel_height}\n\tplateau_size: {plateau_size}'
                        )
            #}}}
            # if NO failures, continue to shifting the bkg and running subtraction: {{{
            if not loop_failures:
                print('Now, shifting glass for each pattern.')
                self.shifted_glass_ref = {} # This will contain the shifted glass stuff for the dataset
                d = tqdm(data) # Make a new progress bar
                for i, idx in enumerate(d):
                    # define the offset: {{{  
                    tth_offset = self.data_peaks[idx]['tth'][glass_peak_idx] - self.glass_ref_peaks['tth'][0]
                    #}}}
                    # Get a copy of the glass reference data: {{{
                    air_sub = self.patterns['air_sub_glass']
                    glass = self.patterns['glass']
                    if air_sub:
                        shifted_glass = air_sub['data'].copy()
                        fn = air_sub['fn']
                    else:
                        shifted_glass = glass['data'].copy()
                        fn = glass['fn']
                    #}}}
                    # Perform the 2theta shift: {{{
                    shifted_x1 = [x+tth_offset for x in shifted_glass[:,0]]
                    shifted_glass[:,0] = shifted_x1 # Update the 2 theta with the shift
                    # Run peak finding with defaults. (Set by the glass manual assignment)
                    shifted_peaks = self.find_peak_positions(
                            x = shifted_glass[:,0], 
                            y = shifted_glass[:,1],
                            height = self._height,
                            threshold=self._threshold,
                            distance = self._distance,
                            prominence = self._prominence,
                            width = self._width,
                            wlen = self._wlen,
                            rel_height = self._rel_height,
                            plateau_size = self._plateau_size,
                    )
                    self.shifted_glass_ref[idx] = {
                            'pattern_info': {
                                'data': shifted_glass,
                                'tth': shifted_glass[:,0],
                                'yobs': shifted_glass[:,1],
                                'fn':fn,
                                },
                            'peak_info': shifted_peaks,
                    }
                    #}}}
                    # First Scale Background: {{{ 
                    ref_peak = self.shifted_glass_ref[idx]['peak_info']['yobs'][0] # Shifted glass peak
                    data_peak = self.data_peaks[idx]['yobs'][glass_peak_idx] # Data glass peak

                    scaled_glass = self.scale_reference(shifted_glass, ref_peak, data_peak)
                    self.shifted_glass_ref[idx].update({'scaled_glass': scaled_glass}) # Update the dictionary
                    #}}}
                    # Then background subtract/interpolate if necessary: {{{
                    d1 = data[idx]['data'] # This is the dataset for the current pattern
                    d2 = scaled_glass['data'] # This is the dataset for the current scaled glass
                    glass_sub_data = self.subtract_patterns(d1 = d1, d2 = d2, tolerance = tolerance_for_bkgsub)
                    self.bkgsub_data[idx] = {
                            'data': glass_sub_data,
                            'tth': glass_sub_data[:,0],
                            'yobs': glass_sub_data[:,1],
                            'fn':data[idx]['fn'],
                    }
                    #}}}

            #}}} 
        #}}}
        # Print information about the data peaks: {{{
        if print_results or plot_result:
            dp = res # This gives the index you selected
        if print_results:      
            print(f'{res["peak_info"]}\n')
            for i, idx in enumerate(res['peak_idx']): 
                tth = res['tth'][i]
                intensity = res['yobs'][i]
                print(f'Peak_IDX: {idx}\n\ttth: {tth}\n\tIntensity: {intensity}')
        #}}}
        # Plot the result: {{{
        if plot_result:
            self.plot_pattern_with_peaks(
                pattern_tth = x,
                pattern_yobs = y,
                pattern_name = name,
                peaks_tth= res['tth'],
                peaks_yobs= res['yobs'],
                peaks_name = f'Data Peaks (idx: {idx})',
                height = plot_height,
                width = plot_width,
                legend_x = legend_x,
                legend_y = legend_y,
            )
        #}}} 
        # Return for if you are not running in a loop: {{{
        if not run_in_loop:
            return res
        #}}}
    #}}}
    # output_results: {{{
    def output_results(self,):
        '''
        This will output the data and copy the metadata for the data
        to the output directory.
        '''
        prog = tqdm(self.bkgsub_data) # Create a progress bar
        md_srce = os.path.join(self._data_dir,'meta')
        md_dest = os.path.join(self.output_dir, 'meta')
        # Save all of the data in .xy format: {{{
        os.chdir(self.output_dir) # Go to the output directory
        for i, idx in enumerate(prog):
            res = self.bkgsub_data[idx]

            x = res['tth']
            y = res['yobs']
            fn = res['fn']  
            # write the xy file: {{{
            with open(fn,'w+') as f:
                f.write('X\tI\n') # Write the header
                for j,xval in enumerate(x): 
                    yval = y[j]
                    f.write(f'{xval}\t{yval}\n')
                f.close()

            #}}}
        # copy the metadata folder and everything in it to the destination: {{{
        if not os.path.exists(md_dest):
            shutil.copytree(
                md_srce,
                md_dest,
            )
        #}}}
            
        #}}} 
        print(f'Your data were saved under:\n\t{self.output_dir}')
    #}}}
#}}}
