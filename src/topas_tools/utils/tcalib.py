# Authorship: {{{
# Written By: Dario Lewczyk
# Date: 02-20-2024
#}}}
# Imports: {{{
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from lmfit import minimize, Parameters, fit_report
#}}}
# TCal: {{{
class TCal:
    '''
    This class allows you to correct thermocouple temperature
    using a calibration curve. 
    '''
    # __init__: {{{
    def __init__(self,):
        ''' 
        This has all the important calibration information 
        from the paper on Si lattice expansion. 
        '''
        # Literature Temps and LPs (1974 Paper): {{{
        t_1974 = [
            25, #0
            157,#1
            356,#2
            496,#3
            651,#4
            813,#5
        ] # These are from the 1974 paper
        # LPs: {{{ 
        Si_1974_0 = 5.4309 #25C
        Si_1974_1 = 5.4309 #157C
        Si_1974_2 = 5.4309 #356 C
        Si_1974_3 = 5.4309 #496C
        Si_1974_4 = 5.4309 #651C
        Si_1974_5 = 5.4309 #813C
        #}}}

        #}}}
        # Literature Temps and LPs (1984 Paper): {{{
        # Temps: {{{
        int_temp = np.array([ # These are the temperatures from the okada paper
            298.5,
            373.5,
            493.1,
            599.2,
            749.9,
            956.5,
            1162.5,
            1311.3,
            1417.3,
            1513.2,
            #371.7,
        ])
        self._temp = list(int_temp-273.15) # Convert to C
        #}}}
        # LPs: {{{
        # Si 0: {{{
        si_0 = np.array([
            5.431018,
            5.431019,
            5.431022,
        ]) # T0
        #}}}
        # Si 1: {{{
        si_1 = np.array([
            5.432119,
            5.432116,
            5.432114,
        ]) # T1
        #}}}
        # Si 2: {{{
        si_2 = np.array([
            5.434320,
            5.434322,
            5.434321,
        ]) # T2
        #}}} 
        # Si 3: {{{
        si_3 = np.array([
            5.436478,
            5.436477,
            5.436480,
        ]) # T3
        #}}}
        # Si 4: {{{
        si_4 = np.array([
            5.43938,
            5.439731,
            5.439734,
        ]) # T4
        #}}} 
        # Si 5: {{{
        si_5 = np.array([
            5.444361,
            5.444361,
            5.444361,
        ]) # T5
        #}}}
        # Si 6: {{{
        si_6 = np.array([
            5.449140,
            5.449138,
            5.449135,
        ]) # T6
        #}}}
        # Si 7: {{{
        si_7 = np.array([
            5.452719,
            5.452718,
            5.452715,
        ]) # T7
        #}}} 
        # Si 8: {{{
        si_8 = np.array([
            5.455279,
            5.455269,
            5.455267,
        ]) # T8
        #}}} 
        # Si 9: {{{
        si_9 = np.array([
            5.457751,
            5.457754,
            5.457745,
        ]) # T9
        #}}}
        # Si 10: {{{
        si_10 = np.array([
            5.432013,
            5.432014,
            5.432012,
        ]) # T10
        #}}} 
        avg_lps = [
            si_0.mean(), #25.35 C
            si_1.mean(), # 100.35C
            si_2.mean(), # 219.95C
            si_3.mean(), # 326.05C
            si_4.mean(), # 476.75C
            si_5.mean(), # 683.35C
            si_6.mean(), # 889.35C
            si_7.mean(), # 1038.15C
            si_8.mean(), # 1144.15C
            si_9.mean(), # 1240.05C
            #si_10.mean(), # 98.55C
        ]
        #}}}
        # acorr: {{{
        self._acorr = [
            5.431074, #25.35 C
            5.432171, # 100.35C
            5.434375, # 219.95C
            5.436533, # 326.05C
            5.439789, # 476.75C
            5.444415, # 683.35C
            5.449192, # 889.35C
            5.452772, # 1038.15C
            5.455326, # 1144.15C
            5.457805, # 1240.05C
        ]
        #}}}
        #}}} 
        # Combined Literature Data: {{{

        self._comb_lit_t = [
            t_1974[0],
            25.350000000000023, #1984
            100.35000000000002, #1984
            t_1974[1],
            219.95000000000005, #1984
            326.05000000000007, #1984
            t_1974[2],
            476.75, #1984
            t_1974[3],
            t_1974[4],
            683.35, #1984
            t_1974[5],
            889.35, #1984
            1038.15, #1984
            1144.15, #1984
            1240.0500000000002, #1984
        ]

        self._comb_lit_si = [
            Si_1974_0, # 25C
            5.431074, #25.35 C
            5.432171, # 100.35C
            Si_1974_1, # 157C
            5.434375, # 219.95C
            5.436533, # 326.05C
            Si_1974_2,# 356C
            5.439789, # 476.75C
            Si_1974_3, #496C
            Si_1974_4, #651C
            5.444415, # 683.35C
            Si_1974_5, #813C
            5.449192, # 889.35C
            5.452772, # 1038.15C
            5.455326, # 1144.15C
            5.457805, # 1240.05C
        ]
        #}}} 
        
    #}}}
    # plot_si_lp_vs_expansion: {{{
    def plot_si_lp_vs_expansion(self):
        ''' 
        This plots the literature Si temperatures and lattice parameters
        as well as the percent expansions
        '''
        fig = make_subplots(
            rows=2, 
            cols=1,
            subplot_titles= ['Average Si Lattice Parameter', 'Percent Expansion of Si Lattice Parameter'],
            shared_xaxes= True,
            vertical_spacing=0.05,
        )
        fig.add_scatter(
            x = self._temp,
            y = self._acorr,
            row = 1,
            col = 1,
        )
        pct_acorr = [(val/self._acorr[0] - 1)*100 for val in self._acorr]
        fig.add_scatter(
            x = self._temp,
            y = pct_acorr,
            row = 2,
            col = 1
        )
        #fig.update_xaxes(title_text = 'Temperature/ deg. C',row = 1, col = 1)
        fig.update_xaxes(title_text = 'Temperature/ deg. C',row = 2, col = 1)
     
        fig.update_yaxes(title_text = 'Avg. Lattice Parameter/'+u'\u212b',row = 1, col = 1)
        fig.update_yaxes(title_text = '% Expansion',row = 2, col = 1)
     
        fig.update_layout(
            #title = 'Avgerage Lattice Parameter for Si',
            #xaxis_title = 'Temperature/ deg. C',
            height = 1500,
            width = 800,
            template = 'simple_white',
            font = dict(
                size = 20
            ),
            showlegend = False,
        )

    #}}}
    # _lit_fit_model: {{{
    def _lit_fit_model(self, lp, c1, c2, c3, c4, c5):
        ''' 
        This is the functional form used to fit the Si calibration data
        '''
        return c1 / (1 + c2 * np.exp(-c3 * lp)) + np.exp(c4*lp) + c5
    #}}}
    # _get_temp_from_lattice_params: {{{
    def _get_temp_from_lattice_params(self, prm, lps = None, temp = None):
        ''' 
        This is a function that creates a model for lmfit to optimize
        '''
        c1 = prm['c1']
        c2 = prm['c2']
        c3 = prm['c3']
        c4 = prm['c4']
        c5 = prm['c5']
        model = self._lit_fit_model(lps, c1, c2, c3, c4, c5)
        residual = temp - model
        return residual
        
    #}}}
    # refine_calibration: {{{
    def refine_calibration(self,):
        ''' 
        This function uses the model functions to create an lmfit model 
        to optimize
        '''
        si_cal_params = Parameters()
        si_cal_params.add('c1', value = 0)
        si_cal_params.add('c2', value = 1)
        si_cal_params.add('c3', value = 0)
        si_cal_params.add('c4', value = 0)
        si_cal_params.add('c5', value = 3)

        x = np.array(self._acorr)
        y = np.array(self._temp)
        out = minimize(self._get_temp_from_lattice_params, si_cal_params, kws = {'lps': x, 'temp': y})
        print(fit_report(out))
        rsq = 1-out.redchi/np.var(y, ddof = 2)
        print(f'R^2: {np.around(rsq, 5)}')
        return out
    #}}}
    # si_cal_model: {{{
    def si_cal_model(self, lps:list = None, out = None):
        '''
        This function takes lattice parameters and 
        a model output. 

        It will use the parameters in the model output to generate 
        a list of temperatures for each lattice parameter given
        '''
        out_vals = out.last_internal_values
        c1 = out_vals[0]
        c2 = out_vals[1]
        c3 = out_vals[2]
        c4 = out_vals[3]
        c5 = out_vals[4]

        y = []
        for lp in lps: 
            y.append(self._lit_fit_model(lp, c1, c2, c3, c4, c5))
        return(y)
        
    #}}}
    # plot_modeled_si_data_vs_actual_data: {{{ 
    def plot_modeled_si_data_vs_actual_data(self, out = None, exp_thermocouple_temps = None, exp_si_lps = None, times = None):
        '''
        This uses the results of the refinement of 
        literature data to give you subplots of 
        1) The fit to the literature data 
        2) Your measured thermocouple data against the temperature calculated by your refined lattice parameters
        '''
        x = np.array(self._acorr) # Literature Si Lp
        y = np.array(self._temp) # Literature Temps
        tc_vs_si_lp_fit = self.si_cal_model(x, out) # Calculate the temperature based on lattice parameters

        fig = make_subplots(
            rows=1, 
            cols=2,
            subplot_titles= ['Modeled Temp vs. Si Lattice Param', 'Experimental Data'],
            shared_yaxes=True
        )
        # Subplot 1: Literature data with Fit: {{{
        # Lit Data: {{{
        fig.add_scatter(
            x = x,
            y = y,
            row = 1,
            col = 1,
            name = 'Literature Si Data'
        )
        #}}} 
        # Fit to the Lit Data: {{{
        fig.add_scatter(
            x = x,
            y = tc_vs_si_lp_fit,
            row=1,
            col=1,
            mode = 'lines',
            line = dict(color = 'red'),
            name = 'Fit Literature Data'
        )
        #}}} 
        #}}} 
        # Experimental data with Fit: {{{

        # Experimental Data: {{{
        fig.add_scatter(
            x = times,
            y = exp_thermocouple_temps,
            mode = 'lines+markers',
            marker=dict(size=8, symbol="diamond", line=dict(width=2, color="DarkSlateGrey")),
            line = dict(color = 'black'),
            name = 'Experimental Tc Data',
            row = 1,
            col = 2
        )
        #}}}
        # Fit Experimental Data: {{{
        fit_tc_vs_time = self.si_cal_model(exp_si_lps, out) # Gives temperatures based on Si LPs
        fig.add_scatter(
            x = times,
            y = fit_tc_vs_time,
            mode = 'lines+markers',
            marker=dict(size=8, symbol="star", line=dict(width=2, color="red")),
            line = dict(color = 'red'),
            name = 'Si LP Converted to T',
            row = 1,
            col = 2,
        )
        #}}} 
        #}}} 
        # Update Layout: {{{
        fig.update_xaxes(title_text = 'Avg. Lattice Parameter/'+u'\u212b',row = 1, col = 1, ticks = 'inside',)
        fig.update_xaxes(title_text = 'Time/min' ,row = 1, col = 2)
     
        fig.update_yaxes(title_text = 'Temperature/'+u'\u2103',row = 1, col = 1, ticks = 'inside',)
        #fig.update_yaxes(title_text = '% Expansion',row = 1, col = 2)
     
        fig.update_layout(
            #title = 'Avgerage Lattice Parameter for Si',
            #xaxis_title = 'Temperature/ deg. C',
            height = 800,
            width = 1200,
            template = 'simple_white',
            font = dict(
                size = 14
            ),
            showlegend = True,
        )
        fig.update_layout(
            xaxis2 = dict(
                #range = [0, 89.65],
                ticks = 'inside',
                mirror = 'allticks',
            ),
            yaxis2 = dict(
                range = [20, 1250],
                ticks = 'inside',
                mirror = 'allticks',
            ),
            xaxis1 = dict(
                mirror = 'allticks',
            ),
            yaxis1 = dict(
                mirror = 'allticks',
            ),
         
        )
        #}}} 
        fig.show()
    #}}}
    # _t_cal_model: {{{
    def _t_cal_model(self,t, a, b, c):
        '''
        This is a model made to fit experimental thermocouple data 
        to calibrated experimental thermocouple data using a fit with refined Si lattice parameters. 
    
        t: this is the temperature
        a, b, c: These are lattice parameters refined
        02/02/2024
        '''
        return a + t/b + t**2/c
    #}}}
    # correct_t: {{{
    def correct_t(
            self,
            t:float = None,
        ):
        '''
        This function was made on 02/02/2024
        It uses the "a_corr" corrected lattice parameter values
        from the Okado (1974) paper
        A function was made to fit those data very well (R^2 ~0.9998)
        That function fit the Si data collected in the beam
        The T from that correction and the thermocouple were plotted and a new function generated
        The final function's parameters and functional form are presented in this function. 
        '''
        a = 8.82662177
        b = 1.70318312
        c = 12164.0983
     
        a_err = 3.45387154
        b_err = 0.03785038
        c_err = 1539.47610
     
        try:
            self.tcalc =  self._t_cal_model(t, a,b, c,)
            self.min_tcalc = self._t_cal_model(t,
                a - a_err,
                b - b_err,
                c - c_err,
            )
            self.max_tcalc = self._t_cal_model(t,
                a + a_err,
                b + b_err,
                c + c_err,
            )
        except:
            print(f'Invalid temp value: {t}... Setting to 0.0')
            self.tcalc = 0
            self.min_tcalc = 0
            self.max_tcalc = 0 
        return self.tcalc
     
    #}}}
#}}}
