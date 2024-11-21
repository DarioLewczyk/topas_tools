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
        fileextension:str = 'yaml',
        metadata_data:dict = None,
        ):
        if metadata_data == None:
            self.metadata_data = {}
        else:
            self.metadata_data = metadata_data
        md = DataCollector(fileextension=fileextension, metadata_data = self.metadata_data)
        md.scrape_files() # This gives us the yaml files in order in data_dict
        self.metadata = md.file_dict # This is the dictionary with all of the files.
        self.get_metadata(time_key=time_key, temp_key=temp_key)
        
        #os.chdir(self._data_dir) # Returns us to the original directory.
    #}}}
    # get_metadata: {{{
    def get_metadata(
        self,
        time_key:str = 'time:',
        temp_key:str = 'element_temp',
        setpoint_key:str = 'setpoint',
        det_z_key:str = 'Det_1_Z',
        voltage_key:str = 'Voltage_percent'
        ): 
        metadata = tqdm(self.metadata,desc="Working on Metadata")
        for i, key in enumerate(metadata):
            #metadata.set_description_str(f'Working on Metadata {key}:')
            filename = self.metadata[key] # Gives us the filename to read.
            time = None
            temp = None
            setpoint = None
            detector_pos = None
            # Work to parse the data: {{{
            with open(filename,'r') as f:
                lines = f.readlines()
                for j,line in enumerate(lines): 
                    line = line.strip() # This gets a clean line
                    if time_key in line:
                        t = re.findall(r'\d+\.\d+',line) # This gives me the epoch time if it is on a        line.
                        if t:
                            time = float(t[0]) # Gives us the epoch time in float form.   
                    if temp_key in line:
                        temp = np.around(float(re.findall(r'\d+\.\d?',line)[0]) - 273.15, 2) #           This gives us the Celsius temperature of the element thermocouple.  
                    if voltage_key in line:
                        voltage = float(re.findall(r'\d+\.\d+',line)[0])
                    if line.startswith(setpoint_key):
                        setpoint = float(re.findall(r'\d+\.\d?', line)[0])
                    if line == f'{det_z_key}:': 
                        try:
                            value_line = lines[j+2].strip() # This should be: value: ##.##.
                            detector_pos = float(re.findall(r'\d+\.\d+',value_line)[0])
                        except:
                            pass
                        
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
                'pattern_index': i,
                'filename': filename,
            }
            
            #}}}
    #}}}
#}}}

