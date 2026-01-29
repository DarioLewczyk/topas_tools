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
        y_err = None, 
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
        **kwargs
        ):
        '''
        This allows you to plot a dataset
        kwargs:
            hovertemplate: if you have one, you can use it. 
            symbol: marker symbol if you choose
        '''
        # default kwargs: {{{

        hovertemplate = kwargs.get('hovertemplate', None)
        symbol = kwargs.get('symbol', 'circle')
        #}}}
        self._fig = go.Figure()
        # Plot Data: {{{
        if not color:
            color = self._get_random_color()
        self._fig.add_scatter(
                x = x,
                y = y,
                error_y=dict(type='data', array=y_err, visible=True) if y_err is not None else None,
                mode = mode,
                marker = dict(
                    symbol = symbol,
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
                hovertemplate = hovertemplate,
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
            y_err:list = None,
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
            **kwargs
            ):
        '''
        Allows you to add data to the existing plot 
        either on the same y axis or add a new one. 

        use "lines+markers" if you want to have a solid line connecting points
        kwargs: 
            hovertemplate
            symbol: marker symbol if you choose to change it
        '''
        # kwargs: {{{
        hovertemplate = kwargs.get('hovertemplate',None)
        symbol = kwargs.get('symbol','circle')
        #}}}
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
            error_y=dict(type='data', array=y_err, visible=True) if y_err is not None else None,
            name = name,
            mode = mode,
            marker = dict(
                symbol = symbol,
                line = dict(
                width = 2,
                color =color,
                ),
                color = color,
                size = marker_size,
            ),
            line =dict(
                color = color,
                dash = dash,
            ),
            yaxis = yaxis,
            showlegend = show_in_legend,
            hovertemplate = hovertemplate
        )
        #}}}
        # Update Layout: {{{
        if xrange != None and not y2 and not y3:
            self._fig.update_layout(
                    xaxis = dict(
                        range = xrange, 
                        ticks = ticks,
                    )
            )
        if yrange != None and not y2 and not y3:
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
            if yrange != None:
                self._fig.update_layout(
                    yaxis2 = dict(range=yrange)
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
            if yrange != None:
                self._fig.update_layout(
                    yaxis3 = dict(range=yrange)
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
    # plot_histogram: {{{
    def plot_histogram(self, 
            x, 
            nbins, 
            color = None, 
            opacity = 0.7,
            name:str = 'Data',
            xaxis_title:str = 'X',
            yaxis_title:str = 'Counts',
            title_text:str = 'Data Histogram',
            bargap:float = 0.05,
            show_figure:bool = False,
            template:str = 'simple_white',
            *args,
            **kwargs,
            ):

        '''
        Allows you to quickly plot data in a histogram form
        
        *args allows you to pass arguments through to plotly's
        "update_layout" function.
        '''
        if color == None:
            color = self._get_random_color()
        self._fig = go.Figure()
        
        # Add the histogram: {{{
        self._fig.add_histogram(
            x = x, 
            nbinsx = nbins,
            marker_color = color,
            opacity = opacity,
            name = name,
        )
        #}}} 
        # Update the layout: {{{
        self._fig.update_layout(
            title = title_text,
            xaxis_title = xaxis_title,
            yaxis_title = yaxis_title,
            bargap = bargap,
            template = 'simple_white',
            *args,
            **kwargs,
        )
        #}}}
        if show_figure:
            self.show_figure()

    #}}}
    # add_data_to_histogram: {{{
    def add_data_to_histogram(self, 
            x, 
            nbins, 
            color = None,
            opacity = 0.7,
            name:str = 'Data',
            bargap:float = 0.05,
            show_figure:bool = False,
            barmode = 'group',
            *args,
            **kwargs,
        ):
        '''
        Allows you to add additional series to the histogram

        barmode: 
            "group": bars for different traces side by side
            "stack": bars are stacked on top of each other
            "relative": like stack but + / - are opposites
            "overlay": bars drawn on top of each other... opacity determines visibility

        *args: 
            can pass though any arguments to the "update_layout"
        '''
        if color == None:
            color = self._get_random_color()
        # add data to histogram: {{{
        self._fig.add_histogram(
            x = x, 
            nbinsx = nbins,
            marker_color = color,
            opacity = opacity,
            name = name,
        )
        #}}}
        # update layout: {{{
        self._fig.update_layout(
            bargap = bargap,
            barmode = barmode, 
            *args,
            **kwargs,
        )
        
        #}}}
        if show_figure:
            self.show_figure()
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
    # customize_axis: {{{
    def customize_axis(self,fig:go.Figure = None, axis= 'y', scale = 'log', minor_ticks = True, minor_tick_interval = 0.1):
        '''
        Customize the axis of a plotly fig.

        PRMS: 
        - fig: Plotly Figure object
        - axis: 'x' or 'y' to specify the axis
        - scale: 'linear' or 'log' to set the axis scale
        - minor_ticks: Bool to add minor ticks
        - tick0: Starting point for the ticks
        - dtick: Interval between ticks
        '''
        axis_key = f'{axis}axis'
        fig.update_layout({
            axis_key: dict(
                type = scale, 
            )
        })
        if minor_ticks:
            fig.update_layout({
                axis_key: dict(
                    tickmode = 'linear',
                    dtick = minor_tick_interval,
                    showgrid = True,
                    gridwidth = 0.5,
                    gridcolor = 'LightGray'
                )
            })
    #}}}
    # plot_waterfall: {{{ 
    def plot_waterfall(self, 
            tth_arr = None, 
            time_arr = None, 
            i_arr = None, 
            min_on_zmax = 1000, # This sets the minimum value you would like the colorscale to max out on. 
            min_on_zmin = -1000, # This sets the max value you would like on the colorscale min
            num_max_buttons = 5,
            num_min_buttons = 5,
            **kwargs
        ):
        '''
        This will plot a waterfall plot 
        You can change up the z scaling with buttons 

        If you would like to adjust parameters for fitting, you can do so using kwargs: 

            button_layer_1_height
            button_layer_2_height
            colorscale
            height
            width
            title
            time_units
            hovertemplate
        '''
        # Set the attributes to plot: {{{
        if type(tth_arr) != type(None):
            self.tth_arr = tth_arr
            self.time_arr = time_arr
            self.i_arr = i_arr 
            self.max_i = max([max(i) for i in self.i_arr])
        #}}}
        # kwargs: {{{
        button_layer_1_height = kwargs.get('button_layer_1_height', 1.17)
        button_layer_2_height = kwargs.get('button_layer_2_height', 1.1)
        colorscale = kwargs.get('colorscale', 'viridis')
        height = kwargs.get('height', 800)
        width = kwargs.get('width', 1000)
        title_text = kwargs.get('title', 'Waterfall Plot')
        self.time_units = kwargs.get('time_units', self.time_units)
        hovertemplate = kwargs.get('hovertemplate', f'2{self._theta}{self._degree}:'+'%{x}<br>Time/'+f'{self.time_units}: '+'%{y} <br>Intensity: %{z}')
        #}}}
        # Set up the min and max ranges for buttons: {{{
        min_steps = (0 - min_on_zmin)/(num_min_buttons -1)
        max_steps = (self.max_i - min_on_zmax)/ (num_max_buttons-1)
 
        zmin_arange = np.arange(min_on_zmin, 0+min_steps,min_steps)
        zmax_arange = np.arange(min_on_zmax, self.max_i+max_steps, max_steps)
        #}}}

        self.fig = go.Figure()
        self.fig.add_heatmap(
            x = self.tth_arr,
            y = self.time_arr,
            z = self.i_arr,
            hovertemplate = hovertemplate,
            colorscale = colorscale,
        )
        # Create the min buttons: {{{
        zmin_buttons = [
            dict(
                label = f'I_min: {np.around(v,2)}',
                method = 'restyle',
                args = [
                    {'zmin': v},
                ]
            )for v in zmin_arange
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
            )for v in zmax_arange
        ]
        #}}}
        # Update the layout: {{{
        self.fig.update_layout( 
            height = height,
            width = width,
            margin = dict(t=200,b=0,l=0,r=0),
            autosize = False,
            title_text = title_text,
            xaxis_title = f'2{self._theta}{self._degree}',
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
        self.fig.show()
    #}}} 
    # plot_topas_xy_output: {{{
    def plot_topas_xy_output(self, xy_file:str = None, xy_data = None, tth = None, yobs = None, ycalc = None, ydiff = None, *args, **kwargs):
        ''' 
        Allows you to quickly plot the xy output file from TOPAS
        where it outputs 2theta, yobs, ycalc, ydiff
        '''
        # Default stuff for this plot: {{{
        if not xy_file:
            kwargs.setdefault('title_text', "TOPAS_REFINED_PATTERN")
        else:
            kwargs.setdefault('title_text', f"xy_file")
        kwargs.setdefault('xaxis_title', f'2{self._theta}{self._degree}')
        kwargs.setdefault('yaxis_title', f'Intensity')
        kwargs.setdefault('mode', 'lines') 
        #}}}
        # Check if xy file: {{{
        if xy_file != None:
            try:
                xy_data = np.loadtxt(xy_file) # This should load the xy file if it is present
            except:
                raise ValueError(f'XY File: {xy_file} not found... or invalid format')
        #}}}
        # Check if xy data: {{{
        elif type(xy_data) != type(None):
            try:
                tth = xy_data[:,0]
                yobs = xy_data[:,1]
                ycalc = xy_data[:,2]
                ydiff = xy_data[:,3]
            except:
                cols = len(xy_data[0,:]) 
                print(f'Expected 4 columns, got {cols}')
                raise ValueError(f'XY Data Not Valid Format: \n{xy_data}')

        #}}}
        # Plot the data: {{{
        self.plot_data(tth, yobs, name = 'Observed', color = 'blue', *args, **kwargs)
        self.add_data_to_plot(tth, ycalc, name = 'Calculated', color = 'red',*args, **kwargs)
        self.add_data_to_plot(tth, ydiff, name = 'Difference', color = 'grey', *args, **kwargs)
        #}}}
        self.show_figure()
       
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
        self._update_default_kwargs = {} # Blank to start
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
        high_contrast_colors = [
            (0, 0, 0),       # Black
            #(255, 0, 0),     # Red
            (0, 0, 255),     # Blue
            (0, 255, 0),     # Green
            (255, 165, 0),   # Orange
            (128, 0, 128),   # Purple
            (255, 20, 147),  # Deep Pink
            (139, 69, 19),   # Saddle Brown
            (75, 0, 130),    # Indigo
            (255, 69, 0)     # Red-Orange
        ]

        if self.color_index == len(high_contrast_colors)-1:
            self.color_index = 0 #Reset the color index
        r,g,b = high_contrast_colors[self.color_index]
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
    # _update_default_kwargs: {{{
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
#}}}
