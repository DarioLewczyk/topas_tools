# Authorship: {{{
'''
Written by: Dario Lewczyk
Date: 04-26-2023
Purpose: 
    To create waterfall plots for XRD patterns
    One thing to note is that the filenames have to have a number in them
    that has a specific number of digits (6) in this case. That is the time

    It will use the time as the plot y axis. 

    The function will also go through and determine the range of x for the entire dataset imported. 

    The user may specify a specific range of files if they want. 
'''
#}}}
# Imports: {{{
import os, re, glob, sys
from tqdm import tqdm
import plotly.graph_objects as go
import numpy as np
import texttable
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
            os.system('cls')
        else:
            os.system('clear')
    #}}}
    # prompt_user: {{{
    def prompt_user(self, iterable:list = None):
        '''
        This function will prompt the user to make a selection from a list given. 
        The function will return the value selected. 
        '''
        # Loop for user selection: {{{
        selecting = True
        result = None
        while  selecting:  
            selection = input('Please select the number of your choice.\nIf you want to quit, simply press return or type none.\n')
            # Check if the selection was valid: {{{
            if selection.isdigit():
                selection = int(selection)
                result = iterable[selection]
                selecting = False
            #}}}
            # Check for quit: {{{
            elif selection.lower() == 'none' or selection == '':
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
            self.generate_table(cd_folders,header = 'Directories')
            selection = self.prompt_user(cd_folders)
            
            if selection == None or selection == 'done_selecting':
                navigating = False
            elif selection == 'back_directory':
                os.chdir(os.path.dirname(current_directory)) # This goes back a directory.
            else:
                os.chdir(selection) # Change directory to the new one.
            self.clear()
        #}}} 
    #}}}
#}}}
# DataCollector: {{{
class DataCollector:
    '''
    This will allow us to import all of the data we need. 
    '''
    # __init__: {{{
    def __init__(
            self,
            fileextension:str = 'xy', 
            position_of_time = 1,
            time_units:str = 'min', 
            file_time_units:str = 'sec',
            skiprows = 1,
        ):
        self.fileextension = fileextension
        self.position_of_time = position_of_time # This is the index of numbers in your filename that the time will be at 
        self.time_units = time_units # The units of time to be plotted
        self.file_time_units = file_time_units # The units of time recorded in the filename
        self.skiprows = skiprows # Rows that do not contain data in your files.
        self.file_dict = {} # This will be initialized as empty
    #}}}
    # scrape_files: {{{
    def scrape_files(self):
        self.files = glob.glob(f'*.{self.fileextension}') 
        tmp = {}
        for f in self.files:
            numbers = re.findall(r'\d{6}',f) # HAVE TO CHANGE MANUALLY IF YOU HAVE A DIFF LEN FOR TIMECODE
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
            timecodes = list(self.file_dict.keys()) 
            min_t = min(timecodes)
            max_t = max(timecodes)
            min_index = timecodes.index(min_t)
            max_index = timecodes.index(max_t)
            print(f'You have {len(timecodes)} patterns in this directory.')
            print('#'*80)
            selection = input('Enter the index of the pattern you want to start with and the number of patterns to plot separated by comma or space.\nIf you want to plot all of the data, press return\n')
            
            numbers = re.findall(r'\d+', selection)
            if len(numbers) == 2:  
                self.first_pattern_idx = int(numbers[0])
                number_of_patterns  = int(numbers[1])  
                proposed_final_idx = self.first_pattern_idx + number_of_patterns # This will give a possible index (may be out of range)
                if proposed_final_idx <= max_index:
                    self.last_pattern_idx = proposed_final_idx
                else:
                    self.last_pattern_idx = max_index
                selecting = False
            elif len(numbers) >0:
                # This means that it is not 2 but is not zero
                print('Your selection: {} was invalid.'.format(selection))
            else:
                self.first_pattern_idx = min_index 
                self.last_pattern_idx = max_index
                selecting = False 
    #}}}
    # get_arrs: {{{
    def get_arrs(self):
        '''
        This function is used to obtain the data from the files that fall within the time
        frame selected.
        ''' 
        ys = []
        files = []
        first_time = min(list(self.file_dict.keys()))
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
        # Get the tth and I vals: {{{
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
        #}}}
    #}}}
#}}}
# Plotter: {{{
class Plotter(DataCollector):
    def __init__(
            self, 
            min_on_zmax = 10, # This sets the minimum value you would like the colorscale to max out on. 
            min_on_zmin = -10, # This sets the max value you would like on the colorscale min
            num_max_buttons = 5,
            num_min_buttons = 5,

        ):
        DataCollector.__init__(self)
        self.theta = u'\u03B8'
        self.degree = u'\u00B0'

        self.min_on_zmax = min_on_zmax
        self.min_on_zmin = min_on_zmin
        self.num_max_buttons = num_max_buttons
        self.num_min_buttons = num_min_buttons

        self.scrape_files()
        self.set_time_range()
        self.get_arrs()

        min_steps = (0 - self.min_on_zmin)/(self.num_min_buttons -1)
        max_steps = (self.max_i - self.min_on_zmax)/ (self.num_max_buttons-1)
 
        self.zmin_arange = np.arange(self.min_on_zmin, 0+min_steps,min_steps)
        self.zmax_arange = np.arange(self.min_on_zmax, self.max_i+max_steps, max_steps)
    
        self.hovertemplate = f'2{self.theta}{self.degree}:'+'%{x}<br>Time/'+f'{self.time_units}: '+'%{y} <br>Intensity: %{z}'

    # plot_waterfall: {{{
    def plot_waterfall(self):
        '''
        This will plot a waterfall plot 
        You can change up the z scaling with buttons 
        '''
        fig = go.Figure()
        fig.add_heatmap(
            x = self.tth_arr,
            y = self.time_arr,
            z = self.i_arr,
            hovertemplate = self.hovertemplate,
        )
        # Create the min buttons: {{{
        zmin_buttons = [
            dict(
                label = f'I_min: {np.around(v,2)}',
                method = 'restyle',
                args = [
                    {'zmin': v},
                ]
            )for v in self.zmin_arange
        ]
        #}}}
        # Create the max buttons: {{{
        zmax_buttons = [
            dict(
                label = f'I_max: {np.around(v,2)}',
                method = 'restyle',
                args = [
                    {'zmax':v},
                ]
            )for v in self.zmax_arange
        ]
        #}}}
        # Update the layout: {{{
        button_layer_1_height = 1.17
        button_layer_2_height = 1.1

        fig.update_layout(
            height = self.height,
            width = self.width,
            margin = dict(t=200,b=0,l=0,r=0),
            autosize = False,
            title_text = f'{os.path.basename(os.getcwd())} Waterfall Plot',
            xaxis_title = f'2{self.theta}{self.degree}',
            yaxis_title = f'Time/{self.time_units}',
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
        fig.show()
    #}}}
#}}}
# Run: {{{
class Run(Utils,Plotter):
    # __init__: {{{
    def __init__(
            self,
            min_on_zmax = 200,
            min_on_zmin = -100,
            num_max_buttons = 5,
            num_min_buttons = 5,
            height = 800,
            width = 1000, 
            ):
        self.height = height
        self.width = width
        self.starting_dir = os.getcwd()
        self.starting_dir_contents = os.listdir()
        Utils.__init__(self) # Gives us access to the utilities.
        selection = input('Do you need to navigate to another folder before running?\n(y/n)\n')
        if selection:
            if selection.lower() == 'y' or selection.lower() == 'yes':
                self.navigate_filesystem()
        self.clear()
        Plotter.__init__(
            self,
            min_on_zmax = min_on_zmax, # This sets the minimum value you would like the colorscale to max out on. 
            min_on_zmin = min_on_zmin, # This sets the max value you would like on the colorscale min
            num_max_buttons = num_max_buttons,
            num_min_buttons = num_min_buttons,
        )
        self.plot_waterfall()
        os.chdir(self.starting_dir) # Return us to the beginning.
    #}}} 
#}}}
# When script is run: {{{
if __name__ == "__main__":
    run = input('Run the script return for yes or type y. For no, type n\n')
    if run.lower() == 'y' or run == '':
        min_on_zmax = 200
        min_on_zmin = -100
        num_max_buttons = 5
        num_min_buttons = 5
        # Set User values: {{{
        usr_zmax = re.findall(r'\D?\d+\.?\d+',input(f'Min Value for Colorscale Max Default: {min_on_zmax}\n'))
        usr_zmin = re.findall(r'\D?\d+\.?\d+',input(f'Min Value for Colorscale Min Default: {min_on_zmin}\n'))
        usr_max_buttons = re.findall(r'\d+',input(f'Number of Buttons for Max CS Default: {num_max_buttons}'))
        usr_min_buttons = re.findall(r'\d+',input(f'Number of Buttons for Min CS Default: {num_min_buttons}'))
        
        if usr_zmax:
            min_on_zmax = float(usr_zmax[0])
        if usr_zmin:
            min_on_zmin = float(usr_zmin[0])
        if usr_max_buttons:
            num_max_buttons = int(usr_max_buttons[0])
        if usr_min_buttons:
            num_min_buttons = int(usr_min_buttons[0])
        #}}} 
        Run(
            min_on_zmax= min_on_zmax, 
            min_on_zmin=min_on_zmin, 
            num_max_buttons=num_max_buttons, 
            num_min_buttons=num_min_buttons
        )
    else:
        pass

#}}}