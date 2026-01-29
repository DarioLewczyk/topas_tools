# Authorship: {{{
'''
Written by: Dario C. Lewczyk
Purpose: Allow the user to quickly view and manipulate
2D detector data after a beamline experiment
'''
#}}}
# Imports: {{{
import os, re, glob, sys
from tqdm import tqdm
import plotly.graph_objects as go
import numpy as np
import texttable
import copy
from topas_tools.utils.topas_utils import DataCollector, Utils
from topas_tools.utils.bkgsub_utils import BkgsubUtils
from topas_tools.plotting.plotting_utils import GenericPlotter
import pyFAI
import fabio
#}}}
# ImagePlotter: {{{
class ImagePlotter(Utils, DataCollector,GenericPlotter, BkgsubUtils):
    # __init__: {{{
    def __init__(self,
        data_dir:str = None,
        fileextension:str = 'tiff',
        mode = 0,
        metadata:dict = None,
        **kwargs,
        ):
        '''
        The initialization of this class 
        will automatically find tiff images in a directory
        
        data_dir = None # Can leave this as None if you are already in the directory you want to be in. 
        fileextension: # This is the fileextension of the datatype you want to search for 
        mode = 0 # This is 0 if you have timestamps in your filenames, 1 if you dont
        metadata = None # You can set this if you want to draw on metadata information.


        kwargs: 
        position_of_time = 1 # This refers to when you run regular expressions on the filename, where does the timestamp show up?
        len_of_time = 6 # Refers to how long your timecode in the filename is. If it is present.
        time_units = min # Refers to the time unit you would like displayed (if available)
        file_time_units = sec # Refers to the time units recorded in the filename
        skiprows = 1 # Refers to the number of rows numpy should skip when reading data from .xy files
        '''
        # Kwargs: {{{
        position_of_time = kwargs.get('position_of_time',1)
        len_of_time = kwargs.get('len_of_time',6)
        time_units = kwargs.get('time_units','min')
        file_time_units = kwargs.get('file_time_units','sec')
        skiprows = kwargs.get('skiprows',1)
        #}}}
        GenericPlotter.__init__(self) # Initialize the Plotting utilities 
        BkgsubUtils.__init__(self) # Initialize the bkgsub_utils to get peak finding ability
        self.home_dir = os.getcwd()
        self.metadata_data = metadata
        # If no data directory defined: {{{
        if not data_dir:
            print(f'You are currently in: {self.home_dir}\nNavigate to the data directory.')
            self.data_dir = self.navigate_filesystem()
        else:
            self.data_dir = data_dir
        os.chdir(self.data_dir)
        #}}}  
        # Collect the data files: {{{
        DataCollector.__init__(self,
                fileextension=fileextension,
                position_of_time=position_of_time,
                len_of_time=len_of_time,
                file_time_units=file_time_units,
                mode = mode,
                )
        self.scrape_files()
        #}}}
    #}}}
    # plot_image: {{{
    def plot_image(self,
            x,
            y,
            z,
            hovertemplate = None, 
            title_text:str = 'Image', 
            xaxis_title:str = 'X',
            yaxis_title:str = 'Y',
            show_figure:bool = True,
            **kwargs,
            ):  
        '''
        This function allows you to plot 2D image data like tiffs with their intensities
        
        kwargs: 
            min_on_zmax = 10 # This is is the minimum button value for the max
            min_on_zmin = -10 # This is the minimum button value for the min row
            num_max_buttons = 5 # How many buttons for max range?
            num_min_buttons = 5 # How many buttons for the min range?
            height = 1000 # height of the fig
            width = 800 # width of the fig
            button_x = 0 # Position in x of the buttons
            button_y = 1.2 # position in y of the top layer buttons
            xanchor = 'left' # Button anchor position
            colorscale = "viridis" # Can set to any colormap
        ''' 
        # kwargs: {{{
        min_on_zmax = kwargs.get('min_on_zmax',10)
        min_on_zmin = kwargs.get('min_on_zmin',-10)
        num_max_buttons = kwargs.get('num_max_buttons',5)
        num_min_buttons = kwargs.get('num_min_buttons',5)
        height = kwargs.get('height',1000)
        width = kwargs.get('width',800)
        button_x = kwargs.get('button_x', 0.0)
        button_y = kwargs.get('button_y', 1.2)
        xanchor = kwargs.get('xanchor', 'left')
        colorscale = kwargs.get('colorscale', 'viridis')
        #}}}
        # Get ranges for buttons: {{{
        # NOTE: self.max_im_z is automatically calculated when we import the image.
        min_steps = (0 - min_on_zmin)/(num_min_buttons - 1)
        max_steps = (np.nanmax(z) -min_on_zmax)/(num_max_buttons - 1)

        zmin_arange = np.arange(min_on_zmin, 0 + min_steps, min_steps)
        zmax_arange = np.arange(min_on_zmax, np.nanmax(z) + max_steps, max_steps) 
        #}}}
        # Make the image plot: {{{
        self.image_fig = go.Figure()
        self.image_fig.add_heatmap(
            x = x,
            y = y,
            z = z,
            hovertemplate = hovertemplate,
            colorscale = colorscale, 
            zmin = 0,
            zauto = False,
        )
        #}}}
        # Create the min buttons: {{{
        zmin_buttons = [
            dict(
                label = f'I_min: {np.around(v, 2)}',
                method = 'restyle',
                args = [
                    {'zmin':v},
                ]
            ) for v in zmin_arange
        ]
        #}}}
        # Create the min buttons: {{{
        zmax_buttons = [
            dict(
                label = f'I_max: {np.around(v, 2)}',
                method = 'restyle',
                args = [
                    {'zmax':v},
                ]
            ) for v in zmax_arange
        ]
        #}}}
        # update layout: {{{
        button_layer_1_height = button_y
        button_layer_2_height = button_y - 0.05

        self.image_fig.update_layout(
            height = height,
            width = width, 
            margin = dict(t = 200, b = 0, l = 0, r = 0), 
            autosize = False,
            title_text = title_text,
            xaxis_title = xaxis_title,
            yaxis_title = yaxis_title,
            updatemenus = [
                dict(
                    buttons = zmax_buttons,
                    yanchor = 'top',
                    type = 'buttons',
                    y = button_layer_1_height,
                    x = button_x,
                    xanchor = xanchor,
                    pad = {'r':10, 't':10},
                    direction = 'right',

                ),
                dict(
                    buttons = zmin_buttons,
                    yanchor = 'top',
                    type = 'buttons',
                    y = button_layer_2_height,
                    x = button_x,
                    xanchor = xanchor,
                    pad = {'r':10, 't':10},
                    direction = 'right',
                ),

            ]
        )
        #}}}
        if show_figure:
            self.image_fig.show()
    #}}} 
    # _plot_2d_diffraction_image: {{{
    def _plot_2d_diffraction_image(self,
            fileindex:int = 0, 
            title_text:str = '2D Diffraction Image',
            show_mask:bool = False,
            plot_distances:bool = False, 
            show_figure:bool = True,
            **kwargs,
            ):
        '''
        This function leverages plot_image to make a plot for 2D area detector data.
        The kwargs from this function automatically get passed into the plot_image function
        '''
        if show_mask or plot_distances:
            show_figure = False
        self.get_imarr(fileindex=fileindex) # Gets the data and the zmax for the image 
        # Get xyz for pixels: {{{
        if not plot_distances:
            x = self.im_x
            y = self.im_y
            z = self.im_z
            xaxis_title = 'Pixel (X)'
            yaxis_title = 'Pixel (Y)'
        #}}} 
        # Get xyz for distances: {{{
        else:
            x = self.im_x_dist
            y = self.im_y_dist
            z = self.im_z
            xaxis_title = 'X distance (m)'
            yaxis_title = 'Y distance (m)'
        #}}}
        hovertemplate = xaxis_title + ': %{x}<br>' + yaxis_title + ': %{y}<br>Intensity: %{z}'
        self.plot_image(x, y, z, hovertemplate = hovertemplate, title_text = title_text,xaxis_title = xaxis_title, yaxis_title = yaxis_title,show_figure = show_figure, **kwargs),
        # show mask: {{{
        if show_mask:
            if not plot_distances:
                x = self.mask_x
                y = self.mask_y
                z = self.nan_mask
            else:
                x = self.mask_x_dist
                y = self.mask_y_dist
                z = self.nan_mask
                
            self.image_fig.add_heatmap(
                    x = x,
                    y = y,
                    z = z,
                    hovertemplate = hovertemplate,
                    hoverongaps = False,# Turns off hovertemplate for the plot when values are NaN
            ) 
        #}}}
        # plot PONI: {{{
        if plot_distances:
            self.image_fig.add_scatter(
                x = [self.poni_x],
                y = [self.poni_y],
                name = 'PONI',
                mode = 'markers',
                hovertemplate = hovertemplate,
                marker = dict(
                    color = 'red',
                    symbol = 'x',
                    size = 10,
                    line = dict(
                        width = 1,
                    ),
                ),
            )
        #}}}
        if show_mask or plot_distances:
            self.image_fig.show()
    #}}}
    # _load_cake_data: {{{
    def _load_cake_data(self, radial = None, chi = None, cake = None): 
        if type(radial) != type(None) and type(chi) != type(None) and type(cake) != type(None):
            self.radial = radial
            self.chi = chi
            self.cake = cake
    #}}}
    # _get_axis_labels: {{{
    def _get_axis_labels(self, unit:str = '2th_deg'):
        if unit == '2th_deg':
            x_label  = f'2{self._theta}{self._degree}'
        else:
            x_label  = unit
        y_label = 'Integrated Intensity'
        return (x_label, y_label)
    #}}}
    # plot_cake: {{{ 
    def plot_cake(self, 
            radial = None,
            chi = None,
            cake = None,
            unit:str = '2th_deg', 
            **kwargs):
        '''
        This function uses pyFAI to take a 2D area detector image and create a cake plot 
        for visualization

        '''  
        self._load_cake_data(radial,chi,cake)
        # Make the hovertemplate: {{{
        x_label, y_label = self._get_axis_labels(unit)
        y_label = f'Azimuthal angle {self._degree}'
        hovertemplate = x_label +': %{x}<br>'+ y_label +': %{y}<br>Intensity: %{z}'
        #}}} 
        # Make the cake plot: {{{
        self.plot_image(x = self.radial, 
                y = self.chi, 
                z = self.cake, 
                hovertemplate=hovertemplate, 
                title_text = 'Cake Plot', 
                xaxis_title= x_label,
                yaxis_title = y_label,
                **kwargs)
        #}}} 
    #}}}
    # plot_1d_pattern_from_cake: {{{
    def plot_1d_pattern_from_cake(self,chi_idx:int = 0, radial = None, chi = None, cake = None, unit:str = '2th_deg'):
        '''
        This function lets you plot any of the integrated patterns in a cake plot

        '''
        x_label, y_label = self._get_axis_labels()
        self._load_cake_data(radial,chi,cake)
        x = self.radial
        y = self.cake[chi_idx]
        # Plot data: {{{
        self.plot_data(
            x = x,
            y = y, 
            name = 'Cake pattern',
            mode = 'lines', 
            title_text=f'Pattern at Azimuthal Position: {np.around(self.chi[chi_idx], 3)}{self._degree}',
            xaxis_title = x_label,
            yaxis_title = y_label,
            color = 'black',
            show_figure = True,
        )
        #}}} 
    #}}}
    # plot_all_1d_cake_patterns: {{{
    def plot_all_1d_cake_patterns(self,radial = None, chi = None, cake = None, unit:str = '2th_deg'):
        xaxis_title, yaxis_title = self._get_axis_labels(unit)
        self._load_cake_data(radial,chi,cake)
        # Loop through the patterns: {{{
        for i, pattern in enumerate(self.cake):
            # make the initial plot: {{{
            if i == 0:
                self.plot_data(
                    x = self.radial,
                    y = pattern,
                    name = f'{np.around(self.chi[i], 4)}{self._degree}',
                    color = 'black', 
                    mode = 'lines',
                    xaxis_title=xaxis_title,
                    yaxis_title= yaxis_title,
                    title_text = '2D Integration (All Azimuthal Angles)',
                    width = 1200
                )
            #}}} 
            # add to the plot: {{{
            else:
                self.add_data_to_plot(
                    x = self.radial,
                    y = pattern,
                    name = f'{np.around(self.chi[i], 4)}{self._degree}',
                    mode = 'lines',
                    legend_x=1.2
                )
            #}}}
        #}}}        
        self.show_figure()
    #}}}
    # plot_1d_integrated_pattern: {{{
    def plot_1d_integrated_pattern(self, x = None, y = None, unit:str = '2th_deg', **kwargs):
        '''
        This lets you plot a 1D integrated diffraction pattern

        kwargs:
            title_text
            color
        '''
        # kwargs: {{{
        title_text = kwargs.get('title_text','1D integrated pattern')
        color = kwargs.get('color', 'black')
        mode = kwargs.get('mode','lines') 
        #}}}
        xaxis_title, yaxis_title = self._get_axis_labels(unit)
        self.plot_data(x, y, 
            title_text = title_text,
            xaxis_title= xaxis_title,
            yaxis_title = yaxis_title,
            show_legend = False,
            color = color,
            mode = mode,
            show_figure = True,
        )
    #}}}
#}}}
