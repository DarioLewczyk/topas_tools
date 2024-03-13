# Authorship; {{{
'''
Written by Dario Lewczyk
03/05/2023
Purpose: 
    This file contains some advanced plotly templates 
    for making figures such as lattice parameter figures
    with subplots for temperature and mole fraction. 

    These functions will have a high degree of customization
    for the visual style. 
'''
#}}}
# Imports: {{{
import plotly.graph_objects as go
from plotly.subplots import make_subplots # THis allows us to add a secondary y axis
#}}}
# AdvancedPlotting: {{{
class AdvancedPlotting:
    '''
    This class contains all of the advanced plotting tools to 
    generate figures such as lattice parameter figures with separate subplots 
    and temperature/mole fraction. 
    '''
    # __init__: {{{
    def __init__(self):
        pass
    #}}}
    # _base_subplot: {{{
    def _base_subplot(
            self,
            rows:int=2, 
            cols:int=1,
            specs = None,
            subplot_titles:list= None,
            shared_xaxes:bool=True,
            vertical_spacing:float =0.05,
            row_heights:list=[0.7, 0.3]
        ):
        '''
        Creates a base subplot for you to add data to with the externally 
        facing functions.
        '''
        self.fig = make_subplots(
            rows=rows, 
            cols=cols,
            specs=specs,
            subplot_titles= subplot_titles,
            shared_xaxes= shared_xaxes,
            vertical_spacing = vertical_spacing,
            row_heights=row_heights,
        )
    #}}}
    # plot_mole_balance: {{{ 
    def plot_mole_balance(
            self,
            time:list = None,
            total:list = None,
            temperature:list = None,
            subplot_title = 'Mole Balance',
            vertical_spacing = [0.7, 0.3],
            specs:list = None,
            **kwargs
        ):
        '''
        This function will create subplots with the top figure being mole balance
        The bottom figure will be a temperature figure. 

        **kwargs:

        THIS NEEDS WORK AT SOME POINT
        
        '''
        # kwargs: {{{
        self._default_kwargs = {
                'vertical_spacing':0.05,
                'row_heights':[0.7,0.3],

        }
        #}}}
        # base subplot: {{{
        self._base_subplot(
            subplot_titles=[subplot_title, ''],
            vertical_spacing=vertical_spacing, 
            specs=specs,
        )
        #}}}
        # Plot data: {{{ 
        # Mole balance: {{{
        self.fig.add_scatter(
            x = time,
            y = total,
            mode = 'lines+markers',
            marker=dict(size=8, symbol="diamond", line=dict(width=2, color="black")),
            line = dict(color = 'black'),
            name = 'Total Moles Ta',
            showlegend = False,
            row = 1,
            col = 1
        )
        #}}}

        #}}}
    #}}}

#}}}
