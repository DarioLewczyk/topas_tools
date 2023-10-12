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
                        value = split[1] # This is the phase name
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
                                rec = words[0]
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
                        split = list(filter(lambda x: len(x) > 0, line.split(' '))) # Don't record any blank strings
                        x_idx = None
                        y_idx = None
                        z_idx = None
                        occ_idx = None
                        occ = None
                        beq_idx = None
                        bval_recorded = False
                        site = None
                        for j, val in enumerate(split):
                            ints,floats,words = self._get_ints_floats_words(val) # This gets these quantities for the current entry.
                            if j == 1:
                                site = val # This should be the site label
                                out_phase_dict[phase_num]['sites'][site] = {}
                            if j > 1:
                                # Find KWDS: {{{
                                val = val.strip('\t') # Get rid of tabs
                                val = val.strip(' ') # Get rid of spaces
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
                                if beq_idx:
                                    if j == beq_idx +1:
                                        b_val_keyword = re.findall(r'\w+_\w+',val) # This should find any keyword for bvals
                                        if b_val_keyword:
                                            out_phase_dict[phase_num]['sites'][site].update({'b_val_prm':b_val_keyword[0]}) # This will record the variable. 
                                        else:
                                            bval = re.findall(r'\d+\.\d+|\d+',val)
                                            out_phase_dict[phase_num]['sites'][site].update({'bval': float(bval[0])})
                                            bval_recorded = True
                                    elif j == beq_idx+2 and not bval_recorded:
                                        bval = re.findall(r'\d+\.\d+|\d+',val)
     
                                        out_phase_dict[phase_num]['sites'][site].update({'bval': float(bval[0])})
                                        bval_recorded = True
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
# TOPAS_Refinements: {{{
class TOPAS_Refinements(Utils, UsefulUnicode,OUT_Parser):
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
            phases_to_disable:list = None,
            threshold_for_off:float = 0.01,
            phases_to_enable:list = None,
            threshold_for_on:float = 0.0195, # this was obtained by looking at an Rwp curve 
            off_sf_value:float = 1.0e-100,
            on_sf_value:float = 1.0e-5,
            debug:bool = False,
        ):
        '''
        Code to run automated Rietveld Refinements based on Adam/Gerry's Code

        subtract_bkg: This will remove background terms from the individual phase contributions to ycalc
        scale_factors_to_monitor: you can give either a list or a string of the phase scale factor to monitor.
        threshold_for_scale_factor: This is the value the normalize scale factor can be below which, the program will set the scale factor to 0.
        
        phases_to_add: This is a list of phases you would like to have added as the refinement progresses. 
        threshold_to_add_phase: this is a percentage above your initial Rwp. When it passes this, the new phase turns on.
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
                    found = re.findall(r'(\w+\d?)*',fn_str)[0]
                    formula = found.split('_')[0]
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
    def _get_relevant_lines_for_monitoring(self,out:str = None,  off_phases:list = None, on_phases:list = None, debug:bool = False):
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
                                    'type': 'off'
                            }# Record the line
                            if j == len(off_phases):
                                break # If you reach the end, no point in reading more lines.
                    #}}}
                    # Handle the cases where you want to turn on a phase: {{{
    
                    for j, on in enumerate(on_phases):
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
        '''
        # get the relevant lines: {{{
        relevant_lines = self._get_relevant_lines_for_monitoring(out, off_phases,on_phases,debug)
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
                        if rwp_pct_diff >= threshold_for_on and not stopped:
                            entry['stopped'] = True # We are adding the phase so we can stop monitoring
                            # IF this is the case, we have yet to enable the phase. 
                            self._modify_sf_line(out=out,line_idx=line_idx,str_num=str_num,replacement_value=on_sf_value,debug=debug)
                            #}}}
                        elif rwp_pct_diff < threshold_for_on:
                            # No need to add the phase
                            self._out_file_monitor[key]['rwps'].append(current_rwp) # Add the newest Rwp
                    except:
                        # This case does not need to deal with Rwps. 
                        pass
                #}}}
                # Handle the Phase OFF Case: {{{
                elif entry_type == 'off':
                    if norm_val > threshold_for_off:
                        # This means we keep going. The scale factor hasnt fallen far enough
                        entry['values'].append(current_value)
                    elif norm_val <= threshold_for_off and not stopped:
                        entry['stopped'] = True # We are removing the phase, so stop monitoring it. 
                        # Now, DISABLE the phase: {{{
                        self._modify_sf_line(out=out,line_idx=line_idx,str_num=str_num,replacement_value=off_sf_value,debug=debug)
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
        ):
        '''
        This will gather and sort all of the output files from your refinements for you. 
        
        csv_labels: 
            This tells the program what each individual entry of the labels mean. 
        sort_hkli:
            This will sort each hkli file by tth but doing so results in a significantly slower processing time.
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
                substance = f.split('_')[0] # Since this substance should be exactly the same as for the xy files, we will also match them here too.
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
        # Categorize the Refined Data: {{{ 
        csvs = tqdm(self.sorted_csvs)
        # import and process CSV, XY, OUT, HKLI:     
        for i, csv in enumerate(csvs):
            csvs.set_description_str(f'Reading {csv}: ')
            csv_contents = [float(line) for line in open(csv)] # This gives us the values in the csv. 
            # Handle the XY Data: {{{
            csvs.set_description_str(f'Reading {self.sorted_xy[i]}: ')
            ttheta, yobs,ycalc,ydiff = self._parse_xy(self.sorted_xy[i])
            #}}}
            # Handle the OUT files: {{{ 
            
            if parse_out_files: 
                csvs.set_description_str(f'Reading {self.sorted_out[i]}: ')
                c_matrix = self._parse_c_matrix(out_file=self.sorted_out[i],correlation_threshold= correlation_threshold)
                out_phase_dict = self._parse_out_phases(out_file=self.sorted_out[i]) # Read the output file.
                corr_dict = self._get_correlations(c_matrix,flag_search)
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
                csvs.set_description_str(f'Reading {self.sorted_bkg_xy[i]}: ') # The background should be only 1D with one bkg for each pattern.
                bkg_tth, bkg_yobs,bkg_ycalc, bkg_ydiff = self._parse_xy(self.sorted_bkg_xy[i]) # Get the data. only care about tth and ycalc.
                bkg_dict.update({
                    'tth': bkg_tth,
                    'ycalc': bkg_ycalc,
                })
                bkg_name = self.sorted_bkg_xy[i]
            else:
                self.sorted_bkg_xy = None
            #}}}
            # Handle the Phase XY files: {{{
            phase_xy_data_dict = {}
            if self.sorted_phase_xy:
                for si, s in enumerate(self._phase_xy):
                    # This will get a dictionary for each substance.
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
                'out_dict': out_phase_dict,
                'c_matrix_filtered': corr_dict,
                'hkli':hkli_data_dict,
                'phase_xy': phase_xy_data_dict,
                'bkg': bkg_dict,
                'bkg_name': bkg_name,
 
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
                        phase_isolated = phase_name.split('_')[0] # This will only be the substance name
                        # We will not worry if the substance is in the CSV keys presented. 
                        if phase_isolated:
                            # If this is true, we can grab information from the output. 
                            if phase_isolated not in self.out_plot_dict:
                                # This is the first entry.
                                self.out_plot_dict[phase_isolated] = {}
                            for key in keys:
                                value = phase[key] # This gives the entry
                                # Update the dict with float and int values: {{{
                                if type(value) == float or type(value) == int:
                                    if key not in self.out_plot_dict[phase_isolated]:
                                        self.out_plot_dict[phase_isolated][key] = [value]
                                    else:
                                        self.out_plot_dict[phase_isolated][key].append(value)
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
     
                                        if bval_label not in self.out_plot_dict[phase_isolated]:
                                            self.out_plot_dict[phase_isolated][bval_label] = [bval]
                                        else:
                                            self.out_plot_dict[phase_isolated][bval_label].append(bval)      
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
                    for plot_key in entry_keys:
                        if plot_key.lower() in keys or plot_key.strip(f'{substance}_') in keys: # Need to check if the keys we are searching for are present.
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
                specific_substance = specific_substance,
            )
            if not specific_substance:
                if max(yobs) > self._max_i:
                    self._max_i = max(yobs)
            else:
                if max(ycalc) > self._max_i:
                    self._max_i = max(ycalc)
            #}}}
            if waterfall:  
                time = np.around(self.rietveld_data[i]['corrected_time']/60,4) 
                self.x = tth # This only needs to be 1 series.
                self.y.append(time) # This puts it into minutes
                if not specific_substance:
                    self.z.append(yobs) # This adds the observed intensity.
                else:
                    self.z.append(ycalc) # Adds calculated intensity
                hovertemplate = f"2{self._theta}{self._degree}" + "%{x}<br>Intensity: %{z}<br>" + "Time: %{y}<br>"
            else:
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
#}}}

