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
from generic_plotly_utils import GenericPlotter
#import pandas as pd
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
# OUT_Parser: {{{
class OUT_Parser:
    # __init__:{{{ 
    def __init__(self):
        pass
    #}}} 
    #_get_ints_floats_words: {{{
    def _get_ints_floats_words(self,txt:str = None): 
        '''
        This function just returns 3 lists after doing a re search for
        integers
        floats
        words
        Returns a 3 tuple of the lists
     
        Use the lambda function to pre-screen the returns to exclude blanks
        '''
        ints = list(filter(lambda x: len(x) >0,re.findall(r'\d+', txt)))
        floats = list(filter(lambda x: len(x) >0,re.findall(r'\d+\.\d+e?\-?\d+',txt)))
        words = list(filter(lambda x: len(x) >0,re.findall(r'\w+_?\w+',txt)))
        return(ints,floats,words)
    #}}}
    # _parse_out_phases: {{{
    def _parse_out_phases(self,out_file:str = None, idx:int = None):
        '''
        This function is able to read in output files in a general manner and update a dictionary 
        called "out_phase_dict" as an attribute. 
        The function takes an output file to read. 
        

        The way that the dictionary produced is formatted is as follows: 
        
        '''
        out_phase_dict = {} # Initialize the current pattern output file dictionary
        with open(out_file,'r') as out:
            lattice_macros = ['Cubic', 'Tetragonal', 'Hexagonal', 'Rhombohedral']
            lattice_macro_keys = [
                ['a'], # Cubic
                ['a', 'c'], # Tetragonal
                ['a', 'c'], # Hexagonal
                ['a', 'ga'], # Rhombohedral
            ]
            lines = out.readlines()
            phase = None
            comment_block = False # This tracks if the program sees a comment block to ignore all text between the two lines. 
            phase_num = 0 # This counts all of the str, hkl_Is, xo_Is
            last_phase_type = None # This will keep track of the 
            end_of_out = False # This will change to True when it finds "C_matrix_normalized"
            for i, line in enumerate(lines):
                skipline = False # This is to skip over the end of comment blocks and str, hkl_Is, xo_I lines.
                # Check for early items like Rwp: {{{
                if 'r_wp' in line:
                    items = re.findall(r'r_wp\s+\d+\.\d+',line)
                    if items:
                        line = items[0] #This gives us the R_wp separated by whitespace
                        rwp = float(line.split(' ')[-1])
                        out_phase_dict['rwp'] = rwp
                #}}}
                # Check for Comments: {{{
                if '\'' in line: # Search for comment indicator
                    splitline = line.split("'")# splits the line based on the presence of a single quote.
                    if len(splitline) >1: 
                        line = splitline[0] # This redefines the line as the line without the comment. 
                elif "/*" in line: # Look for start comment block
                    comment_block = True # This marks the start of a comment block
                elif "*/" in line:# Look for end comment block
                    comment_block = False # This marks the end of a comment block
                    skipline = True
                #}}}
                # Start by finding a structure: {{{
                if 'str' in line and not comment_block and not skipline: # Look for the start of a structure object that is not inside of a comment block 
                    if last_phase_type != None:
                        phase_num += 1
                    last_phase_type = 'str'
                    out_phase_dict[phase_num] = {'phase_type': last_phase_type}
                    skipline = True
                 
                elif 'hkl_Is' in line and not comment_block and not skipline: # Check for the hkl_Is flag for an hkl phase. Also make sure that the phase is not inside of a comment block
                    if last_phase_type != None:
                        phase_num += 1
                    last_phase_type = 'hkl_Is'
                    out_phase_dict[phase_num] = {'phase_type': last_phase_type}
                    skipline = True
                elif 'xo_Is' in line and not comment_block and not skipline: # Check for the xo_Is flag for peaks phases. 
                    if last_phase_type != None:
                        phase_num += 1
                    last_phase_type = 'xo_Is'
                    out_phase_dict[phase_num] = {'phase_type': last_phase_type}
                    skipline = True
                elif 'C_matrix_normalized' in line or 'out' in line:
                    end_of_out = True # This stops recording
                 
                #}}}
                # Add the phase data: {{{
                if not comment_block and last_phase_type != None and not end_of_out and not skipline: # This will record values ONLY if we have not reached the C_matrix, are not in a comment block, or are inside of a phase.
                    ints,floats,words = self._get_ints_floats_words(line) # This is used a lot, so let's just use it here. 
                    # Phase Name: {{{
                    if 'phase_name' in line:
                        split = re.findall(r'\w+',line)
                        key = split[0] # This is the label
                        value = '_'.join(split[1:]) # This is the phase name
                        out_phase_dict[phase_num].update({key:value})
                    #}}}
                    # Phase MAC: {{{
                    elif 'phase_MAC' in line:
                        split = re.findall(r'\d+\.\d+',line)[0]
                        key = 'phase_MAC'
                        value = float(split)
                        out_phase_dict[phase_num].update({key:value})
                    #}}}
                    # LVol FWHM CS G L: {{{
                    elif 'LVol_FWHM_CS_G_L' in line:
                        #key = 'LVol_FWHM_CS_G_L'
                        #out_phase_dict[phase_num][key] = {}
                        split = line.split(',')
                        macro_vars = ['k', 'lvol', 'kf', 'lvolf', 'csgc', 'csgv', 'cslc', 'cslv'] # These are the parameters that are separated by commas for this macro. 
                        # Find what value to record: {{{
                        for j, value in enumerate(split):
                            macro_var = macro_vars[j] # This tells the program what to look for
                            rec = None # This is the default value to record for the macro var key
                            ints,floats,words = self._get_ints_floats_words(value)
                         
                            if macro_var == 'k' or macro_var == 'kf' or macro_var == 'lvol' or macro_var == 'lvolf' or macro_var == 'csgv' or macro_var == 'cslv': # Numerical variables
                                if ints and not floats:
                                    rec = int(ints[0])
                                elif floats:
                                    rec = float(floats[0])
                            elif macro_var == 'csgc' or macro_var == 'cslc': # String variables
                                if words:
                                    rec = words[0] # This takes the string
                            out_phase_dict[phase_num].update({macro_var: rec})
                        #}}}    
                    #}}}
                    # e0_from_Strain: {{{
                    elif 'e0_from_Strain' in line:
                        #key = 'e0_from_Strain'
                        split = line.split(',')
                        macro_vars = ['e0', 'sgc', 'sgv','slc', 'slv'] # These are the parameters separated by commas for this macro
                        # Figure Out what needs to be recorded: {{{
                        for j, value in enumerate(split):
                            macro_var = macro_vars[j] # Tells the program what to look for. 
                            rec = None
                            ints,floats,words = self._get_ints_floats_words(value)
                            if macro_var == 'e0' or macro_var == 'sgv' or macro_var == 'slv':
                                if ints and not floats:
                                    rec = int(ints[0])
                                elif floats:
                                    rec = float(floats[0])
                            elif macro_var == 'sgc' or macro_var == 'slc': 
                                try:
                                    rec = words[0]
                                except:
                                    rec = None

                            out_phase_dict[phase_num].update({macro_var:rec})
                        #}}}
                    #}}}
                    # Get lattice parameters if not in a macro: {{{
                    elif re.findall(r'^\s+a|^\s+b|^\s+c|^\s+al|^\s+be|^\s+ga',line):
                        #print(line)
                        words = re.findall(r'a|b|c|al|be|ga',line)
                        out_phase_dict[phase_num][words[0]] = float(floats[0])
                    #}}}
                    # MVW: {{{
                    elif 'MVW' in line:
                        split = line.split(',')
                        macro_vars = ['m_v','v_v','w_v'] # This is the mass value, volume value, weight value.
                        for j, value in enumerate(split):
                            ints,floats,words = self._get_ints_floats_words(value)
                            macro_var = macro_vars[j] # This is the current macro variable to look for. 
                            rec = None
                            if floats:
                                rec = float(floats[0]) # This should give me the calculated value
                            out_phase_dict[phase_num].update({macro_var:rec}) # This records the macro value

                    #}}}
                    # Get the cell mass: {{{
                    elif 'cell_mass' in line: 
                        out_phase_dict[phase_num]['cell_mass'] = float(floats[0])
                    #}}}
                    # Get the volume: {{{
                    elif 'volume' in line:
                        out_phase_dict[phase_num]['volume'] = float(floats[0])
                    #}}}
                    # Get the weight percent: {{{
                    elif 'weight_percent' in line: 
                        out_phase_dict[phase_num]['weight_percent'] = float(floats[0])
                    #}}}
                    # Get R_Bragg: {{{
                    elif 'r_bragg' in line:
                        out_phase_dict[phase_num]['r_bragg'] = float(floats[0])
                    #}}}
                    # Get space_group: {{{
                    elif 'space_group' in line:
                        sg = re.findall(r'\w+\d?\/?\w+',line)
                        out_phase_dict[phase_num]['space_group'] = sg[-1]
                    #}}}
                    # Parse Sites: {{{
                    elif 'site' in line.lower():
                        if 'sites' not in list(out_phase_dict[phase_num].keys()):
                            out_phase_dict[phase_num]['sites'] = {} # Initialize a bin to hold these data.
                        site_args = [
                            'site', # Not important
                            'element_label', # This is the element plus an index, typically. 
                            'x', # This is the label "x"
                            'xval', # This is the value for x
                            'y', # This may not be the next value (if you have mins and maxes, they will come before this)
                            'yval', # Value for y
                            'z', # This may not be next, if mins and maxes exist,they will be before this. 
                            'zval', # value for z
                            'element', # This should be the actual element name (e.g. no number)
                            'occ', #This will be a float for the occupancy. 
                            'beq', # This may or may not be present. but is the key to look for b values
                            'beq_label', # If the next entry is a string, it is the B-value label
                            'bval', # The next thing should be the actual B value
                         
                        ]
                        #split = list(filter(lambda x: len(x) > 0, line.split(' '))) # Don't record any blank strings
                        #split = list(filter(lambda x: len(x)>1 , re.findall(r'\S+', line)))
                        split = re.findall(r'\S+',line) # This should only give strings that are not whitespace
                        x_idx = None
                        y_idx = None
                        z_idx = None
                        occ_idx = None
                        occ = None
                        beq_idx = None
                        bval_recorded = False
                        site = None 
                        #print(split)
                        for j, val in enumerate(split): 
                            #ints,floats,words = self._get_ints_floats_words(val) # This gets these quantities for the current entry.
                            if j == 1:
                                site = val # This should be the site label
                                out_phase_dict[phase_num]['sites'][site] = {}
                            if j > 1:
                                # Find KWDS: {{{
                                #val = val.strip('\t') # Get rid of tabs
                                #val = val.strip(' ') # Get rid of spaces 
                                if val == 'x':
                                    x_idx = j
                                elif val == 'y':
                                    y_idx = j
                                elif val == 'z':
                                    z_idx = j
                                elif val == 'beq':
                                    beq_idx = j
                                if val == 'occ':
                                    occ_idx = j # This is where occ is called. This means that the atom will be next then the float.
                                #}}}
                                # Record Vals: {{{
                                if x_idx:
                                    if j == x_idx+1:
                                        coord = re.findall(r'\d+\.\d+|\d+',val) # This gets the coordinate
                                        out_phase_dict[phase_num]['sites'][site].update({'x': float(coord[0])})
                                if y_idx:
                                    if j == y_idx+1:
                                        coord = re.findall(r'\d+\.\d+|\d+',val) # This gets the coordinate
                                        out_phase_dict[phase_num]['sites'][site].update({'y': float(coord[0])})
                                if z_idx:
                                    if j == z_idx+1:
                                        coord = re.findall(r'\d+\.\d+|\d+',val) # This gets the coordinate
                                        out_phase_dict[phase_num]['sites'][site].update({'z': float(coord[0])})
                                if beq_idx and not bval_recorded:
                                    # Get the variable name: {{{
                                    if j == beq_idx +1: 
                                        try:
                                            b_val_keyword = re.findall(r'\w+_\w+',val)[0] # This should find any keyword for bvals 
                                            out_phase_dict[phase_num]['sites'][site].update({'b_val_prm':b_val_keyword}) # This will record the variable. 
                                        except:
                                            out_phase_dict[phase_num]['sites'][site].update({'b_val_prm':None}) # If the previous criteria are not met, record nothing.
                                            try:
                                                bval = float(re.findall(r'\d+\.\d+|\d+',val)[0])
                                                out_phase_dict[phase_num]['sites'][site].update({'bval': bval})
                                                bval_recorded = True
                                            except:
                                                out_phase_dict[phase_num]['sites'][site].update({'bval': None})

                                    #}}}
                                    # Get the variable value: {{{
                                    elif j == beq_idx+2: 
                                        try:
                                            bval = float(re.findall(r'\d+\.\d+|\d+',val)[0]) 
                                            out_phase_dict[phase_num]['sites'][site].update({'bval': bval})
                                            bval_recorded = True
                                        except:
                                            out_phase_dict[phase_num]['sites'][site].update({'bval':None})
                                    #}}}
                                if occ_idx:
                                    if j == occ_idx+1:
                                        occ = val # This should be the atom name for the occupancy
                                    elif j == occ_idx+2:
                                        occupancy = re.findall(r'\d+\.\d+|\d+',val)
                                        out_phase_dict[phase_num]['sites'][site].update({f'{occ}_occ':float(occupancy[0])})
                                #}}}
                    #}}}
                    # Parse TOPAS Scale: {{{
                    elif 'scale ' in line: 
                        #If the e isnt in the float, that means that we are dealing with a replacement that doesnt have a decimal point before the e so it isnt matching. 
                        # This has been thoroughly validated
                        floats = re.findall(r'\d+\.?\d+?e\-?\d+|\d+\.?e\-?\d+',line)  
                        out_phase_dict[phase_num][words[1]] = float(floats[0]) # The scale factor will be the first item in the list of floats here.
                 
                    #}}}
                    # Parse user-defined Scale Factors: {{{
                    elif 'scale_factor' in line: 
                        # It is possible that this will be 0.0000 which may not match nicely. Regardless since this is calculated by TOPAS, it should have more 
                        # than 1 digit past the decimal. 
                        # The line below will only default to looking for something like 0.0000 if it is unable to find something matching the format: 
                        
                        floats = re.findall(r'\d+\.\d+e\-?\d+|\d+\.\d+',line) 
                        if words[0] == 'prm':
                            words[0] = words[1]
                        out_phase_dict[phase_num]['scale_factor'] = float(floats[0]) # We are using the second match here because I am dividing by 1e-7 everytime and that is going to be the first match.
                        out_phase_dict[phase_num]['usr_sf_name'] = words[0]
                 
                    #}}}
                    # Parse Phase_LAC_1_on_cm and Phase_Density_g_on_cm3: {{{
                    elif 'Phase_LAC_1_on_cm' in line or 'Phase_Density_g_on_cm3' in line:
                        floats = list(float(x) for x in floats)
                        out_phase_dict[phase_num][words[0]] = floats
                    #}}}
                    # If you Need anything else, UNCOMMENT PRINT HERE TO FIGURE OUT HOW TO ADD IT: {{{
                    else:
                        #print(i,line)
                        pass
                    #}}} 
                    # Check for lattice parameters: {{{
                    for j, latt in enumerate(lattice_macros):
                        if latt in line:
                            splitline = line.split(',')
                            for k, value in enumerate(splitline):
                                ints,floats,words = self._get_ints_floats_words(value)
                                out_phase_dict[phase_num][lattice_macro_keys[j][k]] = float(floats[0])
                     
                    #}}}
                #}}}
        return out_phase_dict
    #}}}
#}}}
# Mole_Fraction_Tools: {{{
class Mole_Fraction_Tools:
    '''
    This class is designed to make obtaining mole fractions easy
    for any sample or set of samples you may be working with. 
    It leverages a csv version of the periodic table and some 
    NLP to the molar mass of formulas and provides tools that can be used inside
    of the TOPAS_Refinements class.
    '''
    def __init__(self, formulas:list = None, ):
        '''
        formulas: A list of strings for each of the formulas you are dealing with. 
        The formulas are case sensitive so make sure that your input is appropriately formatted
        '''
        self._formulas = formulas
        # Define the periodic Table: {{{
        self._ptable = {'AtomicNumber': {0: 1,1: 2,2: 3,3: 4,4: 5,5: 6,6: 7,7: 8,8: 9,9: 10,10: 11,11: 12,12: 13,13: 14,14: 15,15: 16,16: 17,17: 18,18: 19,19: 20,20: 21,21: 22,22: 23,23: 24,24: 25,25: 26,26: 27,27: 28,28: 29,29: 30,30: 31,31: 32,32: 33,33: 34,34: 35,35: 36,36: 37,37: 38,38: 39,39: 40,40: 41,41: 42,42: 43,43: 44,44: 45,45: 46,46: 47,47: 48,48: 49,49: 50,50: 51,51: 52,52: 53,53: 54,54: 55,55: 56,56: 57,57: 58,58: 59,59: 60,60: 61,61: 62,62: 63,63: 64,64: 65,65: 66,66: 67,67: 68,68: 69,69: 70,70: 71,71: 72,72: 73,73: 74,74: 75,75: 76,76: 77,77: 78,78: 79,79: 80,80: 81,81: 82,82: 83,83: 84,84: 85,85: 86,86: 87,87: 88,88: 89,89: 90,90: 91,91: 92,92: 93,93: 94,94: 95,95: 96,96: 97,97: 98,98: 99,99: 100,100: 101,101: 102,102: 103,103: 104,104: 105,105: 106,106: 107,107: 108,108: 109,109: 110,110: 111,111: 112,112: 113,113: 114,114: 115,115: 116,116: 117,117: 118},'Element': {0: 'Hydrogen',1: 'Helium',2: 'Lithium',3: 'Beryllium',4: 'Boron',5: 'Carbon',6: 'Nitrogen',7: 'Oxygen',8: 'Fluorine',9: 'Neon',10: 'Sodium',11: 'Magnesium',12: 'Aluminum',13: 'Silicon',14: 'Phosphorus',15: 'Sulfur',16: 'Chlorine',17: 'Argon',18: 'Potassium',19: 'Calcium',20: 'Scandium',21: 'Titanium',22: 'Vanadium',23: 'Chromium',24: 'Manganese',25: 'Iron',26: 'Cobalt',27: 'Nickel',28: 'Copper',29: 'Zinc',30: 'Gallium',31: 'Germanium',32: 'Arsenic',33: 'Selenium',34: 'Bromine',35: 'Krypton',36: 'Rubidium',37: 'Strontium',38: 'Yttrium',39: 'Zirconium',40: 'Niobium',41: 'Molybdenum',42: 'Technetium',43: 'Ruthenium',44: 'Rhodium',45: 'Palladium',46: 'Silver',47: 'Cadmium',48: 'Indium',49: 'Tin',50: 'Antimony',51: 'Tellurium',52: 'Iodine',53: 'Xenon',54: 'Cesium',55: 'Barium',56: 'Lanthanum',57: 'Cerium',58: 'Praseodymium',59: 'Neodymium',60: 'Promethium',61: 'Samarium',62: 'Europium',63: 'Gadolinium',64: 'Terbium',65: 'Dysprosium',66: 'Holmium',67: 'Erbium',68: 'Thulium',69: 'Ytterbium',70: 'Lutetium',71: 'Hafnium',72: 'Tantalum',73: 'Wolfram',74: 'Rhenium',75: 'Osmium',76: 'Iridium',77: 'Platinum',78: 'Gold',79: 'Mercury',80: 'Thallium',81: 'Lead',82: 'Bismuth',83: 'Polonium',84: 'Astatine',85: 'Radon',86: 'Francium',87: 'Radium',88: 'Actinium',89: 'Thorium',90: 'Protactinium',91: 'Uranium',92: 'Neptunium',93: 'Plutonium',94: 'Americium',95: 'Curium',96: 'Berkelium',97: 'Californium',98: 'Einsteinium',99: 'Fermium',100: 'Mendelevium',101: 'Nobelium',102: 'Lawrencium',103: 'Rutherfordium',104: 'Dubnium',105: 'Seaborgium',106: 'Bohrium',107: 'Hassium',108: 'Meitnerium',109: 'Darmstadtium ',110: 'Roentgenium ',111: 'Copernicium ',112: 'Nihonium',113: 'Flerovium',114: 'Moscovium',115: 'Livermorium',116: 'Tennessine',117: 'Oganesson'},'Symbol': {0: 'H',1: 'He',2: 'Li',3: 'Be',4: 'B',5: 'C',6: 'N',7: 'O',8: 'F',9: 'Ne',10: 'Na',11: 'Mg',12: 'Al',13: 'Si',14: 'P',15: 'S',16: 'Cl',17: 'Ar',18: 'K',19: 'Ca',20: 'Sc',21: 'Ti',22: 'V',23: 'Cr',24: 'Mn',25: 'Fe',26: 'Co',27: 'Ni',28: 'Cu',29: 'Zn',30: 'Ga',31: 'Ge',32: 'As',33: 'Se',34: 'Br',35: 'Kr',36: 'Rb',37: 'Sr',38: 'Y',39: 'Zr',40: 'Nb',41: 'Mo',42: 'Tc',43: 'Ru',44: 'Rh',45: 'Pd',46: 'Ag',47: 'Cd',48: 'In',49: 'Sn',50: 'Sb',51: 'Te',52: 'I',53: 'Xe',54: 'Cs',55: 'Ba',56: 'La',57: 'Ce',58: 'Pr',59: 'Nd',60: 'Pm',61: 'Sm',62: 'Eu',63: 'Gd',64: 'Tb',65: 'Dy',66: 'Ho',67: 'Er',68: 'Tm',69: 'Yb',70: 'Lu',71: 'Hf',72: 'Ta',73: 'W',74: 'Re',75: 'Os',76: 'Ir',77: 'Pt',78: 'Au',79: 'Hg',80: 'Tl',81: 'Pb',82: 'Bi',83: 'Po',84: 'At',85: 'Rn',86: 'Fr',87: 'Ra',88: 'Ac',89: 'Th',90: 'Pa',91: 'U',92: 'Np',93: 'Pu',94: 'Am',95: 'Cm',96: 'Bk',97: 'Cf',98: 'Es',99: 'Fm',100: 'Md',101: 'No',102: 'Lr',103: 'Rf',104: 'Db',105: 'Sg',106: 'Bh',107: 'Hs',108: 'Mt',109: 'Ds ',110: 'Rg ',111: 'Cn ',112: 'Nh',113: 'Fl',114: 'Mc',115: 'Lv',116: 'Ts',117: 'Og'},'AtomicMass': {0: 1.007,1: 4.002,2: 6.941,3: 9.012,4: 10.811,5: 12.011,6: 14.007,7: 15.999,8: 18.998,9: 20.18,10: 22.99,11: 24.305,12: 26.982,13: 28.086,14: 30.974,15: 32.065,16: 35.453,17: 39.948,18: 39.098,19: 40.078,20: 44.956,21: 47.867,22: 50.942,23: 51.996,24: 54.938,25: 55.845,26: 58.933,27: 58.693,28: 63.546,29: 65.38,30: 69.723,31: 72.64,32: 74.922,33: 78.96,34: 79.904,35: 83.798,36: 85.468,37: 87.62,38: 88.906,39: 91.224,40: 92.906,41: 95.96,42: 98.0,43: 101.07,44: 102.906,45: 106.42,46: 107.868,47: 112.411,48: 114.818,49: 118.71,50: 121.76,51: 127.6,52: 126.904,53: 131.293,54: 132.905,55: 137.327,56: 138.905,57: 140.116,58: 140.908,59: 144.242,60: 145.0,61: 150.36,62: 151.964,63: 157.25,64: 158.925,65: 162.5,66: 164.93,67: 167.259,68: 168.934,69: 173.054,70: 174.967,71: 178.49,72: 180.948,73: 183.84,74: 186.207,75: 190.23,76: 192.217,77: 195.084,78: 196.967,79: 200.59,80: 204.383,81: 207.2,82: 208.98,83: 210.0,84: 210.0,85: 222.0,86: 223.0,87: 226.0,88: 227.0,89: 232.038,90: 231.036,91: 238.029,92: 237.0,93: 244.0,94: 243.0,95: 247.0,96: 247.0,97: 251.0,98: 252.0,99: 257.0,100: 258.0,101: 259.0,102: 262.0,103: 261.0,104: 262.0,105: 266.0,106: 264.0,107: 267.0,108: 268.0,109: 271.0,110: 272.0,111: 285.0,112: 284.0,113: 289.0,114: 288.0,115: 292.0,116: 295.0,117: 294.0},'NumberofNeutrons': {0: 0,1: 2,2: 4,3: 5,4: 6,5: 6,6: 7,7: 8,8: 10,9: 10,10: 12,11: 12,12: 14,13: 14,14: 16,15: 16,16: 18,17: 22,18: 20,19: 20,20: 24,21: 26,22: 28,23: 28,24: 30,25: 30,26: 32,27: 31,28: 35,29: 35,30: 39,31: 41,32: 42,33: 45,34: 45,35: 48,36: 48,37: 50,38: 50,39: 51,40: 52,41: 54,42: 55,43: 57,44: 58,45: 60,46: 61,47: 64,48: 66,49: 69,50: 71,51: 76,52: 74,53: 77,54: 78,55: 81,56: 82,57: 82,58: 82,59: 84,60: 84,61: 88,62: 89,63: 93,64: 94,65: 97,66: 98,67: 99,68: 100,69: 103,70: 104,71: 106,72: 108,73: 110,74: 111,75: 114,76: 115,77: 117,78: 118,79: 121,80: 123,81: 125,82: 126,83: 126,84: 125,85: 136,86: 136,87: 138,88: 138,89: 142,90: 140,91: 146,92: 144,93: 150,94: 148,95: 151,96: 150,97: 153,98: 153,99: 157,100: 157,101: 157,102: 159,103: 157,104: 157,105: 160,106: 157,107: 159,108: 159,109: 161,110: 161,111: 173,112: 171,113: 175,114: 173,115: 176,116: 178,117: 176},'NumberofProtons': {0: 1,1: 2,2: 3,3: 4,4: 5,5: 6,6: 7,7: 8,8: 9,9: 10,10: 11,11: 12,12: 13,13: 14,14: 15,15: 16,16: 17,17: 18,18: 19,19: 20,20: 21,21: 22,22: 23,23: 24,24: 25,25: 26,26: 27,27: 28,28: 29,29: 30,30: 31,31: 32,32: 33,33: 34,34: 35,35: 36,36: 37,37: 38,38: 39,39: 40,40: 41,41: 42,42: 43,43: 44,44: 45,45: 46,46: 47,47: 48,48: 49,49: 50,50: 51,51: 52,52: 53,53: 54,54: 55,55: 56,56: 57,57: 58,58: 59,59: 60,60: 61,61: 62,62: 63,63: 64,64: 65,65: 66,66: 67,67: 68,68: 69,69: 70,70: 71,71: 72,72: 73,73: 74,74: 75,75: 76,76: 77,77: 78,78: 79,79: 80,80: 81,81: 82,82: 83,83: 84,84: 85,85: 86,86: 87,87: 88,88: 89,89: 90,90: 91,91: 92,92: 93,93: 94,94: 95,95: 96,96: 97,97: 98,98: 99,99: 100,100: 101,101: 102,102: 103,103: 104,104: 105,105: 106,106: 107,107: 108,108: 109,109: 110,110: 111,111: 112,112: 113,113: 114,114: 115,115: 116,116: 117,117: 118},'NumberofElectrons': {0: 1,1: 2,2: 3,3: 4,4: 5,5: 6,6: 7,7: 8,8: 9,9: 10,10: 11,11: 12,12: 13,13: 14,14: 15,15: 16,16: 17,17: 18,18: 19,19: 20,20: 21,21: 22,22: 23,23: 24,24: 25,25: 26,26: 27,27: 28,28: 29,29: 30,30: 31,31: 32,32: 33,33: 34,34: 35,35: 36,36: 37,37: 38,38: 39,39: 40,40: 41,41: 42,42: 43,43: 44,44: 45,45: 46,46: 47,47: 48,48: 49,49: 50,50: 51,51: 52,52: 53,53: 54,54: 55,55: 56,56: 57,57: 58,58: 59,59: 60,60: 61,61: 62,62: 63,63: 64,64: 65,65: 66,66: 67,67: 68,68: 69,69: 70,70: 71,71: 72,72: 73,73: 74,74: 75,75: 76,76: 77,77: 78,78: 79,79: 80,80: 81,81: 82,82: 83,83: 84,84: 85,85: 86,86: 87,87: 88,88: 89,89: 90,90: 91,91: 92,92: 93,93: 94,94: 95,95: 96,96: 97,97: 98,98: 99,99: 100,100: 101,101: 102,102: 103,103: 104,104: 105,105: 106,106: 107,107: 108,108: 109,109: 110,110: 111,111: 112,112: 113,113: 114,114: 115,115: 116,116: 117,117: 118},'Period': {0: 1,1: 1,2: 2,3: 2,4: 2,5: 2,6: 2,7: 2,8: 2,9: 2,10: 3,11: 3,12: 3,13: 3,14: 3,15: 3,16: 3,17: 3,18: 4,19: 4,20: 4,21: 4,22: 4,23: 4,24: 4,25: 4,26: 4,27: 4,28: 4,29: 4,30: 4,31: 4,32: 4,33: 4,34: 4,35: 4,36: 5,37: 5,38: 5,39: 5,40: 5,41: 5,42: 5,43: 5,44: 5,45: 5,46: 5,47: 5,48: 5,49: 5,50: 5,51: 5,52: 5,53: 5,54: 6,55: 6,56: 6,57: 6,58: 6,59: 6,60: 6,61: 6,62: 6,63: 6,64: 6,65: 6,66: 6,67: 6,68: 6,69: 6,70: 6,71: 6,72: 6,73: 6,74: 6,75: 6,76: 6,77: 6,78: 6,79: 6,80: 6,81: 6,82: 6,83: 6,84: 6,85: 6,86: 7,87: 7,88: 7,89: 7,90: 7,91: 7,92: 7,93: 7,94: 7,95: 7,96: 7,97: 7,98: 7,99: 7,100: 7,101: 7,102: 7,103: 7,104: 7,105: 7,106: 7,107: 7,108: 7,109: 7,110: 7,111: 7,112: 7,113: 7,114: 7,115: 7,116: 7,117: 7},'Group': {0: 1.0,1: 18.0,2: 1.0,3: 2.0,4: 13.0,5: 14.0,6: 15.0,7: 16.0,8: 17.0,9: 18.0,10: 1.0,11: 2.0,12: 13.0,13: 14.0,14: 15.0,15: 16.0,16: 17.0,17: 18.0,18: 1.0,19: 2.0,20: 3.0,21: 4.0,22: 5.0,23: 6.0,24: 7.0,25: 8.0,26: 9.0,27: 10.0,28: 11.0,29: 12.0,30: 13.0,31: 14.0,32: 15.0,33: 16.0,34: 17.0,35: 18.0,36: 1.0,37: 2.0,38: 3.0,39: 4.0,40: 5.0,41: 6.0,42: 7.0,43: 8.0,44: 9.0,45: 10.0,46: 11.0,47: 12.0,48: 13.0,49: 14.0,50: 15.0,51: 16.0,52: 17.0,53: 18.0,54: 1.0,55: 2.0,56: 3.0,57: "nan",58: "nan",59: "nan",60: "nan",61: "nan",62: "nan",63: "nan",64: "nan",65: "nan",66: "nan",67: "nan",68: "nan",69: "nan",70: "nan",71: 4.0,72: 5.0,73: 6.0,74: 7.0,75: 8.0,76: 9.0,77: 10.0,78: 11.0,79: 12.0,80: 13.0,81: 14.0,82: 15.0,83: 16.0,84: 17.0,85: 18.0,86: 1.0,87: 2.0,88: 3.0,89: "nan",90: "nan",91: "nan",92: "nan",93: "nan",94: "nan",95: "nan",96: "nan",97: "nan",98: "nan",99: "nan",100: "nan",101: "nan",102: "nan",103: 4.0,104: 5.0,105: 6.0,106: 7.0,107: 8.0,108: 9.0,109: 10.0,110: 11.0,111: 12.0,112: 13.0,113: 14.0,114: 15.0,115: 16.0,116: 17.0,117: 18.0},'Phase': {0: 'gas',1: 'gas',2: 'solid',3: 'solid',4: 'solid',5: 'solid',6: 'gas',7: 'gas',8: 'gas',9: 'gas',10: 'solid',11: 'solid',12: 'solid',13: 'solid',14: 'solid',15: 'solid',16: 'gas',17: 'gas',18: 'solid',19: 'solid',20: 'solid',21: 'solid',22: 'solid',23: 'solid',24: 'solid',25: 'solid',26: 'solid',27: 'solid',28: 'solid',29: 'solid',30: 'solid',31: 'solid',32: 'solid',33: 'solid',34: 'liq',35: 'gas',36: 'solid',37: 'solid',38: 'solid',39: 'solid',40: 'solid',41: 'solid',42: 'artificial',43: 'solid',44: 'solid',45: 'solid',46: 'solid',47: 'solid',48: 'solid',49: 'solid',50: 'solid',51: 'solid',52: 'solid',53: 'gas',54: 'solid',55: 'solid',56: 'solid',57: 'solid',58: 'solid',59: 'solid',60: 'artificial',61: 'solid',62: 'solid',63: 'solid',64: 'solid',65: 'solid',66: 'solid',67: 'solid',68: 'solid',69: 'solid',70: 'solid',71: 'solid',72: 'solid',73: 'solid',74: 'solid',75: 'solid',76: 'solid',77: 'solid',78: 'solid',79: 'liq',80: 'solid',81: 'solid',82: 'solid',83: 'solid',84: 'solid',85: 'gas',86: 'solid',87: 'solid',88: 'solid',89: 'solid',90: 'solid',91: 'solid',92: 'artificial',93: 'artificial',94: 'artificial',95: 'artificial',96: 'artificial',97: 'artificial',98: 'artificial',99: 'artificial',100: 'artificial',101: 'artificial',102: 'artificial',103: 'artificial',104: 'artificial',105: 'artificial',106: 'artificial',107: 'artificial',108: 'artificial',109: 'artificial',110: 'artificial',111: 'artificial',112: 'artificial',113: 'artificial',114: 'artificial',115: 'artificial',116: 'artificial',117: 'artificial'},'Radioactive': {0: "nan",1: "nan",2: "nan",3: "nan",4: "nan",5: "nan",6: "nan",7: "nan",8: "nan",9: "nan",10: "nan",11: "nan",12: "nan",13: "nan",14: "nan",15: "nan",16: "nan",17: "nan",18: "nan",19: "nan",20: "nan",21: "nan",22: "nan",23: "nan",24: "nan",25: "nan",26: "nan",27: "nan",28: "nan",29: "nan",30: "nan",31: "nan",32: "nan",33: "nan",34: "nan",35: "nan",36: "nan",37: "nan",38: "nan",39: "nan",40: "nan",41: "nan",42: 'yes',43: "nan",44: "nan",45: "nan",46: "nan",47: "nan",48: "nan",49: "nan",50: "nan",51: "nan",52: "nan",53: "nan",54: "nan",55: "nan",56: "nan",57: "nan",58: "nan",59: "nan",60: 'yes',61: "nan",62: "nan",63: "nan",64: "nan",65: "nan",66: "nan",67: "nan",68: "nan",69: "nan",70: "nan",71: "nan",72: "nan",73: "nan",74: "nan",75: "nan",76: "nan",77: "nan",78: "nan",79: "nan",80: "nan",81: "nan",82: "nan",83: 'yes',84: 'yes',85: 'yes',86: 'yes',87: 'yes',88: 'yes',89: 'yes',90: 'yes',91: 'yes',92: 'yes',93: 'yes',94: 'yes',95: 'yes',96: 'yes',97: 'yes',98: 'yes',99: 'yes',100: 'yes',101: 'yes',102: 'yes',103: 'yes',104: 'yes',105: 'yes',106: 'yes',107: 'yes',108: 'yes',109: 'yes',110: 'yes',111: 'yes',112: 'yes',113: 'yes',114: 'yes',115: 'yes',116: 'yes',117: 'yes'},'Natural': {0: 'yes',1: 'yes',2: 'yes',3: 'yes',4: 'yes',5: 'yes',6: 'yes',7: 'yes',8: 'yes',9: 'yes',10: 'yes',11: 'yes',12: 'yes',13: 'yes',14: 'yes',15: 'yes',16: 'yes',17: 'yes',18: 'yes',19: 'yes',20: 'yes',21: 'yes',22: 'yes',23: 'yes',24: 'yes',25: 'yes',26: 'yes',27: 'yes',28: 'yes',29: 'yes',30: 'yes',31: 'yes',32: 'yes',33: 'yes',34: 'yes',35: 'yes',36: 'yes',37: 'yes',38: 'yes',39: 'yes',40: 'yes',41: 'yes',42: "nan",43: 'yes',44: 'yes',45: 'yes',46: 'yes',47: 'yes',48: 'yes',49: 'yes',50: 'yes',51: 'yes',52: 'yes',53: 'yes',54: 'yes',55: 'yes',56: 'yes',57: 'yes',58: 'yes',59: 'yes',60: "nan",61: 'yes',62: 'yes',63: 'yes',64: 'yes',65: 'yes',66: 'yes',67: 'yes',68: 'yes',69: 'yes',70: 'yes',71: 'yes',72: 'yes',73: 'yes',74: 'yes',75: 'yes',76: 'yes',77: 'yes',78: 'yes',79: 'yes',80: 'yes',81: 'yes',82: 'yes',83: 'yes',84: 'yes',85: 'yes',86: 'yes',87: 'yes',88: 'yes',89: 'yes',90: 'yes',91: 'yes',92: "nan",93: "nan",94: "nan",95: "nan",96: "nan",97: "nan",98: "nan",99: "nan",100: "nan",101: "nan",102: "nan",103: "nan",104: "nan",105: "nan",106: "nan",107: "nan",108: "nan",109: "nan",110: "nan",111: "nan",112: "nan",113: "nan",114: "nan",115: "nan",116: "nan",117: "nan"},'Metal': {0: "nan",1: "nan",2: 'yes',3: 'yes',4: "nan",5: "nan",6: "nan",7: "nan",8: "nan",9: "nan",10: 'yes',11: 'yes',12: 'yes',13: "nan",14: "nan",15: "nan",16: "nan",17: "nan",18: 'yes',19: 'yes',20: 'yes',21: 'yes',22: 'yes',23: 'yes',24: 'yes',25: 'yes',26: 'yes',27: 'yes',28: 'yes',29: 'yes',30: 'yes',31: "nan",32: "nan",33: "nan",34: "nan",35: "nan",36: 'yes',37: 'yes',38: 'yes',39: 'yes',40: 'yes',41: 'yes',42: 'yes',43: 'yes',44: 'yes',45: 'yes',46: 'yes',47: 'yes',48: 'yes',49: 'yes',50: "nan",51: "nan",52: "nan",53: "nan",54: 'yes',55: 'yes',56: 'yes',57: 'yes',58: 'yes',59: 'yes',60: 'yes',61: 'yes',62: 'yes',63: 'yes',64: 'yes',65: 'yes',66: 'yes',67: 'yes',68: 'yes',69: 'yes',70: 'yes',71: 'yes',72: 'yes',73: 'yes',74: 'yes',75: 'yes',76: 'yes',77: 'yes',78: 'yes',79: 'yes',80: 'yes',81: 'yes',82: 'yes',83: "nan",84: "nan",85: 'yes',86: 'yes',87: 'yes',88: 'yes',89: 'yes',90: 'yes',91: 'yes',92: 'yes',93: 'yes',94: 'yes',95: 'yes',96: 'yes',97: 'yes',98: 'yes',99: 'yes',100: 'yes',101: 'yes',102: 'yes',103: 'yes',104: 'yes',105: 'yes',106: 'yes',107: 'yes',108: 'yes',109: 'yes',110: 'yes',111: 'yes',112: 'yes',113: 'yes',114: 'yes',115: 'yes',116: "nan",117: "nan"},'Nonmetal': {0: 'yes',1: 'yes',2: "nan",3: "nan",4: "nan",5: 'yes',6: 'yes',7: 'yes',8: 'yes',9: 'yes',10: "nan",11: "nan",12: "nan",13: "nan",14: 'yes',15: 'yes',16: 'yes',17: 'yes',18: "nan",19: "nan",20: "nan",21: "nan",22: "nan",23: "nan",24: "nan",25: "nan",26: "nan",27: "nan",28: "nan",29: "nan",30: "nan",31: "nan",32: "nan",33: 'yes',34: 'yes',35: 'yes',36: "nan",37: "nan",38: "nan",39: "nan",40: "nan",41: "nan",42: "nan",43: "nan",44: "nan",45: "nan",46: "nan",47: "nan",48: "nan",49: "nan",50: "nan",51: "nan",52: 'yes',53: 'yes',54: "nan",55: "nan",56: "nan",57: "nan",58: "nan",59: "nan",60: "nan",61: "nan",62: "nan",63: "nan",64: "nan",65: "nan",66: "nan",67: "nan",68: "nan",69: "nan",70: "nan",71: "nan",72: "nan",73: "nan",74: "nan",75: "nan",76: "nan",77: "nan",78: "nan",79: "nan",80: "nan",81: "nan",82: "nan",83: "nan",84: 'yes',85: "nan",86: "nan",87: "nan",88: "nan",89: "nan",90: "nan",91: "nan",92: "nan",93: "nan",94: "nan",95: "nan",96: "nan",97: "nan",98: "nan",99: "nan",100: "nan",101: "nan",102: "nan",103: "nan",104: "nan",105: "nan",106: "nan",107: "nan",108: "nan",109: "nan",110: "nan",111: "nan",112: "nan",113: "nan",114: "nan",115: "nan",116: 'yes',117: 'yes'},'Metalloid': {0: "nan",1: "nan",2: "nan",3: "nan",4: 'yes',5: "nan",6: "nan",7: "nan",8: "nan",9: "nan",10: "nan",11: "nan",12: "nan",13: 'yes',14: "nan",15: "nan",16: "nan",17: "nan",18: "nan",19: "nan",20: "nan",21: "nan",22: "nan",23: "nan",24: "nan",25: "nan",26: "nan",27: "nan",28: "nan",29: "nan",30: "nan",31: 'yes',32: 'yes',33: "nan",34: "nan",35: "nan",36: "nan",37: "nan",38: "nan",39: "nan",40: "nan",41: "nan",42: "nan",43: "nan",44: "nan",45: "nan",46: "nan",47: "nan",48: "nan",49: "nan",50: 'yes',51: 'yes',52: "nan",53: "nan",54: "nan",55: "nan",56: "nan",57: "nan",58: "nan",59: "nan",60: "nan",61: "nan",62: "nan",63: "nan",64: "nan",65: "nan",66: "nan",67: "nan",68: "nan",69: "nan",70: "nan",71: "nan",72: "nan",73: "nan",74: "nan",75: "nan",76: "nan",77: "nan",78: "nan",79: "nan",80: "nan",81: "nan",82: "nan",83: 'yes',84: "nan",85: "nan",86: "nan",87: "nan",88: "nan",89: "nan",90: "nan",91: "nan",92: "nan",93: "nan",94: "nan",95: "nan",96: "nan",97: "nan",98: "nan",99: "nan",100: "nan",101: "nan",102: "nan",103: "nan",104: "nan",105: "nan",106: "nan",107: "nan",108: "nan",109: "nan",110: "nan",111: "nan",112: "nan",113: "nan",114: "nan",115: "nan",116: "nan",117: "nan"},'Type': {0: 'Nonmetal',1: 'Noble Gas',2: 'Alkali Metal',3: 'Alkaline Earth Metal',4: 'Metalloid',5: 'Nonmetal',6: 'Nonmetal',7: 'Nonmetal',8: 'Halogen',9: 'Noble Gas',10: 'Alkali Metal',11: 'Alkaline Earth Metal',12: 'Metal',13: 'Metalloid',14: 'Nonmetal',15: 'Nonmetal',16: 'Halogen',17: 'Noble Gas',18: 'Alkali Metal',19: 'Alkaline Earth Metal',20: 'Transition Metal',21: 'Transition Metal',22: 'Transition Metal',23: 'Transition Metal',24: 'Transition Metal',25: 'Transition Metal',26: 'Transition Metal',27: 'Transition Metal',28: 'Transition Metal',29: 'Transition Metal',30: 'Metal',31: 'Metalloid',32: 'Metalloid',33: 'Nonmetal',34: 'Halogen',35: 'Noble Gas',36: 'Alkali Metal',37: 'Alkaline Earth Metal',38: 'Transition Metal',39: 'Transition Metal',40: 'Transition Metal',41: 'Transition Metal',42: 'Transition Metal',43: 'Transition Metal',44: 'Transition Metal',45: 'Transition Metal',46: 'Transition Metal',47: 'Transition Metal',48: 'Metal',49: 'Metal',50: 'Metalloid',51: 'Metalloid',52: 'Halogen',53: 'Noble Gas',54: 'Alkali Metal',55: 'Alkaline Earth Metal',56: 'Lanthanide',57: 'Lanthanide',58: 'Lanthanide',59: 'Lanthanide',60: 'Lanthanide',61: 'Lanthanide',62: 'Lanthanide',63: 'Lanthanide',64: 'Lanthanide',65: 'Lanthanide',66: 'Lanthanide',67: 'Lanthanide',68: 'Lanthanide',69: 'Lanthanide',70: 'Lanthanide',71: 'Transition Metal',72: 'Transition Metal',73: 'Transition Metal',74: 'Transition Metal',75: 'Transition Metal',76: 'Transition Metal',77: 'Transition Metal',78: 'Transition Metal',79: 'Transition Metal',80: 'Metal',81: 'Metal',82: 'Metal',83: 'Metalloid',84: 'Noble Gas',85: 'Alkali Metal',86: 'Alkaline Earth Metal',87: 'Actinide',88: 'Actinide',89: 'Actinide',90: 'Actinide',91: 'Actinide',92: 'Actinide',93: 'Actinide',94: 'Actinide',95: 'Actinide',96: 'Actinide',97: 'Actinide',98: 'Actinide',99: 'Actinide',100: 'Actinide',101: 'Actinide',102: 'Actinide',103: 'Transactinide',104: 'Transactinide',105: 'Transactinide',106: 'Transactinide',107: 'Transactinide',108: 'Transactinide',109: 'Transactinide',110: 'Transactinide',111: 'Transactinide',112: "nan",113: 'Transactinide',114: "nan",115: 'Transactinide',116: "nan",117: 'Noble Gas'},'AtomicRadius': {0: 0.79,1: 0.49,2: 2.1,3: 1.4,4: 1.2,5: 0.91,6: 0.75,7: 0.65,8: 0.57,9: 0.51,10: 2.2,11: 1.7,12: 1.8,13: 1.5,14: 1.2,15: 1.1,16: 0.97,17: 0.88,18: 2.8,19: 2.2,20: 2.1,21: 2.0,22: 1.9,23: 1.9,24: 1.8,25: 1.7,26: 1.7,27: 1.6,28: 1.6,29: 1.5,30: 1.8,31: 1.5,32: 1.3,33: 1.2,34: 1.1,35: 1.0,36: 3.0,37: 2.5,38: 2.3,39: 2.2,40: 2.1,41: 2.0,42: 2.0,43: 1.9,44: 1.8,45: 1.8,46: 1.8,47: 1.7,48: 2.0,49: 1.7,50: 1.5,51: 1.4,52: 1.3,53: 1.2,54: 3.3,55: 2.8,56: 2.7,57: 2.7,58: 2.7,59: 2.6,60: 2.6,61: 2.6,62: 2.6,63: 2.5,64: 2.5,65: 2.5,66: 2.5,67: 2.5,68: 2.4,69: 2.4,70: 2.3,71: 2.2,72: 2.1,73: 2.0,74: 2.0,75: 1.9,76: 1.9,77: 1.8,78: 1.8,79: 1.8,80: 2.1,81: 1.8,82: 1.6,83: 1.5,84: 1.4,85: 1.3,86: "nan",87: "nan",88: "nan",89: "nan",90: "nan",91: "nan",92: "nan",93: "nan",94: "nan",95: "nan",96: "nan",97: "nan",98: "nan",99: "nan",100: "nan",101: "nan",102: "nan",103: "nan",104: "nan",105: "nan",106: "nan",107: "nan",108: "nan",109: "nan",110: "nan",111: "nan",112: "nan",113: "nan",114: "nan",115: "nan",116: "nan",117: "nan"},'Electronegativity': {0: 2.2,1: "nan",2: 0.98,3: 1.57,4: 2.04,5: 2.55,6: 3.04,7: 3.44,8: 3.98,9: "nan",10: 0.93,11: 1.31,12: 1.61,13: 1.9,14: 2.19,15: 2.58,16: 3.16,17: "nan",18: 0.82,19: 1.0,20: 1.36,21: 1.54,22: 1.63,23: 1.66,24: 1.55,25: 1.83,26: 1.88,27: 1.91,28: 1.9,29: 1.65,30: 1.81,31: 2.01,32: 2.18,33: 2.55,34: 2.96,35: "nan",36: 0.82,37: 0.95,38: 1.22,39: 1.33,40: 1.6,41: 2.16,42: 1.9,43: 2.2,44: 2.28,45: 2.2,46: 1.93,47: 1.69,48: 1.78,49: 1.96,50: 2.05,51: 2.1,52: 2.66,53: "nan",54: 0.79,55: 0.89,56: 1.1,57: 1.12,58: 1.13,59: 1.14,60: 1.13,61: 1.17,62: 1.2,63: 1.2,64: 1.2,65: 1.22,66: 1.23,67: 1.24,68: 1.25,69: 1.1,70: 1.27,71: 1.3,72: 1.5,73: 2.36,74: 1.9,75: 2.2,76: 2.2,77: 2.28,78: 2.54,79: 2.0,80: 2.04,81: 2.33,82: 2.02,83: 2.0,84: 2.2,85: "nan",86: 0.7,87: 0.9,88: 1.1,89: 1.3,90: 1.5,91: 1.38,92: 1.36,93: 1.28,94: 1.3,95: 1.3,96: 1.3,97: 1.3,98: 1.3,99: 1.3,100: 1.3,101: 1.3,102: "nan",103: "nan",104: "nan",105: "nan",106: "nan",107: "nan",108: "nan",109: "nan",110: "nan",111: "nan",112: "nan",113: "nan",114: "nan",115: "nan",116: "nan",117: "nan"},'FirstIonization': {0: 13.5984,1: 24.5874,2: 5.3917,3: 9.3227,4: 8.298,5: 11.2603,6: 14.5341,7: 13.6181,8: 17.4228,9: 21.5645,10: 5.1391,11: 7.6462,12: 5.9858,13: 8.1517,14: 10.4867,15: 10.36,16: 12.9676,17: 15.7596,18: 4.3407,19: 6.1132,20: 6.5615,21: 6.8281,22: 6.7462,23: 6.7665,24: 7.434,25: 7.9024,26: 7.881,27: 7.6398,28: 7.7264,29: 9.3942,30: 5.9993,31: 7.8994,32: 9.7886,33: 9.7524,34: 11.8138,35: 13.9996,36: 4.1771,37: 5.6949,38: 6.2173,39: 6.6339,40: 6.7589,41: 7.0924,42: 7.28,43: 7.3605,44: 7.4589,45: 8.3369,46: 7.5762,47: 8.9938,48: 5.7864,49: 7.3439,50: 8.6084,51: 9.0096,52: 10.4513,53: 12.1298,54: 3.8939,55: 5.2117,56: 5.5769,57: 5.5387,58: 5.473,59: 5.525,60: 5.582,61: 5.6437,62: 5.6704,63: 6.1501,64: 5.8638,65: 5.9389,66: 6.0215,67: 6.1077,68: 6.1843,69: 6.2542,70: 5.4259,71: 6.8251,72: 7.5496,73: 7.864,74: 7.8335,75: 8.4382,76: 8.967,77: 8.9587,78: 9.2255,79: 10.4375,80: 6.1082,81: 7.4167,82: 7.2856,83: 8.417,84: 9.3,85: 10.7485,86: 4.0727,87: 5.2784,88: 5.17,89: 6.3067,90: 5.89,91: 6.1941,92: 6.2657,93: 6.0262,94: 5.9738,95: 5.9915,96: 6.1979,97: 6.2817,98: 6.42,99: 6.5,100: 6.58,101: 6.65,102: "nan",103: "nan",104: "nan",105: "nan",106: "nan",107: "nan",108: "nan",109: "nan",110: "nan",111: "nan",112: "nan",113: "nan",114: "nan",115: "nan",116: "nan",117: "nan"},'Density': {0: 8.99e-05,1: 0.000179,2: 0.534,3: 1.85,4: 2.34,5: 2.27,6: 0.00125,7: 0.00143,8: 0.0017,9: 0.0009,10: 0.971,11: 1.74,12: 2.7,13: 2.33,14: 1.82,15: 2.07,16: 0.00321,17: 0.00178,18: 0.862,19: 1.54,20: 2.99,21: 4.54,22: 6.11,23: 7.15,24: 7.44,25: 7.87,26: 8.86,27: 8.91,28: 8.96,29: 7.13,30: 5.91,31: 5.32,32: 5.78,33: 4.81,34: 3.12,35: 0.00373,36: 1.53,37: 2.64,38: 4.47,39: 6.51,40: 8.57,41: 10.2,42: 11.5,43: 12.4,44: 12.4,45: 12.0,46: 10.5,47: 8.69,48: 7.31,49: 7.29,50: 6.69,51: 6.23,52: 4.93,53: 0.00589,54: 1.87,55: 3.59,56: 6.15,57: 6.77,58: 6.77,59: 7.01,60: 7.26,61: 7.52,62: 5.24,63: 7.9,64: 8.23,65: 8.55,66: 8.8,67: 9.07,68: 9.32,69: 6.97,70: 9.84,71: 13.3,72: 16.7,73: 19.3,74: 21.0,75: 22.6,76: 22.6,77: 21.5,78: 19.3,79: 13.5,80: 11.9,81: 11.3,82: 9.81,83: 9.32,84: 7.0,85: 0.00973,86: 1.87,87: 5.5,88: 10.1,89: 11.7,90: 15.4,91: 19.0,92: 20.5,93: 19.8,94: 13.7,95: 13.5,96: 14.8,97: 15.1,98: 13.5,99: "nan",100: "nan",101: "nan",102: "nan",103: 18.1,104: 39.0,105: 35.0,106: 37.0,107: 41.0,108: 35.0,109: "nan",110: "nan",111: "nan",112: "nan",113: "nan",114: "nan",115: "nan",116: "nan",117: "nan"},'MeltingPoint': {0: 14.175,1: "nan",2: 453.85,3: 1560.15,4: 2573.15,5: 3948.15,6: 63.29,7: 50.5,8: 53.63,9: 24.703,10: 371.15,11: 923.15,12: 933.4,13: 1683.15,14: 317.25,15: 388.51,16: 172.31,17: 83.96,18: 336.5,19: 1112.15,20: 1812.15,21: 1933.15,22: 2175.15,23: 2130.15,24: 1519.15,25: 1808.15,26: 1768.15,27: 1726.15,28: 1357.75,29: 692.88,30: 302.91,31: 1211.45,32: 1090.15,33: 494.15,34: 266.05,35: 115.93,36: 312.79,37: 1042.15,38: 1799.15,39: 2125.15,40: 2741.15,41: 2890.15,42: 2473.15,43: 2523.15,44: 2239.15,45: 1825.15,46: 1234.15,47: 594.33,48: 429.91,49: 505.21,50: 904.05,51: 722.8,52: 386.65,53: 161.45,54: 301.7,55: 1002.15,56: 1193.15,57: 1071.15,58: 1204.15,59: 1289.15,60: 1204.15,61: 1345.15,62: 1095.15,63: 1585.15,64: 1630.15,65: 1680.15,66: 1743.15,67: 1795.15,68: 1818.15,69: 1097.15,70: 1936.15,71: 2500.15,72: 3269.15,73: 3680.15,74: 3453.15,75: 3300.15,76: 2716.15,77: 2045.15,78: 1337.73,79: 234.43,80: 577.15,81: 600.75,82: 544.67,83: 527.15,84: 575.15,85: 202.15,86: 300.15,87: 973.15,88: 1323.15,89: 2028.15,90: 1873.15,91: 1405.15,92: 913.15,93: 913.15,94: 1267.15,95: 1340.15,96: 1259.15,97: 1925.15,98: 1133.15,99: "nan",100: "nan",101: "nan",102: "nan",103: "nan",104: "nan",105: "nan",106: "nan",107: "nan",108: "nan",109: "nan",110: "nan",111: "nan",112: "nan",113: "nan",114: "nan",115: "nan",116: "nan",117: "nan"},'BoilingPoint': {0: 20.28,1: 4.22,2: 1615.0,3: 2742.0,4: 4200.0,5: 4300.0,6: 77.36,7: 90.2,8: 85.03,9: 27.07,10: 1156.0,11: 1363.0,12: 2792.0,13: 3538.0,14: 553.0,15: 717.8,16: 239.11,17: 87.3,18: 1032.0,19: 1757.0,20: 3109.0,21: 3560.0,22: 3680.0,23: 2944.0,24: 2334.0,25: 3134.0,26: 3200.0,27: 3186.0,28: 2835.0,29: 1180.0,30: 2477.0,31: 3106.0,32: 887.0,33: 958.0,34: 332.0,35: 119.93,36: 961.0,37: 1655.0,38: 3609.0,39: 4682.0,40: 5017.0,41: 4912.0,42: 5150.0,43: 4423.0,44: 3968.0,45: 3236.0,46: 2435.0,47: 1040.0,48: 2345.0,49: 2875.0,50: 1860.0,51: 1261.0,52: 457.4,53: 165.03,54: 944.0,55: 2170.0,56: 3737.0,57: 3716.0,58: 3793.0,59: 3347.0,60: 3273.0,61: 2067.0,62: 1802.0,63: 3546.0,64: 3503.0,65: 2840.0,66: 2993.0,67: 3503.0,68: 2223.0,69: 1469.0,70: 3675.0,71: 4876.0,72: 5731.0,73: 5828.0,74: 5869.0,75: 5285.0,76: 4701.0,77: 4098.0,78: 3129.0,79: 630.0,80: 1746.0,81: 2022.0,82: 1837.0,83: 1235.0,84: 610.0,85: 211.3,86: 950.0,87: 2010.0,88: 3471.0,89: 5061.0,90: 4300.0,91: 4404.0,92: 4273.0,93: 3501.0,94: 2880.0,95: 3383.0,96: 983.0,97: 1173.0,98: "nan",99: "nan",100: "nan",101: "nan",102: "nan",103: "nan",104: "nan",105: "nan",106: "nan",107: "nan",108: "nan",109: "nan",110: "nan",111: "nan",112: "nan",113: "nan",114: "nan",115: "nan",116: "nan",117: "nan"},'NumberOfIsotopes': {0: 3.0,1: 5.0,2: 5.0,3: 6.0,4: 6.0,5: 7.0,6: 8.0,7: 8.0,8: 6.0,9: 8.0,10: 7.0,11: 8.0,12: 8.0,13: 8.0,14: 7.0,15: 10.0,16: 11.0,17: 8.0,18: 10.0,19: 14.0,20: 15.0,21: 9.0,22: 9.0,23: 9.0,24: 11.0,25: 10.0,26: 14.0,27: 11.0,28: 11.0,29: 15.0,30: 14.0,31: 17.0,32: 14.0,33: 20.0,34: 19.0,35: 23.0,36: 20.0,37: 18.0,38: 21.0,39: 20.0,40: 24.0,41: 20.0,42: 23.0,43: 16.0,44: 20.0,45: 21.0,46: 27.0,47: 22.0,48: 34.0,49: 28.0,50: 29.0,51: 29.0,52: 24.0,53: 31.0,54: 22.0,55: 25.0,56: 19.0,57: 19.0,58: 15.0,59: 16.0,60: 14.0,61: 17.0,62: 21.0,63: 17.0,64: 24.0,65: 21.0,66: 29.0,67: 16.0,68: 18.0,69: 16.0,70: 22.0,71: 17.0,72: 19.0,73: 22.0,74: 21.0,75: 19.0,76: 25.0,77: 32.0,78: 21.0,79: 26.0,80: 28.0,81: 29.0,82: 19.0,83: 34.0,84: 21.0,85: 20.0,86: 21.0,87: 15.0,88: 11.0,89: 12.0,90: 14.0,91: 15.0,92: 153.0,93: 163.0,94: 133.0,95: 133.0,96: 83.0,97: 123.0,98: 123.0,99: 103.0,100: 33.0,101: 73.0,102: 203.0,103: "nan",104: "nan",105: "nan",106: "nan",107: "nan",108: "nan",109: "nan",110: "nan",111: "nan",112: "nan",113: "nan",114: "nan",115: "nan",116: "nan",117: "nan"},'Discoverer': {0: 'Cavendish',1: 'Janssen',2: 'Arfvedson',3: 'Vaulquelin',4: 'Gay-Lussac',5: 'Prehistoric',6: 'Rutherford',7: 'Priestley/Scheele',8: 'Moissan',9: 'Ramsay and Travers',10: 'Davy',11: 'Black',12: 'Wshler',13: 'Berzelius',14: 'BranBrand',15: 'Prehistoric',16: 'Scheele',17: 'Rayleigh and Ramsay',18: 'Davy',19: 'Davy',20: 'Nilson',21: 'Gregor',22: '   del Rio',23: 'Vauquelin',24: 'Gahn, Scheele',25: 'Prehistoric',26: 'Brandt',27: 'Cronstedt',28: 'Prehistoric',29: 'Prehistoric',30: 'de Boisbaudran',31: 'Winkler',32: 'Albertus Magnus',33: 'Berzelius',34: 'Balard',35: 'Ramsay and Travers',36: 'Bunsen and Kirchoff',37: 'Davy',38: 'Gadolin',39: 'Klaproth',40: 'Hatchett',41: 'Scheele',42: 'Perrier and Segr�',43: 'Klaus',44: 'Wollaston',45: 'Wollaston',46: 'Prehistoric',47: 'Stromeyer',48: 'Reich and Richter',49: 'Prehistoric',50: 'Early historic times',51: 'von Reichenstein',52: 'Courtois',53: 'Ramsay and Travers',54: 'Bunsen and Kirchoff',55: 'Davy',56: 'Mosander',57: 'Berzelius',58: 'von Welsbach',59: 'von Welsbach',60: 'Marinsky et al.',61: 'Boisbaudran',62: 'Demarcay',63: 'de Marignac',64: 'Mosander',65: 'de Boisbaudran',66: 'Delafontaine and Soret',67: 'Mosander',68: 'Cleve',69: 'Marignac',70: 'Urbain/ von Welsbach',71: 'Coster and von Hevesy',72: 'Ekeberg',73: "J. and F. d'Elhuyar",74: 'Noddack, Berg, and Tacke',75: 'Ten"nan"t',76: 'Ten"nan"t',77: 'Ulloa/Wood',78: 'Prehistoric',79: 'Prehistoric',80: 'Crookes',81: 'Prehistoric',82: 'Geoffroy the Younger',83: 'Curie',84: 'Corson et al.',85: 'Dorn',86: 'Perey',87: 'Pierre and Marie Curie',88: 'Debierne/Giesel',89: 'Berzelius',90: 'Hahn and Meitner',91: 'Peligot',92: 'McMillan and Abelson',93: 'Seaborg et al.',94: 'Seaborg et al.',95: 'Seaborg et al.',96: 'Seaborg et al.',97: 'Seaborg et al.',98: 'Ghiorso et al.',99: 'Ghiorso et al.',100: 'Ghiorso et al.',101: 'Ghiorso et al.',102: 'Ghiorso et al.',103: 'Ghiorso et al.',104: 'Ghiorso et al.',105: 'Ghiorso et al.',106: 'Armbruster and M�nzenberg',107: 'Armbruster and M�nzenberg',108: 'GSI, Darmstadt, West Germany',109: "nan",110: "nan",111: "nan",112: "nan",113: "nan",114: "nan",115: "nan",116: "nan",117: "nan"},'Year': {0: 1766.0,1: 1868.0,2: 1817.0,3: 1798.0,4: 1808.0,5: "nan",6: 1772.0,7: 1774.0,8: 1886.0,9: 1898.0,10: 1807.0,11: 1755.0,12: 1827.0,13: 1824.0,14: 1669.0,15: "nan",16: 1774.0,17: 1894.0,18: 1807.0,19: 1808.0,20: 1878.0,21: 1791.0,22: 1801.0,23: 1797.0,24: 1774.0,25: "nan",26: 1735.0,27: 1751.0,28: "nan",29: "nan",30: 1875.0,31: 1886.0,32: 1250.0,33: 1817.0,34: 1826.0,35: 1898.0,36: 1861.0,37: 1808.0,38: 1794.0,39: 1789.0,40: 1801.0,41: 1778.0,42: 1937.0,43: 1844.0,44: 1803.0,45: 1803.0,46: "nan",47: 1817.0,48: 1863.0,49: "nan",50: "nan",51: 1782.0,52: 1811.0,53: 1898.0,54: 1860.0,55: 1808.0,56: 1839.0,57: 1803.0,58: 1885.0,59: 1885.0,60: 1945.0,61: 1879.0,62: 1901.0,63: 1880.0,64: 1843.0,65: 1886.0,66: 1878.0,67: 1843.0,68: 1879.0,69: 1878.0,70: 1907.0,71: 1923.0,72: 1801.0,73: 1783.0,74: 1925.0,75: 1803.0,76: 1804.0,77: 1735.0,78: "nan",79: "nan",80: 1861.0,81: "nan",82: 1753.0,83: 1898.0,84: 1940.0,85: 1900.0,86: 1939.0,87: 1898.0,88: 1899.0,89: 1828.0,90: 1917.0,91: 1841.0,92: 1940.0,93: 1940.0,94: 1944.0,95: 1944.0,96: 1949.0,97: 1950.0,98: 1952.0,99: 1953.0,100: 1955.0,101: 1958.0,102: 1961.0,103: 1969.0,104: 1970.0,105: 1974.0,106: 1981.0,107: 1983.0,108: 1982.0,109: 1994.0,110: 1994.0,111: 1996.0,112: 2004.0,113: 1999.0,114: 2010.0,115: 2000.0,116: 2010.0,117: 2006.0},'SpecificHeat': {0: 14.304,1: 5.193,2: 3.582,3: 1.825,4: 1.026,5: 0.709,6: 1.04,7: 0.918,8: 0.824,9: 1.03,10: 1.228,11: 1.023,12: 0.897,13: 0.705,14: 0.769,15: 0.71,16: 0.479,17: 0.52,18: 0.757,19: 0.647,20: 0.568,21: 0.523,22: 0.489,23: 0.449,24: 0.479,25: 0.449,26: 0.421,27: 0.444,28: 0.385,29: 0.388,30: 0.371,31: 0.32,32: 0.329,33: 0.321,34: 0.474,35: 0.248,36: 0.363,37: 0.301,38: 0.298,39: 0.278,40: 0.265,41: 0.251,42: "nan",43: 0.238,44: 0.243,45: 0.244,46: 0.235,47: 0.232,48: 0.233,49: 0.228,50: 0.207,51: 0.202,52: 0.214,53: 0.158,54: 0.242,55: 0.204,56: 0.195,57: 0.192,58: 0.193,59: 0.19,60: "nan",61: 0.197,62: 0.182,63: 0.236,64: 0.182,65: 0.17,66: 0.165,67: 0.168,68: 0.16,69: 0.155,70: 0.154,71: 0.144,72: 0.14,73: 0.132,74: 0.137,75: 0.13,76: 0.131,77: 0.133,78: 0.129,79: 0.14,80: 0.129,81: 0.129,82: 0.122,83: "nan",84: "nan",85: 0.094,86: "nan",87: "nan",88: 0.12,89: 0.113,90: "nan",91: 0.116,92: "nan",93: "nan",94: "nan",95: "nan",96: "nan",97: "nan",98: "nan",99: "nan",100: "nan",101: "nan",102: "nan",103: "nan",104: "nan",105: "nan",106: "nan",107: "nan",108: "nan",109: "nan",110: "nan",111: "nan",112: "nan",113: "nan",114: "nan",115: "nan",116: "nan",117: "nan"},'NumberofShells': {0: 1,1: 1,2: 2,3: 2,4: 2,5: 2,6: 2,7: 2,8: 2,9: 2,10: 3,11: 3,12: 3,13: 3,14: 3,15: 3,16: 3,17: 3,18: 4,19: 4,20: 4,21: 4,22: 4,23: 4,24: 4,25: 4,26: 4,27: 4,28: 4,29: 4,30: 4,31: 4,32: 4,33: 4,34: 4,35: 4,36: 5,37: 5,38: 5,39: 5,40: 5,41: 5,42: 5,43: 5,44: 5,45: 5,46: 5,47: 5,48: 5,49: 5,50: 5,51: 5,52: 5,53: 5,54: 6,55: 6,56: 6,57: 6,58: 6,59: 6,60: 6,61: 6,62: 6,63: 6,64: 6,65: 6,66: 6,67: 6,68: 6,69: 6,70: 6,71: 6,72: 6,73: 6,74: 6,75: 6,76: 6,77: 6,78: 6,79: 6,80: 6,81: 6,82: 6,83: 6,84: 6,85: 6,86: 7,87: 7,88: 7,89: 7,90: 7,91: 7,92: 7,93: 7,94: 7,95: 7,96: 7,97: 7,98: 7,99: 7,100: 7,101: 7,102: 7,103: 7,104: 7,105: 7,106: 7,107: 7,108: 7,109: 7,110: 7,111: 7,112: 7,113: 7,114: 7,115: 7,116: 7,117: 7},'NumberofValence': {0: 1.0,1: "nan",2: 1.0,3: 2.0,4: 3.0,5: 4.0,6: 5.0,7: 6.0,8: 7.0,9: 8.0,10: 1.0,11: 2.0,12: 3.0,13: 4.0,14: 5.0,15: 6.0,16: 7.0,17: 8.0,18: 1.0,19: 2.0,20: "nan",21: "nan",22: "nan",23: "nan",24: "nan",25: "nan",26: "nan",27: "nan",28: "nan",29: "nan",30: 3.0,31: 4.0,32: 5.0,33: 6.0,34: 7.0,35: 8.0,36: 1.0,37: 2.0,38: "nan",39: "nan",40: "nan",41: "nan",42: "nan",43: "nan",44: "nan",45: "nan",46: "nan",47: "nan",48: 3.0,49: 4.0,50: 5.0,51: 6.0,52: 7.0,53: 8.0,54: 1.0,55: 2.0,56: "nan",57: "nan",58: "nan",59: "nan",60: "nan",61: "nan",62: "nan",63: "nan",64: "nan",65: "nan",66: "nan",67: "nan",68: "nan",69: "nan",70: "nan",71: "nan",72: "nan",73: "nan",74: "nan",75: "nan",76: "nan",77: "nan",78: "nan",79: "nan",80: 3.0,81: 4.0,82: 5.0,83: 6.0,84: 7.0,85: 8.0,86: 1.0,87: 2.0,88: "nan",89: "nan",90: "nan",91: "nan",92: "nan",93: "nan",94: "nan",95: "nan",96: "nan",97: "nan",98: "nan",99: "nan",100: "nan",101: "nan",102: "nan",103: "nan",104: "nan",105: "nan",106: "nan",107: "nan",108: "nan",109: "nan",110: "nan",111: "nan",112: 3.0,113: 4.0,114: 5.0,115: 6.0,116: 7.0,117: 8.0}}
        #}}}        
    # get_formula_weights: {{{
    def get_formula_weights(self):
        '''
        This function will take the formulas provided at initialization
        and decompose them to give you the mass of the substance
        '''
        fws = {}
        # Get Formula Weights: {{{
        for formula in self._formulas: 
            masses = []
            components = re.findall(r'[A-Z]{1}[a-z]?\d+|[A-Z][a-z]?',formula)
            for element in components:
                # find the coefficient: {{{
                try:
                    multiplier = int(re.findall(r'\d+',element)[0])
                    element = re.findall(r'[A-Z]{1}[a-z]?',element)[0]
                except:
                    multiplier = 1
                #}}}
                # Get the mass of the element: {{{
                all_elements = list(self._ptable['Symbol'].values())
                try:
                    el_num = all_elements.index(element)
                    fw = self._ptable['AtomicMass'][el_num]
                    mass = fw * multiplier
                    masses.append(mass)
                except:
                    raise ValueError(f'Element: {element} Not Found!')
                #}}}
            fw = sum(masses)
            fws[formula] = fw

        #}}}
        return fws
    #}}}
#}}}
# TOPAS_Refinements: {{{
class TOPAS_Refinements(Utils, UsefulUnicode,OUT_Parser,GenericPlotter):
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
        OUT_Parser.__init__(self)
        GenericPlotter.__init__(self)
        self._data_collected = False # This tracks if the "get_data" function was run
        self.color_index = 0
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
            get_individual_phases:bool = False,
            subtract_bkg:bool = True,
            phases_to_enable:list = None,
            phases_to_disable:list = None,
            threshold_for_on:float = 0.0195, # this was obtained by looking at an Rwp curve 
            threshold_for_off:float = 0.01, 
            off_sf_value:float = 1.0e-100,
            on_sf_value:float = 1.0e-5,
            debug:bool = False,  
        ):
        '''
        Code to run automated Rietveld Refinements based on Adam/Gerry's Code

        subtract_bkg: This will remove background terms from the individual phase contributions to ycalc

        phases_to_enable: This is a list of phases you would like to have added as the refinement progresses. 
        phases_to_disable: you can give either a list or a string of the phase scale factor to monitor.

        threshold_for_off: This is the value the normalize scale factor can be below which, the program will set the scale factor to 0.
        threshold_for_on: this is a percentage above your initial Rwp. When it passes this, the new phase turns on.

        polymorph_tags is a dictionary that allows us to specify a tag to accompany a formula name. 
            ex: 'Ta2O5' is the key and the value could be a list: ['HT', 'LT']
        
        NOTE: for each of the thresholds, you can also give a list of thresholds (indices must match those of the phases you give)
        
        '''
        # if you input a string for either "phases_to_disable" or "phases_to_enable": {{{
        if type(phases_to_disable) == list or phases_to_disable== None:
            pass
        else:
            phases_to_disable= [phases_to_disable]
        if type(phases_to_enable) == list or phases_to_enable== None:
            pass
        else:
            phases_to_enable= [phases_to_enable] # Make it match the type expected.
        self._out_file_monitor = {} # This is the monitoring dictionary.   
        #}}}

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
        txt_out_linenum = None
        my_csv_line = None
        pattern_linenum = None
        phase_hkli_out = []
        phase_hkli_line = []
        for i, line in enumerate(template):
            if 'Out_X_Yobs_Ycalc_Ydiff' in line:
                xy_out_linenum = i 
            if 'out_prm_vals_on_convergence' in line:
                txt_out_linenum = i
            if 'out' in line:
                # Don't need to look for anything but out by itself. 
                my_csv_line = i
            if 'xdd' in line:
                pattern_linenum = i
            if 'Create_hklm_d_Th2_Ip_file' in line:
                phase_hkli_out.append(i)
                phase_hkli_line.append(line) # We need to process this line to get the phase name 
        
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
        for index,number in enumerate(rng):
            pattern = f'{data_dir}\\{data.file_dict[data_dict_keys[number-1]]}' # Use the custom range we defined. Must subtract 1 to put it in accordance with the index. 
            output = f'result_{data_dict_keys[number-1]}_{str(number).zfill(6)}' # zfill makes sure that we have enough space to record all of the numbers of the index, also use "number" to keep the timestamp. 
            if pattern_linenum:
                template[pattern_linenum] = f'xdd "{pattern}"\n' # write the current pattern
            if xy_out_linenum:
                template[xy_out_linenum] = f'Out_X_Yobs_Ycalc_Ydiff("{output}.xy")\n'
            if txt_out_linenum:
                template[txt_out_linenum] = f'out_prm_vals_on_convergence "{output}.txt"\n' # I am making this a text file since I manually output csv files. This would overwrite those.
            if my_csv_line: 
                template[my_csv_line] = f'out "{output}.csv"\n'

            
            if phase_hkli_out:
                for phase_i, line_idx in enumerate(phase_hkli_out):
                    # We need to use Re to get the phase ID
                    lne = phase_hkli_line[phase_i]
                    fn_str = lne.split('(') [-1] # This takes whatever is written in the text field
                    found = re.findall(r'(\w+\d?)*',fn_str)[0] # This will give all of the text you put for the filename. 
                    split_hkli_fn = found.split('_')
                    formula = []
                    for word in split_hkli_fn:
                        if word != 'result':
                            formula.append(word)
                        else:
                            break
                    #formula = found.split('_')[0]
                    formula = '_'.join(formula) 
                    template[line_idx] = f'\tCreate_hklm_d_Th2_Ip_file({formula}_{output}.hkli)\n'

            # Use the Dummy.inp file: {{{
            with open('Dummy.inp','w') as dummy:
                for line in template:
                    dummy.write(line)
            self.refine_pattern('Dummy.inp') # Run the actual refinement
            # Monitor Refinement Parameters: {{{
            '''
            If you want to monitor scale factor values, it MUST
            happen before the Dummy file is copied to a new file. 

            Likewise, if you want a phase to be added...

            Both will be handled with the same function.
            '''
            out = 'Dummy.out' # This is the name of the file we are looking for.
            if phases_to_disable != None or phases_to_enable != None:  
                self._modify_out_for_monitoring(
                        out=out, 
                        on_phases=phases_to_enable,
                        off_phases=phases_to_disable,
                        threshold_for_on=threshold_for_on,
                        threshold_for_off=threshold_for_off,
                        current_idx=index,
                        off_sf_value=off_sf_value,
                        on_sf_value=on_sf_value,
                        debug=debug
                    )

                
            #}}}
            copyfile(out,f'{output}.out')
            template = [line for line in open(out)] # Make the new template the output of the last refinement. 
            #}}}
            # Get the single phase patterns: {{{ 
            if get_individual_phases:
                self._calculate_phase_from_out(out = f'{output}.out',subtract_bkg=subtract_bkg)
            #}}}
        #}}}
    #}}}
    # _parse_scale_factor_line: {{{
    def _parse_scale_factor_line(self,line:str = None, debug:bool = False):
        '''
        This function allows us to quickly parse the text in the scale factor keyword line. 
        It will find values in the form: 
        1.2233e-2
        or 
        1e-100
        '''
        number =re.findall(r'(\d+?\.\d+e?\-?\+?\d+)',line) # This will find any value that could possibly show up.
        if len(number) == 0:
            if debug:
                print(line)
            number = re.findall(r'\d?\.?\d+?',line)
        number = number[0]
        return float(number)

    #}}}
    # _get_relevant_lines_for_monitoring: {{{ 
    def _get_relevant_lines_for_monitoring(self,out:str = None,  off_phases:list = None, on_phases:list = None, threshold_for_off:float = None, threshold_for_on:float = None, debug:bool = False):
        '''
        Since we are adding more kinds of monitoring than simply scale factor to remove a phase, 
        it seems fitting that we should create some kind of framework to make the task of accomplishing this easier.

        turning off phases is accomplished by looking at the scale factors. 
        turning on phases is accomplished by looking at the Rwp as a guide then changing scale factor.
        '''
        relevant_lines = {}
        rwp = None # This will store the Rwp for those phases we want to turn on. 
        # Open the Output File: {{{
        with open(out,'r') as f:
            lines = f.readlines()
            # Go through each of the lines: {{{
            for i, line in enumerate(lines):
                scale_kwd = re.findall(r'^\s*scale',line) # Search the output for the line pertaining to scale factor
                rwp_kwd = re.findall('r_wp\s+\d+\.\d+',line) # Search the ouput for the line pertaining to the Rwp
                if rwp_kwd:
                    rwp = float(rwp_kwd[0].split(' ')[-1]) # This should give me the rwp value
                if scale_kwd:
                    line_prms = re.findall(r'\S+',line) # This will split the line into only words and values.
                    prm_name = line_prms[1] # The second word should always be a parameter name for the scale factor.
                    str_value = line_prms[2] # The third item is the value (may include an error oo.)
                    # Handle cases where you want to turn a phase off: {{{
                    for j, off in enumerate(off_phases):
                        # assign its threshold: {{{
                        try:
                            threshold = threshold_for_off[j] # If the user gave a list of thresholds for each phase...
                        except:
                            threshold = threshold_for_off
                        #}}}
                        #define the index for the dict: {{{ 
                        if j == 0 and len(relevant_lines) == 0:
                            # This is the first entry
                            k = j
                        else:
                            k = len(relevant_lines)
                        #}}}
                        if debug: 
                            print(off.lower()) 
                            print(prm_name.lower())
                        if  off.lower() in prm_name.lower():
                            if debug:
                                print('%s Inside'%off.lower()) 
                                print('%s Inside'%prm_name.lower())
                            value = self._parse_scale_factor_line(line,debug=debug)
                            relevant_lines[k] = {
                                    'linenumber': i,
                                    'line': line,
                                    'value': value, 
                                    'name': prm_name, 
                                    'string_number':str_value,
                                    'type': 'off',
                                    'threshold': threshold,
                            }# Record the line 
                            
                            if j == len(off_phases):
                                break # If you reach the end, no point in reading more lines.
                    #}}}
                    # Handle the cases where you want to turn on a phase: {{{
                    if on_phases != None:
                        for j, on in enumerate(on_phases):
                            # Assign its threshold: {{{
                            try:
                                threshold = threshold_for_on[j]  # IF the user gave a list of thresholds
                            except:
                                threshold = threshold_for_on
                            #}}}
                            if j == 0 and len(relevant_lines) == 0:
                                k = j
                            else:
                                k = len(relevant_lines)
                            if on.lower() in prm_name.lower():
                                value = self._parse_scale_factor_line(line,debug)
                                relevant_lines[k] = {
                                    'linenumber': i, 
                                    'line': line, 
                                    'value': value, 
                                    'name':prm_name, 
                                    'string_number': str_value,
                                    'type': 'on',
                                    'threshold':threshold,
                                    'rwp':rwp,
                                } # record the line 
                                if j == len(off_phases)-1:
                                    break # IF you reach the end, stop reading
    
                    #}}}
            #}}}
            f.close()
        #}}}
        return relevant_lines
    #}}} 
    # _modify_sf_line: {{{
    def _modify_sf_line(self, out:str = None, line_idx:int = None, str_num:str = None, replacement_value:float = None, debug:bool = False,):
        '''
        The purpose of this function is to make modifications to the scale factor line
        of an output file to either turn on or off a phase. 
        '''
        with open(out,'r') as f:
            lines = f.readlines() 
            f.close()
                        
        relevant_line = lines[line_idx] # Recall the line we stored 
                        
        relevant_line = relevant_line.replace(str_num, str(replacement_value)) # Replace the value with zero must be like this to not mess up other things.
        if 'min 0' not in relevant_line:
            relevant_line = f'{relevant_line} min 0' #this makes sure that the phase actually is disabled. 
        #relevant_line = relevant_line.replace(name, f'!{name}') # Replace the variable name with the variable name plus ! which will fix the value to zero 
        lines[line_idx] = relevant_line
        #line.replace(name,f'!{name}') # This locks the phase to 0
        if debug:
            print(f'relevant_line: {line_idx}, line to be written: {relevant_line}, TEST: {lines[line_idx]}')
        with open(out,'w') as f:
            f.writelines(lines) # Just rewrite the lines to the file 
            f.close()

    #}}}
    # _modify_out_for_monitoring: {{{
    def _modify_out_for_monitoring(self,
            out:str = None,
            on_phases:list = None, 
            off_phases:list = None, 
            threshold_for_on:float = None, 
            threshold_for_off:float = None, 
            current_idx:int = None,
            off_sf_value:float = 1.0e-100,
            on_sf_value:float = 1.0e-6,
            debug:bool = False
        ):
        '''
        This function handles the actual runtime modifications of output files 
        It uses thresholds provided by the user to determine when to add or remove phases (it does this by
        making scale factors either reasonable e.g. 1.5e-5 or extremely low e.g. 1e-100) to turn phases on or off.

        on_phases = list of phases you want to monitor the Rwp to turn on
        off_phases = list of phases you want to monitor the scale factor to turn off

        The threshold for on should be a percent deviation from the initial Rwp
        The threshold for off should be a percentage of the max value of a scale factor.
        
        current_idx: this is the current index of patterns you have refined.        

        out: this is the output file's filename.

        This needs to be able to also take into account, things written after the tag for the formula. e.g. Ta2O5_HT
        '''
        # get the relevant lines: {{{
        relevant_lines = self._get_relevant_lines_for_monitoring(out, off_phases,on_phases,threshold_for_off,threshold_for_on,debug)
        #}}} 
        # check to see if the index is zero or not: {{{
        if current_idx == 0:
            for i, key in enumerate(relevant_lines):
                entry = relevant_lines[key]
                value = entry['value']
                name = entry['name']
                entry_type = entry['type']
                if entry_type == 'on':
                    rwp = entry['rwp']
                else:
                    rwp = None
                self._out_file_monitor[i] = {
                        'values': [value],
                        'name':name,
                        'type': entry_type,
                        'rwps':[rwp],
                        'stopped':False,
                }
        #}}}
        # For all other indices: {{{
        else:
            # Loop through the out file monitor: {{{
            for i, key in enumerate(self._out_file_monitor):
                entry = self._out_file_monitor[key] # this is the current substance entry for the history
                current_entry = relevant_lines[key] # This is the current substance entry
                line_idx = current_entry['linenumber'] # This gives us the linenumber for the scale factor.
                str_num = current_entry['string_number'] # This is the current string for the scale factor.
                threshold = current_entry['threshold'] # This is the appropriate threshold for the given phase

                values = entry['values'] # List of the scale factors.
                name = entry['name'] # should contain the substance name with some other things like "sf_"
                entry_type = entry['type'] # Either 'off' or 'on'
                rwps = entry['rwps'] # Will be either a float for the Rwp or 'None'
                stopped = entry['stopped'] # Either True or False

                max_value = max(values) # This gets us the largest value present.
                current_value = current_entry['value'] # This gives the current value
                norm_val = current_value/max_value # This gives us the normalized value relative to the max.
                # Handle Phase ON Cases: {{{ 
                if entry_type == 'on':
                    try:
                        min_rwp = min(rwps) # This will give us the min Rwp value (remember that low Rwp is good, high Rwp is bad)
                        current_rwp = current_entry['rwp'] # This gives us the current Rwp
                        rwp_pct_diff = (current_rwp - min_rwp)/min_rwp # If this is positive, that could trigger the turning on of a phase. we are not dealing with a percentage 
                        if rwp_pct_diff >= threshold and not stopped:
                            entry['stopped'] = True # We are adding the phase so we can stop monitoring
                            # IF this is the case, we have yet to enable the phase. 
                            self._modify_sf_line(out=out,line_idx=line_idx,str_num=str_num,replacement_value=on_sf_value,debug=debug) 
                            print(f'ENABLED {name}')
                        elif rwp_pct_diff < threshold:
                            # No need to add the phase
                            self._out_file_monitor[key]['rwps'].append(current_rwp) # Add the newest Rwp
                    except:
                        # This case does not need to deal with Rwps. 
                        pass
                #}}}
                # Handle the Phase OFF Case: {{{
                elif entry_type == 'off':
                    if norm_val > threshold:
                        # This means we keep going. The scale factor hasnt fallen far enough
                        entry['values'].append(current_value)
                    elif norm_val <= threshold and not stopped:
                        entry['stopped'] = True # We are removing the phase, so stop monitoring it. 
                        # Now, DISABLE the phase: {{{
                        self._modify_sf_line(out=out,line_idx=line_idx,str_num=str_num,replacement_value=off_sf_value,debug=debug)
                        print(f'DISABLED {name}')
                        #}}} 

                #}}}

            #}}} 
        #}}} 
    #}}}
    # _monitor_scale_factor: {{{
    def _monitor_scale_factor(self,out:str = None, scale_factors:list = None, threshold:float = None, current_idx:int = None, debug:bool = False, sf_value:float = 1.0e-100):
        '''
        This function will monitor a scale factor or a series of scale factors
        to determine when they fall below a certain threshold. When they do, the program sets their scale factor to 0.0

        scale factors MUST be strings with the phase name you care about.

        eg: scale factor name in .inp: "Ta2O5_scale_factor"
        you would input: "Ta2O5"
        
        The function will parse the output file for the keyword "scale" and then find the word that you put in after scale. 
        '''
        
        relevant_lines = {}
        # Get the relevant lines: {{{
        with open(out,'r') as f:
            lines = f.readlines()
            for i,line in enumerate(lines):
                for j,sf in enumerate(scale_factors): 
                    scale_kwd = re.findall(r'^\s*scale',line) # This will have values ONLY IF the line starts with scale 
                    if scale_kwd:
                        line_prms = re.findall(r'\S+',line) # This will split the line into only words and values.
                        prm_name = line_prms[1] # The second word should always be a parameter name for the scale factor.
                        str_value = line_prms[2] # The third item is the value (may include an error too.) 
                        if  sf.lower() in prm_name.lower():
                            number =re.findall(r'(\d+?\.\d+e?\-?\+?\d+)',line) # This will find any value that could possibly show up.     
                            if len(number) == 0:
                                print(line)
                                number = re.findall(r'\d?\.?\d+?',line)
                            number = number[0]
                            value = float(number)
                            relevant_lines[j] = {'linenumber': i, 'line': line,'value': value, 'name': prm_name, 'string_number':str_value}# Record the line
                    if j == len(scale_factors)-1: 
                        break # If you reach the end, no point in reading more lines. 
            f.close() 
        #}}} 
        # Do the check: {{{
        if current_idx == 0: 
            for i,key in enumerate(relevant_lines):
                entry = relevant_lines[key]
                value = entry['value'] # This is the value of the scale factor
                name = entry['name'] # This is the prm name
                self._monitored_scale_factors[i] = {'values': [value], 'name': name, 'stopped':False} # Record the value and name
        #}}}
        else:
            # Check the current value against the max of the series to this point.
            for i, sf in enumerate(scale_factors):
                monitored_scale_factor = self._monitored_scale_factors[i]
                max_value = max(monitored_scale_factor['values'])
                current_value = relevant_lines[i]['value']
                norm_value =current_value/max_value
                if norm_value > threshold:
                    # No need to disable the phase
                    self._monitored_scale_factors[i]['values'].append(current_value)
                elif not self._monitored_scale_factors[i]['stopped'] and norm_value <= threshold:
                    # Need to tell the program to stop paying attention after this so that nothing gets messed up.
                    self._monitored_scale_factors[i].update({
                        'stopped': True,
                    })
                    # Need to disable the phase
                    with open(out,'r') as f:
                        lines = f.readlines() 
                        f.close()
                    line_idx = relevant_lines[i]['linenumber']
                    relevant_line = lines[line_idx] # Recall the line we stored
                    
                    name = relevant_lines[i]['name']
                    str_num = relevant_lines[i]['string_number'] #Need this to find the value we need to replace with zero 
                    relevant_line = relevant_line.replace(str_num, str(sf_value)) # Replace the value with zero must be like this to not mess up other things.
                    #relevant_line = relevant_line.replace(name, f'!{name}') # Replace the variable name with the variable name plus ! which will fix the value to zero 
                    lines[line_idx] = relevant_line
                    #line.replace(name,f'!{name}') # This locks the phase to 0
                    if debug:
                        print(f'relevant_line: {line_idx}, line to be written: {relevant_line}, TEST: {lines[line_idx]}')
                    with open(out,'w') as f:
                        f.writelines(lines) # Just rewrite the lines to the file 
                        f.close()
    #}}}
    # _monitor_rwp: {{{
    def _monitor_rwp(self,out:str = None, phases_to_add:list = None, threshold:float = None,current_idx:int = None ):
        '''
        The purpose of this function will be to monitor the Rwp values of a refinement 
        to determine when to turn on the phase(s) you have selected. 
        '''
        relevant_lines = {}
        # Get the relevant lines: {{{
        with open(out,'r') as f:
            lines = f.readlines()
            for i,line in enumerate(lines):
                for j,sf in enumerate(scale_factors): 
                    scale_kwd = re.findall(r'^\s*scale',line) # This will have values ONLY IF the line starts with scale 
                    if scale_kwd:
                        line_prms = re.findall(r'\S+',line) # This will split the line into only words and values.
                        prm_name = line_prms[1] # The second word should always be a parameter name for the scale factor.
                        str_value = line_prms[2] # The third item is the value (may include an error too.) 
                        if  sf.lower() in prm_name.lower():
                            number =re.findall(r'(\d+?\.\d+e?\-?\+?\d+)',line) # This will find any value that could possibly show up.     
                            if len(number) == 0:
                                print(line)
                                number = re.findall(r'\d?\.?\d+?',line)
                            number = number[0]
                            value = float(number)
                            relevant_lines[j] = {'linenumber': i, 'line': line,'value': value, 'name': prm_name, 'string_number':str_value}# Record the line
                    if j == len(scale_factors)-1: 
                        break # If you reach the end, no point in reading more lines. 
            f.close() 
        #}}} 
    
    #}}}
    # _calculate_phase_from_out: {{{
    def _calculate_phase_from_out(
            self,
            out:str = None,
            str_end:str = "Create_hklm_d_Th2_Ip_file",
            xy_out_prefix:str = 'result',
            iters:int = 0, 
            subtract_bkg:bool = True
        ):
        '''
        This function will take the .out file generated by TOPAS and 
        will parse through the file gathering: 
            1. the heading information (changing iterations to 1)
            2. the lines for each phase omitting the line: "Create_hklm_d_Th2_Ip_file" (change this if your strs end with something else.)
            3. the output lines (for the xy file)
        for the output file given as "out"

        This function also creates an input file with only background terms and instrumental profile stuff
        By default, the program removes all background terms from the phase outputs. 
        '''
        # Parse the OUT file: {{{
        with open(out) as f: 
            inp_dict = {'phases': {}} # This will hold all of the relevant information for the inp.
            phase_lines = [] # This will hold the lines needed to reconstruct the phase pattern
            header_lines = [] # This will hold the header lines.
            phase_num = 0 # This is the counter for the phases in you inp
            lines = f.readlines()
            keep_reading = False # This will inform the program that the first str has been reached
            header_done = False # This informs the program that the header has been completed. 
            for i, lne in enumerate(lines):
                line = copy.deepcopy(lne) # Need to preserve the original line
                # Handle header lines: {{{
                if not header_done and 'str' not in line and 'iters' not in line:
                    header_lines.append(line)
                if 'iters' in line:
                    line = f'iters {iters}\n' # Redefine the line to be one iteration
                    header_lines.append(line)
                #}}}
                # Statements to map phases: {{{
                if 'Create_hklm_d_Th2_Ip_file' in line:
                    inp_dict['phases'][phase_num].update({
                        'end':i-1, # This keeps the hkli file from being overwritten
                        'phase_lines':copy.deepcopy(phase_lines),
                    })
                    keep_reading=False
                    phase_lines.clear() # Reset the list
                    phase_num+=1 # Move to the next phase
                if 'str' in line:
                    if not keep_reading:
                        pass # We don't need to do anything. It is the first phase. 
                    inp_dict['phases'][phase_num] = {
                        'start': i, # This is the line the str starts on. 
                    }
                    keep_reading = True # Tells the program to keep reading lines.
                    header_done=True
                if keep_reading:
                    phase_lines.append(line) # This adds the line to the list which will be added to a dict. 
                if 'phase_name' in line: 
                    symbol = re.findall(r'(\w+\d?)+',line)[-1]
                    inp_dict['phases'][phase_num].update({
                        'symbol':symbol,
                    })
                #}}}
                # Handle Output: {{{
                if 'Out_X_Yobs_Ycalc_Ydiff' in line:
                    inp_dict['out'] = {'start':i,'line':line} # This tells the program which line the xy output is on.
                #}}}
            inp_dict['header'] = header_lines
        #}}}
        # Loop through the structures: {{{ 
        for phase in inp_dict['phases']: 
            inp_file = []
            entry = inp_dict['phases'][phase]
            substance = entry['symbol'] 
            phase_lines = entry['phase_lines']
            header = inp_dict['header']
            output = inp_dict['out']['line'].replace('result',substance)
            output_line = inp_dict['out']['start']
            for line in header:
                if subtract_bkg:
                    if 'bkg' not in line and 'One_on_X' not in line:
                        # Only add a line from the header if it is not a background term. 
                        inp_file.append(line)
                else:  
                    inp_file.append(line)
            for line in phase_lines:
                inp_file.append(line)
            inp_file.append(output)
            # Use the Dummy.inp file: {{{
            with open('Dummy_PS.inp','w') as dummy:
                for line in inp_file:
                    dummy.write(line)
                dummy.close()
            self.refine_pattern('Dummy_PS.inp') # Run the actual refinement
            #copyfile('Dummy.out',f'{output}.out')
            #template = [line for line in open('Dummy.out')] # Make the new template the output of the last refinement. 
        #}}}
        # Make a BKG xy file: {{{
        bkg_inp = []
        for line in header:
            bkg_inp.append(line) 
        output = inp_dict['out']['line'].replace('result','bkg')
        bkg_inp.append(output) # Make an output file with "bkg" as the xy name
        #print(output)
        #print(bkg_inp)
        # Use the dummy.inp; {{{
        with open('Dummy_PS.inp','w') as dummy:
            for line in bkg_inp:
                dummy.write(line)
            dummy.close()
            self.refine_pattern('Dummy_PS.inp') # Run the actual refinement.
        #}}}
        #}}}
        #}}}


    #}}}
    # get_data: {{{
    def get_data(self, 
            csv_labels:list = None, # This is a list of what each entry in the csvs is 
            csv_prefix:str = 'result', 
            xy_prefix:str = 'result',
            out_prefix:str = 'result',
            hkli_prefix:str = 'result',
            print_files:bool = False,
            get_orig_patt_and_meta:bool = True,
            #parse_c_matrices:bool = False, # This is inside of the out file. so i am getting rid of this. 
            parse_out_files:bool = True,
            parse_hkli:bool = False,
            sort_hkli:bool = False,
            correlation_threshold:int = 50,
            flag_search:str = 'CHECK',
            #polymorph_tags:dict = None, 
        ):
        '''
        This will gather and sort all of the output files from your refinements for you. 
        
        csv_labels: 
            This tells the program what each individual entry of the labels mean. 
        sort_hkli:
            This will sort each hkli file by tth but doing so results in a significantly slower processing time.
        polymorph_tags: 
            This could be a dictionary which contains the substance flag e.g. Ta2O5 and a list of specific versions to look for e.g. HT)
        ''' 
        self.rietveld_data = {}
        self.sorted_csvs = sorted(glob.glob(f'{csv_prefix}_*.csv')) #gathers csvs with the given prefix
        self.sorted_xy = sorted(glob.glob(f'{xy_prefix}_*.xy'))
        self.sorted_out = sorted(glob.glob(f'{out_prefix}_*.out')) 
        self.sorted_phase_xy = None # This will stay none unless you also parse hkli. 
        self.sorted_bkg_xy = sorted(glob.glob('bkg*.xy')) # These are the background curves if they are there.
        if parse_hkli:
            self.sorted_hkli = sorted(glob.glob(f'*_{hkli_prefix}_*.hkli')) # These files should be in the format: Substance_result_Info.hkli
        else:
            self.sorted_hkli = None
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
            # Create the necessary variables: {{{
            for substance in substances:
                relevant_files = sorted(glob.glob(f'{substance}_{hkli_prefix}_*.hkli')) # This gives only files pertaining to your substance. 
                self.sorted_phase_xy = sorted(glob.glob(f'{substance}_*.xy')) # This gives only the xy files pertaining to your substance.
                self._phase_xy[substances.index(substance)] = {'substance': substance, 'files': self.sorted_phase_xy}
                self._hkli[substances.index(substance)] = {'substance': substance,'files': relevant_files} 
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
            pass
        
        
        #}}}
        # Categorize the Refined Data: {{{ 
        csvs = tqdm(self.sorted_csvs)
        # import and process CSV, XY, OUT, HKLI:     
        for i, csv in enumerate(csvs):
            csvs.set_description_str(f'Reading {csv}: ')
            csv_contents = [float(line) for line in open(csv)] # This gives us the values in the csv. 
            # Handle the XY Data: {{{
            try:
                csvs.set_description_str(f'Reading {self.sorted_xy[i]}: ')
                ttheta, yobs,ycalc,ydiff = self._parse_xy(self.sorted_xy[i])
            except:
                ttheta, yobs,ycalc,ydiff = (0,0,0,0)
            #}}}
            # Handle the OUT files: {{{ 
            
            if parse_out_files: 
                try:
                    csvs.set_description_str(f'Reading {self.sorted_out[i]}: ')
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
                    csvs.set_description_str(f'Reading {hkli_file}: ')
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
                    csvs.set_description_str(f'Reading {self.sorted_bkg_xy[i]}: ') # The background should be only 1D with one bkg for each pattern.
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
                        csvs.set_description_str(f'Reading {phase_xy_file}: ')
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
    def _sort_csv_keys(self):
        '''
        This will sort the csvs to give you unique results grouped together 
        with only the key values you care about. 

        Example, if you want lattice parameters but scale factors also exist, this will 
        give you the lattice parameters for substance A and substance B separated  and ignore their scale factors
        '''
        self.csv_plot_data = {}
        # Get the unique substances: {{{
        self._create_string_from_csv_data(0)
        #}}}  
        # This code will produce a dictionary with data from the output file: {{{
        for i, entry in enumerate((self.rietveld_data)):
            csv = self.rietveld_data[entry]['csv'] # The keys here are integers. The names of the substances are one level deeper if there is a "phase_name" key in the entry. 
            # Parse the CSV Dictionary to get data for plotting: {{{
            for j, key in enumerate(csv):
                # Remember that the first "phase" recorded is "Rwp". Skip this one. 
                value = csv[key]
                if j == 0:
                    if 'rwp' not in self.csv_plot_data:
                        self.csv_plot_data['rwp'] = [value]
                    else:
                        self.csv_plot_data['rwp'].append(value)
                if j != 0:
                    splitkey = re.findall(r'(\w+\d*)+',key) # This should only return substances.
                    substance = splitkey[0] # This will be the substance name.
                    key = '_'.join(splitkey[1:]).lower() # This will make keys from the other words in your csv entry label separated by _ and in lowercase.
                    if substance in self._unique_substances:
                        # If this is true, we can grab information from the output. 
                        if substance not in self.csv_plot_data:
                            # This is the first entry.
                            self.csv_plot_data[substance] = {}
                        # Update the dict with float and int values: {{{
                        if type(value) == float or type(value) == int:
                            if key not in self.csv_plot_data[substance]:
                                self.csv_plot_data[substance][key] = [value]
                            else:
                                self.csv_plot_data[substance][key].append(value)
                        #}}}
                #}}}
        #}}} 
    #}}}
    # _sort_out_keys: {{{ 
    def _sort_out_keys(self,):
        '''
        This function will create a dictionary of all of the TOPAS prms from the output file. 
        The output dictionary being read was created in the output parser.  
        '''
        self.out_plot_dict = {}
        # This code will produce a dictionary with data from the output file: {{{
        for i, entry in enumerate((self.rietveld_data)):
            out =self.rietveld_data[entry]['out_dict'] # The keys here are integers. The names of the substances are one level deeper if there is a "phase_name" key in the entry. 
            for j, phase_num in enumerate(out):
                # Remember that the first "phase" recorded is "Rwp". Skip this one. 
                if j == 0:
                    if 'rwp' not in self.out_plot_dict:
                        self.out_plot_dict['rwp'] = [out[phase_num]] # In this case, phase_num is te key that gives Rwp
                    else:
                        self.out_plot_dict['rwp'].append(out[phase_num]) # Adds the rwp
                else:
                    phase = out[phase_num] # This is the phase entry. Could be hkl_Is, str, or xo_Is
                    keys = list(phase.keys()) # This will be the list of each of the keys.
                    if 'phase_name' in keys:
                        phase_name = phase['phase_name'] # This is the phase name given in the UT file. Search this for a match to self._unique_substances.
                        #phase_isolated = phase_name.split('_')[0] # This will only be the substance name
                        # We will not worry if the substance is in the CSV keys presented. 
                        #if phase_isolated:
                        # If this is true, we can grab information from the output. 
                        if phase_name not in self.out_plot_dict:
                            # This is the first entry.
                            self.out_plot_dict[phase_name] = {}
                        for key in keys:
                            value = phase[key] # This gives the entry
                            # Update the dict with float and int values: {{{
                            if type(value) == float or type(value) == int:
                                if key not in self.out_plot_dict[phase_name]:
                                    self.out_plot_dict[phase_name][key] = [value]
                                else:
                                    self.out_plot_dict[phase_name][key].append(value)
                            #}}}
                            # Update the dict with values from the sites dictionary: {{{
                            elif type(value) == dict:
                                sites = value
                                for label in sites:
                                    site = sites[label]
                                    try:
                                        bval_label = site['b_val_prm']  # This is the label the user gave the B-value parameter
                                        bval = site['bval'] # This is the refined parameter. 
                                    except:
                                        bval_label = f'{phase_name} None'
                                        bval = 0
 
                                    if bval_label not in self.out_plot_dict[phase_name]:
                                        self.out_plot_dict[phase_name][bval_label] = [bval]
                                    else:
                                        self.out_plot_dict[phase_name][bval_label].append(bval)      
                            #}}}
        #}}}
    #}}}
    # _get_time{{{
    def _get_time(self,index, time_units:str):
        '''
        This function will obtain for you, the time relative to the start of the run. 
        This uses the epoch time from metadata. SO MAKE SURE IT IS PRESENT. 
        Also, this uses the absolute beginning pattern's epoch time
        '''
        metadata_keys = list(self.metadata_data.keys()) #these are the "readable times" 0th index is the first pattern of the series. 
        t0 = self.metadata_data[metadata_keys[0]]['epoch_time'] # This gives us the epoch time for the first pattern. 
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
            yrange:list = None,
            template:str = None, 
            font_size:int = None,
            height =800,
            width =1000,
            show_legend:bool = True,
            legend_x:float = 0.99,
            legend_y:float = 0.99,
            legend_xanchor:str = 'right',
            legend_yanchor:str = 'top',
            showgrid:bool = False,
            dtick:float = 1,
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
                yanchor = legend_yanchor,
                y = legend_y,
                xanchor = legend_xanchor,
                x = legend_x,
            ),
            showlegend = show_legend,
            xaxis = dict(
                range = tth_range,
                showgrid = showgrid,
                dtick = dtick,
            ),
        )
        #}}}
        # If yrange: {{{
        if yrange:
            fig.update_layout(
                yaxis = dict(
                    range = yrange,
                ),
            )
        #}}}
    #}}}
    # plot_pattern: {{{
    def plot_pattern(self,
            index:int = 0, 
            template:str = 'simple_white',
            time_units:str = 'min', 
            tth_range:list = None,
            yrange:list = None,
            use_calc_temp:bool = True,
            height = 800,
            width = 1000,
            show_legend:bool = True,
            legend_x:float = 1.0,
            legend_y:float = 1.0,
            legend_xanchor:str = 'right',
            legend_yanchor:str = 'top',
            font_size:int = 20,
            rwp_decimals:int = 2,
            temp_decimals:int = 2,
            printouts:bool = True,
            run_in_loop:bool = False,
            specific_substance:str= None,
            plot_hkli:bool = True,
            single_pattern_offset:float = 0,
            hkli_offset:float = -60,
            button_xanchor = 'right',
            button_yanchor = 'top',
            button_x = 1.4,
            button_y = 1.,
            showgrid = False,
            dtick = 1,
        ):
        '''
        This will allow us to plot any of the loaded patterns 

        plot_hkli will allow hkl to be plotted for each phase IF the data are present
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
        # plot the hkli: {{{
        if plot_hkli and self.sorted_hkli:
            hkli = data['hkli'] # This is the hkli entry but its keys are indices of the substances. 
            for i in hkli:
                # Get Data for HKLI Plot: {{{
                substance = hkli[i]['substance']
                hkli_data = hkli[i]['hkli']
                hkl = hkli_data['hkl'] # 3-tuple of h,k,l
                hkl_tth = hkli_data['tth']
                ones = np.ones(len(hkl_tth)) 

                hkl_intensity = [hkli_offset*(i+1)]*ones # Make a list of intensities arbitrarily starting from 10.
                hkl_d = hkli_data['d']
                hkl_hovertemplate = []
                hkl_ht = '{}<br>hkl: {}<br>d-spacing: {} {}<br>' 
                for idx, mi in enumerate(hkl):
                    hkl_hovertemplate.append(hkl_ht.format(substance,mi,hkl_d[idx],self._angstrom)+f'2{self._theta}{self._degree}'+"%{x}")
                #}}}
                hkl_color = self._get_random_color()
                # Get Data for Phase Plots: {{{
                if self.sorted_phase_xy:
                    phase_data = data['phase_xy']
                    phase_substance = phase_data[i]['substance']
                    phase_tth= phase_data[i]['tth']
                    phase_ycalc= phase_data[i]['ycalc']
                    self.pattern_plot.add_scatter(
                            x = phase_tth,
                            y = np.array(phase_ycalc)+single_pattern_offset*(i+1), #If you give an offset, it will apply to each pattern and will offset based upon the index of the pattern
                            hovertemplate = hovertemplate,
                            marker = dict(
                                color = hkl_color,
                            ),
                            name = f'{phase_substance} phase',
                    )
                #}}}
                # Plot the Actual HKLs: {{{
                self.pattern_plot.add_scatter(
                    x = hkl_tth,
                    y = hkl_intensity,
                    hovertemplate = hkl_hovertemplate,
                    marker = dict( 
                        symbol = 'line-ns',
                        line = dict(
                            width = 2,
                            color = hkl_color,
                        ), 
                        size = 15,
                        color = hkl_color,
                    ),
                    mode = 'markers',
                    name = f'{substance} hkl',
                )

                #}}}

        #}}}
        # plot background: {{{
        if self.sorted_bkg_xy:
            bkg_data = data['bkg']
            bkg_tth = bkg_data['tth']
            bkg_ycalc = bkg_data['ycalc']
            self.pattern_plot.add_scatter(
                x = bkg_tth,
                y = bkg_ycalc,
                hovertemplate = hovertemplate,
                marker = dict(
                    color = 'black',
                ),
                name = 'Background',
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
            yrange = yrange,
            template=template,
            font_size=font_size,
            height=height,
            width = width,
            show_legend=show_legend,
            legend_x = legend_x,
            legend_y = legend_y,
            legend_xanchor = legend_xanchor,
            legend_yanchor= legend_yanchor,
            showgrid = showgrid,
            dtick = dtick,
        ) 
        #}}}
        # Update buttons: {{{
        self._add_buttons(self.pattern_plot,xanchor=button_xanchor,yanchor=button_yanchor,button_x=button_x,button_y=button_y,)
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
            if specific_substance == None:
                yobs = self.rietveld_data[index]['xy']['yobs']
                ycalc = self.rietveld_data[index]['xy']['ycalc']
                ydiff = self.rietveld_data[index]['xy']['ycalc']
                hovertemplate = f'{title_text}<br>Pattern Index: {index}<br>' + hovertemplate
                #title = f'Time: {np.around(self._current_time,2)} {time_units}, ({temp_label}: {np.around(temp,temp_decimals)}{self._deg_c}) Rwp: {np.around(self._rwp,rwp_decimals)}',  
            else:
                phases = self.rietveld_data[index]['phase_xy'] 
                for key in phases:
                    entry = phases[key]
                    substance = entry['substance']
                    if substance == specific_substance:
                        ycalc = entry['ycalc'] # This is the calculated y for the given substance.
                title_text = f'{title_text} {specific_substance} Series'
                yobs = None
                ydiff = None
                hovertemplate = f'{title_text}<br>Pattern Index: {index}<br>Substance: {specific_substance}<br>'+hovertemplate 
            return(tth,yobs, ycalc, ydiff, hovertemplate, title_text, xaxis_title, yaxis_title)
        #}}}
    #}}}
    # _add_buttons: {{{
    def _add_buttons(self,plot:go.Figure = None, xanchor = 'right',yanchor = 'top',button_x = 1.25, button_y = 1,):
        '''
        The purpose of this function is to add buttons to a plotly plot
        with relative ease. 

        It assumes that you are going to want to add buttons based on substance. 

        e.g. SiO2 (hkl) and (phase) 
        '''
        # Button Vars: {{{
        buttons = []
        data = plot.data
        all_on = [True]*len(data)
        phases_off  = copy.deepcopy(all_on) # Make a copy of all on to turn off all hkls
        hkls = [] # These are the indices for the "hkl" plots
        phases = []  # These are the indices for the "phase" plots
        bkgs = [] # This is a list of the background curves
        diff = [] # This is a list of the ydiff curves (should only be one)
        phase_names = [] # These will be the button names
        buttons.append(
            dict(
                label = 'Show All',
                method = 'update',
                args = [{'visible': all_on}]
            )
        )
        #}}}
        # Find the indices of HKLS, PHASES, and BKG for buttons: {{{
        for i, plt in enumerate(data):
            plot_name = plt['name']
            if 'hkl' in plot_name:
                # Now we know it is a substance.  
                phases_off[i] = False # Turn off the hkl 
                hkls.append(i)
            if 'phase' in plot_name.lower():
                phases_off[i] = False # Turn off the phase plot
                phases.append(i) 
                phase_names.append(plot_name)
            if plot_name.lower() == 'background':
                phases_off[i] = False # Turn off the background
                bkgs.append(i)
            if plot_name.lower() == 'ydiff':
                diff.append(i) 
        #}}}
        # Update Phase Buttons: {{{
        for i,hkl in enumerate(hkls):
            #print(f'HKL: {hkls}\nPhases: {phases}')
            current_phase= copy.deepcopy(phases_off)
            current_phase[hkl] = True # Sets the current hkl to visible
            current_phase[phases[i]] = True # This sets the current phase to visible
            current_phase[diff[0]] = False # This turns off the ydiff curve.
            buttons.append(
                dict(
                    label = f'Show {phase_names[i]}',
                    method = 'update',
                    args = [{
                        'visible':current_phase,
                    }]
                )
            )
        #}}}
        # Update the Background Button: {{{
        if bkgs:
            for bkg in bkgs:
                curr = copy.deepcopy(phases_off)
                curr[bkg] = True # Turns on the bkg
                buttons.append(
                    dict(
                        label = f'Show Background',
                        method = 'update',
                        args = [{
                            'visible': curr,
                        }]
                    )
                )
        #}}}
        # Update Buttons to show only the regular data: {{{
        buttons.append(
            dict(
                label = 'Only Refinement',
                method = 'update',
                args = [{
                    'visible':phases_off,
                }]
            )
        )
        #}}}
        # Update the layout: {{{
        # Update the layout with buttons
        plot.update_layout(
            updatemenus=[
                dict(
                    #type = "buttons",
                    direction = "down",
                    buttons= buttons,
                    #pad={"r": 10, "t": 10},
                    showactive=True,
                    x=button_x,
                    y = button_y,
                    xanchor=xanchor, 
                    yanchor = yanchor,
                ),
            ]
        )
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
        try:
            norm = [v/max(data) for v in data]
        except:
            norm = [v/(1e-100) for v in data]

        return norm
    #}}}
    # _get_random_color: {{{
    def _get_random_color(self,):
        contrasting_colors = [
                (240,163,255),
                (0,117,220),
                (153,63,0),
                (76,0,92),
                (25,25,25),
                (0,92,49),
                (43,206,72),
                (255,204,153),
                (128,128,128),
                (148,255,181),
                (143,124,0),
                (157,204,0),
                (194,0,136),
                (0,51,128),
                (255,164,5),
                (255,168,187),
                (66,102,0),
                (255,0,16),
                (94,241,242),
                (0,153,143),
                (224,255,102),
                (116,10,255),
                (153,0,0),
                (255,255,128),
                (255,255,0),
                (255,80,5),
        ]
        if self.color_index == len(contrasting_colors)-1:
            self.color_index = 0 #Reset the color index
        r,g,b = contrasting_colors[self.color_index]
        color = f'rgb({r},{g},{b})'
        self.color_index+=1 # This is advances through the contrasting colors
        return color
    #}}}
    # plot_csv_info: {{{
    def plot_csv_info(self, 
            plot_type:str = 'rwp',
            use_out_data:bool = False,
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
            legend_x:float = 0.99,
            legend_y:float = 1.2,
            legend_xanchor:str = 'right',
            legend_yanchor:str = 'top',
            debug:bool = False,
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
            8.) "Size L" or "csl" or "sizel"
            9.) "Size G" or "csg" or "sizeg"
            10.) "Strain L" or "strl" or 'strainl'
            11.) "Strain G" or "strg" or 'straing'
            12.) "eta"
            13.) "stephens"


        if you want to plot data from "out" files, set the "use_calc_temp" to True

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
        if specific_substance != None and type(specific_substance) == str:
            specific_substance = [specific_substance]
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
            keys = ['bvals', 'beq','bval', 'b value', 'b val', 'b values', 'b_value','b_val','b_values','B'] # tells the code what the likely keywords to look for are.
            yaxis_title = 'B-Values'
            title = 'B-Values'
        #}}}
        # Size L: {{{
        if plot_type == 'size l' or plot_type == 'csl' or plot_type == 'sizel':
            keys = ['size_l', 'csl','lorentzian_size','Size_L','cslv']
            yaxis_title = 'Lorentzian Size'
            title = 'Lorentzian Size'
        #}}}
        # Size G: {{{
        if plot_type == 'size g' or plot_type == 'csg' or plot_type == 'sizeg':
            keys = ['size_g', 'csg','gaussian_size','Size_G', 'csgv']
            yaxis_title = 'Gaussian Size'
            title = 'Gaussian Size' 
        #}}}
        # Strain L: {{{ 
        if plot_type == 'strain l' or plot_type == 'strl' or plot_type == 'strainl':
            keys = ['strain_l', 'strl','lorentzian_strain','Strain_L','slv']
            yaxis_title = 'Lorentzian Strain'
            title = 'Lorentzian Strain'
        #}}}
        # Strain G: {{{
        if plot_type == 'strain g' or plot_type == 'strg' or plot_type == 'straing':
            keys = ['strain_g', 'strg','gaussian_strain','Strain_G','sgv']
            yaxis_title = 'Gaussian Strain'
            title = 'Gaussian Strain' 
        #}}}
        # Lvol: {{{ 
        if plot_type.lower() == 'lvol':
            keys = ['lvol']
            yaxis_title = 'LVol'
            title = 'LVol'
        #}}}
        # Lvolf: {{{
        if plot_type.lower() == 'lvolf': 
            keys = ['lvolf']
            yaxis_title = 'Lvolf'
            title = 'LVolf'
        #}}}
        # e0: {{{ 
        if plot_type.lower() == 'e0':
            keys = ['e0']
            yaxis_title = f'e{self._subscript_zero}'
            title = f'e{self._subscript_zero}'
        #}}}
        # phase_MAC: {{{
        if plot_type.lower() == 'phase_mac':
            keys = ['phase_MAC']
            yaxis_title = 'Phase MAC'
            title = 'Phase MAC'
        #}}}
        # cell_mass: {{{
        if plot_type.lower() == 'cell_mass' or plot_type.lower() == 'cm' or plot_type.lower == 'mass':
            keys = ['cell_mass']
            yaxis_title = 'Cell Mass'
            title = 'Cell Mass'
        #}}}
        # eta: {{{
        if plot_type.lower() == 'eta':
            keys = ['eta']
            yaxis_title = 'Eta'
            title = 'Eta Values'
        #}}}
        # stephens: {{{
        if plot_type.lower() == 'stephens':
            keys = [
                's400',
                's040',
                's004',
                's220',
                's202',
                's022',
                's310',
                's103',
                's031',
                's130',
                's301',
                's013',
                's211',
                's121',
                's112',
            ]
            yaxis_title = 'Stephens Parameter'
            title = 'Stephens Parameters'
        #}}}
        #}}}
        # Update the title text: {{{
        if additional_title_text:
            title = f'{additional_title_text} {title}' # combines what the user wrote with the original title.
        #}}}
        # For the CSV Data, we need to find the data that we care about inside of self.csv_plot_data: {{{
        self._sort_csv_keys() # This gets self.csv_plot_data
        for entry in self.rietveld_data:
            if plot_temp:
                if 'temperature' not in self.csv_plot_data:
                    self.csv_plot_data['temperature'] = []
                if use_calc_temp:
                    t = self.rietveld_data[entry]['corrected_temperature']
                    temp_label = 'Corrected Temperature'
                else:
                    t = self.rietveld_data[entry]['temperature']
                    temp_label = 'Element Temperature'

                self.csv_plot_data['temperature'].append(t) # Record the temperature
            if 'time' not in self.csv_plot_data:
                self.csv_plot_data['time'] = []
            self._get_time(entry,time_units) # This gives us the time in the units we wanted (self._current_time)
            self.csv_plot_data['time'].append(self._current_time) # Add the time
        # IF YOU WANT TO USE THE OUTPUT, Also DEFINE plot_data : {{{
        if use_out_data:
            self._sort_out_keys() # This gets self.out_plot_dict
            self.out_plot_dict['temperature'] = self.csv_plot_data['temperature']
            self.out_plot_dict['time'] = self.csv_plot_data['time']
            plot_data = self.out_plot_dict # This local dictionary will be used to make the plot in this function. 
        else:
            plot_data = self.csv_plot_data # This is the local dictionary used to make the plot. 
        #}}}
        #}}}
        # plot the data: {{{
        fig = go.Figure()
        second_yaxis = False
        third_yaxis = False
        x = plot_data['time']
        base_ht = f'Time/{time_units}: '+'%{x}<br>' # This is the basis for all hovertemplates
        
        if keys == ['rwp']:
            hovertemplate = base_ht+'Rwp: %{y}'
            y = plot_data['rwp']
            fig.add_scatter(
                    x = x,
                    y = y,
                    hovertemplate = hovertemplate, 
                    yaxis = 'y1',
                    name = 'Rwp',
            )
            

        else:
            for substance in plot_data:
                color = self._get_random_color() # This gives us a color
                if not specific_substance:
                    usr_substance = substance.lower() # If a specific substance is not given, it is set as the current. 
                else:
                    for sub in specific_substance:
                        if sub.lower() == substance.lower():
                            usr_substance = sub.lower()
                            break
                        else:
                            usr_substance = None
                
                if substance != 'time' and substance != 'temperature' and substance != 'rwp' and substance.lower() == usr_substance:
                    entry = plot_data[substance] # This will be a dictionary entry with keys. 
                    entry_keys = list(entry.keys()) # These will be the keys for the entry. 
                    if debug:
                        print(f'ENTRY KEYS: {entry_keys}')
                    for plot_key in entry_keys:
                        try:
                            # This will be done to see if there are any matches to a value that may have a number.
                            
                            numerical_check = re.findall(r'(\w+\d*)*.',plot_key)[0] # This will match to anything that represents a formula.
                            numerical_check = numerical_check.strip(f'{substance}_')
                            if 'b_value' in numerical_check:
                                numerical_check = 'b_value'
                        except:
                            numerical_check = ''
                        if plot_key.lower() in keys or plot_key.strip(f'{substance}_') in keys or numerical_check in keys: # Need to check if the keys we are searching for are present.
                            if debug:
                                print(f'PASSED TEST: \n\tplot key: {plot_key}\n\tnumerical check: {numerical_check}\n')
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
                y = plot_data['temperature'],
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
            title_text = f'Plot of {title} vs. Time',
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
                yanchor = legend_yanchor,
                xanchor = legend_xanchor,
                y = legend_y,
                x = legend_x,
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
            waterfall:bool = False,
            fig_title:str = 'Multi Pattern Plot', 
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
            legend_x:float = 0.99,
            legend_y:float = 0.99,
            legend_xanchor:str = 'right',
            legend_yanchor:str = 'top',
            font_size:int = 20,
            rwp_decimals:int = 2,
            temp_decimals:int = 2, 
            standard_colors:bool = False,
            specific_substance:str= None,
            zmin_args:tuple = (-10, 5), # The first is the minimum intensity button, the second is the number of buttons
            zmax_args:tuple = (10, 5), # The first is the minimum I for the max buttons and the second is the number of buttons
            button_layer_1_height = 1.17,
            button_layer_2_height = 1.1,
            showgrid:bool = False,
            dtick:float = 1,
            plot_total_intensity_v_time = False,
            ):
        '''
        '
        This function will run a loop mode of "plot_pattern"
        This allows us to have multiple pattern fits overlaid on 
        one-another.

        Use the "offset" to change the spacing of the patterns.

        The "indices" can be either a list of specific files or a
        3-tuple that goes into np.linspace(low, high, number) 

        "standard_colors": If True, this will default to the standard color scheme

        using "specific_substance" you can plot the phase contribution of a single substance over time
        '''
        self._max_i = 0
        if type(indices) == tuple:
            lo,hi,num = indices
            indices= np.around(np.linspace(lo,hi,num),0) #Creates a range
        self.multi_pattern = go.Figure()
        if waterfall:
            # This necessitates a more complex list structure. 
            self.x = [] # This is going to be 2 theta range
            self.y = [] # This is the time axis
            self.z = [] # This will be a list of lists for intensity.
        if plot_total_intensity_v_time:
            self.x = [] # This will be the time range
            self.y = [] # This will be the observed intensity
            self.ycalc= [] # This will be the calculated intensity
            self.temp = [] # This holds the temp
             
        for index, i in enumerate(indices):
            # Get the data for current index: {{{ 
            tth, yobs, ycalc, ydiff, hovertemplate, title_text, xaxis_title, yaxis_title = self.plot_pattern(
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
                specific_substance = specific_substance,
            )
            if not specific_substance:
                if max(yobs) > self._max_i:
                    self._max_i = max(yobs)
            else:
                if max(ycalc) > self._max_i:
                    self._max_i = max(ycalc)
            #}}}
            # If You Want a Waterfall: {{{
            if waterfall:  
                time = np.around(self.rietveld_data[i]['corrected_time']/60,4) 
                self.x = tth # This only needs to be 1 series.
                self.y.append(time) # This puts it into minutes
                if not specific_substance:
                    self.z.append(yobs) # This adds the observed intensity.
                else:
                    self.z.append(ycalc) # Adds calculated intensity
                hovertemplate = f"2{self._theta}{self._degree}" + "%{x}<br>Intensity: %{z}<br>" + "Time: %{y}<br>"
            #}}}
            # Not a waterfall: {{{
            elif not waterfall and not plot_total_intensity_v_time: 
                color1 = self._get_random_color()
                color2 = self._get_random_color()
                color3 = self._get_random_color()
                if standard_colors:
                    colors = ['blue','red','grey']
                else:
                    colors = [color1, color2, color3]
                if not specific_substance:
                    ydict = {'yobs':yobs}
                else:
                    ydict = {'ycalc':ycalc}
                if show_ycalc:
                    ydict.update({'ycalc':ycalc})
                if show_ydiff:
                    ydict.update({'ydiff':ydiff}) 
                # Add the plots: {{{ 
                for j, key in enumerate(ydict):
                    if not specific_substance:
                        self.multi_pattern.add_scatter(
                            x = tth,
                            y = np.array(ydict[key])+(offset*index),
                            hovertemplate = hovertemplate,
                            marker = dict(
                                color = colors[j],
                            ),
                            name = f'Pattern # {i}: {key}',
                        )
                    else:
                        self.multi_pattern.add_scatter(
                            x = tth,
                            y = np.array(ydict['ycalc'])+(offset*index),
                            hovertemplate = hovertemplate,
                            marker = dict(
                                color = colors[0],
                            ),
                            name = f'Pattern #{i}: {specific_substance}'
                        )
                #}}}
 
            #}}}
            # Plot the total intensity vs. Time: {{{
            elif plot_total_intensity_v_time:  
                colors = ['blue','green']
                ydict = {'yobs':sum(np.array(yobs)),'ycalc':sum(np.array(ycalc))} # sum the total intensity
                time = np.around(self.rietveld_data[i]['corrected_time']/60,4)  # Get the time that the pattern was taken at.
                try:
                    temp = np.around(self.rietveld_data[i]['corrected_temperature'],2)  #  Get the corrected_temperature
                except:
                    temp = np.around(self.rietveld_data[i]['temperature']-273.15,2) # Get the noncorrected temp
                total_i_ht = "t = %{x} min<br>Total Intensity: %{y}"
                # Collect the data: {{{
                for j, key in enumerate(ydict):
                    self.x.append(time) 
                    self.y.append(ydict['yobs'])
                    self.ycalc.append(ydict['ycalc'])
                    self.temp.append(temp) 
                #}}}
            #}}}
        # Plot the total intensity if you selected it: {{{
        if plot_total_intensity_v_time:
            hovertemplate = "%{x} min<br>Total Intensity: %{y}<br>" 
            self.multi_pattern.add_scatter(
                x = self.x,
                y = self.y,
                hovertemplate = hovertemplate,
                marker = dict(
                    color = 'blue',
                    size = 5
                ),
                mode = 'lines+markers',
                name = 'Observed Total I',
                yaxis = 'y1'
            )
            if specific_substance:
                name = f'Calculated Total I ({specific_substance})'
            else:
                name = 'Calculated Total I'
            self.multi_pattern.add_scatter(
                x = self.x,
                y = self.ycalc,
                hovertemplate=hovertemplate,
                marker = dict(
                    color = 'green',
                ),
                name = name,
                mode = 'lines+markers',
                marker_size = 5,
                yaxis = 'y1'

            )
            self.multi_pattern.add_scatter(
                    x = self.x,
                    y = self.temp,
                    marker = dict(
                        color = 'red',
                    ),
                    name = 'Temperature',
                    yaxis = 'y2'
            )
        # Update Layout: {{{
        self.multi_pattern.update_layout( 
            yaxis2 = dict(
                title = f'Temperature/{self._deg_c}',
                
                overlaying = 'y',
                side = 'right', 
            ),
            font = dict(
                size = 20,
            ),
        )
        xaxis_title = 'Time / min'
        yaxis_title = 'Total Intensity'
        #}}}
        #}}}
        # Waterfall Plot Added: {{{ 
        if waterfall: 
            self.multi_pattern.add_heatmap(
                x = self.x,
                y = self.y,
                z = self.z, 
                hovertemplate = hovertemplate,
            )
            yaxis_title = 'Time / min'
            # Get Button Args: {{{ 
            min_on_zmin, num_min_buttons = zmin_args # unpack the tuple
            min_on_zmax, num_max_buttons = zmax_args # unpack the tuple
            min_steps = (0 -min_on_zmin)/(num_min_buttons -1)
            max_steps = (self._max_i -min_on_zmax)/ (num_max_buttons-1)
  
            zmin_arange = np.arange(min_on_zmin, 0+min_steps,min_steps)
            zmax_arange = np.arange(min_on_zmax, self._max_i+max_steps, max_steps)
            #}}}
            # Make buttons to change scaling: {{{
            zmin_buttons = [
                dict(
                    label = f'I_min: {np.around(v,2)}',
                    method = 'restyle',
                    args = [
                        {'zmin': v},
                    ]
                ) for v in zmin_arange
            ]
            zmax_buttons = [
                dict(
                    label = f'I_max: {np.around(v,2)}',
                    method = 'restyle',
                    args = [
                        {'zmax': v},
                    ]
                ) for v in zmax_arange
            ]
            #}}}
        #}}}
        # Update Layout: {{{
        
        self._update_pattern_layout(
                fig = self.multi_pattern,
                title_text=fig_title,
                xaxis_title=xaxis_title,
                yaxis_title=yaxis_title,
                tth_range=tth_range,
                template=template,
                font_size=font_size,
                height=height,
                width=width,
                show_legend=show_legend,
                legend_x = legend_x,
                legend_y=legend_y,
                legend_xanchor=legend_xanchor,
                legend_yanchor=legend_yanchor,
                showgrid = showgrid,
                dtick = dtick,
        )
        # Waterfall Update: {{{
        if waterfall:
            self.multi_pattern.update_layout( 
                    margin = dict(t=200,b=0,l=0,r=0),
                    autosize = False,
                    updatemenus = [
                    dict(
                        buttons = zmax_buttons,
                        yanchor = 'top',
                        type = 'buttons',
                        y = button_layer_1_height,
                        x = 0,
                        xanchor = 'left',
                        pad = {'r':10, 't':10},
                        direction = 'right',
                    ),
                    dict(
                        buttons = zmin_buttons,
                        yanchor = 'top',
                        type = 'buttons',
                        y = button_layer_2_height,
                        x=0,
                        xanchor = 'left',
                        pad = {'r':10,'t': 10},
                        direction = 'right',
                    )
                ],
                
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
                    if flag == flag_search and name1!= name2:
                        corr_dict[i][name1].update({
                            j:{name2:correlation} 
                        })
                        if debug:
                            print(f'\t{j} ({name2}): {correlation}')
                if corr_dict[i][name1] == {}:
                    corr_dict.pop(i) # If there is only one value, it is the value itself. 
            #}}} 
        return corr_dict
    #}}}
    # _parse_hkli: {{{
    def _parse_hkli(self,hkli_file:str = None,sort_hkli:bool = False):
        '''
        This allows us to parse files created by TOPAS6 using the: Create_hklm_d_Th2_Ip_file() macro
        format of data: 
            0: h
            1: k
            2: l
            3: multiplicity
            4: d-spacing
            5: 2 theta
            6: Intensity
        This will create a tuple from hkl

        If you want to have the hkli sorted by tth, you can but it significantly slows processing.
        ''' 
        hkli_data = np.loadtxt(hkli_file) # This gives us our data in an array. Now just need to parse it.  
        # assign the columns to variables: {{{
        h = hkli_data[:,0]
        k = hkli_data[:,1]
        l = hkli_data[:,2]
        m = hkli_data[:,3]
        d = hkli_data[:,4]
        tth = hkli_data[:,5]
        intensity = hkli_data[:,6]
        #}}}
        # Group hkl into a tuple: (h,k,l):{{{
        hkl = [(int(h[i]), int(k[i]), int(l[i])) for i, v in enumerate(hkli_data)]
        #}}}
        # Sort by 2theta: {{{
        if sort_hkli:
            sorted_tth = sorted(tth) # This creates a separate list that is sorted from low to hi tth
            j = list(tth) # Cast tth as a list so we can use the index functionality to sort the other arrays
            sorted_hkl = []
            sorted_m = []
            sorted_d = []
            sorted_i = []
            for val in sorted_tth:
                sorted_hkl.append(hkl[j.index(val)])
                sorted_m.append(m[j.index(val)])
                sorted_d.append(d[j.index(val)])
                sorted_i.append(intensity[j.index(val)])
            
            tth = sorted_tth
            hkl = sorted_hkl
            m = sorted_m
            d = sorted_d
            intensity = sorted_i
        #}}}
        # update the hkli out: {{{
        hkli_out = {
            'hkl':hkl,
            'm': m,
            'd':d,
            'tth':tth,
            'i':intensity,
        }
        #}}} 
        return hkli_out

    #}}} 
    # _parse_xy: {{{
    def _parse_xy(self,xy_file:str = None,delimiter:str = ','):
        '''
        This function returns a tuple of all of the information your xy file should have
        '''
        xy_data = np.loadtxt(xy_file, delimiter=delimiter) # imports the xy data to an array
        tth = xy_data[:,0]
        yobs = xy_data[:,1]
        ycalc = xy_data[:,2]
        ydiff = xy_data[:,3]
        return (tth, yobs, ycalc, ydiff)

    #}}}
    # _get_mol_fraction_data: {{{
    def _get_mol_fraction_data(self,formulas:list = None, fu_element:list = None, element_name:str = None):
        '''
        This function creates a dictionary for all of the mole fraction 
        data needed to generate plots.

        The formulas you input should correspond to the keys of the 
        csv plot data dictionary. 

        fu_element: This is a list of the formula units needed for each ion e.g. Ta2O5 for Ta you put: 2
        element_name: for Ta2O5 and Ta3N5 system, you would input "Ta"
        '''
        self.mol_fraction_data = {'Element': element_name}
        # Get Important Varibales: {{{

        mft = Mole_Fraction_Tools(formulas)
        fws = mft.get_formula_weights() # This will give us a dictionary of masses

        total_wp = [] # Need to normalize relative to the scale factors included.
        # Update Dict with Vals for Each Formula: {{{
        for i,formula in enumerate(formulas):
            try:
                fw = fws[formula] # current formula weight 
                sf = np.array(self.csv_plot_data[formula]['scale_factor'])
                wp = np.array(self.csv_plot_data[formula]['weight_percent'])
                zm = np.array(self.csv_plot_data[formula]['mass'])
                v = np.array(self.csv_plot_data[formula]['volume']) 
                self.mol_fraction_data[formula] = {
                        'mass': fw,
                        'scale_factor': sf,
                        'weight_percent':wp, 
                        'zm':zm,
                        'v':v,
                }
                total_wp.append(wp)
            except:
                raise 
        norm_factor_wp = sum(total_wp) # This gives the normalization factor.
        #}}}
        # Do normalizations and calculations for formulas: {{{
        total_mol_fraction = [] 
        for i, formula in enumerate(formulas): 
            entry = self.mol_fraction_data[formula]
            try:
                wp = entry['weight_percent'] 
                fw = entry['mass'] # Mass of the formula
                norm_wp = wp/norm_factor_wp
                mf = norm_wp*fu_element[i]/fw
                entry.update({
                    'norm_wp':norm_wp,
                    'unnormalized_mf_wp': mf,
                }) 
                total_mol_fraction.append(mf)
            except:
                pass
        mol_fraction_norm_constant = sum(total_mol_fraction)
        for formula in formulas:
            entry = self.mol_fraction_data[formula]
            try:
                mf = entry['unnormalized_mf_wp']
                norm_mf = mf/mol_fraction_norm_constant
                self.mol_fraction_data[formula].update({'norm_mf_from_wp': norm_mf})
            except:
                pass

        #}}}
        #}}}
    #}}}
    # plot_mole_fraction: {{{
    def plot_mole_fraction(self,
            plot_type:'wp',
            formulas:list = None,
            fu_element:list = None,
            element_name:str = None,
            xaxis_title:str = 'time / min',
            width = 1200,
            height = 800,
            template:str = 'simple_white',
            xrange:list = None,
            yrange:list = None,
            show_legend:bool = True,
            font_size:int = 20,
            marker_size:int = 5,
            mode:str = 'markers+lines',
            color:str = None,
            legend_xanchor:str = 'right',
            legend_yanchor:str = 'top',
            legend_x:float = 1.55,
            legend_y:float = 0.99,

        ):
        '''
        This function will plot mole fractions for a given substance. 
        based on what you provide.
        ''' 
        self._get_mol_fraction_data(formulas,fu_element,element_name)
        if plot_type == 'wp':
            plot_title = f'Weight Percent - Derived Mole Fraction {element_name}'
            key = 'norm_mf_from_wp'
        elif plot_type == 'sf':
            plot_title = f'Scale Factor - Derived Mole Fraction {element_name}'
            key = 'mf_from_sf'
        yaxis_title = f'mole fraction ({element_name})'
        # Get important plot prms: {{{
        time = np.array(self.csv_plot_data['time'])
        temp = np.array(self.csv_plot_data['temperature'])
        #}}}
        # Make Plots: {{{
        for i, formula  in enumerate(formulas):
            entry = self.mol_fraction_data[formula]
            mf = entry[key]
            if i == 0:
                self.plot_data(
                    x = time,
                    y =mf,
                    name = f'{formula} Mole Fraction',
                    mode = mode,
                    title_text=plot_title,
                    xaxis_title=xaxis_title,
                    yaxis_title=yaxis_title,
                    template=template,
                    xrange=xrange,
                    yrange=yrange,
                    height=height,
                    width=width,
                    show_legend=show_legend,
                    font_size=font_size,
                    marker_size=marker_size, 
                    color=color,
                )
            else:
                self.add_data_to_plot(
                    x = time,
                    y = mf,
                    name = f'{formula} Mole Fraction',
                    mode = mode,
                    xrange = xrange,
                    yrange = yrange,
                    marker_size=marker_size,
                    color = color,
                
                )
        #}}}
        # Finish off with the temperature curve: {{{
        self.add_data_to_plot(
            x = time,
            y = temp,
            name = f'Temperature',
            mode = mode,
            marker_size=marker_size,
            show_figure=True,
            y3 = True,
            y3_title = f'Temperature / {self._deg_c}',
            color = 'red',
            legend_xanchor=legend_xanchor,
            legend_yanchor=legend_yanchor,
            legend_x = legend_x,
            legend_y = legend_y,
        )
        #}}} 
    #}}}
#}}}

