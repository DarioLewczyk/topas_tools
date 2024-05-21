# Authorship; {{{
'''
Written by Dario Lewczyk
09/01/2023
Purpose: I want to have a simple interface for generating plots with Plotly
It should not have any specifically built-in assumptions 
other than that I typically like to plot either lines or points. 
So that is an assumption. 
'''
#}}}
# Imports: {{{
import re
import copy

import plotly.graph_objects as go
import numpy as np

from topas_tools.utils.topas_utils import UsefulUnicode
#}}}
# GenericPlotter: {{{
class GenericPlotter(UsefulUnicode):
    # __init__: {{{
    def __init__(self):
        super().__init__()
    #}}}
    # plot_data: {{{
    def plot_data(self,
        x = None,
        y = None,
        name = 'series',
        show_in_legend:bool = True,
        mode:str = 'markers',
        title_text:str = 'Figure',
        xaxis_title:str = 'X',
        yaxis_title:str = 'Y',
        template:str = 'simple_white',
        xrange:list = None ,
        yrange:list = None, 
        height = 800,
        width = 1000, 
        show_legend:bool = True,
        font_size:int = 16,
        marker_size:int = 5,
        dash:str = None,
        color:str = None,
        show_figure:bool = False,
        legend_xanchor:str = 'right',
        legend_yanchor:str = 'top',
        legend_x:float = 0.99,
        legend_y:float = 0.99, 
        ticks:str = 'inside',
        mirror_x = 'allticks', 
        mirror_y = 'allticks',
        ):
        '''
        This allows you to plot a dataset
        '''
        self._fig = go.Figure()
        # Plot Data: {{{
        if not color:
            color = self._get_random_color()
        self._fig.add_scatter(
                x = x,
                y = y,
                mode = mode,
                marker = dict(
                    color = color,
                    size = marker_size,
                ),
                line = dict(
                    color = color,
                    dash = dash,
                ),
                name = name,
                yaxis = 'y1',
                showlegend = show_in_legend,
        )
        #}}}
        # Update Layout: {{{
        if xrange == None:
            xrange = [min(x),max(x)]
        if yrange != None:
            self._fig.update_layout(yaxis = dict(range = yrange))
            yrange = [min(y)*0.98,max(y)*1.02]
        self._fig.update_layout(
            height = height,
            width = width,
            title_text = title_text,
            #xaxis_title = xaxis_title,
            #yaxis_title = yaxis_title,
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
                title = xaxis_title, 
                domain = [0.15,1], 
                range = xrange, 
                ticks = ticks,
                mirror = mirror_x,
            ),
            yaxis = dict(
                title = yaxis_title,  
                ticks = ticks,
                mirror = mirror_y,
            ),
        )
        #}}}
        if show_figure:
            self._fig.show()
    #}}} 
    # add_data_to_plot: {{{
    def add_data_to_plot(self,
            x:list = None,
            y:list = None,
            name:str = 'series',
            show_in_legend:bool = True,
            mode = 'markers',
            xrange:list = None,
            yrange:list = None,
            marker_size:int = 5,
            dash:str = None,
            y2:bool = False,
            y2_title:str = 'Y2',
            y2_position:float = 0,
            y3:bool = False,
            y3_title:str = 'Y3',
            color:str = None,
            show_figure:bool = False,
            legend_xanchor:str = 'right',
            legend_yanchor:str = 'top',
            legend_x:float = 0.99,
            legend_y:float = 0.99,  
            ticks:str = 'inside',
            ):
        '''
        Allows you to add data to the existing plot 
        either on the same y axis or add a new one. 

        use "lines+markers" if you want to have a solid line connecting points
        '''
        # Determine the Yaxis to plot on: {{{: 
        if y2:
            yaxis = 'y2'
        elif y3:
            yaxis = 'y3'
        else:
            yaxis = 'y1'
        #}}}
        if not color:
            color = self._get_random_color()
        # Plot: {{{
        self._fig.add_scatter(
            x = x,
            y = y,
            name = name,
            mode = mode,
            marker = dict(
                color = color,
                size = marker_size,
            ),
            line =dict(
                color = color,
                dash = dash,
            ),
            yaxis = yaxis,
            showlegend = show_in_legend,
        )
        #}}}
        # Update Layout: {{{
        if xrange != None:
            self._fig.update_layout(
                    xaxis = dict(
                        range = xrange, 
                        ticks = ticks,
                    )
            )
        if yrange != None:
            self._fig.update_layout(
                    yaxis = dict(
                        range = yrange, 
                        ticks = ticks,
                        )
                    )
        self._fig.update_layout(
            legend = dict(
                yanchor = legend_yanchor,
                y = legend_y,
                xanchor = legend_xanchor,
                x = legend_x,
            ),
        )
        # Y2: {{{
        if y2: 
            self._fig.update_layout(
                    yaxis2 = dict(
                        title = y2_title,
                        anchor = 'free',
                        overlaying = 'y',
                        side = 'left',
                        position = y2_position, 
                        ticks = ticks,
                    ),
            )
        #}}} 
        # Y3: {{{
        if y3:
            self._fig.update_layout(
                    yaxis3 = dict(
                        title = y3_title,
                        anchor = 'x',
                        overlaying = 'y',
                        side = 'right', 
                        ticks = ticks,
                    )
            )
        #}}}
        #}}}
        if show_figure:
            self._fig.show()
    #}}} 
    # show_figure: {{{
    def show_figure(self):
        self._fig.show()
    #}}}
    # _get_random_color: {{{
    def _get_random_color(self,):
        rand_color = list(np.random.choice(range(256),size=3))
        color = f'rgb({rand_color[0]},{rand_color[1]},{rand_color[2]})'
        return color 
    #}}}
    # plot_series: {{{
    def plot_series(
        self,
        x_series, 
        y_series, 
        names, 
        colors,
        title = 'Plot', 
        x_title = 'X-axis', 
        y_title = 'Y-axis', 
        mode = 'lines+markers',
        marker_size = 5,
        width = 1500,
        height = 800,
        legend_x = 1.5, 
        xrange = None,
        yrange = None,
        ):
        '''
        This function allows us to plot lots of data in a series. 

        For example, you input data as such: 
        x_series = [ x1, x2 ] 
        y_series = [ [y1a, y1b, y1c], [y2a, y2b, y2c]]
        where the xs in the x series will apply to the cluster of ys given
        '''
        first_plot = True
        show_figure = False 
        # Loop: {{{
        for i, series in enumerate(y_series):
            x = x_series[i] # This gives the x values for the series
            color = colors[i] 
            if type(mode) == list: 
                try:
                    selected_mode = mode[i]
                except:
                    selected_mode = 'lines+markers' # Defaults if you gave the wrong number of items
            else:
                selected_mode = mode
                
                    
            for j, y in enumerate(series):
                # Only show the figure on the last iteration: {{{
                if i+1 == len(y_series) and j + 1 == len(series): 
                    show_figure = True
                #}}}
                # First Plot: {{{ 
                if first_plot:
                    self.plot_data(
                        x= x,
                        y = y,
                        name = names[i][j],
                        mode =selected_mode,
                        title_text= title,
                        yaxis_title= y_title,
                        xaxis_title= x_title,
                        color = color, 
                        legend_x= legend_x,
                        width=width,
                        marker_size=marker_size,
                        height = height,
                        xrange = xrange,
                        yrange = yrange,
                        show_figure=show_figure,
                    )
                    first_plot = False
                #}}}
                # All other Plots: {{{
                else:  
                    self.add_data_to_plot(
                        x = x,
                        y = y,
                        name = names[i][j],
                        mode= selected_mode,
                        marker_size=marker_size,
                        color = color,
                        show_figure=show_figure,
                        legend_x= legend_x,
                        xrange = xrange,
                        yrange = yrange,
                    )
                #}}}
        #}}}
    #}}}
#}}}
# PlottingUtils: {{{
class PlottingUtils(GenericPlotter):
    '''
    This is a class to house the niche functions for 
    making nice plots with "RefinementPlotter"
    '''
    # __init__: {{{
    def __init__(self,rietveld_data:dict = {}):
        self.rietveld_data = rietveld_data
        self.color_index = 0 # Initialize the color as the default
        super().__init__()
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
            ticks:str = 'inside'
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
                ticks = ticks,
            ),
            yaxis = dict(
                ticks = ticks,
            )
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
    # _add_buttons: {{{
    def _add_buttons(self,plot:go.Figure = None, xanchor = 'right',yanchor = 'top',button_x = 1.25, button_y = 1,plot_calc_patterns:bool = True):
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
        if plot_calc_patterns:
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
    # _normalize: {{{
    def _normalize(self, data:list = None):
        try:
            norm = [v/max(data) for v in data]
        except:
            norm = [v/(1e-100) for v in data]

        return norm
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
#}}}
