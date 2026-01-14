# Authorship: {{{ 
# Written by Dario Lewczyk
# Date: 02-20-2024
#}}}
# Imports: {{{
import re
import numpy as np
from tqdm import tqdm
from topas_tools.utils.topas_utils import DataCollector
#}}}
# MetadataParser: {{{
class MetadataParser:
    '''
    This class is used to parse the metadata files generated
    at the 28-ID-1 beamline at NSLS-II

    Though it is specifically built for that beamline, minor modifications should
    allow it to be used for other beamlines.
    '''
    # __init__{{{
    def __init__(
        self, 
        time_key:str = 'time:',
        temp_key:str = 'element_temp',
        setpoint_key:str = 'setpoint',
        det_z_key:str = 'Det_1_Z',
        fileextension:str = 'yaml',
        voltage_key:str = 'Voltage_percent',
        metadata_data:dict = None,
        mode = 0,
        ):
        if metadata_data == None:
            self.metadata_data = {}
        else:
            self.metadata_data = metadata_data
        md = DataCollector(fileextension=fileextension, metadata_data = self.metadata_data, mode = mode)
        md.scrape_files() # This gives us the yaml files in order in data_dict
        self.metadata = md.file_dict # This is the dictionary with all of the files.
        try:
            self.get_metadata(time_key=time_key, temp_key=temp_key, setpoint_key=setpoint_key, det_z_key=det_z_key, voltage_key=voltage_key) 
        except:
            print('Failed to get metadata')
        try:
            self._sort_metadata_by_epoch_time() # Sort the metadata 
        except:
            print('Failed to sort by epoch time')
        try:
            self._calculate_time_from_start_of_run() # Get the corrected times.
        except:
            print('Failed to calculate corrected times')
        
        #os.chdir(self._data_dir) # Returns us to the original directory.
    #}}}
    # get_metadata: {{{
    def get_metadata(
        self,
        time_key:str = 'time:',
        temp_key:str = 'element_temp',
        setpoint_key:str = 'setpoint',
        det_z_key:str = 'Det_1_Z',
        voltage_key:str = 'Voltage_percent',
        exposure_key:str = 'sp_computed_exposure',
        frame_num_key:str = 'sp_num_frames',
        time_per_frame_key:str = 'sp_time_per_frame',
        ): 
        metadata = tqdm(self.metadata,desc="Working on Metadata")
        for i, key in enumerate(metadata):
            #metadata.set_description_str(f'Working on Metadata {key}:')
            filename = self.metadata[key] # Gives us the filename to read.
            time = None
            temp = None
            voltage = None
            setpoint = None
            detector_pos = None
            exposure_time = None
            num_frames = None
            subframe_exposure = None
            # Work to parse the data: {{{
            with open(filename,'r') as f:
                lines = f.readlines()
                for j,line in enumerate(lines): 
                    line = line.strip() # This gets a clean line
                    splitline  = line.split(' ')
                    # Time Determination: {{{
                    if time_key in line:
                        t = re.findall(r'\d+\.\d+',line) # This gives me the epoch time if it is on a        line.
                        if t:
                            time = float(t[0]) # Gives us the epoch time in float form.   
                    #}}}
                    # Temp Determination: {{{
                    if temp_key in line:
                        temp = np.around(float(re.findall(r'\d+\.\d?',line)[0]) - 273.15, 2) #           This gives us the Celsius temperature of the element thermocouple.  
                    #}}}
                    # Voltage (deprecated for MTF Because we use PID): {{{
                    if voltage_key in line:
                        voltage = float(re.findall(r'\d+\.\d+',line)[0])
                    #}}}
                    # Setpoint: {{{
                    if line.startswith(setpoint_key):
                        setpoint = float(re.findall(r'\d+\.\d?', line)[0])
                    #}}}
                    # Detector Position: {{{
                    if line == f'{det_z_key}:': 
                        try:
                            value_line = lines[j+2].strip() # This should be: value: ##.##.
                            detector_pos = float(re.findall(r'\d+\.\d+',value_line)[0])
                        except:
                            pass
                    #}}}
                    # Exposure Related Parameters: {{{
                    if exposure_key in line:
                        try:
                            exposure_time = float(re.findall(r'\d+\.\d?', line)[0])
                        except:
                            try:
                                exposure_time = float(splitline[-1])
                            except:
                                exposure_time = 0
                    if frame_num_key in line:
                        try:
                            num_frames = float(re.findall(r'\d+\.\d?', line)[0])
                        except:
                            try:
                                num_frames = float(splitline[-1])
                            except:
                                num_frames = 0

                    if time_per_frame_key in line:
                        try:
                            subframe_exposure = float(re.findall(r'\d+\.\d?', line)[0])
                        except:
                            try:
                                subframe_exposure = float(splitline[-1])
                            except:
                                subframe_exposure = 0
                    #}}}
                        
                f.close() 
            #}}}
            # Update Metadata Dictionary Entry: {{{
            self.metadata_data[key] = {
                'readable_time': int(key),
                'epoch_time': time,
                'temperature': temp,
                'setpoint': setpoint,
                'pct_voltage': voltage,
                'detector_z_pos': detector_pos,
                'exposure_time': exposure_time,
                'num_subframes': num_frames,
                'subframe_exposure':subframe_exposure,
                'pattern_index': i,
                'filename': filename,
            } 
            #}}}
    #}}}
    # _sort_metadata_by_epoch_time: {{{
    def _sort_metadata_by_epoch_time(self,):
        # sort the metadata dictionary by epoch time: {{{ 
        sorted_metadata = sorted(self.metadata_data.items(), key = lambda item: item[1]['epoch_time']) 
        # Convert the sorted list of tuples back to a dictionary 
        self.metadata_data = {k: v for k,v in sorted_metadata}  
        #}}}
    #}}}
    # _calculate_time_from_start_of_run: {{{
    def _calculate_time_from_start_of_run(self,):
        ''' 
        This function will automatically go through and calculate 
        the difference in time from the initial time at which the run 
        was started in seconds. 
        
        This time will be recorded as "corrected_time"
        '''
        t0 = None # epoch time of first point.
        for  i, (key, entry) in enumerate(self.metadata_data.items()):
            epoch_time = entry['epoch_time'] # Current epoch time
            if t0 == None:
                t0 = epoch_time
            present_time_s = epoch_time - t0 # This gives the exact time difference
            self.metadata_data[key].update({'corrected_time': present_time_s})
    #}}}
#}}}

