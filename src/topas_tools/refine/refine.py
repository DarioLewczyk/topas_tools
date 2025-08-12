# Authorship: {{{
# Written by: Dario Lewczyk
# Date: 02/20/2024
#}}}
# Imports: {{{
import os
import re
import subprocess
import copy

import numpy as np
from shutil import copyfile
from tqdm import tqdm
from topas_tools.utils.topas_utils import Utils, UsefulUnicode, DataCollector
from topas_tools.utils.metadata_parser import MetadataParser
from topas_tools.utils.out_file_parser import OUT_Parser
from topas_tools.utils.file_modifier import FileModifier

#}}}
# TOPAS_Refinements: {{{
class TOPAS_Refinements(Utils, UsefulUnicode, OUT_Parser, FileModifier):
    '''
    This class is designed to refine patterns for use with 
    the TOPAS software package in an automated fashion with the ability 
    to de-convolute refined patterns for use in plotting later. 

    It also allows for the automation of in and out points of phases with thresholds.
    '''
    # __init__: {{{
    def __init__(self,
            topas_version:int = 6,
            fileextension:str = 'xy',  
        ):
        '''
        topas_version: Sets what what number to use when looking for the TOPAS directory. 
        fileextension: sets the fileextension of your datafiles. Typically, ".xy" 
        '''
        # Make attrs based on inputs: {{{ 
        self.topas_dir = 'C:\\TOPAS%s'%topas_version # sets the directory
        self.fileextension= fileextension# This is the extension of your data. 
        #}}}
        # Additional initialization tasks: {{{
        self.current_dir = os.getcwd() # This saves the original location
        Utils.__init__(self)
        UsefulUnicode.__init__(self)
        OUT_Parser.__init__(self)
        FileModifier.__init__(self)
        #GenericPlotter.__init__(self) # Possible we dont need this here. 
        self._data_collected = False # This tracks if the "get_data" function was run
        #self.color_index = 0 # Probably dont need this here either. 
        #}}}
    #}}}
    # refine_pattern: {{{
    def refine_pattern(self, input_file):
        '''
        This performs a Rietveld Refinement using TOPAS. 
        "input_file" is the filename of the input file we are refining 
        '''
        working_dir = os.getcwd()
        refine_cmd = 'tc ' + working_dir + '\\'
        os.chdir(self.topas_dir) # This will change the directory to TOPAS Home
        subprocess.call(refine_cmd + input_file)
        os.chdir(working_dir)
    #}}}
    # run_auto_rietveld: {{{
    def run_auto_rietveld(self,
            refinements:int = 200, 
            time_range:list = None, 
            data_dir:str = None, 
            template_dir:str = None,
            reverse_order:bool = False,
            get_individual_phases:bool = False,
            subtract_bkg:bool = True,
            phases_to_enable:list = None,
            phases_to_disable:list = None,
            threshold_for_on:float = 0.0195, # this can be an Rwp percent deviation or a time.
            threshold_for_off:float = 0.01, 
            on_method:str = 'rwp', 
            off_method:str = 'sf',
            time_error:float = 1.1, 
            on_sf_value:float = 1.0e-5, 
            check_order:bool = False,
            snr_threshold:float = 2.0,
            **kwargs
        ):
        '''
        Expansion of the code written by Adam A Corrao and Gerrard Mattei. 

            1. refinements: number of patterns to refine
            2. time_range: The start and end times (low time, high time) over which you want to refine
            3. data_dir: directory with data files.
            4. template_dir: directory with a template ".inp"
            5. reverse_order: allows you to reverse the order of your refinements
            6. get_individual_phases: Do you want deconvoluted calculated patterns?
            7. subtract_bkg: Do you want to perform background subtraction? Rolling ball method
            8. phases_to_enable: Phase(s) to monitor to enable
            9. phases_to_disable: Phase(s) to monitor to disable
            10. threshold_for_on: Threshold(s) to trigger on
            11. threshold_for_off: Threshold(s) to trigger off (percent of scale factor)
            12. on_method: either "time" or "rwp"
            13. off_method: either 'time' or 'sf'
            14. time_error: if "on_method" is time, how much ±?    
            15. on_sf_value: SF Value(s) for when a phase is enabled.     
            16. check_order: If time recording gets messed up, this will ensure order is set properly
            17. snr_threshold: If you want to filter data that are possible of bad quality use this. Generally a good value is 2. 
        NOTE: both on and off methods can be lists because some phases you may want to treat
        in different ways.

        '''
        debug = kwargs.get('debug',False) # Set this to True if you want to see debugging information. 
        
        off_sf_value = 1.0e-100 # This SF val ensures a phase will stop refining. 
        self.reverse_order = reverse_order  
        # if you input a string for either "phases_to_disable" or "phases_to_enable": {{{
        if type(phases_to_disable) == list or phases_to_disable== None:
            pass
        else:
            phases_to_disable= [phases_to_disable]
        if type(phases_to_enable) == list or phases_to_enable== None:
            pass
        else:
            phases_to_enable= [phases_to_enable] # Make it match the type expected. 
        #}}} 
        # Navigate the Filesystem to the appropriate directories: {{{
        metadata_dir = None # This is none by default but if you want to turn on a phase based on time, you need it. 
        if not data_dir:
            print(f'Navigate to your ".{self.fileextension}" scan file directory.')
            data_dir = self.navigate_filesystem()
        else:
            if not os.path.isdir(data_dir):
                print(f'"{data_dir}" is invalid. Navigate to ".{self.fileextension}" directory.')
                data_dir = self.navigate_filesystem()
        if not template_dir:
            print('Navigate to your ".inp" file template directory.')
            template_dir = self.navigate_filesystem()
        else:
            if not os.path.isdir(template_dir):
                print(f'"{template_dir}" is invalid. Navigate to the ".inp" file  directory.')
                template_dir = self.navigate_filesystem()
        # Handle the metadata if you want to monitor times: {{{
        # Check if you need times: {{{ 
        need_time = False
        if check_order:
            need_time = True
        elif type(on_method) == list or type(off_method) == list:
            if 'time' in on_method or 'time' in off_method:
                need_time = True
        elif type(on_method) == str or type(off_method) == str:
            if on_method == 'time' or off_method == 'time':
                need_time = True
        if time_range:
            need_time = True
            print('need time')
        #}}}
        if need_time:
            # Find the metadata directory: {{{
            metadata_dir = os.path.join(data_dir, 'meta') # metadata should be in your data path + meta
            print(metadata_dir)
            try:
                os.chdir(metadata_dir)
            except: 
                md_valid = os.path.isdir(metadata_dir)
                while not md_valid:
                    print('Navigate to the metadata directory.')
                    metadata_dir = self.navigate_filesystem()
                    try:
                        os.chdir(metadata_dir)
                    except:
                        pass
                
            #}}}
            # get all of the metadata data: {{{ 
            self._md = MetadataParser() # initialize the parser 
            #self._md.get_metadata() # obtain all of the metadata we need
            self.metadata_data = self._md.metadata_data # Store the metadata.
            #}}}
            os.chdir(self.current_dir) # return to the starting directory.
        else:
            self.metadata_data = None
        #}}}
        #}}}
        os.chdir(template_dir) # Go to the directory with the input file
        template_file = '{}.inp'.format(os.path.basename(template_dir))
        template = [line for line in open(template_file)] # This reads the template file
        # Parse the template for important linenumbers: {{{
        xy_out_linenum = None
        txt_out_linenum = None
        my_csv_line = None
        pattern_linenum = None
        phase_hkli_out = []
        phase_hkli_line = []
        for i, line in enumerate(template):
            line = line.strip() # cleans line of unnecessary leading spaces
            if line.startswith('Out_X_Yobs_Ycalc_Ydiff'):
                xy_out_linenum = i 
            if line.startswith('out_prm_vals_on_convergence'):
                txt_out_linenum = i
            if line.startswith('out'):
                # Don't need to look for anything but out by itself. 
                my_csv_line = i
            if line.startswith('xdd'):
                pattern_linenum = i
            if line.startswith('Create_hklm_d_Th2_Ip_file'):
                phase_hkli_out.append(i)
                phase_hkli_line.append(line) # We need to process this line to get the phase name 
        
        #}}}
        # Get the data: {{{
        os.chdir(data_dir) # Go to the directory with the scans
        data = DataCollector(fileextension=self.fileextension) # Initialize the DataCollector
        data.scrape_files() # This collects and orders the files 
        # CHECK THE ORDER OF THE XYs: {{{
        if check_order:
            file_dict = data._resort_with_metadata(file_dict=data.file_dict, metadata_data=self.metadata_data)
            data.file_dict = file_dict
        #}}} 
        data_dict_keys = list(data.file_dict.keys()) # Filename timecodes in order
        os.chdir(template_dir) # Return to the template directory 
        
        rng_start = 1 # This is the initial start for the range
        rng_end = len(data_dict_keys) # This is the initial end for the range.
        if time_range:
            rng_start, rng_end = self._get_time_range(
                    metadata_data=self.metadata_data, 
                    time_range= time_range, 
                    max_idx=rng_end
            ) # Get new range
        tmp_rng = np.linspace(rng_start, rng_end, refinements) # Gives a range over the total number of scans that we want to refine. 
        
        if self.reverse_order:
            tmp_rng = tmp_rng[::-1] # This reverses the order of the array by converting it to a list slice 
        #}}}
        # If user needs to use metadata to order the refinements...: {{{
        if check_order: 
            tmp_rng = data.check_order_against_time(
                    tmp_rng=tmp_rng,
                    data_dict_keys=data_dict_keys, 
                    metadata_data=self.metadata_data
            )
        #}}}
        # Begin the Refinements: {{{
        '''
        This part uses a range made by the selection of the user. 
        Since we don't need to pair the data with the metadata, we should be able to simply reverse the order of the range. 
        ''' 
        
        rng = tqdm([int(fl) for fl in tmp_rng]) # This sets the range of files we want to refine.  

        for index,number in enumerate(rng):     
            file_time = data_dict_keys[number-1]
            xy_filename = data.file_dict[file_time]
            if debug:
                print(f'Number: {number} ')
                print(f'file_time: {file_time}\nxy_filename: {xy_filename}')
            # Get the time (if needed): {{{
            try:
                md_keys = list(self.metadata_data.keys())
                md_entry = self.metadata_data[file_time] # Get the metadata for the current time
                start_time = self.metadata_data[md_keys[0]]['epoch_time'] # This gives us the starting time
                current_epoch_time = md_entry['epoch_time'] # This gives the current epoch time
                time = (current_epoch_time - start_time)/60 # This is in minutes 
            except:
                time = None
            #print(f'File Time: {file_time}\nXY_Filename: {xy_filename}\nTime = {time} minutes')
            #}}} 
            pattern = f'{data_dir}\\{xy_filename}' # Use the custom range we defined. Must subtract 1 to put it in accordance with the index. 
            output = f'result_{data_dict_keys[number-1]}_{str(number).zfill(6)}' # zfill makes sure that we have enough space to record all of the numbers of the index, also use "number" to keep the timestamp. 
            if pattern_linenum:
                template[pattern_linenum] = f'xdd "{pattern}"\n' # write the current pattern
            if xy_out_linenum:
                template[xy_out_linenum] = f'Out_X_Yobs_Ycalc_Ydiff("{output}.xy")\n'
            if txt_out_linenum:
                template[txt_out_linenum] = f'out_prm_vals_on_convergence "{output}.txt"\n' # I am making this a text file since I manually output csv files. This would overwrite those.
            if my_csv_line: 
                template[my_csv_line] = f'out "{output}.csv"\n'

            
            if phase_hkli_out:
                for phase_i, line_idx in enumerate(phase_hkli_out):
                    # We need to use Re to get the phase ID
                    lne = phase_hkli_line[phase_i]
                    fn_str = lne.split('(') [-1] # This takes whatever is written in the text field
                    found = re.findall(r'(\w+\d?)*',fn_str)[0] # This will give all of the text you put for the filename. 
                    split_hkli_fn = found.split('_')
                    formula = []
                    for word in split_hkli_fn:
                        if word != 'result':
                            formula.append(word)
                        else:
                            break
                    #formula = found.split('_')[0]
                    formula = '_'.join(formula) 
                    template[line_idx] = f'\tCreate_hklm_d_Th2_Ip_file({formula}_{output}.hkli)\n'

            # Use the Dummy.inp file: {{{
            with open('Dummy.inp','w') as dummy:
                for line in template:
                    dummy.write(line) 
            # Check the quality of the diffraction pattern first: {{{
            skip_refinement = False
            if snr_threshold != None:
                xdat, ydat = self._load_raw_xy(xy_filename, data_dir) # This gets you the pattern data and also returns you to the same directory
                snr = self.calculate_snr(ydat)
                if snr > snr_threshold:
                    print(f'Your SNR threshold of: {snr_threshold} triggered to prevent \npattern: "{xy_filename}" from being refined')
                    skip_refinement = True 
            #}}} 
            if not skip_refinement:
                self.refine_pattern('Dummy.inp') # Run the actual refinement
                # Monitor Refinement Parameters: {{{
                '''
                If you want to monitor scale factor values, it MUST
                happen before the Dummy file is copied to a new file. 
    
                Likewise, if you want a phase to be added...
    
                Both will be handled with the same function.
                '''
                out = 'Dummy.out' # This is the name of the file we are looking for.
                if phases_to_disable != None or phases_to_enable != None:   
                    self._modify_out_for_monitoring(
                            out=out, 
                            on_phases=phases_to_enable,
                            off_phases=phases_to_disable,
                            threshold_for_on=threshold_for_on,
                            threshold_for_off=threshold_for_off,
                            current_idx=index,
                            off_sf_value=off_sf_value,
                            on_sf_value=on_sf_value,
                            on_method = on_method, # This is to tell if we are working with times or not
                            off_method = off_method, # This tells whether to look for times of scale factors
                            current_time = time, # This is either a time or None
                            debug=debug,
                            time_error=time_error, # This is the +/- the time can be off to trigger the turning on of a phase.
                        )
    
                 
                #}}}
                copyfile(out,f'{output}.out')
                template = [line for line in open(out)] # Make the new template the output of the last refinement. 
                #}}}
                # Get the single phase patterns: {{{ 
                if get_individual_phases:
                    self._calculate_phase_from_out(out = f'{output}.out',subtract_bkg=subtract_bkg)
                #}}}
        #}}}
    #}}}
    # _get_line_info: {{{
    def _get_line_info(self,string:str, index:int = 0, mode = 0, return_re_list:bool = False):
        '''
        This gives us a parameter by name. 
        By default, it will give any combination of letters and numbers with separations
        use the index to select where the desired prm falls when you use re
     
        mode = 0: gets parameter names and names for substances with separation by "_"
        mode = 1: gets numerical values.
        mode = 2: This will only give word keys.
        '''
        conv_float = False
        if mode == 0:
            res = r'\w+[\d+\w+]' # This should give any parameter name
        elif mode == 1:
            res = r'\d+\.?\d+?e\-?\d+|\d+\.?e\-?\d+|\d+\.?\d*' # This should be able to get us any value and not just basic floats. 
            conv_float = True
        elif mode == 2:
            res = r'\S+'
        lst = re.findall(res,string)
        try:
            result = lst[index]
            if conv_float:
                result = float(result)
        except:
            raise ValueError(f'index: {index} is invalid for the regular expressions:\n{lst}')
        if return_re_list:
            return lst
        else:
            return result

    #}}} 
    # _calculate_phase_from_out: {{{
    def _calculate_phase_from_out(
            self,
            out:str = None,
            str_end:str = "Create_hklm_d_Th2_Ip_file",
            xy_out_prefix:str = 'result',
            iters:int = 0, 
            subtract_bkg:bool = True
        ):
        '''
        This function will take the .out file generated by TOPAS and 
        will parse through the file gathering: 
            1. the heading information (changing iterations to 1)
            2. the lines for each phase omitting the line: "Create_hklm_d_Th2_Ip_file" (change this if your strs end with something else.)
            3. the output lines (for the xy file)
        for the output file given as "out"

        This function also creates an input file with only background terms and instrumental profile stuff
        By default, the program removes all background terms from the phase outputs. 
        '''
        # Parse the OUT file: {{{ 
        with open(out) as f: 
            inp_dict = {'phases': {}} # This will hold all of the relevant information for the inp.
            phase_lines = [] # This will hold the lines needed to reconstruct the phase pattern
            header_lines = [] # This will hold the header lines.
            phase_num = 0 # This is the counter for the phases in you inp
            lines = f.readlines()
            keep_reading = False # This will inform the program that the first str has been reached
            header_done = False # This informs the program that the header has been completed. 
            symbol = None
            for i, lne in enumerate(lines):
                line = copy.deepcopy(lne) # Need to preserve the original line
                # Handle header lines: {{{
                if not header_done and 'str' not in line and 'iters' not in line:
                    header_lines.append(line)
                if 'iters' in line:
                    line = f'iters {iters}\n' # Redefine the line to be one iteration
                    header_lines.append(line)
                #}}}
                # Statements to map phases: {{{
                # Create_hklm_d_Th2_Ip_file line: {{{
                if 'Create_hklm_d_Th2_Ip_file' in line:
                    inp_dict['phases'][phase_num].update({
                        'end':i-1, # This keeps the hkli file from being overwritten
                        'phase_lines':copy.deepcopy(phase_lines),
                    })
                    keep_reading=False
                    phase_lines.clear() # Reset the list
                    phase_num+=1 # Move to the next phase
                #}}}
                # str line: {{{
                splitline = line.strip('\t\n') # if we get rid of these modifiers, we can check if str starts the line
                if splitline.startswith('str'):
                    if not keep_reading:
                        pass # We don't need to do anything. It is the first phase. 
                    inp_dict['phases'][phase_num] = {
                        'start': i, # This is the line the str starts on. 
                    }
                    keep_reading = True # Tells the program to keep reading lines.
                    header_done=True
                #}}}
                # phase_name line: {{{
                if 'phase_name' in line:  
                    symbol = re.findall(r'(\w+\d?)+',line)[-1]
                    test = re.findall(r"(\w+\d?)+",line) 
                    try:
                        inp_dict['phases'][phase_num].update({
                            'symbol':symbol,
                        })  
                    except:
                        pass
                    
                #}}}
                # Keep reading: {{{
                if keep_reading: 
                    if symbol: 
                        bare_line = copy.deepcopy(line).strip('\t\n') 
                        bare_line_no_comments = bare_line.split("'")[0] # remove all comments
                        bare_line_no_comments = bare_line_no_comments.replace('@','')
                        # Check for a mismatched key for lattice parameters: {{{
                        split_bareline = bare_line_no_comments.split(' ')
                        if split_bareline[0] in ['a','b','c','al','be','ga']:
                            split_bareline = self._get_line_info(bare_line_no_comments, mode = 2, return_re_list = True)
                            if split_bareline[1] == '=':
                                test_str = '_'.join(split_bareline[2].split('_')[0:2])
                                if test_str != symbol:
                                    #print(split_bareline)
                                    #print(line)
                                    try:
                                        value = float(self._get_line_info(split_bareline[3], index=0, mode=1)) 
                                    except:
                                        value = float(0)

                                    line = f'\t{split_bareline[0]}\t{value}'
                                    #print(f'{symbol}: {split_bareline[0]} = {value} ')
                            #}}}
                    phase_lines.append(line) # This adds the line to the list which will be added to a dict. 
                #}}}
                #}}}
                # Handle Output: {{{
                if 'Out_X_Yobs_Ycalc_Ydiff' in line: 
                    inp_dict['out'] = {'start':i,'line':line} # This tells the program which line the xy output is on.
                #}}} 
                # INP DICT WORKS HERE...
            inp_dict['header'] = header_lines 
        #print(f'inp_dict after: {inp_dict["phases"]}') # FAILED
        #}}}
        # Loop through the structures: {{{ 
        for phase in inp_dict['phases']:  
            inp_file = []
            entry = inp_dict['phases'][phase] 
            substance = entry['symbol'] 
            phase_lines = entry['phase_lines']
            header = inp_dict['header'] 
            output = inp_dict['out']['line'].replace('result',substance)
            output_line = inp_dict['out']['start']
            for line in header:
                if subtract_bkg:
                    if 'bkg' not in line and 'One_on_X' not in line:
                        # Only add a line from the header if it is not a background term. 
                        inp_file.append(line)
                else:  
                    inp_file.append(line)
            for line in phase_lines:
                inp_file.append(line)
            inp_file.append(output)
            # Use the Dummy.inp file: {{{
            with open('Dummy_PS.inp','w') as dummy:
                for line in inp_file:
                    dummy.write(line)
                dummy.close()
            self.refine_pattern('Dummy_PS.inp') # Run the actual refinement
            #copyfile('Dummy.out',f'{output}.out')
            #template = [line for line in open('Dummy.out')] # Make the new template the output of the last refinement. 
        #}}}
        # Make a BKG xy file: {{{
        bkg_inp = []
        for line in header:
            bkg_inp.append(line) 
        output = inp_dict['out']['line'].replace('result','bkg')
        bkg_inp.append(output) # Make an output file with "bkg" as the xy name
        #print(output)
        #print(bkg_inp)
        # Use the dummy.inp; {{{
        with open('Dummy_PS.inp','w') as dummy:
            for line in bkg_inp:
                dummy.write(line)
            dummy.close()
            self.refine_pattern('Dummy_PS.inp') # Run the actual refinement.
        #}}}
        #}}}
        #}}}
    #}}}
#}}}

