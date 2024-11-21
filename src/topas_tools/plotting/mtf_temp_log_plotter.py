# Authorship: {{{ 
'''
Written by: Dario C. Lewczyk
Date: 11-13-24
Purpose: Make nice plots of the thermometry data for MTF
'''
#}}}
# Imports: {{{
from topas_tools.plotting.plotting_utils import GenericPlotter
import numpy as np
#}}}
# MTFTempPlotter: {{{
class MTFTempPlotter(GenericPlotter):
    # __init__: {{{
    def __init__(self): 
        GenericPlotter.__init__(self) # Get all the functionality of the generic plotter
    #}}} 
    # plot_mtf_temp_log:  {{{
    def plot_mtf_temp_log(self, mtf_temp_logs:dict = None, idx:int = 0, title:str = None):
        '''
        This will plot for you, the information for the temperature log vs. time
        includes 
            Thermocouple C temperature
            Setpoint
        '''
        fn, time, temperature_c, temperature_d, delta_t, setpoint, kp, ki, kd = self.parse_temp_logs(mtf_temp_logs, idx)

        if title:
            pass
        else:
            title = fn

        self.plot_data(time, temperature_c, name = 'temperature', 
              mode = 'lines+markers', 
              color='red', 
              title_text=title,
             xaxis_title= 'Time (min)', yaxis_title=f'Temperature / {self._degree_celsius}')
        self.add_data_to_plot(time, setpoint, color = 'blue', mode = 'lines', dash='dash', name = 'setpoint')
        self.show_figure()

    #}}}
    # plot_diff_from_setpoint: {{{ 
    def plot_diff_from_setpoint(self, mtf_temp_logs:dict = None, idx:int = 0, title:str = None, threshold_to_ignore:float = None):
        '''
        This will plot the difference between your setpoint and measured temperature.

        threshold_to_ignore: if you want to ignore differences below a certain value, you can input it here. This may clean up the graph a bit for visualization so you do not include ramps in the fluctuations.
        '''
        fn, time, temperature_c, temperature_d, delta_t, setpoint, kp, ki, kd = self.parse_temp_logs(mtf_temp_logs, idx)
        sp_diff = temperature_c - setpoint
        if title:
            title_text = title
        else:
            title_text = fn

        if threshold_to_ignore != None:
            for i, v in enumerate(sp_diff):
                if v <= threshold_to_ignore:
                    sp_diff[i] = 0 # This replaces the value with zero. 

        self.plot_data(
            time, sp_diff, 
            name = 'measured_temp - setpoint',
            color = 'red',
            mode = 'lines+markers',
            title_text = title_text,
            xaxis_title= 'Time (min)', 
            yaxis_title=f'Temperature / {self._degree_celsius}',
        )
        self.add_data_to_plot(
            time, 
            np.zeros(len(time)),
            show_in_legend=False,
            mode = 'lines',
            dash = 'dash',
            color = 'blue',

        )
        self.show_figure()
    #}}}
    # plot_pid_prms: {{{ 
    def plot_pid_prms(self,mtf_temp_logs:dict = None, idx:int = 0, title:str = None):
        fn, time, temperature_c, temperature_d, delta_t, setpoint, kp, ki, kd = self.parse_temp_logs(mtf_temp_logs, idx)
        if title:
            title_text = title
        else:
            title_text = fn
        self.plot_data(
            time,
            kp,
            name = 'kP',
            mode = 'lines+markers',
            color = 'red',
            title_text = title_text,
            xaxis_title = 'Time (min)',
            yaxis_title = 'kP',
            
        )
        self.add_data_to_plot(
            time, 
            ki,
            name = 'kI',
            mode = 'lines+markers',
            y2 = True,
            y2_title= 'kI',
            color = 'green',

        )
        self.add_data_to_plot(
            time,
            kd,
            name = 'kD',
            mode = 'lines+markers',
            y3 = True,
            y3_title = 'kD',
            color = 'blue',

                )
        self.show_figure()
    #}}}
    # parse_temp_logs: {{{
    def parse_temp_logs(self, mtf_temp_logs:dict = None, idx:int = 0):
        '''
        Returns a tuple with all the information from the temperature logs
        Returns in the order: 
        filename, time, temperature_c, temperature_d, 
        delta_t, setpoint, kp, ki, kd
        '''
        # prms: {{{ 
        log = mtf_temp_logs[idx]
        fn = log['filename']
        time = log['time']
        temperature_c = log['temperature_c']
        temperature_d = log['temperature_d']
        delta_t = log['delta_t']
        setpoint = log['setpoint']
        kp = log['kp']
        ki = log['ki']
        kd = log['kd']
        #}}}
        return (fn, time, temperature_c, temperature_d, delta_t, setpoint, kp, ki, kd)
    #}}}
#}}}
