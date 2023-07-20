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
        for i, key in enumerate(self.metadata):
            filename = self.metadata[key] # Gives us the filename to read.
            time = None
            temp = None
            # Work to parse the data: {{{
            with open(filename,'r') as f:
                lines = f.readlines()
                for line in lines:
                    t = re.findall(r'\d+\.\d+',line) # This gives me the epoch time if it is on a        line.
                    if time_key in line and t:
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
        self.topas_dir = 'C:\\TOPAS%s'%topas_version # sets the directory
        self.fileextension= fileextension# This is the extension of your data.
        self.current_dir = os.getcwd() # This saves the original location
        Utils.__init__(self)
        UsefulUnicode.__init__(self)
        self._data_collected = False # This tracks if the "get_data" function was run
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
            template_dir:str = None
        ):
        '''
        Code to run automated Rietveld Refinements based on Adam/Gerry's Code
        '''
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
            if 'Results_1.csv' in line:
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
        #}}}
        # Begin the Refinements: {{{
        rng = tqdm([int(fl) for fl in tmp_rng])
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
            print_files:bool = False,
            get_orig_patt_and_meta:bool = True,
        ):
        '''
        This will gather and sort all of the output files from your refinements for you. 
        
        csv_labels: 
            This tells the program what each individual entry of the labels mean. 
        '''
        self.rietveld_data = {}
        self.sorted_csvs = sorted(glob.glob(f'{csv_prefix}_*.csv')) #gathers csvs with the given prefix
        self.sorted_xy = sorted(glob.glob(f'{xy_prefix}_*.xy'))
        # Print Statements: {{{
        if print_files:
            print('I   CSV\tXY')
            for i, fn in enumerate(self.sorted_csvs):
                print(f'{i}: {fn}\t{self.sorted_xy[i]}')
        #}}}
        # Categorize the Refined Data: {{{ 
        for i, csv in enumerate(self.sorted_csvs):     
            csv_contents = [float(line) for line in open(csv)] # This gives us the values in the csv. 
            # Handle the XY Data: {{{
            xy_data = np.loadtxt(self.sorted_xy[i], delimiter=',') # imports the xy data to an array
            ttheta = xy_data[:,0]
            yobs = xy_data[:,1]
            ycalc = xy_data[:,2]
            ydiff = xy_data[:,3]
            #}}}
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
            } # Create an entry for the csv data
            # If you have provided CSV labels: {{{
            if csv_labels:
                for j, line in enumerate(csv_contents):
                    if j <= len(csv_labels)-j: 
                        self.rietveld_data[i]['csv'][csv_labels[j]] = np.around(line, 4) # This records a dictionary entry with the name of the float
                    else:
                        self.rietveld_data[i][f'csv_data_{j}'] = np.around(line,4) # If too few labels given
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
                    'pattern_index':md['pattern_index'],
                })
            #}}}
            
            
        #}}} 
        self._data_collected = True #Now, the data have been collected and plot pattern will be informed
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
    def _sort_csv_keys(self,keys:list = None):
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
                            for key in keys:
                                if intermediate == key:
                                    if key not in self._csv_plot_data[unique_element]:
                                        self._csv_plot_data[unique_element][key] = [] #This gives an empty list
                                    self._csv_plot_data[unique_element][key].append(csv[csv_key]) # This adds the value for the dictionary

                            
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
    # plot_pattern: {{{
    def plot_pattern(self,
            index:int = 0, 
            time_units:str = 'min',
            height = 800,
            width = 1000,
            font_size:int = 20,
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
        temp = self.rietveld_data[index]['temperature']
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
        self.pattern_plot.update_layout(
            height = height,
            width = width,
            title_text = f'Time: {self._current_time} {time_units}, (Element Temp: {temp}{self._deg_c}) Rwp: {self._rwp}',
            xaxis_title = f'2{self._theta}{self._degree}',
            yaxis_title = 'Intensity',
            template = 'simple_white',
            font = dict(
                size = font_size,
            ),
            legend = dict(
                yanchor = 'top',
                y = 0.99,
                xanchor = 'right',
                x = 0.99,
            ),
        )
        #}}}
        #}}}
        print('Additional Refinement Information:')
        print(self._csv_string)
        self.pattern_plot.show()
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
        max_val = max(data)
        normalized = [val/max_val for val in data]
        return normalized
    #}}}
    # plot_csv_info: {{{
    def plot_csv_info(self, 
            plot_type:str = 'rwp',
            plot_temp:bool = True,
            time_units:str = 'min', 
            normalized:bool = False,
            height = 800,
            width = 1100,
            font_size = 20,
            yaxis_2_position = 0.15,

            ):
        ''' 
        plot_type: This can be any of the below. 
            1.) "lattice parameters" or "lattice" or "lp"
            2.) "scale factor" or "sf"
            3.) "rwp" 
            4.) "volume" or "vol"

        The purpose of this function is to give the user a 
        look at the data output in csv form by TOPAS at the 
        conclusion of the refinement series. 

        This is a little complex since we do not necessarily know what we want to plot 
        the user will decide that. 

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
        #}}}
        # Scale Factor: {{{
        elif plot_type == 'scale factor' or plot_type == 'sf':
            keys = ['scale_factor', 'sf','scale factor'] # These are the variations likely to be used
            yaxis_title = 'Scale Factor'
            normalized = True
        #}}}
        # Rwp: {{{
        elif plot_type == 'rwp':
            keys = ['rwp']
            yaxis_title = 'Rwp'
        #}}}
        # Volume: {{{
        elif plot_type == 'volume' or plot_type == 'vol':
            keys = ['vol', 'volume', 'cell volume', 'cell_volume']
            yaxis_title = f'Volume / {self._angstrom}{self._cubed}'
        #}}}
        #}}}
        # Get a dictionary containing only the data we care about: {{{
        self._sort_csv_keys(keys) 
        for entry in self.rietveld_data:
            if plot_temp:
                if 'temperature' not in self._csv_plot_data:
                    self._csv_plot_data['temperature'] = []
                self._csv_plot_data['temperature'].append(self.rietveld_data[entry]['temperature']) # Record the temperature
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
            )
            

        else:
            for substance in self._csv_plot_data:
                rand_color = list(np.random.choice(range(256),size = 3)) # This generates a random color for each of the substances
                color = f'rgb({rand_color[0]},{rand_color[1]},{rand_color[2]})'
                if substance != 'time' and substance != 'temperature':
                    entry = self._csv_plot_data[substance] # This will be a dictionary entry with keys. 
                    entry_keys = list(entry.keys()) # These will be the keys for the entry. 
                    for plot_key in entry_keys:
                        # Handle most cases: {{{ 
                        if plot_key != 'al' or plot_key != 'be' or plot_key != 'ga' or plot_key != 'alpha' or plot_key != 'beta' or plot_key != 'gamma':
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
            yaxis3_title = f'Temperature /{self._deg_c}'
            hovertemplate = base_ht + f'Temperature/{self._deg_c}: '+'%{y}'
            fig.add_scatter(
                x = x,
                y = self._csv_plot_data['temperature'],
                hovertemplate = hovertemplate,
                yaxis = 'y3',
                name = f'Temperature/{self._deg_c}',
                mode = 'lines+markers',
                marker = dict(color = 'red'),
                line = dict(color = 'red'),
            )
            third_yaxis = True
        #}}}
        # Update layout: {{{
        fig.update_layout(
            height = height,
            width = width,
            title_text = f'Plot of Time vs. {plot_type}',
            xaxis_title = xaxis_title,
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
        fig.show()
       
        
    #}}}
#}}}

