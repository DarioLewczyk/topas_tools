# Authorship; {{{
'''
Written by Dario Lewczyk
9/1/23
Purpose: I want to have a simple interface for generating plots with Plotly
It should not have any specifically built-in assumptions 
other than that I typically like to plot either lines or points. 
So that is an assumption. 
'''
#}}}
# Imports: {{{
import plotly.graph_objects as go
import numpy as np
import re
#}}}
# GenericPlotter: {{{
class GenericPlotter:
    # __init__: {{{
    def __init__(self):
        # Unicode Attrs: {{{
        self._angstrom_symbol = u'\u212b'
        self._degree_symbol = u'\u00b0'
        self._degree_celsius = u'\u2103'
        self._theta = u'\u03b8'
        #}}} 
    #}}}
    # plot_data: {{{
    def plot_data(self,
            x = None,
            y = None,
            name = 'series',
            mode:str = 'markers',
            title_text:str = 'Figure',
            xaxis_title:str = 'X',
            yaxis_title:str = 'Y',
            template:str = 'simple_white',
            xrange:list = None ,
            height = 800,
            width = 1000, 
            show_legend:bool = True,
            font_size:int = 20,
            marker_size:int = 12,
            show_figure:bool = False,
            ):
        '''
        This allows you to plot a dataset
        '''
        self._fig = go.Figure()
        # Plot Data: {{{
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
                ),
                name = name,
                yaxis = 'y1',
        )
        #}}}
        # Update Layout: {{{
        if xrange == None:
            xrange = [min(x),max(x)]
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
                yanchor = 'top',
                y = 0.99,
                xanchor = 'right',
                x = 0.99,
            ),
            showlegend = show_legend,
            xaxis = dict(
                title = xaxis_title, 
                domain = [0.15,1], 
                range = xrange,
            ),
            yaxis = dict(
                title = yaxis_title,
            ),
        )
        #}}}
        if show_figure:
            self._fig.show()
    #}}} 
    # add_data_to_plot: {{{
    def add_data_to_plot(self,
            x,
            y,
            name,
            mode = 'markers',
            marker_size:int = 12,
            y2:bool = False,
            y2_title:str = 'Y2',
            y2_position:float = 0,
            y3:bool = False,
            y3_title:str = 'Y3',
            show_figure:bool = False,
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
            ),
            yaxis = yaxis,
        )
        #}}}
        # Update Layout: {{{
        # Y2: {{{
        if y2: 
            self._fig.update_layout(
                    yaxis2 = dict(
                        title = y2_title,
                        anchor = 'free',
                        overlaying = 'y',
                        side = 'left',
                        position = y2_position,
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
#}}}
