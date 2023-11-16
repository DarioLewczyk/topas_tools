# Author: {{{
'''
Dario Lewczyk
Date: 11/16/23
Purpose: Pearson's can output up to 20 CIFS per CIF file 
but this is inconvenient for use with TOPAS and other software.
This will take critical info and auto generate separate cif files
'''
#}}}
# Imports: {{{
import os, sys
import tqdm
import re
from glob import glob
import copy
#}}}
# filename_kwargs: {{{
pcd_kwargs = {
    '_database_code_PCD':r'\d+', # database code is a number
    '_journal_year':r'\d+', # journal year is a number
    '_diffrn_radiation_type':r'\w+\-?\w+\,?\s*\w+\s*\w+', # Filter works to get X-rays, Cu Ka
}
#}}}
# PCDCIFParser: {{{
class PCDCIFParser:
    '''
    Allows you to automatically create 
    CIF files from a single CIF file created 
    from PCD output
    '''
    #  __init__: {{{
    def __init__(self):
        self._home = os.getcwd()
        self._unacceptable_characters = [
                ' ',#space
                ',',#comma
                "'",#apostrophe
                ';',#semicolon
                ':',#colon
                '.',#period
                '?',# question mark
        ]
        self._end_cif_flag = 'End of data set' # This should be the end of cif flag
        self.find_initial_files()
        self.create_output_folder()
        self.create_cifs()
    #}}}
    # find_initial_files:  {{{ 
    def find_initial_files(self,):
        self._cifs = glob('*.cif')
        print(f'{len(self._cifs)} in the directory')

    #}}}
    # create_output_folder: {{{
    def create_output_folder(self,):
        inputting = True
        while inputting:
            folder_name = input('Please type the name of the folder you wish to store these files in:\n')
            if folder_name:
                try:
                    os.chdir(folder_name) # The path exists already
                except:
                    os.mkdir(folder_name) # The path doesnt exist yet
                self._dest = os.path.join(self._home,folder_name) # Make the fullpath of the folder
                inputting = False
        os.chdir(self._home)
    #}}}
    # remove_unacceptable_characters:{{{
    def remove_unacceptable_characters(self,value):
        '''
        There are several characters that are unacceptable for filenames. 
        This function removes them. 
        '''
        for u in self._unacceptable_characters:
            try:
                value = value.replace(u,'_')
            except:
                pass
        return value
    #}}}
    # create_cifs: {{{
    def create_cifs(self,):
        cifs = tqdm.tqdm(self._cifs) # Create a progress bar
        for i, cif in enumerate(cifs):
            cifs.set_description_str(f'Parsing "{cif}"')
            counter = 0 # counter in case duplicate names get made
            cif_counter = 0 # This is the counter for the cif lines dictionary
            
            values = [] # Important values for filename
            self.cif_dict= {
                cif_counter: {
                    'lines': [],
                    'relevant_lines': [],
                }
            } # These are the lines of the cif
            # Open the CIF: {{{
            with open(cif) as f:
                lines = f.readlines() # Lines of the CIF
                stop_writing = False
                found_formula = False
                for j, line in enumerate(lines):
                    # Advance the dictionary entry: {{{
                    if stop_writing:
                        cif_counter += 1 # Advance the count
                        self.cif_dict[cif_counter] = {
                                'lines': [],
                                'relevant_lines': [],
                        }
                        stop_writing = False # Reset this so we write to the new dict
                        found_formula = False # Need a new formula
                    #}}}        
                    # Find the formula: {{{
                    try:
                        if not found_formula:
                            formula = re.findall(r'#\s*(\w+\d*\.?\d*\w*)', line)[1] # should match the formula in the comment region
                            found_formula = True 
                            values.append(self.remove_unacceptable_characters(formula))
                            # record the relevant line: {{{
                            self.cif_dict[cif_counter]['relevant_lines'].append(line)
                            #}}}
                    except:
                        pass
                    #}}}
                    # Parse the keys we care about: {{{
                    for key, regex in pcd_kwargs.items():
                        if key in line:
                            # record the relevant_lines: {{{
                            self.cif_dict[cif_counter]['relevant_lines'].append(line)
                            #}}} 
                            value = None # Safety if nothing matches
                            if key == '_diffrn_radiation_type':
                                # This is an annoying key: 
                                filtered_value = list(filter(None,re.findall(regex,line)))
                                if len(filtered_value) != 2:
                                    filtered_value = list(filter(None,re.findall(r'\S+',line)))
                                value =filtered_value[-1]   
                            else:
                                # Other entries are easy
                                value = re.findall(regex,line) # This gives the value for 
                                value = str(value[0])
                            if value:
                                values.append(self.remove_unacceptable_characters(value))
                    #}}}
                    if self._end_cif_flag not in line:
                        self.cif_dict[cif_counter]['lines'].append(line) # Add all lines
                    else:
                        # Add the values to the dictionary: {{{
                        self.cif_dict[cif_counter].update({'values': copy.deepcopy(values)})
                        values = [] # empty values
                        #}}} 
                        stop_writing = True # Signals progression of cif dictionary
                    
                # Now, make the new files:  {{{
                for i, entry in self.cif_dict.items():
                    lines = entry['lines'] # Recorded lines for the file
                    try:
                        values = entry['values'] # Recorded values for the file for new filename
                    except:
                        values = []
                    newcif = '_'.join(values)+'.cif' # Make the new filename
                    os.chdir(self._dest) # Go to the destination folder
                    if newcif in os.listdir():
                        newcif = '_'.join(values)+f'{counter}.cif'
                        counter += 1
                    with open(newcif,'w') as nc:
                        for newline in lines:
                            nc.write(newline)
                        nc.close() 
                    os.chdir(self._home)
                #}}}     
            f.close()
            os.chdir(self._home) # Return home
            #}}} 
    #}}}
#}}}
# run in script form: {{{
if __name__ == '__main__':
    pcd = PCDCIFParser()

#}}}
