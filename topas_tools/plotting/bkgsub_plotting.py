# Authorship: {{{
'''
Written by: Dario C. Lewczyk
Date: 05-20-24
Purpose: Visualization of BKG sub tasks 
'''
#}}}
# Imports: {{{
import numpy as np
from topas_tools.plotting.plotting_utils import GenericPlotter
#}}}
# BkgSubPlotter: {{{
class BkgSubPlotter(GenericPlotter):
    # __init__: {{{
    def __init__(self):
        super.__init__() 
    #}}}
    # plot_pattern_with_peaks: {{{
    def plot_pattern_with_peaks(self,
            pattern_tth = None,
            pattern_yobs = None,
            pattern_name:str = 'pattern',
            peaks_tth = None,
            peaks_yobs = None, 
            peaks_name:str = 'peaks',
            title_text:str = 'Pattern + Peaks',
            **kwargs
        ):
        '''
        for **kwargs, you can give a height and width or change the legend position.
        This function allows you to visualize a dataset with peaks found
        being overlaid.
        ''' 
        # kwargs: {{{
        height = kwargs.get('height', 800)
        width = kwargs.get('width', 1000)
        legend_x = kwargs.get('legend_x', 0.99)
        legend_y = kwargs.get('legend_y', 0.99)
        #}}}
        # Plot the pattern: {{{
        self.plot_data(
            pattern_tth,
            pattern_yobs,
            name = pattern_name,
            mode = 'lines',
            title_text= title_text,
            xaxis_title= f'2{self._theta}{self._degree}',
            yaxis_title = 'Intensity',
            color = 'blue',
            height=height,
            width = width,
        )
        #}}}
        # Plot the peaks: {{{
        self.add_data_to_plot(
            peaks_tth,
            peaks_yobs,
            name = peaks_name,
            mode = 'markers',
            marker_size = 10,
            color = 'red',
            legend_x = legend_x,
            legend_y = legend_y,
            show_figure=True
        )
        #}}}
    #}}}
    # plot_bkgsub_pattern: {{{
    def plot_bkgsub_pattern(self, idx:int = 0, bkg_sub_data:dict = None, **kwargs):
        '''
        Plot the background subtracted data.
        input the background subtracted data and an index
        '''
        # Defaults:  {{{ 
        height = kwargs.get('height', 800)
        width= kwargs.get('width', 1000)
        legend_x = kwargs.get('legend_x', 0.99)
        legend_y = kwargs.get('legend_y', 0.99)
        #}}}
        # Get data arrays: {{{
        x = bkg_sub_data[idx]['tth']
        y = bkg_sub_data[idx]['yobs']
        fn = bkg_sub_data[idx]['fn']
        zeros = np.zeros(len(x)) # Get an array of zeros to make visualization easy
        #}}}
        # Plot bkgsub data: {{{
        self.plot_data(
            x = x,
            y = y, 
            name = f'bkgsub_{idx}',
            color = 'black',
            mode = 'lines+markers',
            title_text = fn,
            xaxis_title=f'2{self._theta}{self._degree}',
            yaxis_title = 'Intensity',
            width = width,
            height = height,
            
        )
        #}}}
        # plot zeros: {{{
        self.add_data_to_plot(
            x=x,
            y=zeros,
            show_in_legend=False,
            color = 'blue',
            mode = 'lines',
            dash = 'dash', 
            legend_x=legend_x,
            legend_y = legend_y,
            show_figure=True,
        )
        #}}}

    #}}}
#}}}
