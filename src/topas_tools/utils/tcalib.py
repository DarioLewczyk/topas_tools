# Authorship: {{{
# Written By: Dario Lewczyk
# Date: 02-20-2024
#}}}
# Imports: {{{
import numpy as np
#}}}
# TCal: {{{
class TCal:
    '''
    This class allows you to correct thermocouple temperature
    using a calibration curve. 
    '''
    # __init__: {{{
    def __init__(self,):
        pass
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
