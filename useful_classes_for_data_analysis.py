# Authorship: {{{
'''
Written by Dario Lewczyk
7/11/23
Purpose:
    Provide classes that can be used in other pieces of code to reduce
    the number of times I need to write helpful functions like these. 
'''
#}}}
# Imports: {{{
import os, re, glob, sys
from tqdm import tqdm
import plotly.graph_objects as go
import numpy as np
import texttable
import copy
import subprocess
from shutil import copyfile
from PIL import Image # This allows us to load tiff images.
#}}}
# Notes on Operation: {{{
'''
The classes, "Utils", "DataCollector", and "MetadataParser" 
were used in their original code in the following way: 
    Initialize the Utils – then run "navigate_filesystem". 

    Initialize the MetadataParser – Then, we would need to go to the directory where the metadata are
        IF after initializing "MetadataParser" you get "self.metadata_data" that is populated,
        then it is presumed that there is actually metadata. 

    When the class in "waterfall_plot_generator.py," "Plotter" is initialized, "DataCollector" is
    also initialized
        – After initialization, run "scrape_files()" in the directory where data are located. 
        – Run "set_time_range()" which gives sets only the patterns we care about 
        – Finally, run get_arrs and tell it if metadata are present. This will get us arrays for
        diffraction patterns. 
        ** May not be entirely useful for processing original Tiff images. So I will have to look
        more into how to handle the original images. 
'''
#}}}
# UsefulUnicode: {{{
class UsefulUnicode: 
    def __init__(self,):
        self._theta = u'\u03B8' # Theta symbol
        self._degree = u'\u00B0' # Degree symbol
        self._deg_c = u'\u2103' # Degree C symbol
        self._angstrom = u'\u212b' # Angstrom symbol
        self._cubed = u'\u00b3' # Cubed (superscript 3)
#}}}
# Utils: {{{
class Utils: 
    def __init__(self):
        pass
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
#}}}
# DataCollector: {{{
class DataCollector: 
    '''
    This class gives us the tools necessary to allow us to import the
    data that we are interested in. 
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
        ):
        self.fileextension = fileextension
        self.position_of_time = position_of_time # This is the index of numbers in your filename         that the time will be at
        self.len_of_time = len_of_time # This is the length of the time code in the File name
        self.time_units = time_units # The units of time to be plotted
        self.file_time_units = file_time_units # The units of time recorded in the filename
        self.skiprows = skiprows # Rows that do not contain data in your files.
        if self.fileextension == 'tif' or self.fileextension == 'tiff':
            self.image = True# Tells the get_arrs function whether or not to treat your data as an image
        else:
            self.image = False # Treats the data as CSV type

        self.file_dict = {} # This will be initialized as empty
        
    #}}}
    # scrape_files: {{{
    def scrape_files(self):
        self.files = glob.glob(f'*.{self.fileextension}')
        tmp = {}
        for f in self.files:
            numbers = re.findall(r'\d{'+str(self.len_of_time)+r'}',f) # HAVE TO CHANGE MANUALLY IF       YOU HAVE A DIFF LEN FOR TIMECODE
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

#}}}
# MetadataParser: {{{
class MetadataParser:
    # __init__{{{
    def __init__(
        self,
        #nav_filesystem:bool = False,
        time_key:str = 'time:',
        temp_key:str = 'element_temp',
        ):
        #self._data_dir = os.getcwd() # PRESERVE THE ORIGINAL DIRECTORY.
        #Utils.__init__(self) # Gives access to the utils
        #if nav_filesystem:
        #    print('Please navigate to the METADATA folder for your data.')
        #    self.navigate_filesystem() # This allows us to move to the directory with the metadata
        #    self._metadata_dir = os.getcwd()
        md = DataCollector(fileextension='yaml')
        md.scrape_files() # This gives us the yaml files in order in data_dict
        self.metadata = md.file_dict # This is the dictionary with all of the files.
        self.get_metadata(time_key=time_key, temp_key=temp_key)
        #os.chdir(self._data_dir) # Returns us to the original directory.
    #}}}
    # get_metadata: {{{
    def get_metadata(
        self,
        time_key:str = 'time:',
        temp_key:str = 'element_temp',
        ):
        self.metadata_data = {}
        metadata = tqdm(self.metadata)
        for i, key in enumerate(metadata):
            metadata.set_description_str(f'Working on Metadata {key}:')
            filename = self.metadata[key] # Gives us the filename to read.
            time = None
            temp = None
            # Work to parse the data: {{{
            with open(filename,'r') as f:
                lines = f.readlines()
                for line in lines: 
                    if time_key in line:
                        t = re.findall(r'\d+\.\d+',line) # This gives me the epoch time if it is on a        line.
                        if t:
                            time = float(t[0]) # Gives us the epoch time in float form.   
                    if temp_key in line:
                        temp = np.around(float(re.findall(r'\d+\.\d?',line)[0]) - 273.15, 2) #           This gives us the Celsius temperature of the element thermocouple.  
                        
                f.close() 
            #}}}
            # Update Metadata Dictionary Entry: {{{
            self.metadata_data[key] = {
                'readable_time': int(key),
                'epoch_time': time,
                'temperature': temp,
                'pattern_index': i,
            }
            
            #}}}
    #}}}
#}}}
# TOPAS_Refinements: {{{
class TOPAS_Refinements(Utils, UsefulUnicode):
    # __init__: {{{
    def __init__(self,
            topas_version:int = 6,
            fileextension:str = 'xy',  
        ):
        '''
        topas_version: just sets what what number to use when looking for the TOPAS directory. 
        fileextension: sets the fileextension of your datafiles. In my case, this is .xy
        reverse_order: This tells the program whether or not to analyze the data chronologically or reverse chronologically.
        '''
        # Make attrs based on inputs: {{{ 
        self.topas_dir = 'C:\\TOPAS%s'%topas_version # sets the directory
        self.fileextension= fileextension# This is the extension of your data. 
        #}}}
        # Additional initialization tasks: {{{
        self.current_dir = os.getcwd() # This saves the original location
        Utils.__init__(self)
        UsefulUnicode.__init__(self)
        self._data_collected = False # This tracks if the "get_data" function was run
        #}}}
    #}}}
    # refine_pattern: {{{
    def refine_pattern(self, input_file):
        '''
        This performs a Rietveld Refinement using TOPAS. 
        The input should be the name of the diffraction pattern
        that you want to refine. 
        '''
        working_dir = os.getcwd()
        refine_cmd = 'tc ' + working_dir + '\\'
        os.chdir(self.topas_dir) # This will change the directory to TOPAS Home
        subprocess.call(refine_cmd + input_file)
        os.chdir(working_dir)
    #}}}
    # run_auto_rietveld: {{{
    def run_auto_rietveld(self,
            num_of_scans_to_refine:int = 200, 
            data_dir:str = None, 
            template_dir:str = None,
            reverse_order:bool = False,
        ):
        '''
        Code to run automated Rietveld Refinements based on Adam/Gerry's Code
        '''
        self.reverse_order = reverse_order # This will keep track of if you chose to reverse the order in case that info is needed elsewhere.
        # Navigate the Filesystem to the appropriate directories: {{{
        if not data_dir:
            print('Navigate to the "Data Directory"')
            data_dir = self.navigate_filesystem()
        else:
            if not os.path.isdir(data_dir):
                print('Your "data_dir" is invalid. Navigate to the data dir now.')
                data_dir = self.navigate_filesystem()
        if not template_dir:
            print('Navigate to the "Template_Dir"')
            template_dir = self.navigate_filesystem()
        else:
            if not os.path.isdir(template_dir):
                print('Your "template_dir" is invalid. Navigate to the template directory now.')
                template_dir = self.navigate_filesystem()
        #}}}
        os.chdir(template_dir) # Go to the directory with the input file
        template_file = '{}.inp'.format(os.path.basename(template_dir))
        template = [line for line in open(template_file)] # This reads the template file
        # Parse the template for important linenumbers: {{{
        xy_out_linenum = None
        csv_out_linenum = None
        my_csv_line = None
        pattern_linenum = None
        for i, line in enumerate(template):
            if 'Out_X_Yobs_Ycalc_Ydiff' in line:
                xy_out_linenum = i 
            if 'out_prm_vals_on_convergence' in line:
                csv_out_linenum = i
            if 'out' in line:
                # Don't need to look for anything but out by itself. 
                my_csv_line = i
            if 'xdd' in line:
                pattern_linenum = i
        
        #}}}
        # Get the data: {{{
        os.chdir(data_dir) # Go to the directory with the scans
        data = DataCollector(fileextension=self.fileextension) # Initialize the DataCollector
        data.scrape_files() # This collects and orders the files
        data_dict_keys = list(data.file_dict.keys()) # Filename timecodes in order
        os.chdir(template_dir) # Return to the template directory 
        tmp_rng = np.linspace(1, len(data_dict_keys), num_of_scans_to_refine) # Gives a range over the total number of scans that we want to refine. 
        if self.reverse_order:
            tmp_rng = tmp_rng[::-1] # This reverses the order of the array by converting it to a list slice 
        #}}}
        # Begin the Refinements: {{{
        '''
        This part uses a range made by the selection of the user. 
        Since we don't need to pair the data with the metadata, we should be able to simply reverse the order of the range. 
        '''
        rng = tqdm([int(fl) for fl in tmp_rng]) # This sets the range of files we want to refine. 
        for number in rng:
            pattern = f'{data_dir}\\{data.file_dict[data_dict_keys[number-1]]}' # Use the custom range we defined. Must subtract 1 to put it in accordance with the index. 
            output = f'result_{data_dict_keys[number-1]}_{str(number).zfill(6)}' # zfill makes sure that we have enough space to record all of the numbers of the index, also use "number" to keep the timestamp. 
            if pattern_linenum:
                template[pattern_linenum] = f'xdd "{pattern}"\n' # write the current pattern
            if xy_out_linenum:
                template[xy_out_linenum] = f'Out_X_Yobs_Ycalc_Ydiff("{output}.xy")\n'
            if csv_out_linenum:
                template[csv_out_linenum] = template[csv_out_linenum].split()[0]+f'"{output}.csv"\n'
            if my_csv_line: 
                template[my_csv_line] = f'out "{output}.csv"\n'
            # Use the Dummy.inp file: {{{
            with open('Dummy.inp','w') as dummy:
                for line in template:
                    dummy.write(line)
            self.refine_pattern('Dummy.inp') # Run the actual refinement
            copyfile('Dummy.out',f'{output}.out')
            template = [line for line in open('Dummy.out')] # Make the new template the output of the last refinement. 
            #}}}
        #}}}
    #}}}
    # get_data: {{{
    def get_data(self, 
            csv_labels:list = None, # This is a list of what each entry in the csvs is 
            csv_prefix:str = 'result', 
            xy_prefix:str = 'result',
            out_prefix:str = 'result',
            print_files:bool = False,
            get_orig_patt_and_meta:bool = True,
            parse_c_matrices:bool = False,
            correlation_threshold:int = 50,
            flag_search:str = 'CHECK',
        ):
        '''
        This will gather and sort all of the output files from your refinements for you. 
        
        csv_labels: 
            This tells the program what each individual entry of the labels mean. 
        '''
        self.rietveld_data = {}
        self.sorted_csvs = sorted(glob.glob(f'{csv_prefix}_*.csv')) #gathers csvs with the given prefix
        self.sorted_xy = sorted(glob.glob(f'{xy_prefix}_*.xy'))
        self.sorted_out = sorted(glob.glob(f'{out_prefix}_*.out'))
        # Print Statements: {{{
        if print_files:
            print('I   CSV\tXY')
            for i, fn in enumerate(self.sorted_csvs):
                print(f'{i}: {fn}\t{self.sorted_xy[i]}')
        #}}}
        # Categorize the Refined Data: {{{ 
        csvs = tqdm(self.sorted_csvs)
        # import and process CSV, XY, OUT:     
        for i, csv in enumerate(csvs):
            csvs.set_description_str(f'Reading {csv}: ')
            csv_contents = [float(line) for line in open(csv)] # This gives us the values in the csv. 
            # Handle the XY Data: {{{
            csvs.set_description_str(f'Reading {self.sorted_xy[i]}: ')
            xy_data = np.loadtxt(self.sorted_xy[i], delimiter=',') # imports the xy data to an array
            ttheta = xy_data[:,0]
            yobs = xy_data[:,1]
            ycalc = xy_data[:,2]
            ydiff = xy_data[:,3]
            #}}}
            # Handle the OUT files: {{{
            if parse_c_matrices:
                csvs.set_description_str(f'Reading {self.sorted_out[i]}: ')
                c_matrix = self._parse_c_matrix(out_file=self.sorted_out[i],correlation_threshold= correlation_threshold)
                corr_dict = self._get_correlations(c_matrix,flag_search)
            else:
                c_matrix = None
                corr_dict = None
            #}}}
            # UPDATE Rietveld Data: {{{
            self.rietveld_data[i] = {
                'csv': {},
                'csv_name': csv,
                'csv_contents': csv_contents,
                'xy':{
                    '2theta':ttheta,
                    'yobs':yobs,
                    'ycalc':ycalc,
                    'ydiff':ydiff,
                },
                'xy_name':self.sorted_xy[i],
                'out_name': self.sorted_out[i],
                'c_matrix': c_matrix,
                'c_matrix_filtered': corr_dict,
            } # Create an entry for the csv data
            #}}}
            # If you have provided CSV labels: {{{
            if csv_labels:
                for j, line in enumerate(csv_contents):
                    if j <= len(csv_labels)-1: 
                        self.rietveld_data[i]['csv'][csv_labels[j]] = line # This records a dictionary entry with the name of the float
                    else:
                        self.rietveld_data[i][f'csv_data_{j}'] = line # If too few labels given
            #}}}
            # If No Provided CSV labels: {{{
            else:
                for j, line in enumerate(csv_contents):\
                    self.rietveld_data[i]['csv'][f'csv_data_{j}'] = np.around(line,4) # Add a generic label
            #}}}
        #}}} 
        # Match to XY Files: {{{
        if get_orig_patt_and_meta:
            print('Navigate to the data directory.')
            self.data_dir = self.navigate_filesystem()
            self.meta_dir = os.path.join(self.data_dir,'meta') # This gives us the metadata folder
            # Get all of the original data and times: {{{
            self._dc = DataCollector()
            self._dc.scrape_files() # Gathers all of the original data
            self.file_dict = self._dc.file_dict # Gives us the dictionary of all of the original filenames and times
            self.file_dict_keys = list(self.file_dict.keys()) # Gives us the times. 
            #}}}
            # Work with the metadata: {{{
            os.chdir(self.meta_dir) # Go into the metadata
            self._md = MetadataParser()
            self._md.get_metadata()
            self.metadata_data = self._md.metadata_data
            #}}}
            os.chdir(self.current_dir) # Return to the original directory.
            # Now, we want to update the "rietveld_data" dict: {{{
            for i in self.rietveld_data:
                entry = self.rietveld_data[i] # Gives us the data entry.
                file_time = int(re.findall(r'\d+',entry['csv_name'])[0]) # This gives the time of the file. 
                md = self.metadata_data[file_time]
                fd = self.file_dict[file_time]
                self.rietveld_data[i].update({
                    'original_name':fd,
                    'readable_time':md['readable_time'],
                    'epoch_time':md['epoch_time'],
                    'temperature':md['temperature'],
                    'corrected_temperature': self.correct_t(md['temperature']), # Correct the temperature using the function
                    'min_t':self.min_tcalc,  # Min temp (error bar)
                    'max_t':self.max_tcalc, # Max temp (error bar)
                    'pattern_index':md['pattern_index'],
                })
            for i in self.rietveld_data:
                entry = self.rietveld_data[i] # Get the current entry 
                self._get_time(i,time_units='s') # get the time in seconds
                self.rietveld_data[i].update({
                    'corrected_time': self._current_time
                })
            #}}}
            
            
        #}}} 
        self._data_collected = True #Now, the data have been collected and plot pattern will be informed
    #}}}
    # correct_t: {{{
    def correct_t(
        self,
        t:float = None,
        ):
        '''
        This function was made on 07/21/2023
        It uses the "a_corr" corrected lattice parameter values
        from the Okado (1974) paper
        A function was made to fit those data very well (R^2 ~0.99993)
        That function fit the Si data collected in the beam
        The T from that correction and the thermocouple were plotted and a new function generated
        The final function's parameters and functional form are presented in this function. 
        '''
        p1 = 0.69234863 # Slope
        p2 = -15.5280975 # Intercept
    
        p1_err = 0.00516 # Slope Error
        p2_err = 4.14 # Intercept Error
     
        self.tcalc = p1*t + p2 # This will be used
        self.min_tcalc = (p1-p1_err)*t + (p2 - p2_err) # This is the low reference
        self.max_tcalc = (p1 + p1_err)*t + (p2 + p2_err) # This is the high reference

        return self.tcalc
     
    #}}}
    # _create_string_from_csv_data: {{{
    def _create_string_from_csv_data(self, index):
        '''
        The purpose of this is to take the labels that the user inputs
        and group them by their attribute. 

        Example is: if you have 'Rwp', 'Si a', 'Ta a', 'Ta b'
        This code will find the unique entries e.g. Rwp, Si, Ta
        and then create a string that can be printed to group the labels with the values. 
        '''
        csv = self.rietveld_data[index]['csv']
        csv_keys = list(csv.keys()) # These are the labels the user gives
        self._rwp = csv[csv_keys[0]] # Rwp should be first
        # Get the unique keys: {{{
        unique = [] # These are the first words of the keys
        prev = '' # This is the previous word found
        for v in csv_keys:
            identifier = re.findall(r'\w+',v)[0] # This gives the first word found
            if identifier != prev:
                unique.append(identifier)
                prev = identifier
        #}}}
        # Get the string: {{{
        intermediate_string = []
        prev_i = 0
        for i, un in enumerate(unique):
            for j, key in enumerate(csv_keys):
                if un in key:
                    if i != prev_i:
                        intermediate_string.append(f'\n{key}: {csv[key]}') # adds the key and value pair
                        prev_i = i # update the previous i
                    else:
                        intermediate_string.append(f'{key}: {csv[key]}') # Add the next entry in a group.
        #}}}
        self._unique_substances = unique
        self._unique_substances.pop(0) #this removes the Rwp
        self._csv_string = ','.join(intermediate_string) # Create the final string as a hidden variable

    #}}}
    # _sort_csv_keys: {{{
    def _sort_csv_keys(self,keys:list = None,debug:bool = False):
        '''
        This will sort the csvs to give you unique results grouped together 
        with only the key values you care about. 

        Example, if you want lattice parameters but scale factors also exist, this will 
        give you the lattice parameters for substance A and substance B separated  and ignore their scale factors
        '''
        self._csv_plot_data = {}
        # Get the unique substances: {{{
        self._create_string_from_csv_data(0)
        #}}} 
        for entry in self.rietveld_data:
            csv = self.rietveld_data[entry]['csv']
            csv_keys = list(csv.keys()) #This gives us the csv keys
            # If Rwp: {{{  
            if keys[0].lower() == 'rwp':
                if entry == 0:
                    self._csv_plot_data['rwp'] = [csv[csv_keys[0]]] # This is the rwp
                else:
                    self._csv_plot_data['rwp'].append(csv[csv_keys[0]]) # Add the next rwp
            #}}}
            # Other cases: {{{
            else:
                '''
                Now, we have a list of the unique substances present. 

                These will be listed as a list under: "self._unique_substances"
                    ex: ["Si", "Ti", "Ta"]
                We need to go through all of the keys to match the first word to the unique substances then match the next word to what we are looking for. 
                '''
                for i, unique_element in enumerate(self._unique_substances):
                    for j, csv_key in enumerate(csv_keys): 
                        if unique_element in csv_key:
                            if unique_element not in self._csv_plot_data:
                                self._csv_plot_data[unique_element] = {}
                            # This means that we have found an entry related to the substance
                            intermediate_identifier = re.findall(r'\w+',csv_key)
                            intermediate_identifier.pop(0) # Get rid of the element. 
                            intermediate = '_'.join(intermediate_identifier) # This will give us a 1 word phrase 
                            if debug and i == 0:
                                print(f'csv_key: {csv_key}\nintermediate_identifier: {intermediate_identifier}\nintermediate: {intermediate}')
                            for key in keys:
                                #print(f'Intermediate: {intermediate}\tKey: {key}')
                                if intermediate.lower() == key or '_'.join(intermediate.split('_')[:-1]).lower() == key:
                                    if intermediate.lower() not in self._csv_plot_data[unique_element]:
                                        self._csv_plot_data[unique_element][intermediate.lower()] = [] #This gives an empty list
                                    self._csv_plot_data[unique_element][intermediate.lower()].append(csv[csv_key]) # This adds the value for the dictionary
                                

                            
            #}}}

            
    #}}}
    # _get_time{{{
    def _get_time(self,index, time_units:str):
        '''
        This function will obtain for you, the time relative to the start of the run. 
        This uses the epoch time from metadata. SO MAKE SURE IT IS PRESENT. 
        '''
        t0 = self.rietveld_data[0]['epoch_time'] # This gives us the epoch time for the first pattern. 
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
        self._current_time = (t1-t0)/divisor
        #}}}


    #}}}
    # _update_pattern_layout: {{{
    def _update_pattern_layout(self,
            fig:go.Figure = None,  
            title_text:str = None, 
            xaxis_title:str = None,
            yaxis_title:str = None,
            tth_range:list = None,
            template:str = None, 
            font_size:int = None,
            height =800,
            width =1000,
            show_legend:bool = True,
            ):
        #Update the layout: {{{
        
        fig.update_layout(
            height = height,
            width = width,
            title_text = title_text,
            xaxis_title = xaxis_title,
            yaxis_title = yaxis_title,
            template = template,
            font = dict(
                size = font_size,
            ),
            legend = dict(
                yanchor = 'top',
                y = 0.99,
                xanchor = 'right',
                x = 0.99,
            ),
            showlegend = show_legend,
            xaxis = dict(
                range = tth_range,
            )
        )
        #}}}
    #}}}
    # plot_pattern: {{{
    def plot_pattern(self,
            index:int = 0, 
            template:str = 'simple_white',
            time_units:str = 'min', 
            tth_range:list = None,
            use_calc_temp:bool = True,
            height = 800,
            width = 1000,
            show_legend:bool = True,
            font_size:int = 20,
            rwp_decimals:int = 2,
            temp_decimals:int = 2,
            printouts:bool = True,
            run_in_loop:bool = False,
        ):
        '''
        This will allow us to plot any of the loaded patterns 
        '''
        if not self._data_collected:
            print('You did not yet collect data. Do that now...')
            self.get_data()
        
        hovertemplate = f"2{self._theta}{self._degree}" + "%{x}<br>Intensity: %{y}"
        data = self.rietveld_data[index] # This gives us the entry we are interested in. 
        # Get a formatted string from csv: {{{
        self._create_string_from_csv_data(index) # This gives a variable called "self._csv_string" for us to print out. 
        #}}} 
        # Get the time the pattern was taken: {{{
        self._get_time(index,time_units) # This gives us "self._current_time" which is the time in the units we wanted. 
        #}}}
        # Get the plot values and labels: {{{
        tth = self.rietveld_data[index]['xy']['2theta'] # this is the array of 2 theta values
        keys = list(self.rietveld_data[index]['xy'].keys())[1:] # These are the keys we care about. 
        if use_calc_temp:
            temp = self.rietveld_data[index]['corrected_temperature'] 
            temp_label = 'Corrected Temp'
        else:
            temp = self.rietveld_data[index]['temperature']
            temp_label = 'Element Temp'
        #}}}
        # Generate the figure: {{{
        self.pattern_plot = go.Figure()
        colors = ['blue', 'red', 'grey']
        # Add the plots: {{{
        for i, key in enumerate(keys):
            self.pattern_plot.add_scatter(
                x = tth,
                y = self.rietveld_data[index]['xy'][key],
                hovertemplate = hovertemplate,
                marker = dict(
                    color = colors[i],
                ),
                name = key,
            )
        #}}}
        #Update the layout: {{{
        #Get Info for Updating Layout: {{{
        if tth_range == None:
            tth_range = [min(tth), max(tth)] # plot the whole range
        
        title_text = f'Time: {np.around(self._current_time,2)} {time_units}, ({temp_label}: {np.around(temp,temp_decimals)}{self._deg_c}) Rwp: {np.around(self._rwp,rwp_decimals)}'
        xaxis_title = f'2{self._theta}{self._degree}'
        yaxis_title = 'Intensity'
        #}}}
        self._update_pattern_layout(
            fig=self.pattern_plot,
            title_text=title_text,
            xaxis_title=xaxis_title,
            yaxis_title=yaxis_title,
            tth_range=tth_range,
            template=template,
            font_size=font_size,
            height=height,
            width = width,
            show_legend=show_legend,
        ) 
        #}}}
        #}}}
        # Printouts: {{{
        if printouts:
            print('Additional Refinement Information:')
            print(self._csv_string)
            el_t = np.around(self.rietveld_data[index]["temperature"],2)
            c_t = np.around(self.rietveld_data[index]["corrected_temperature"],2)
            mint = np.around(self.rietveld_data[index]["min_t"],2)
            maxt = np.around(self.rietveld_data[index]["max_t"],2)

            print(f'Element Temperature: {el_t}{self._deg_c}\n'+
                    f'Corrected Temperature: {c_t}{self._deg_c}\n'+
                    f'Min Corrected Temperature: {mint}{self._deg_c}, Max Corrected Temperature: {maxt}{self._deg_c}'
                    )
        #}}}
        # Standard Output: {{{
        if not run_in_loop:
            self.pattern_plot.show()
        #}}}
        # Loop Output: {{{
        else:
            yobs = self.rietveld_data[index]['xy']['yobs']
            ycalc = self.rietveld_data[index]['xy']['ycalc']
            ydiff = self.rietveld_data[index]['xy']['ycalc']
            hovertemplate = f'{title_text}<br>Pattern Index: {index}<br>' + hovertemplate
            #title = f'Time: {np.around(self._current_time,2)} {time_units}, ({temp_label}: {np.around(temp,temp_decimals)}{self._deg_c}) Rwp: {np.around(self._rwp,rwp_decimals)}',
            return (tth, yobs,ycalc,ydiff, hovertemplate, title_text,xaxis_title,yaxis_title)
        #}}}
    #}}}
    # plot_times: {{{ 
    def plot_times(self,):
        if not self._data_collected:
            print('You did not yet collect data. Do that now...')
            self.get_data()
        fig = go.Figure()
        # Get the data to plot: {{{
        readable_times = list(self.metadata_data.keys())
        xs = [np.around((self.metadata_data[rt]['epoch_time'] - self.metadata_data[readable_times[0]]['epoch_time']) / 60, 4) for rt in self.metadata_data] # Creates a list of the real times
        ys = np.linspace(1, len(readable_times), len(readable_times)) # Create a line with the total number of patterns. 
        #}}}
        # Plot the data: {{{
        fig.add_scatter(
            x = xs,
            y = ys,
            mode = 'lines+markers', # Shows the markers with a line going through them.
        )
        #}}}
        # Update Layout: {{{
        fig.update_layout(
            height = 800,
            width = 1100,
            title_text = 'Plot of Times',
            xaxis_title = 'Time/min',
            yaxis_title = 'Plot Number',
            font = dict(
                size = 20,
            ),
            template = 'simple_white',
        )
        #}}}
        fig.show() 
    #}}}
    # _normalize: {{{
    def _normalize(self, data:list = None):
        return [v/max(data) for v in data]
    #}}}
    # _get_random_color: {{{
    def _get_random_color(self,):
        rand_color = list(np.random.choice(range(256),size = 3)) # This generates a random color for each of the substances
        color = f'rgb({rand_color[0]},{rand_color[1]},{rand_color[2]})'
        return color
    #}}}
    # plot_csv_info: {{{
    def plot_csv_info(self, 
            plot_type:str = 'rwp',
            plot_temp:bool = True,
            use_calc_temp:bool = True,
            time_units:str = 'min', 
            normalized:bool = False,
            time_range:list = None,
            y_range:list = None,
            height = 800,
            width = 1100,
            font_size = 20,
            yaxis_2_position = 0.15,
            additional_title_text:str = None,
            specific_substance:str = None,
            ):
        ''' 
        plot_type: This can be any of the below. 
            1.) "lattice parameters" or "lattice" or "lp"
            2.) "scale factor" or "sf"
            3.) "rwp" 
            4.) "volume" or "vol"
            5.) "Rbragg" or "rb"
            6.) "Weight Percent" or "wp"
            7.) "B values" or "beq" or "bvals" 

        The purpose of this function is to give the user a 
        look at the data output in csv form by TOPAS at the 
        conclusion of the refinement series. 

        This is a little complex since we do not necessarily know what we want to plot 
        the user will decide that. 

        "specific_substance": Allows you to plot only data from one substance at a time

        some things I am thinking about are: 

        Rwp:
            x = pattern number
            y = Rwp value
        lattice parameter:
            x = pattern number
            y = lattice parameter / Angstrom
        scale factor: 
            x = pattern numebr
            y = scale factor

        For each of these, we would need to know 

        '''

        plot_type = plot_type.lower() # This ensures everything is lowercase.
        if not self._data_collected:
            print('You did not yet collect data. Do that now...')
            self.get_data()
        # Determine what to look for in the data: {{{
        yaxis_title = '' # DEfault
        yaxis2_title = '' # Default
        xaxis_title = f'Time / {time_units}'
        # Lattice Params: {{{ 
        if plot_type == 'lattice parameters' or plot_type == 'lattice' or plot_type == 'lp':
            keys = ['a','b','c', 'al','be','ga', 'alpha', 'beta', 'gamma'] # These are the 
            yaxis_title = f'Lattice Parameter / {self._angstrom}' # This is the a, b, c lattice parameter title
            yaxis2_title = f'Lattice Parameter / {self._degree}' # this is the al, be, ga lattice parameter title
            title = 'Lattice Parameters'
        #}}}
        # Scale Factor: {{{
        elif plot_type == 'scale factor' or plot_type == 'sf':
            keys = ['scale_factor', 'sf','scale factor'] # These are the variations likely to be used
            yaxis_title = 'Scale Factor'
            title = 'Scale Factor'
            normalized = True
        #}}}
        # Rwp: {{{
        elif plot_type == 'rwp':
            keys = ['rwp']
            yaxis_title = 'Rwp'
            title = 'Rwp'
        #}}}
        # Volume: {{{
        elif plot_type == 'volume' or plot_type == 'vol':
            keys = ['vol', 'volume', 'cell volume', 'cell_volume']
            yaxis_title = f'Volume / {self._angstrom}{self._cubed}'
            title = 'Volume'
        #}}}
        # R Bragg: {{{
        if plot_type == 'rbragg' or plot_type == 'rb':
            keys = ['r bragg','r_bragg'] # this tells the code what to search for
            yaxis_title = 'R Bragg'
            title = 'R Bragg'
        #}}}
        # Weight Percent: {{{
        if plot_type == 'weight percent' or plot_type == 'wp': 
            keys = ['weight percent', 'weight_percent']
            yaxis_title = 'Weight Percent'
            title = 'Weight Percent'
        #}}}
        # B-values: {{{
        if plot_type == 'b values' or plot_type == 'beq' or plot_type == 'bvals':
            keys = ['bvals', 'beq','bval', 'b value', 'b val', 'b values', 'b_value','b_val','b_values'] # tells the code what the likely keywords to look for are.
            yaxis_title = 'B-Values'
            title = 'B-Values'
        #}}}
        #}}}
        # Update the title text: {{{
        if additional_title_text:
            title = f'{additional_title_text} {title}' # combines what the user wrote with the original title.
        #}}}
        # Get a dictionary containing only the data we care about: {{{
        self._sort_csv_keys(keys) 
        for entry in self.rietveld_data:
            if plot_temp:
                if 'temperature' not in self._csv_plot_data:
                    self._csv_plot_data['temperature'] = []
                if use_calc_temp:
                    t = self.rietveld_data[entry]['corrected_temperature']
                    temp_label = 'Corrected Temperature'
                else:
                    t = self.rietveld_data[entry]['temperature']
                    temp_label = 'Element Temperature'

                self._csv_plot_data['temperature'].append(t) # Record the temperature
            if 'time' not in self._csv_plot_data:
                self._csv_plot_data['time'] = []
            self._get_time(entry,time_units) # This gives us the time in the units we wanted (self._current_time)
            self._csv_plot_data['time'].append(self._current_time) # Add the time
        #}}}
        # plot the data: {{{
        fig = go.Figure()
        second_yaxis = False
        third_yaxis = False
        x = self._csv_plot_data['time']
        base_ht = f'Time/{time_units}: '+'%{x}<br>' # This is the basis for all hovertemplates
        
        if keys == ['rwp']:
            hovertemplate = base_ht+'Rwp: %{y}'
            y = self._csv_plot_data['rwp']
            fig.add_scatter(
                    x = x,
                    y = y,
                    hovertemplate = hovertemplate, 
                    yaxis = 'y1',
                    name = 'Rwp',
            )
            

        else:
            for substance in self._csv_plot_data:
                color = self._get_random_color() # This gives us a color
                if not specific_substance:
                    usr_substance = substance.lower() # If a specific substance is not given, it is set as the current. 
                else:
                    usr_substance = specific_substance.lower()
                if substance != 'time' and substance != 'temperature' and substance.lower() == usr_substance:
                    entry = self._csv_plot_data[substance] # This will be a dictionary entry with keys. 
                    entry_keys = list(entry.keys()) # These will be the keys for the entry. 
                    for plot_key in entry_keys:
                        # Handle most cases: {{{ 
                        if plot_key != 'al' or plot_key != 'be' or plot_key != 'ga' or plot_key != 'alpha' or plot_key != 'beta' or plot_key != 'gamma':
                            if specific_substance:
                                color = self._get_random_color() # Set a specific color for each lattice parameter if only one substance plotted. 
                            # This is the default section since units should be consistent enough. 
                            # Get the data: {{{
                            if normalized:
                                y = self._normalize(entry[plot_key]) # This will normalize the plot data
                            else:
                                y = entry[plot_key] # This will just give us the data
                            #}}}
                            hovertemplate = base_ht +f'{yaxis_title} ({substance}, {plot_key}): '+'%{y}' # This gives us the hovertemplate for this part.
                            # Add the scatter (Y1): {{{
                            fig.add_scatter(
                                x = x,
                                y = y,
                                hovertemplate = hovertemplate,
                                name = f'{substance} {plot_key}',
                                mode = 'lines+markers',
                                marker = dict(
                                    color = color,
                                ),
                                line = dict(
                                    color = color,
                                ),
                                yaxis = 'y1',
                            )
                            #}}}
                            
                        #}}}
                        # Handle the case where we need to plot lattice angles: {{{
                        else:
                            # In this case, we need a second y axis for the degrees.
                            # get the data: {{{
                            if normalized:
                                y = self._normalize(entry[plot_key])
                            else:
                                y = entry[plot_key]
                            #}}}
                            hovertemplate = base_ht + f'{yaxis2_title} ({substance}, {plot_key}): '+'%{y}'
                            # Add the scatter (Y2):{{{
                            fig.add_scatter(
                                x = x,
                                y = y,
                                hovertemplate = hovertemplate,
                                name = f'{substance} {plot_key}',
                                mode = 'lines+markers',
                                marker = dict(
                                    color = color,
                                ),
                                line = dict(
                                    color = color,
                                ),
                                yaxis = 'y2',
                            ) 
                            second_yaxis = True
                            #}}}
                        #}}}
        # Plot temp data: {{{
        if plot_temp:
            yaxis3_title = f'{temp_label} /{self._deg_c}'
            hovertemplate = base_ht + f'{temp_label}/{self._deg_c}: '+'%{y}'
            fig.add_scatter(
                x = x,
                y = self._csv_plot_data['temperature'],
                hovertemplate = hovertemplate,
                yaxis = 'y3',
                name = f'{temp_label}/{self._deg_c}',
                mode = 'lines+markers',
                marker = dict(color = 'red'),
                line = dict(color = 'red'),
            )
            third_yaxis = True
        #}}}
        # Update layout: {{{
        if time_range == None:
            time_range = [min(x), max(x)]
        # Update the first y axis and plot: {{{
        fig.update_layout(
            height = height,
            width = width,
            title_text = f'Plot of Time vs. {title}',
            xaxis = dict(
                title = xaxis_title,
                domain = [yaxis_2_position, 1], # the active area for x axis
                range = time_range
            ), 
            yaxis = dict(
                title = yaxis_title,
            ),
            font = dict(
                size = font_size,
            ),
            template = 'simple_white',
            legend = dict(
                yanchor = 'top',
                xanchor = 'right',
                y = 1.2,
                x = 0.99,
            ),

        )
        #}}}
        if y_range:
            fig.update(layout_yaxis_range = y_range)
        # if second y axis: {{{
        if second_yaxis:
            fig.update_layout(
                yaxis2 = dict(
                    title = yaxis2_title,
                    anchor = 'free',
                    overlaying = 'y',
                    side = 'left',
                    position = yaxis_2_position,
                ),
            )
        #}}}
        # if third axis: {{{
        if third_yaxis:
            fig.update_layout(
                yaxis3 = dict(
                    title = yaxis3_title,
                    anchor = 'x',
                    overlaying = 'y',
                    side = 'right'

                ),
            )
        #}}}
        #}}}

        #}}}
        fig.show()     
    #}}}
    # plot_multiple_patterns: {{{
    def plot_multiple_patterns(self,
            indices= None, 
            template:str = 'simple_white',
            offset:float = 0,
            show_ycalc:bool = True,
            show_ydiff:bool = False,
            time_units:str = 'min', 
            tth_range:list = None,
            use_calc_temp:bool = True,
            height = 800,
            width = 1000,
            show_legend:bool = True,
            font_size:int = 20,
            rwp_decimals:int = 2,
            temp_decimals:int = 2, 
            standard_colors:bool = False,
            ):
        '''
        This function will run a loop mode of "plot_pattern"
        This allows us to have multiple pattern fits overlaid on 
        one-another.

        Use the "offset" to change the spacing of the patterns.

        The "indices" can be either a list of specific files or a
        3-tuple that goes into np.linspace(low, high, number) 

        "standard_colors": If True, this will default to the standard color scheme
        '''
        if type(indices) == tuple:
            lo,hi,num = indices
            indices= np.around(np.linspace(lo,hi,num),0) #Creates a range
            

        self.multi_pattern = go.Figure()
        for index, i in enumerate(indices):
            # Get the data for current index: {{{
            tth, yobs, ycalc,ydiff, hovertemplate,title_text,xaxis_title,yaxis_title = self.plot_pattern(
                index= i, 
                template= template,
                time_units= time_units, 
                tth_range=tth_range,
                use_calc_temp=use_calc_temp,
                height =height,
                width =width,
                font_size=font_size,
                rwp_decimals= rwp_decimals,
                temp_decimals= temp_decimals,
                printouts=False,
                run_in_loop=True,
            )
            #}}}
            # Generate the figure: {{{
            color1 = self._get_random_color()
            color2 = self._get_random_color()
            color3 = self._get_random_color()
            if standard_colors:
                colors = ['blue','red','grey']
            else:
                colors = [color1, color2, color3]
            ydict = {'yobs':yobs,'ycalc':ycalc,'ydiff':ydiff}
            # Add the plots: {{{
            for j, key in enumerate(ydict):
                if key == 'yobs' or key == 'ycalc' and show_ycalc or key == 'ydiff' and show_ydiff:
                    self.multi_pattern.add_scatter(
                        x = tth,
                        y = np.array(ydict[key])+(offset*index),
                        hovertemplate = hovertemplate,
                        marker = dict(
                            color = colors[j],
                        ),
                        name = f'Pattern # {i}: {key}',
                    )
            #}}}
        # Update Layout: {{{
        self._update_pattern_layout(
            fig = self.multi_pattern,
            title_text=f'Patterns {indices}',
            xaxis_title=xaxis_title,
            yaxis_title=yaxis_title,
            tth_range=tth_range,
            template=template,
            font_size=font_size,
            height=height,
            width=width,
            show_legend=show_legend,
        )
        #}}} 
        #}}}
        self.multi_pattern.show()
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
                    if flag == flag_search:
                        corr_dict[i][name1].update({
                            j:{name2:correlation} 
                        })
                        if debug:
                            print(f'\t{j} ({name2}): {correlation}')
            #}}} 
        return corr_dict
    #}}}
#}}}

