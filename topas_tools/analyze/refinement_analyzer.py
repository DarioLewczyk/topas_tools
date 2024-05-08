# Authorship: {{{
# Written by: Dario Lewczyk
# Date: 02-20-2024
#}}}
# Imports: {{{
import os, sys
import re
import glob
import copy
import numpy as np
import pandas as pd
from tqdm import tqdm
from topas_tools.utils.topas_utils import Utils, DataCollector
from topas_tools.utils.metadata_parser import MetadataParser
from topas_tools.utils.out_file_parser import OUT_Parser
from topas_tools.utils.result_parser import ResultParser
from topas_tools.utils.tcalib import TCal
from topas_tools.plotting.refinement_plotter import RefinementPlotter
from topas_tools.plotting.plotting_utils import GenericPlotter, PlottingUtils
#}}}
# RefinementAnalyzer: {{{ 
class RefinementAnalyzer(Utils,DataCollector, OUT_Parser, ResultParser, TCal,RefinementPlotter):
    '''
    RefinementAnalyzer is designed to provide the user with 
    quick access to TOPAS Rietveld Refinement data at scale.
    This class leverages other classes in modules like the 
    plotting module to deliver high quality figures 
    and actionable data fast.

    Within this class, we should create properties
    which will be attributed to this class and can be set throughout
    the program
    '''
    # __init__: {{{
    def __init__(self,):
        self._rietveld_data = {} # This holds all of the rietveld refinement data for plots and analysis
        self._metadata_data = {} # This holds all the metadata data for the data

        self.current_dir = os.getcwd() # Save the directory where the function is called. 
        DataCollector.__init__(self,metadata_data=self.metadata_data) # Initialize DataCollector with default values. 
        OUT_Parser.__init__(self)
        ResultParser.__init__(self)
        TCal.__init__(self) 
        RefinementPlotter.__init__(self, rietveld_data=self.rietveld_data) 
    #}}}
    # rietveld_data: {{{
    @property
    def rietveld_data(self):
        return self._rietveld_data
    @rietveld_data.setter
    def rietveld_data(self, new_rietveld_data):
        if not isinstance(new_rietveld_data, dict):
            raise ValueError('rietveld_data must be a dictionary!')
            self._rietveld_data = new_rietveld_data 
    #}}} 
    # metadata_data: {{{
    @property
    def metadata_data(self):
        return self._metadata_data
    @metadata_data.setter
    def metadata_data(self, new_metadata_data):
        if not isinstance(new_metadata_data, dict):
            raise ValueError('metadata_data must be a dictionary!')
        self._metadata_data = new_metadata_data
    #}}} 
    # _categorize_refined_data: {{{
    def categorize_refined_data(
            self,
            csv_labels:list = None,
            parse_out_files:bool = True, 
            correlation_threshold:int = 50, 
            flag_search:str = 'CHECK', 
            sort_hkli:bool = False,
            
        ):
        # Categorize the Refined Data: {{{
        csvs = tqdm(self.sorted_csvs, desc = "Reading Files")
        # import and process CSV, XY, OUT, HKLI:     
        for i, csv in enumerate(csvs):
            #csvs.set_description_str(f'Reading {csv}: ')
            csv_contents = [float(line) for line in open(csv)] # This gives us the values in the csv. 
            # Handle the XY Data: {{{
            try:
                #csvs.set_description_str(f'Reading {self.sorted_xy[i]}: ')
                ttheta, yobs,ycalc,ydiff = self._parse_xy(self.sorted_xy[i])
            except:
                ttheta, yobs,ycalc,ydiff = (0,0,0,0)
            #}}}
            # Handle the OUT files: {{{  
            if parse_out_files: 
                try:
                    #csvs.set_description_str(f'Reading {self.sorted_out[i]}: ')
                    c_matrix = self._parse_c_matrix(out_file=self.sorted_out[i],correlation_threshold= correlation_threshold) 
                    out_phase_dict = self._parse_out_phases(out_file=self.sorted_out[i]) # Read the output file.
                    corr_dict = self._get_correlations(c_matrix,flag_search)
                except:
                    c_matrix = None
                    out_phase_dict = None
                    corr_dict = None
            else:
                c_matrix = None
                out_phase_dict = None
                corr_dict = None
            #}}}
            # Handle the hkli files: {{{ 
            hkli_data_dict = {}
            if self.sorted_hkli:
                for si, s in enumerate(self._hkli):
                    '''
                    This section is used to get a dictionary for each substance. 
                    '''
                    hkli_entry = self._hkli[s] # This gets the dictionary entry for each substance. 
                    hkli_substance = hkli_entry['substance'] # String of the substance
                    hkli_file = hkli_entry['files'][i] # This is the hkli file we need for our current iter.
                    #csvs.set_description_str(f'Reading {hkli_file}: ')
                    hkli_data_dict.update({si:{
                        'substance': hkli_substance,
                        'hkli': self._parse_hkli(hkli_file=hkli_file,sort_hkli=sort_hkli),
                        'file':hkli_file,
                        }
                    })
            #}}}
            # Handle BKG: {{{ 
            bkg_dict = {}
            bkg_name = None
            
            if self.sorted_bkg_xy:
                try:
                    #csvs.set_description_str(f'Reading {self.sorted_bkg_xy[i]}: ') # The background should be only 1D with one bkg for each pattern.
                    bkg_tth, bkg_yobs,bkg_ycalc, bkg_ydiff = self._parse_xy(self.sorted_bkg_xy[i]) # Get the data. only care about tth and ycalc.
                    bkg_dict.update({
                        'tth': bkg_tth,
                        'ycalc': bkg_ycalc,
                    })
                    bkg_name = self.sorted_bkg_xy[i]
                except:
                    self.sorted_bkg_xy = None
            else:
                self.sorted_bkg_xy = None
            #}}}
            # Handle the Phase XY files: {{{
            phase_xy_data_dict = {}
            if self.sorted_phase_xy:
                for si, s in enumerate(self._phase_xy):
                    # This will get a dictionary for each substance.
                    try:
                        phase_xy_entry = self._phase_xy[s]
                        phase_xy_substance = phase_xy_entry['substance']
                        phase_xy_file = phase_xy_entry['files'][i] # This is the phase xy file we need for the current iteration.
                        #csvs.set_description_str(f'Reading {phase_xy_file}: ')
                        tth_p, yobs_p, ycalc_p, ydiff_p = self._parse_xy(phase_xy_file) # This returns: tth, yobs, ycalc, ydiff We are only interested in ycalc and tth
                        phase_xy_data_dict.update({
                            si: {
                                'substance': phase_xy_substance,
                                'tth': tth_p,
                                'ycalc': ycalc_p,
                                'file': phase_xy_file,
                            }
                        })
                    except:
                        phase_xy_data_dict.update({
                            'substance':'N/A',
                            'tth': None,
                            'ycalc':None,
                            'file':None,
                        })
            #}}}
            # UPDATE Rietveld Data: {{{
            try:
                self.rietveld_data[i] = {
                    'csv': {},
                    'csv_name': csv,
                    'csv_contents': csv_contents,
                    'csv_labels': csv_labels,
                    'xy':{
                        '2theta':ttheta,
                        'yobs':yobs,
                        'ycalc':ycalc,
                        'ydiff':ydiff,
                    },
                    'xy_name':self.sorted_xy[i],
                    'out_name': self.sorted_out[i],
                    'c_matrix': c_matrix,
                    'out_dict': out_phase_dict,
                    'c_matrix_filtered': corr_dict,
                    'hkli':hkli_data_dict,
                    'phase_xy': phase_xy_data_dict,
                    'bkg': bkg_dict,
                    'bkg_name': bkg_name,
     
                } # Create an entry for the csv data
            except:
                # IF the try statement doesnt work, we should neglect the entry entirely.
                pass
            #}}}
            # If you have provided CSV labels: {{{
            if csv_labels:
                for j, line in enumerate(csv_contents):
                    try:
                        if j <= len(csv_labels)-1: 
                            self.rietveld_data[i]['csv'][csv_labels[j]] = line # This records a dictionary entry with the name of the float
                        else:
                            self.rietveld_data[i][f'csv_data_{j}'] = line # If too few labels given
                    except:
                        pass
            #}}}
            # If No Provided CSV labels: {{{
            else:
                for j, line in enumerate(csv_contents):
                    try:
                        self.rietveld_data[i]['csv'][f'csv_data_{j}'] = np.around(line,4) # Add a generic label
                    except:
                        pass
            #}}}
        #}}} 
    #}}}
    # get_data: {{{
    def get_data(self, 
            data_dir:str = None,
            csv_labels:list = None, 
            file_prefix:str = "result",    
            get_orig_patt_and_meta:bool = True, 
            parse_out_files:bool = True,
            parse_hkli:bool = False, 
            correlation_threshold:int = 50,
            flag_search:str = 'CHECK', 
            check_order:bool = False,
            time_offset:float = 0.0, 
            mtf_version:int = 1,
        ):
        '''
        1. csv_labels: A list of all of the data labels for the CSV files generated.
        2. file_prefix: This should be "result" if you are using my code to generate your data.
        3. get_orig_patt_and_meta: Use this if you want to pair original pattern data with metadata
        4. parse_out_files: Use this if you want to pair data with the output file from the data for getting C matrices and other data.
        5. parse_hkli: gets h,k,l, and intensity for each structure file
        6. correlation_threshold: min correlation percentage to show in c matrix
        7. flag_search: This is the flag to look for under the correlations dictionary for c matrix
        8. check_order: If your file's timecodes are out of order, use this. It cross references metadata epoch time.
        9. time_offset: The offset of time in seconds to shift t0 (useful for doing 2 part refinements) 
        10. mtf_version: This information will change if temperature is corrected. 
        ''' 
        # Default Values Set: {{{
        print_files = False# Use this if you are having trouble finding files.
        sort_hkli = False # You can use this to sort hkli by 2theta but it is SLOW

        csv_prefix = file_prefix # All these should be the same. If not, you can change.
        xy_prefix = file_prefix
        out_prefix = file_prefix
        hkli_prefix = file_prefix
        #}}}
        # Create attributes: {{{ 
        self.corrected_range = None # only updated if you check order
        self.check_order = check_order # Save this as an attribute
        self.time_offset = time_offset
        #}}}
        # Get the sorted CSV, XY, OUT, Bkg XY: {{{
        self.sorted_csvs = sorted(glob.glob(f'{csv_prefix}_*.csv'), key = lambda x: x.split('_')[-1]) 
        self.sorted_xy = sorted(glob.glob(f'{xy_prefix}_*.xy'),key =lambda x: x.split('_')[-1])
        self.sorted_out = sorted(glob.glob(f'{out_prefix}_*.out'),key =lambda x: x.split('_')[-1]) 
        self.sorted_phase_xy = None # This will stay none unless you also parse hkli. 
        self.sorted_bkg_xy = sorted(glob.glob('bkg*.xy'), key = lambda x: x.split('_')[-1]) # These are the background curves if they are there.
        #}}} 
        # Get HKLI Files: {{{
        if parse_hkli:
            self.sorted_hkli = sorted(glob.glob(f'*_{hkli_prefix}_*.hkli')) # These files should be in the format: Substance_result_Info.hkli
        else:
            self.sorted_hkli = None
        #}}}
        # Pre-Process to get HKLI AND Phase XY if Present: {{{
        if self.sorted_hkli:
            self._hkli = {} # Create a dictionary for the sorted files. 
            self._phase_xy = {} # Create a dictionary for the sorted phase xy files
            substances = [] 
            # Get unique substances: {{{
            for f in self.sorted_hkli: 
                substance = f.split('_') # It is possible that the substance label has more than just the substance in it. 
                split_sub = []
                for w in substance:
                    if w != 'result':
                        split_sub.append(w)
                    else:
                        break
                substance = '_'.join(split_sub) # Rejoin the substance tag
                if substance not in substances: 
                    substances.append(substance)
            #}}}
            # Create self._phase_xy and self._hkli: {{{
            for substance in substances:
                hkli_files = glob.glob(f'{substance}_{hkli_prefix}_*.hkli')
                phase_xy_files = glob.glob(f'{substance}_*.xy')
                sorted_hkli = sorted(hkli_files, key = lambda x: x.split('_')[-1]) # This gives only files pertaining to your substance. 
                self.sorted_phase_xy = sorted(phase_xy_files, key = lambda x: x.split('_')[-1]) # This gives only the xy files pertaining to your substance.
                self._phase_xy[substances.index(substance)] = {'substance': substance, 'files': self.sorted_phase_xy}
                self._hkli[substances.index(substance)] = {'substance': substance,'files': sorted_hkli} 
            #}}}
        #}}}
        # GET ORIGINAL Data and METADATA: {{{
        if get_orig_patt_and_meta:
            if data_dir:
                if os.path.isdir(data_dir) and os.path.isdir(os.path.join(data_dir,'meta')):
                    self.data_dir = data_dir
                    self.meta_dir = os.path.join(self.data_dir, 'meta')
                    os.chdir(self.data_dir)
                else:
                    print(f'{data_dir} was invalid! Select the right one.')
                    data_dir = None
            if not data_dir:
                print('Navigate to the data directory.')
                self.data_dir = self.navigate_filesystem()
                self.meta_dir = os.path.join(self.data_dir,'meta') # This gives us the metadata folder
            # Get all of the original data and times: {{{
            self.scrape_files() # Gather the original data.  
            self.file_dict_keys = list(self.file_dict.keys()) # Gives us the times. 
            #}}}
            # Work with the metadata: {{{
            os.chdir(self.meta_dir) # Go into the metadata
            self._md = MetadataParser(metadata_data=self.metadata_data)
            self._md.get_metadata()
            #self.metadata_data = self._md.metadata_data
            #}}}
            os.chdir(self.current_dir) # Return to the original directory.
            # If you need to check the order of patterns against metadata: {{{
            if self.check_order:
                num_scans_refined = len(self.sorted_csvs) # This is the most robust counter of the total patterns.
                tmp_rng = np.linspace(1,len(self.file_dict_keys), num_scans_refined) # Get the original indices of each pattern.
                #dc = DataCollector(metadata_data=self.metadata_data) # Need to init this class to check the order.
                self.corrected_range = dc.check_order_against_time(tmp_rng=tmp_rng, data_dict_keys=self.file_dict_keys,metadata_data=self.metadata_data, mode=1) #Get a new order
                # Correct the file lists: {{{
                # Define temporary lists for data: {{{
                tmp_csv = []
                tmp_xy = []
                tmp_out = [] 
                tmp_bkg_xy = [] 
                #}}}
                for rng_idx in self.corrected_range:
                    tmp_csv.append(self.sorted_csvs[rng_idx]) # Adds the correct csv in the correct order
                    tmp_xy.append(self.sorted_xy[rng_idx])
                    tmp_out.append(self.sorted_out[rng_idx])
                    try:
                        tmp_bkg_xy.append(self.sorted_bkg_xy[rng_idx])
                    except:
                        print('Failed to correct bkg curves!')
                self.sorted_csvs = tmp_csv
                self.sorted_xy = tmp_xy
                self.sorted_out = tmp_out
                self.sorted_bkg_xy = tmp_bkg_xy
                #}}}
                # Now, Handle the phase XYs{{{
                try:
                    for xy_key, xy_val in self._phase_xy.items():
                        tmp_xy_file_list= [] # Updated list
                        tmp_hkli_file_list = [] # Updated list

                        original_xy_file_list = xy_val['files']
                        original_hkli_file_list = self._hkli[xy_key]['files']

                        for i in self.corrected_range:
                            tmp_xy_file_list.append(original_xy_file_list[i]) # Add in the position corrected file.
                            tmp_hkli_file_list.append(original_hkli_file_list[i]) # Add the position corrected file

                        self._phase_xy[xy_key]['files'] = tmp_xy_file_list
                        self._hkli[xy_key]['files'] = tmp_hkli_file_list
                except:
                    print('Failed to re-order substance-specific XY and HKLI files.')
                    raise
                            
                #}}} 
            #}}}
        #}}}
        # Print Statements: {{{
        if print_files:
            print('I   CSV\tXY')
            for i, fn in enumerate(self.sorted_csvs):
                print(f'{i}: {fn}\t{self.sorted_xy[i]}')
        #}}}
        # We need to first check if each of the file lists are of the same length: {{{
        try:
            csvs = len(self.sorted_csvs)
            xys = len(self.sorted_xy)
            outs = len(self.sorted_out) 
            if self.sorted_phase_xy:
                phase_xys = len(self.sorted_phase_xy)
            else:
                phase_xys = len(csvs)
            if self.sorted_bkg_xy:
                bkg_xys = len(self.sorted_bkg_xy)
            else:
                bkg_xys = len(csvs)
            print(f'csvs: {csvs}\nxys: {xys}\nouts: {outs}\nphase_xys: {phase_xys}\nbkg_xys: {bkg_xys}')
            
           
        except:
            print(f'failed to get all files')
        
        
        #}}}
        # categorize the data: {{{
        self.categorize_refined_data(csv_labels, parse_out_files, correlation_threshold, flag_search, sort_hkli)
        #}}} 
        # Update Rietveld Data With Original Pattern Info and Metadata: {{{
        if get_orig_patt_and_meta:
            # Now, we want to update the "rietveld_data" dict: {{{ 
            for i in self.rietveld_data:
                entry = self.rietveld_data[i] # Gives us the data entry. 
                file_time = int(re.findall(r'\d+',entry['csv_name'])[0]) # This gives the time of the file. 
                try:
                    md = self.metadata_data[file_time]
                except:
                    print(f'Failed to find time: {file_time} in metadata.\nYour file times are:')
                    sys.exit()
                fd = self.file_dict[file_time]
                # Correct temperature (IF NEEDED): {{{
                if mtf_version > 1:
                    corrected_t = md['temperature']
                    self.min_tcalc = corrected_t
                    self.max_tcalc = corrected_t
                elif mtf_version == 1:
                    corrected_t = self.correct_t(md['temperature']) # Correct the temperature using the function
                #}}}
                self.rietveld_data[i].update({
                    'original_name':fd,
                    'readable_time':md['readable_time'],
                    'epoch_time':md['epoch_time'],
                    'temperature':md['temperature'],
                    'pct_voltage':md['pct_voltage'],
                    'corrected_temperature': corrected_t,
                    'min_t':self.min_tcalc,  # Min temp (error bar)
                    'max_t':self.max_tcalc, # Max temp (error bar)
                    'pattern_index':md['pattern_index'],
                    'MTF_version': mtf_version,
                })
            for i ,entry in self.rietveld_data.items():     
                self._get_time(i,time_units='s', check_order=self.check_order) # get the time in seconds
                self.rietveld_data[i].update({
                    'corrected_time': self._current_time 
                })
            #}}} 
        #}}} 
        self._data_collected = True #Now, the data have been collected and plot pattern will be informed
    #}}}
    # _get_time{{{
    def _get_time(self,index, time_units:str, check_order:bool = False):
        '''
        This function will obtain for you, the time relative to the start of the run. 
        This uses the epoch time from metadata. SO MAKE SURE IT IS PRESENT. 
        Also, this uses the absolute beginning pattern's epoch time
        '''
        metadata_keys = list(self.metadata_data.keys()) #these are the "readable times" 0th index is the first pattern of the series. 
        t0_idx = 0 # This is the default but can change if the order is messed up. 
        t0 = None
        if check_order:
            for i, (key, entry) in enumerate(self.metadata_data.items()):
                epoch = entry['epoch_time']
                if i == 0:
                    t0 = epoch
                else:
                    t = epoch - t0 # Elapsed time
                    if t < 0:
                        t0_idx = i # This is the index of the metadata keys which is the first time point. 
                        break    
        t0 = self.metadata_data[metadata_keys[t0_idx]]['epoch_time'] # This gives us the epoch time for the first pattern. 
        t1 = self.rietveld_data[index]['epoch_time'] # This is the time of the current pattern. 
        # Determine the appropriate divisor: {{{
        if time_units == 's':
            divisor = 1
        elif time_units == 'min':
            divisor = 60
        elif time_units == 'h':
            divisor = 60**2
        #}}}
        # Get the time: {{{
        self.t0 = t0
        self._current_time = (t1-t0 + self.time_offset)/divisor  # This will correct the output temperature
        #}}}


    #}}}
    # get_pattern_from_time: {{{
    def get_pattern_from_time(self, time:float = None, units:str = 'min'):
        '''
        The purpose of this function is to get the number of the pattern in a time series
        by inputting the time you find from looking at a plot. 

        It gives the index of the pattern relative to the number of patterns you refined. 
        ''' 
        # Convert time to seconds: {{{
        if units == 's':
            conv_time = time
        elif units == 'min':
            conv_time = time*60 # Convert minutes to seconds
        elif units == 'h':
            conv_time = time*60**2 # Convert hours to seconds

        #}}}
        closest_pattern_below = 0
        closest_pattern_above = 0
        pattern_above_idx = None
        exact_pattern = None
        # Go through the patterns and determine if the time given is greater than or less than the recorded time: {{{
        for i, pattern in enumerate(self.rietveld_data):
            p_time = self.rietveld_data[pattern]['corrected_time'] # This gives the time for the pattern
            if p_time < conv_time:
                closest_pattern_below = pattern
            elif p_time > conv_time:
                if not pattern_above_idx:
                    closest_pattern_above = pattern
                    pattern_above_idx = i
            if p_time == conv_time:
                exact_pattern = pattern
                break
        #}}} 
        # Check for the exact pattern: {{{
        if not exact_pattern:
            if closest_pattern_above - 1 > closest_pattern_below:
                exact_pattern = closest_pattern_above - 1 # This will be the pattern between 
            else:
                exact_pattern = f'Either: {closest_pattern_below} or {closest_pattern_above}'
        #}}}
        # Create the Output Printout: {{{ 
        rr_data_below = self.rietveld_data[closest_pattern_below]
        rr_data_above = self.rietveld_data[closest_pattern_above]
        below_csv = rr_data_below['csv_name']
        above_csv = rr_data_above['csv_name']
        
        below_orig = rr_data_below['original_name']
        above_orig = rr_data_above['original_name']


        final_printout = f'{exact_pattern}\nPoss Low IDX:\n\t{below_csv}\n\t{below_orig}\nPoss High IDX:\n\t{above_csv}\n\t{above_orig}'
        #}}}
        print(final_printout)

    #}}}
    # get_pattern_dict: {{{
    def get_pattern_dict(self,
            index:int = None, 
            hkli_threshold = 1e-5, 
            return_dataframes:bool = True, 
            offset_val = -100, 
            offset_multiplier = 1
        ):
        '''
        This function will return a dictionary with all of the relevant information to 
        recreate any of the single pattern plots output by this code. 
        '''
        entry = self.rietveld_data[index]
        self.pattern_dict = {} # This will be a dictionary containing all the info we want for a pattern.  
        xy = entry['xy']
        phase_xy = entry['phase_xy']
        rietveld_hkli = entry['hkli']
        bkg = entry['bkg'] 
        # Update the xy observed data {{{
        self.pattern_dict.update(xy)
        #}}}  
        # Update the phase_xy data: {{{
        for idx, phase_dict in phase_xy.items():
            substance = phase_dict['substance'] # This should accompany each entry recorded. 
            ycalc = phase_dict['ycalc'] # This is the calculated intensity across the tth range for the phase. 
            self.pattern_dict[f'{substance}_ycalc'] = ycalc
        #}}}
        # Update the background data: {{{
        self.pattern_dict['bkg_calc'] = bkg['ycalc']
        #}}}
        base_pattern_info = copy.deepcopy(self.pattern_dict)
        # Update the hkli data: {{{
        hkli_dicts = []
        multiplier = offset_multiplier
        for idx, hkli_dict in rietveld_hkli.items():
            substance = hkli_dict['substance']
            hkli = hkli_dict['hkli'] # This contains: hkl, m, d, tth, i
            hkl = hkli['hkl']
            d = hkli['d']
            tth = hkli['tth']
            offset = [offset_val*multiplier]*len(tth)
            multiplier += 1
            i = hkli['i']
            reported_hkl = []
            reported_d = []
            reported_tth = []
            reported_offset = []
            reported_i = []
            for idx,val in enumerate(i):
                if val > hkli_threshold:
                    reported_hkl.append(hkl[idx])
                    reported_d.append(d[idx])
                    reported_tth.append(tth[idx])
                    reported_offset.append(offset[idx])
                    reported_i.append(val)
            reported_dict = {
                f'{substance}_tth': reported_tth,
                f'{substance}_offset': reported_offset,
                f'{substance}_hkl': reported_hkl,
                f'{substance}_d': reported_d,
                f'{substance}_i': reported_i,
            }
            self.pattern_dict.update(reported_dict) 
            hkli_dicts.append(pd.DataFrame(reported_dict)) # Add dataframes to the output 
        #}}}
        reported_output = []
        reported_output.append(pd.DataFrame(base_pattern_info))
        reported_output.extend(hkli_dicts)
        output = tuple(reported_output) # This makes the output into a tuple of variable length depending upon the phases
        if return_dataframes:
            print(f'returning {len(output)} dataframes...')
            return output 
    #}}}
#}}}
