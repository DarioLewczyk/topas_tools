# Authorship: {{{
# Written by: Dario Lewczyk
# Date: 02-20-2024
#}}}
# Imports: {{{
import os
import re
import glob
import numpy as np
import texttable
from PIL import Image
#}}}
# Utils: {{{
class Utils: 
    # __init__: {{{
    def __init__(self):
        self._default_kwargs = {}
    #}}}
    # generate_table: {{{
    def generate_table(self,
        iterable:list = None,
        header = None,
        index_list:list = None,
        cols_align:list = ['c','l'],
        cols_dtype:list = ['i','t'],
        cols_valign:list = ['b','b'],
        ):
        '''
        This allows us to generate clean text-based tables
        for user selection printouts.
        '''
        # Pre-checks: {{{
        if isinstance(header,str):
            header = ['Index',header]
        else:
            header = ['Index','Item']
        if index_list:
            if len(iterable) != len(index_list):
                print('Incompatible index list for iterable given.')
        #}}}
        # Generate the table: {{{
        table = texttable.Texttable()
        table.set_cols_align(cols_align)
        table.set_cols_dtype(cols_dtype)
        table.set_cols_valign(cols_valign)
   
        table.add_row(header) 
        for i, v in enumerate(iterable):
            if index_list and cols_align == ['c', 'l']:
                table.add_row([index_list[i], v]) 
            elif cols_align != ['c', 'l']:
                table.add_row(v) 
            else:
                table.add_row([i,v]) 
        print(table.draw())
        #}}}
#}}}
    # clear: {{{
    def clear(self):
        if os.name == 'nt':
            os.system('cls') # This is for Windows
        else:
            os.system('clear') # This is for mac and linux
    #}}}
    # prompt_user: {{{
    def prompt_user(self, iterable:list = None,header:str = None):
        '''
        This function will prompt the user to make a selection 
        from a list given.
        The function will return the value selected.
        '''
        # Loop for user selection: {{{
        selecting = True
        result = None
        self.generate_table(iterable,header = header) 
        while  selecting:
            selection = input('Please select the number of your choice.\nIf you want to quit, simply press return or type none.\nIf you want to go back a directory, you can type "b".\n')
            # Check if the selection was valid: {{{
            if selection.isdigit():
                selection = int(selection)
                result = iterable[selection]
                selecting = False
            
            elif selection == 'b': 
                selection = iterable.index('back_directory') # Get the index of the back
                result = iterable[selection]
                selecting = False 
            #}}}
            # Check for quit: {{{
            elif selection.lower() == 'none' or selection == '':
                selecting = False
            #}}}
            # Check for Fragment of Dir Name: {{{
            else:
                possibilities = []
                for i, dirname in enumerate(iterable):
                    tmp_dirname = dirname.lower() 
                    if re.findall(selection.lower(),tmp_dirname):
                        possibilities.append(dirname) # Add the possible choice 
                if len(possibilities) > 1:
                    print()
                    self.generate_table(possibilities,header=header)
                    selection = input('Please select the directory you meant\n')
                    if selection.isdigit():
                        result = possibilities[int(selection)]
                        selecting = False
                elif len(possibilities) == 1:
                    result = possibilities[0] # This was what was meant 
                    selecting = False
            #}}} 
    
        #}}}
        return result
    #}}}
    # navigate_filesystem: {{{
    def navigate_filesystem(self):
        '''
        The purpose of this is to navigate the filesystem of your computer
        to get to a directory if you aren't already where you want to be
        '''
        navigating = True
        # while loop: {{{
        while navigating:
            current_directory = os.getcwd()
            current_directory_contents = os.listdir()
            cd_folders = []
            for f in current_directory_contents:
                if os.path.isdir(f):
                    cd_folders.append(f) 
            cd_folders.extend(['back_directory','done_selecting'])
            
            #self.generate_table(cd_folders,header = 'Directories')
            selection = self.prompt_user(cd_folders)
            
    
            if selection == None or selection == 'done_selecting':
                navigating = False
            elif selection == 'back_directory':
                os.chdir(os.path.dirname(current_directory)) # This goes back a directory.
            else:
                os.chdir(selection) # Change directory to the new one.
            self.clear()
        #}}}
        return os.getcwd() #Final directory is returned
        
    #}}}
    # get_min_max: {{{
    def get_min_max (
            self, 
            vals:list = None, 
            custom_labels:list = None,
            pct:float = 0.5,
            decimals:int = 5, 
        ):
        '''
        This function serves to quickly get the lattice parameters 
        for a single or series of values varying by a percentage ±
        '''
        fract = pct/100
        try:
            print('-'*10)
            for i, v in enumerate(vals):
                minv = np.around(v - v*fract, decimals)
                maxv = np.around(v + v*fract, decimals)
                if custom_labels == None:
                    custom_labels = ['']*len(vals)
                print(f'Min {custom_labels[i]}: {minv}\nMax {custom_labels[i]}: {maxv}')
            print('-'*10)
        except: 
            minv = np.around(vals-vals*fract,decimals)
            maxv = np.around(vals+vals*fract,decimals)
            if not custom_label:
                custom_label = ''
            print(f'Min {custom_label}: {minv}\nMax {custom_label}: {maxv}')
    #}}}
    # _update_internal_kwargs: {{{
    def _update_default_kwargs(self,kwargs:dict = None, alternates:dict = None):
        '''
        This function allows you to update a
        dictionary of internal keyword arguments 
        which is particularly useful for the plotting
        utilities which have lots of kwargs.
        '''  
        # Update the keyword arguments: {{{ 
        for key, val in kwargs.items(): 
            if key in self._default_kwargs:
                self._default_kwargs[key] = val
            else:
                try: 
                    found = False
                    for k2, v2 in alternates.items(): 
                        if key in v2:
                            self._default_kwargs[k2] = val 
                            found = True
                            break
                    if not found:
                        raise ValueError(f'Your key {key} is invalid!')
                except:
                    raise ValueError(f'No alternate keys defined! Your key: {key} is invalid.')
        #}}} 
    #}}}
    # _get_kwarg: {{{
    def _get_kwarg(self, key:str = None):
        '''
        This function acts on self._default_kwargs
        pass a string to get the value if it exists.
        '''
        try:
            val = self._default_kwargs[key] 
        except:
            val = None
        return val
    #}}}
    # get_time_range: {{{ 
    def _get_time_range(self, metadata_data:dict = None, time_range:list = None,max_idx:int = None):
        '''
        This function serves to define a new range for the automated refinement tool 
        to work from. 
        One thing to note is that the indices are always 1 higher than pythonic indices. 
        e.g. 1 == 0 because we use len(range) to get the last data point. 
        '''
        mdd_keys = list(metadata_data.keys())
        t0 = metadata_data[mdd_keys[0]]['epoch_time'] # This is the first time in the series. This will be shown to user
        start = 1
        end = max_idx
        print(f'Starting epoch time: {t0} s')

        found_start = False
        found_end = False
        for i, (rt, entry) in enumerate(metadata_data.items()): 
            ti = entry['epoch_time']
            time = (ti - t0)/60
            # Handle the start case: {{{
            if time >= time_range[0] and not found_start:
                start = i+1 # make the index +1 because we subtract later. 
                print(f'Starting time: {time*60} s')
                found_start = True
            #}}}
            # Handle the end case: {{{
            elif  time >= time_range[1] and not found_end:
                if i+1 < max_idx:
                    end = i+1 # make the index +1 because we subtract later.
                else:
                    end = max_idx
                found_end = True
                break
            #}}}
        return (start,end)
    #}}}
#}}}
# UsefulUnicode: {{{
class UsefulUnicode: 
    '''
    This is a class because these symbols do not need to be
    visible to the end user in a generic sense. 
    '''
    def __init__(self,): 
        self._degree = u'\u00B0' # Degree symbol
        self._deg_c = u'\u2103' # Degree C symbol
        self._subscript_zero = u'\u2080' # Subscript zero
        self._subscript_one =   u'\u2081'
        self._subscript_two =   u'\u2082'
        self._subscript_three = u'\u2083'
        self._subscript_four =  u'\u2084'
        self._subscript_five =  u'\u2085'
        self._subscript_six =   u'\u2086'
        self._subscript_seven = u'\u2087'
        self._subscript_eight = u'\u2088'
        self._subscript_nine =  u'\u2089'
        self._angstrom = u'\u212b' # Angstrom symbol
        self._cubed = u'\u00b3' # Cubed (superscript 3)

        self._angstrom_symbol = u'\u212b'
        self._degree_symbol = u'\u00b0'
        self._degree_celsius = u'\u2103'
        self._theta = u'\u03b8'

        self._sub_a = u'\u2090'
        self._sub_b = u'\u1D47'
        self._sub_c = u'\u1D9c'
        self._sub_d = u'\u1D48'
        self._sub_e = u'\u2091'
        self._sub_f = u'\u1DA0'
        self._sub_g = u'\u1D4D'
        self._sub_h = u'\u2095'
        self._sub_i = u'\u1D62'
        self._sub_j = u'\u2C7C'
        self._sub_k = u'\u2096'
        self._sub_l = u'\u2097'
        self._sub_m = u'\u2098'
        self._sub_n = u'\u2099'
        self._sub_o = u'\u2092'
        self._sub_p = u'\u209A'
        #self._sub_q = u'\u2090'
        self._sub_r = u'\u1D63'
        self._sub_s = u'\u209B'
        self._sub_t = u'\u209C'
        self._sub_u = u'\u1D64'
        self._sub_v = u'\u1D65'
        #self._sub_w = u'\u2090'
        self._sub_x = u'\u2093'
        #self._sub_y = u'\u2090'
        #self._sub_z = u'\u2090'
#}}}
# DataCollector: {{{
class DataCollector: 
    '''
    This class gives us the tools necessary to allow us to import
    data that we are interested in - given a fileextension 
    Additionally, dependent upon what we are looking at.
    e.g. data, metadata, etc.
    '''
    # __init__: {{{
    def __init__(
            self,
            fileextension:str = 'xy',
            position_of_time = 1,
            len_of_time = 6,
            time_units:str = 'min',
            file_time_units:str = 'sec',
            skiprows = 1, 
            metadata_data:dict = {},
        ):
        '''
        1. fileextension: The extension (without a .)
        2. position_of_time: the index in the filenname where time is located (assuming you have time in your filename)
        3. len_of_time: The number of digits you have in your file's time code
        4. time_units: The time units you want at the end of processing
        5. file_time_units: The units of time recorded in the filenname
        6. skiprows: The number of rows to skip when reading the data (necessary when using numpy and headers are present).
        '''
        # Initialize values: {{{
        self._fileextension = fileextension
        self.position_of_time = position_of_time 
        self.len_of_time = len_of_time 
        self.time_units = time_units 
        self.file_time_units = file_time_units 
        self.skiprows = skiprows  
        self.metadata_data = metadata_data # Transfer the metadata or start fresh 
        #}}}
        # Determine if working with images: {{{
        if self._fileextension == 'tif' or self._fileextension == 'tiff':
            self.image = True# get_arrs uses this to determine to treat an image or data
        else:
            self.image = False # Treats the data as CSV type
        #}}}
        self.file_dict = {} # This will be initialized as empty 
    #}}}
    # scrape_files: {{{
    def scrape_files(self):
        '''
        This function finds all files with the extension selected
        and sorts them based on the timecode embedded in their filenames.
        '''
        self.files = glob.glob(f'*.{self._fileextension}')
        tmp = {}
        for f in self.files:
            numbers = re.findall(r'\d{'+str(self.len_of_time)+r'}',f) 
            number = int(numbers[self.position_of_time])
            if number:
                tmp[number] = f # The files will be indexed by their timecode
             # We now sort the dictionary entries by their number (least to greatest.) 
        self.file_dict = dict(sorted(tmp.items())) 
    #}}}
    # set_time_range: {{{
    def set_time_range(self,):
        '''
        This function will allow you to set a time range over which you would like to
        plot the data.
        The function will tell the user the high and low values and allow the user to
        set the bounds.
        '''
        selecting = True
        while selecting:
            # Gather the information we need to progress: {{{
            timecodes = list(self.file_dict.keys())
            min_t = min(timecodes)
            max_t = max(timecodes)
            min_index = timecodes.index(min_t)
            max_index = timecodes.index(max_t)
            #}}}
            print(f'You have {len(timecodes)} patterns in this directory.')
            print('#'*80)
            selection = input('Enter the index of the pattern you want to start with and the             number of patterns to plot separated by comma or space.\nIf you want to plot all of the data,            press return\n') 
            numbers = re.findall(r'\d+', selection)
            # If the length of the user input is appropriate (len == 2): {{{
            if len(numbers) == 2:
                self.first_pattern_idx = int(numbers[0])
                number_of_patterns  = int(numbers[1])
                proposed_final_idx = self.first_pattern_idx + number_of_patterns # This will give a possible index (may be out of range)
                if proposed_final_idx <= max_index:
                    self.last_pattern_idx = proposed_final_idx
                else:
                    self.last_pattern_idx = max_index
                selecting = False
            #}}}
            # The User inputs an invalid selection: {{{
            elif len(numbers) >0 or len(numbers) < 0:
                # This means that it is not 2 but is not zero
                print('Your selection: {} was invalid.'.format(selection))
            #}}}
            # No input is given and thus, all files are loaded: {{{
            else:
                self.first_pattern_idx = min_index
                self.last_pattern_idx = max_index
                selecting = False
            #}}}
    #}}} 
    # get_arrs: {{{
    def get_arrs(self,metadata:bool = False):
        '''
        This function is used to obtain the data from the files that fall within the time
        frame selected.
  
   
        The time recorded in the filename will work to sort but will not work to plot.
        '''
        ys = []
        files = []
        temps = []
        first_time = min(list(self.file_dict.keys()))
        # if there is NOT metadata: {{{
        if not metadata:
            # Filter the data by time range: {{{
            for i, time in enumerate(self.file_dict):
                f = self.file_dict[time]
                # Convert time to selected units: {{{
                if self.time_units == 'min' and self.file_time_units == 'sec':
                    chosen_time_unit = (time-first_time)/60
                elif self.time_units == 'h' and self.file_time_units == 'sec':
                    chosen_time_unit = (time-first_time)/60**2
                elif self.time_units == 'sec' and self.file_time_units == 'sec':
                    chosen_time_unit = time-first_time
                #}}}
                # Get the times and files: {{{
                if i >= self.first_pattern_idx and i <= self.last_pattern_idx:
                    ys.append(chosen_time_unit)
                    files.append(f)
                #}}}
            #}}}
        #}}}
        # If Metadata: {{{
        else:
            # Filter by the Metadata Time Range: {{{
            t0 = self.metadata_data[first_time]['epoch_time']
            for i, time in enumerate(self.file_dict):
                temps.append(self.metadata_data[time]['temperature']) # Add the celsius temp
                f = self.file_dict[time]
                t1 = self.metadata_data[time]['epoch_time'] # Gives the correct time
                # Convert time to selected units: {{{
                if self.time_units == 'min' and self.file_time_units == 'sec':
                    chosen_time_unit = (t1-t0)/60
                elif self.time_units == 'h' and self.file_time_units == 'sec':
                    chosen_time_unit = (t1-t0)/60**2
                elif self.time_units == 'sec' and self.file_time_units == 'sec':
                    chosen_time_unit = t1-t0
                #}}}
                # Get the times and files: {{{
                if i >= self.first_pattern_idx and i <= self.last_pattern_idx:
                    ys.append(chosen_time_unit)
                    files.append(f)
                #}}}
            #}}}
        #}}}
        # Get the tth and I vals {{{ 
        zs = [] # This will be the length of the files but will hold lists of intensities for each.
        self.max_i = 0
        self.min_i = 0
        min_tth = None
        max_tth = None
        max_len = None
        for f in files:
            data = np.loadtxt(f,skiprows=self.skiprows)
            tth = data[:,0]
            iau = data[:,1]
            # Record max angle: {{{
            if max_tth:
                if max_tth < max(tth):
                    max_tth = max(tth)
            else:
                max_tth = max(tth)
            #}}}
            # Record min angle: {{{
            if min_tth:
                if min_tth > min(tth):
                    min_tth = min(tth)
            else:
                min_tth = min(tth)
            #}}}
            # Record datapoints: {{{
            if max_len:
                if max_len < len(tth):
                    max_len = len(tth)
            else:
                max_len = len(tth)
            #}}}
            zs.append(iau) # Record the intensities for the current pattern.
            # Record the max and min intensities: {{{
            if max(iau) > self.max_i:
                self.max_i = max(iau)
            if min(iau) < self.min_i:
                self.min_i = min(iau)
            #}}}
        print(min_tth, max_tth, max_len)
        self.tth_arr = np.linspace(min_tth, max_tth, max_len)
        self.time_arr = np.array(ys)
        self.i_arr = np.array(zs)
        if temps:
            self.temp_arr = np.array(temps)
        else:
            self.temp_arr = None
        #}}}
        
    #}}}
    # get_imarr: {{{
    def get_imarr(self,fileindex:int = 0):
        # Get X, Y, Z Data (IF Image): {{{        
        '''
        Now, we know that we are dealing with an image file. 
        This means that we should first load it using the Image class
        Then We convert to an array with numpy. 
        Xs are represented by each of the indices in the arrays in the primary array
        Ys are represented by each of the indices of arrays in the primary array
        Zs are stored as values in each of the arrays within the primary array.
        '''
        xs = []
        ys = []
        zs = []
        self.max_im_z = 0
        keys = list(self.file_dict.keys())
        image_time_key = keys[fileindex] # This is the time in seconds
        file = self.file_dict[image_time_key] # Get the filename you wanted
        self.image_time = image_time_key - keys[0] # Get relative from the first time.
        self.image_time_min = np.around(self.image_time/60,2)
        self.image_time_h = np.around(self.image_time/(60**2),2)
        
        image = Image.open(file) # In this step, we load the image into memory. Then we can get the array out.
        data  = np.array(image) # This is an array of arrays. (len = Y), len(array[i]) = X, values in array[i] = z
        for y, zarr in enumerate(data):
            inner_z = [] # This holds the 
            ys.append(y)
            for x, z in enumerate(zarr): 
                if y == 0:
                    xs.append(x) # This only needs to happen once since the number should not change. 
                inner_z.append(z) 
                if z > self.max_im_z:
                    self.max_im_z = z
            zs.append(inner_z)
        self.im_x = np.array(xs)
        self.im_y = np.array(ys)
        self.im_z = np.array(zs)

        #}}}
    #}}}
    # check_order_against_time: {{{
    def check_order_against_time(self,tmp_rng:list = None,data_dict_keys:list = None,  metadata_data:dict = None, mode:int= 0 ):
        '''
        This function is designed to reorder the files you are analyzing 
        if you discover that the order is wrong after analysis.

        This will return the re-ordered range (if necessary). 

        Mode:
            0: This is normal mode, returns a range of indices from the original dataset you pull from (for refinements)
            1: This is the alt mode, returns a range of indices from the refined dataset (after refinement, for analysis)
        '''
        fixed_range = []
        negative_times = [] # indices of the patterns we need to reorient. 
        # Now, we need to check if the order is correct regarding the metadata: {{{  
        for idx, number in enumerate(tmp_rng): 
            file_time = data_dict_keys[int(number)-1] 
            md_keys = list(metadata_data.keys()) 
            md_entry = metadata_data[file_time] # Get the metadata for the current time
            start_time = metadata_data[md_keys[0]]['epoch_time'] # This gives us the starting time
            current_epoch_time = md_entry['epoch_time'] # This gives the current epoch time
            time = (current_epoch_time - start_time)/60 # This is in minutes 
            if time <0:
                negative_times.append(idx)
 
        if negative_times:  
            for idx in negative_times: 
                if mode == 0:
                    fixed_range.append(tmp_rng[idx])
                else:
                    fixed_range.append(idx)
            for idx,  number in enumerate(tmp_rng):
                if idx not in negative_times:
                    if mode == 0:
                        fixed_range.append(number) 
                    else:
                        fixed_range.append(idx)
        else:
            fixed_range = tmp_rng

        #}}}
        return fixed_range
    #}}} 
#}}}

