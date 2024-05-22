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
        uninterp_x = bkg_sub_data[idx]['uninterpolated'][:,0]
        uninterp_y = bkg_sub_data[idx]['uninterpolated'][:,1]
        interpolated = bkg_sub_data[idx]['interpolated'] # boolean to tell if interpolation was used
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
        # Plot uninterpolated bkgsub data: {{{
        if interpolated:
            self.add_data_to_plot(
                x = uninterp_x,
                y = uninterp_y, 
                name = f'bkgsub_{idx} (uninterpolated)',
                color = 'red',
                mode = 'markers', 
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
    # plot_bkgsub_data: {{{
    def plot_bkgsub_data(self,
            bkgsub_data:dict,
            **kwargs
        ):
        '''
        This function serves as a sanity check that the background
        subtraction is working as expected.

        kwargs:
            marker_size,
            legend_x,
            legend_y,
            y2_position,
        '''
        # kwargs: {{{
        marker_size = kwargs.get('marker_size', 5)
        legend_x = kwargs.get('legend_x',0.99)
        legend_y = kwargs.get('legend_y',0.99)
        y2_position = kwargs.get('y2_position',0)
        #}}}
        indices = []
        scale_factors = []
        ref_peaks = []
        data_peaks = []
        tth_offsets = []
        # get data to plot: {{{
        for i, entry in bkgsub_data.items():
            indices.append(i)
            scale_factors.append(entry['scale_factor'])
            ref_peaks.append(entry['ref_peak'])
            data_peaks.append(entry['data_peak'])
            tth_offsets.append(entry['tth_offset'])
        #}}}
        # Plot scale factor: {{{
        self.plot_data(
                x = indices,
                y = scale_factors,
                name = 'Scale Factor',
                color = 'blue',
                mode = 'lines+markers',
                marker_size=marker_size,
                title_text= 'BKG Sub Validation',
                xaxis_title='Pattern IDX',
                yaxis_title='Scale Factor',

        )
        #}}}
        # plot peaks: {{{
        self.add_data_to_plot(
            x = indices,
            y = ref_peaks,
            name= 'Ref pattern peaks',
            mode = 'lines+markers',
            marker_size=marker_size,
            color= 'green',
            y2 = True,
            y2_title=f'Peak position (2{self._theta}{self._degree})',
        )
        self.add_data_to_plot(
            x = indices,
            y = data_peaks,
            name= 'Data pattern peaks',
            mode = 'lines+markers',
            marker_size=marker_size,
            color = 'red',
            y2 = True,
            y2_position = y2_position,
            y2_title=f'Peak position (2{self._theta}{self._degree})',
        )
        #}}}
        # plot offset: {{{
        self.add_data_to_plot(
            x = indices,
            y = tth_offsets,
            name = f'2{self._theta} offset',
            mode = 'lines+markers',
            marker_size = marker_size,
            y3 = True,
            y3_title= f'Offset (2{self._theta}{self._degree})',
            color = 'black',
            legend_x=legend_x,
            legend_y = legend_y,
        )
        #}}}
        self.show_figure()
    #}}}
#}}}
