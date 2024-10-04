# Authorship: {{{
# Written by: Dario C. Lewczyk
# Date: 09-13-2024
#}}}
# imports: {{{ 
import os
from glob import glob
import pandas as pd
import numpy as np
from topas_tools.utils.topas_utils import Utils
from jana_tools.plotting.jana_plotting import JANA_Plot
import re
#}}}
# JANA_Tools: {{{ 
class JANA_Tools(Utils, JANA_Plot):
    # __init__: {{{ 
    def __init__(self, hklm_dir:str = None):
        Utils.__init__(self)
        JANA_Plot.__init__(self)
        # define internal variables: {{{
        self.jana_data = {} # This will store the relevant JANA data for you.
        #}}}
        # Get hklm data from directory: {{{
        if hklm_dir == None or not os.path.isdir(hklm_dir):
            print(f'There is no directory: {hklm_dir}. Navigate to the directory where your .prf files are located')
            hklm_dir = self.navigate_filesystem()
        os.chdir(hklm_dir)
        self.hklm_dir = hklm_dir
        #}}}
    #}}}
    # get_hklm_data: {{{
    def get_hklm_data(self,
            fileextension:str = 'prf', 
            modulated:bool = True, 
            num_cols:int = 17,
            lambda_angstrom:float = 1.540593,
            ):
        '''
        This function searches the directory given for 
        .prf files which are where JANA stores the hklm data
        along with other relevant information
        '''
        prf_files = glob(f'*.{fileextension}')
        self.jana_data['data_files'] = prf_files
        # collect and store the data: {{{
        for i, prf_fn in enumerate(prf_files):
            self.prf_file_parser(prf_fn, i,  modulated, num_cols, lambda_angstrom)
        #}}} 


    #}}}
    # get_pattern_data: {{{
    def get_pattern_data(self, 
            fileextension:str = 'm90',  
            ):
        '''
        This function is used to collect patterns from JANA data files.
        '''
        files = glob(f'*.{fileextension}')
        # Loop through files: {{{
        for i, file in enumerate(files):

            # set the jana_data dictionary: {{{ 
            try:
                self.jana_data[i].update({
                    'pattern':{
                    'header': {},
                    'tth':[],
                    'q': [],
                    'yobs':[],
                    'error':[],
                    }
                })
            except:
                self.jana_data[i] = {
                    'pattern':{
                    'header': {},
                    'tth':[],
                    'q': [],
                    'yobs':[],
                    'error':[],
                    }
                } 

        #}}}
            with open(file, 'r') as f:
                lines = f.readlines()
                for line in lines:
                    clean_line = self._clean_line(line)
                    last_entry = None # This is used to keep a record for updating the dictionary
                    # Loop through the entries in the cleaned line: {{{
                    for j, item in enumerate(clean_line):
                        string, value = self._is_string(item) # string is a bool and value is either an int, string, or float
                        if last_entry:
                            self.jana_data[i]['pattern']['header'][last_entry] = value # Set the paired value
                            last_entry = None
                        if j%2 == 0:
                            if string: 
                                self.jana_data[i]['pattern']['header'][value] = None # Set up to record the paired value
                                last_entry = value
                        if not string:
                            if j == 0:
                                self.jana_data[i]['pattern']['tth'].append(value)
                                # Try to convert tth to q: {{{
                                try:
                                    lam = self.jana_data[i]['pattern']['header']['lambda']
                                    q = self.convert_to_q(value, lam)
                                    self.jana_data[i]['pattern']['q'].append(q)
                                except:
                                    pass
                                #}}}
                            if j == 1:
                                self.jana_data[i]['pattern']['yobs'].append(value)
                            if j == 2:
                                self.jana_data[i]['pattern']['error'].append(value)
                    #}}}
                    


        #}}} 
        
    #}}}
    # prf_file_parser: {{{
    def prf_file_parser(self, 
            prf_fn:str = None, 
            idx:int = 0, 
            modulated:bool = True, 
            num_cols:int = 17,
            lambda_angstrom:float = 1.540593,
            ):
        '''
        This function takes a prf file (prf_fn) and will 
        pull out relevant information from it and drop it into a 
        dictionary and return that dictionary.

        modulated: tell the program to get hklm indices if true
        num_cols: Length of columns in the prf file
        lambda_angstrom: This is used to convert the 2theta into q for direct comparison
                        with other data
        '''
        # Initialize vars: {{{ 
        try:
            self.jana_data[idx].update({
                'hklm_data': {
                    'main': {'peaks': {}},
                    'satellite': {'peaks': {}},
                },
            })
        except:
            self.jana_data[idx] = {
                'hklm_data': {
                    'main': {'peaks': {}},
                    'satellite': {'peaks': {}},
                },
            }
        main_q = []
        main_tth = []
        main_ht = [] # holds strings for hover templates for main reflections
        
        satellite_q = []
        satellite_tth = []
        satellite_ht = [] # holds strings for hover templates for satellite reflections

        main_peaks = 0
        satellite_peaks = 0
        #}}}

        with open(prf_fn) as f:
            lines = f.readlines()
            for line in lines:
                # Split and clean the line: {{{
                clean_line = self._clean_line(line)
                #}}}
                if len(clean_line) == num_cols:
                    # Modulated case: {{{
                    if modulated:
                        h = int(clean_line[0])
                        k = int(clean_line[1])
                        l = int(clean_line[2])
                        m = int(clean_line[3])
                        hklm = f'{h} {k} {l} {m}'

                        fsq = float(clean_line[8])
                        fwhm = float(clean_line[9])
                        tth = float(clean_line[10])

                        d = lambda_angstrom / (2* np.sin(np.pi/180*tth)) # Get d spacing in angstrom
                        q = self.convert_to_q(tth = tth, lambda_angstrom=lambda_angstrom)

                        hklm_ht = '{}<br>hklm: ({})<br>d-spacing: {} {}<br>FSQ: {}<br>FWHM: {}' # format: type, hklm, d-spacing, fsq, fwhm
                        # Handle m=0: {{{
                        if m == 0: 
                            self.jana_data[idx]['hklm_data']['main']['peaks'][main_peaks] = {
                                'hklm': hklm,
                                'h': h,
                                'k': k,
                                'l': l,
                                'm': m,
                                'tth': tth,
                                'q': q,
                                'd-spacing': d,
                                'fsq': fsq,
                                'fwhm': fwhm,

                            }
                            intermediate_hklm_ht = hklm_ht.format('main', hklm, np.around(d,4), self._angstrom, fsq, fwhm)
                            main_peaks += 1
                            main_q.append(q)
                            main_tth.append(tth)
                            main_ht.append(intermediate_hklm_ht)
                        #}}} 
                        # m != 0: {{{
                        elif np.abs(m) > 0: 
                            self.jana_data[idx]['hklm_data']['satellite']['peaks'][satellite_peaks] = {
                                'hklm': hklm,
                                'tth': tth,
                                'h': h,
                                'k': k,
                                'l': l,
                                'm': m,
                                'q': q,
                                'd-spacing': d,
                                'fsq': fsq,
                                'fwhm': fwhm,

                            }
                            intermediate_hklm_ht = hklm_ht.format('satellite', hklm, np.around(d,4), self._angstrom, fsq, fwhm)
                            satellite_peaks+= 1
                            satellite_q.append(q)
                            satellite_tth.append(tth)
                            satellite_ht.append(intermediate_hklm_ht)
                        #}}}
                        
                    #}}} 
                    # Alternate case: {{{
                    else: 
                        print(f'You have elected to use the non-modulated case.\n'+
                        'This feature is not available yet.')
                    #}}}
            # Add tth and q arrays: {{{
            self.jana_data[idx]['hklm_data']['main']['tth'] = np.array(main_tth)
            self.jana_data[idx]['hklm_data']['main']['q'] = np.array(main_q)
            self.jana_data[idx]['hklm_data']['main']['hovertemplate'] = main_ht
            if modulated:
                self.jana_data[idx]['hklm_data']['satellite']['tth'] = np.array(satellite_tth)
                self.jana_data[idx]['hklm_data']['satellite']['q'] = np.array(satellite_q)
                self.jana_data[idx]['hklm_data']['satellite']['hovertemplate'] = satellite_ht
            #}}} 
    #}}}
    # _clean_line{{{ 
    def _clean_line(self, line):
        '''
        JANA's lines are a bit strange because they are delimited by spaces and usually also have 
        extra spaces for no apparent reason

        _clean_line() will allow you to pass a string and get a clean version of that string where only real text/values are retained. 
        '''
        splitline = line.split(' ') # split by spaces
        clean_line = [re.sub(r'\n', '', item) for item in splitline]
        clean_line = [item for item in clean_line if item.strip()] # Gets rid of any special or blank characters
        return clean_line
    #}}}
    # _is_string: {{{
    def _is_string(self, value:str = None):
        '''
        Sometimes it is useful to determine when you encounter a true string in a list 
        or if the string is really a float or int. 
        
        This will return (True, str) if the value is a string
        and (False, value) for other datatypes
        '''
        if isinstance(value, str):
            # integer case: {{{
            try: 
                integer = int(value)
                return(False, integer)
            except ValueError:
                pass
            #}}}
            # Float case: {{{
            try: 
                float_val = float(value)
                return (False, float_val)
            except ValueError:
                pass
            #}}}
            # String: {{{
            return (True, value)
            #}}}
        else:
            return False, value
    #}}}
#}}}
