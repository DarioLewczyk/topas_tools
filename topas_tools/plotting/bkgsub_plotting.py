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
    # plot_inverted_bkgsub: {{{
    def plot_chebychev_bkgsub(self,idx:int = 0, chebychev_data:dict = None, **kwargs):
        '''
        This function enables the visualization of background 
        subtraction with chebychev polynomials so you get a sense of the 
        quality of fit.
        '''
        # kwargs: {{{
        marker_size = kwargs.get('marker_size', 3)
        legend_x = kwargs.get('legend_x',0.99)
        legend_y = kwargs.get('legend_y',0.99) 
        #}}}
        # collect the data: {{{
        entry = chebychev_data[idx]
        x =entry['tth']
        y =entry['orig_y']
        yinv =entry['yinv']
        bkgsub =entry['yobs']
        peak_x =entry['peak_x']
        peak_y =entry['peak_y']
        bkg_curve =entry['bkg_curve']
        fn =entry['fn']
        #}}}
        xaxis_title = f'2{self._theta}{self._degree}'
        yaxis_title = 'Intensity'
        # plot the data: {{{
        # original bkgsub: {{{
        self.plot_data(
            x = x,
            y = y,
            color = 'black',
            mode = 'lines',
            xaxis_title = xaxis_title,
            yaxis_title = yaxis_title,
            name = 'Original bkg sub data',
            title_text= 'Background finding',
        )
        #}}}
        # inverted bkgsub: {{{
        self.add_data_to_plot(
            x,
            yinv, 
            color = 'blue',
            mode = 'lines',
            name = 'Inverted bkgsub data',
                )
        #}}}
        # Add peak markers: {{{
        self.add_data_to_plot(
            peak_x,
            peak_y,
            color = 'red',
            mode = 'markers',
            name = 'Inverted baseline peaks',
            marker_size=marker_size,
                )
        #}}}
        # Plot background: {{{
        self.add_data_to_plot(
            x,
            bkg_curve,
            color = 'red',
            mode = 'lines',
            dash = 'dash',
            name = 'Chebychev background curve',
            )
        #}}}
        # baseline_peaks: {{{
        self.add_data_to_plot(
            peak_x,
            np.array(peak_y)*-1,
            color = 'green',
            name = 'Baseline peaks',
            mode = 'markers',
            marker_size=marker_size,
            legend_x = legend_x,
            legend_y = legend_y,
        )
        #}}}
        self.show_figure()
        #}}}
        # Plot the new bkgsub: {{{
        self.plot_data(
            x, bkgsub,
            color = 'black',
            name = 'Chebychev subtracted',
            mode = 'lines',
            xaxis_title = xaxis_title,
            yaxis_title = yaxis_title,
            title_text= 'Chebychev subtracted',
        )
        self.add_data_to_plot(
            x, np.zeros(len(x)),
            show_in_legend=False,mode = 'lines',dash = 'dash',color = 'blue',
        )
        self.show_figure()
        #}}}
        print(f'filename: {fn}')
    #}}}
    # _plot_neg_check: {{{
    def _plot_neg_check(self,working_dict:dict = None):
        '''
        This takes dictionaries: 
            bkgsub_data 
            chebychev_data
        This should only be run after you have evaluated negative values in the range. 
        '''
        # collect data into a single list.{{{ 
        pos_i = []
        neg_i = []
        for i, entry in working_dict.items():
            neg_obs_above_min_tth = entry['negative_above_min_tth'] # Boolean, defines coloring
            if neg_obs_above_min_tth:
                neg_i.append(i)
            else:
                pos_i.append(i)
        #}}}
        # Loop to generate plots: {{{
        data = [pos_i, neg_i] 
        initial_plot = False
        for i, v in enumerate(data):  
            # Negative plot parameters: {{{
            if i == 1: 
                color = 'red'
                name = 'contains_negative'
            #}}}
            # Positive plot prms: {{{ 
            if i == 0:
                color = 'black'
                name = 'only_positive'
            #}}}
            # initial plot definition: {{{ 
            
            if i == 0:
                try:
                    self.plot_data(
                        v,
                        v,
                        color = color,
                        title_text = 'Negative BKG sub patterns',
                        xaxis_title='Pattern IDX',
                        yaxis_title = 'Pattern_IDX', 
                        name = name,
                    )
                    initial_plot = True
                except:
                    pass
            #}}}
            # add additional data: {{{ 
            else:
                if initial_plot:
                    self.add_data_to_plot(
                            v,
                            v,
                            color = color, 
                            name = name, 
                            legend_xanchor='left',
                            legend_x = 0.2,
                    )
                else:
                    self.plot_data(
                        v,
                        v,
                        color = color,
                        title_text = 'Negative BKG sub patterns',
                        xaxis_title='Pattern IDX',
                        yaxis_title = 'Pattern_IDX', 
                        name = name,
                        legend_xanchor='left',
                        legend_x = 0.2,
                    )
            #}}}
        #}}} 
        self.show_figure()
    #}}}
    # plot_negative_peak_ranges: {{{
    def plot_negative_peak_ranges(self,idx:int = 0, working_dict:dict = None, offset = -10):
        '''
        This function serves to show the background subtracted data 
        with the negative ranges highlighted on the plot. (if there are any)
        '''
        
        tth = working_dict[idx]['tth']
        yobs = working_dict[idx]['yobs']

        self.plot_data(
            tth,
            yobs,
            color = 'black',
            name = f'Pattern: {idx}',
            mode = 'lines',
            xaxis_title = f'2{self._theta}',
            yaxis_title = 'Intensity',
            title_text = 'Negative Peak Ranges'
        )
        self.add_data_to_plot(
            tth,
            np.zeros(len(tth)),
            color = 'blue',
            name = 'zeros',
            show_in_legend = False,
            mode = 'lines',
            dash = 'dash',
        )
        tth_range = working_dict[idx]['negative_ranges'] # Get the 2theta ranges
        if tth_range:
            for i, tpl in enumerate(tth_range):
                self.add_data_to_plot(
                    tpl,
                    np.ones(len(tpl))*offset,
                    name = f'idx: {i}',
                    mode = 'lines+markers',
                    legend_x = 1.3,
                )
        self.show_figure()
    #}}}
    # plot_original_vs_bkgsub: {{{
    def plot_original_vs_bkgsub(self, idx:int = 0, patterns:dict = None, bkgsub_data:dict = None, chebychev_data:dict = None,**kwargs):
        '''
        This allows you to directly compare original patterns to background subtraction via glass
        to background subtraction via chebychev polynomial subtraction and anything between. 

        kwargs: legend_x or legend_y or xrange
        '''
        # kwargs: {{{
        legend_x = kwargs.get('legend_x', 0.99)
        legend_y = kwargs.get('legend_y', 0.99)
        xrange = kwargs.get('xrange', None)
        #}}}
        plotted_zeros = False
        dictionaries = [patterns, bkgsub_data, chebychev_data]
        # loop through dicts: {{{
        for i, working_dict in enumerate(dictionaries):
            if type(working_dict) == dict:
                # handle the differences for the dictionaries: {{{
                if i == 0: # Patterns
                    working_dict = working_dict['data'] # This gives access to the 2theta and yobs data
                    color  = 'black'
                    name = f'Orignal pattern # {idx}'
                elif i == 1: # Bkg sub
                    color = 'blue'
                    name = 'bkgsub_data'
                elif i == 2: # Chebychev
                    color = 'green'
                    name = 'chebychev_data'
                #}}}
                tth = working_dict[idx]['tth']
                yobs = working_dict[idx]['yobs']
                # plot make the first plot: {{{
                if not plotted_zeros:
                    self.plot_data(
                        tth,
                        np.zeros(len(tth)),
                        mode = 'lines',
                        dash = 'dash',
                        title_text = 'BKG sub comparison',
                        xaxis_title = f'2{self._theta}',
                        yaxis_title = 'Intensity',
                        color = 'blue',
                        name = 'zeros',
                        show_in_legend = False,
                    )
                    plotted_zeros = True
                #}}}
                self.add_data_to_plot(
                    tth,
                    yobs,
                    color = color,
                    name = name,
                    mode = 'lines',
                    legend_x = legend_x,
                    legend_y = legend_y,
                    xrange = xrange,
                )
        #}}}
        self.show_figure()
    #}}}
#}}}
