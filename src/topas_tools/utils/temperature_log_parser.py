# Authorship: {{{ 
# Written by: Dario C. Lewczyk
# Date: 11-13-24
# Purpose: Parse the temperature logs created at the beamline for the MTF V3+
#}}}
# Imports: {{{
from topas_tools.utils.topas_utils import DataCollector
import numpy as np
#}}}
# MTFLogParser: {{{
class MTFLogParser(DataCollector):
    # __init__: {{{
    def __init__(self, file_dict:dict = {}):
        if file_dict != {}:
            self.file_dict = file_dict
        else:
            DataCollector.__init__(self, fileextension = 'csv', mode = 1)
            self.scrape_files()
        self.mtf_temp_logs = {} # This will hold all the information we care about for each file
        self.parse_mtf_temperature_logs()
    #}}}
    # parse_mtf_temperature_logs: {{{
    def parse_mtf_temperature_logs(self,):
        '''
        This assumes that the file dictionary you give is 
        in the form of a generally indexed dictionary of filenames.

        It also assumes the order of parameters:
        1. time
        2. temperature_c
        3. temperature_d
        4. delta_t
        5. setpoint
        6. kp
        7. ki
        8. kd
        '''
        for i, fn in self.file_dict.items():
            data = np.loadtxt(fn, skiprows=1, delimiter=',')
            time = data[:,0]
            tc = data[:,1]
            td = data[:,2]
            delta_t = data[:,3]
            sp = data[:,4]
            kp = data[:,5]
            ki = data[:,6]
            kd = data[:,7]
            self.mtf_temp_logs[i] = {
                    'filename': fn,
                    'time':time,
                    'temperature_c': tc,
                    'temperature_d':td,
                    'delta_t':delta_t,
                    'setpoint':sp,
                    'kp':kp,
                    'ki':ki,
                    'kd':kd,
            }
    #}}}
#}}}
