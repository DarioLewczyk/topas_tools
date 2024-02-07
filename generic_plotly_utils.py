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
            yrange:list = None, 
            height = 800,
            width = 1000, 
            show_legend:bool = True,
            font_size:int = 20,
            marker_size:int = 12,
            color:str = None,
            show_figure:bool = False,
            legend_xanchor:str = 'right',
            legend_yanchor:str = 'top',
            legend_x:float = 0.99,
            legend_y:float = 0.99, 
            ticks:str = 'inside',
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
                ),
                name = name,
                yaxis = 'y1',
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
            ),
            yaxis = dict(
                title = yaxis_title,  
                ticks = ticks,
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
            xrange:list = None,
            yrange:list = None,
            marker_size:int = 12,
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
            ),
            yaxis = yaxis,
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
    def plot_stuff(
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
