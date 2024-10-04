# Authorship: {{{
'''
Written by Dario Lewczyk
7/11/2023
Purpose: 
    To be able to quickly and efficiently 
    generate plots of Tiff images to be able to see
    directly, (not inferring from the integrated data),
    the quality of the underlying data. 

This should leverage the "useful_classes_for_data_analysis" python
file to assist getting the data. 
'''
#}}}
# Imports: {{{
import os, re, glob, sys
from tqdm import tqdm
import plotly.graph_objects as go
import numpy as np
import texttable
import copy
import useful_classes_for_data_analysis as ud# A custom file with useful classes
#}}}
# TiffPlotter: {{{
class TiffPlotter(ud.DataCollector):
    # __init__: {{{
    def __init__(
        self,
        min_on_zmax = 10,
        min_on_zmin = -10,
        num_max_buttons = 5,
        num_min_buttons = 5,
        fileextension = 'tiff',
        position_of_time = 1,
        len_of_time = 6,
        time_units = 'min',
        file_time_units = 'sec',
        skiprows = 1,
        height = 1000,
        width = 800,
        metadata:dict=None,
        ):
        # Initialize DataCollector: {{{
        '''
        In contrast to the original implementation of the 
        DataCollector, in this case, we are only worried about
        the 
        '''
        ud.DataCollector.__init__(
            self,
            fileextension = fileextension,
            position_of_time=position_of_time,
            len_of_time=len_of_time,
            file_time_units=file_time_units,
        )
        #}}}
        # Init Vars: {{{
        self._min_on_zmax = min_on_zmax
        self._min_on_zmin = min_on_zmin
        self._num_max_buttons = num_max_buttons
        self._num_min_buttons = num_min_buttons
        self._height = height
        self._width = width
        self.metadata = metadata # This is the dictionary of metadata
        self._deg_c = u'\u2103'
        #}}} 
        # Collect_Data: {{{
        self.scrape_files()#This gives us the files sorted in a dict.
        #}}}
    #}}} 
    # plot_tiff: {{{
    def plot_tiff(self, 
            fileindex:int = 0, 
            title_prefix:str = None, 
            title_time_units:str = 'min',
            **kwargs
            ):
        '''
        This will plot the tiff image using plotly and the function 
        "get_imarr" from DataCollector to get the data.

        kwargs:
        height
        width
       
        button_y
        '''
        self.get_imarr(fileindex=fileindex) # Gets the data for the current file
        # kwargs: {{{
        height = kwargs.get('height',self._height)
        width = kwargs.get('width',self._width)
        
        button_y = kwargs.get('button_y',1.2)
        #}}}
        # Get Plot Params: {{{
        # IF METADATA: {{{
        if self.metadata:
            times = list(self.metadata.keys()) # These are the times in order
            current_md = self.metadata[times[fileindex]]
            first_time = self.metadata[times[0]]['epoch_time']
            current_time = current_md['epoch_time']
            current_temp = current_md['temperature']
            self.image_time = current_time - first_time
            self.image_time_min = np.around(self.image_time/60,2)
            self.image_time_h = np.around(self.image_time/(60**2),2)
        else:
            current_temp = 'NOT MEASURED'
            
            
        #}}}
        if title_time_units == 's':
            time = self.image_time
        elif title_time_units == 'min':
            time = self.image_time_min
        elif title_time_units == 'h':
            time = self.image_time_h


        min_steps = (0 - self._min_on_zmin)/(self._num_min_buttons - 1)
        max_steps = (self.max_im_z - self._min_on_zmax)/(self._num_max_buttons - 1)

        self._zmin_arange = np.arange(self._min_on_zmin, 0+min_steps, min_steps)
        self._zmax_arange = np.arange(self._min_on_zmax, self.max_im_z + max_steps, max_steps)
        self.hovertemplate = 'X Pixel: %{x}<br>Y Pixel: %{y}<br>Intensity: %{z}'
        #}}}
        
        self.fig = go.Figure()
        self.fig.add_heatmap(
            x = self.im_x,
            y = self.im_y,
            z = self.im_z,
            hovertemplate = self.hovertemplate,

        )
        # Create Min Buttons: {{{
        zmin_buttons = [
            dict(
                label = f'I_min: {np.around(v,2)}',
                method = 'restyle',
                args = [
                    {'zmin': v},
                ]
            )for v in self._zmin_arange
        ]
        #}}}
        # Create Max Buttons: {{{
        zmax_buttons = [
            dict(
                label = f'I_max: {np.around(v,2)}',
                method = 'restyle',
                args = [
                    {'zmax': v},
                ]
            )for v in self._zmax_arange
        ]   
        #}}}
        # Update Layout: {{{
        button_layer_1_height = button_y
        button_layer_2_height = button_y - 0.05

        self.fig.update_layout(
            height = height,
            width = width,
            margin = dict(t=200,b=0,l=0,r=0),
            autosize=False,
            title_text = f'{title_prefix} {time} {title_time_units} 2D Image, {current_temp}{self._deg_c}',
            xaxis_title = 'Pixel (X)',
            yaxis_title = 'Pixel (Y)',
            updatemenus = [
                dict(
                    buttons = zmax_buttons,
                    yanchor = 'top',
                    type = 'buttons',
                    y = button_layer_1_height,
                    x = 0,
                    xanchor = 'left',
                    pad = {'r': 10, 't': 10},
                    direction = 'right',
                ),
                dict(
                    buttons = zmin_buttons,
                    yanchor = 'top',
                    type = 'buttons',
                    y = button_layer_2_height,
                    x = 0,
                    xanchor = 'left',
                    pad = {'r': 10, 't': 10},
                    direction = 'right',
                )
            ]
        )
        #}}}
        self.fig.show() # Reveal the image.
    #}}}

#}}}
