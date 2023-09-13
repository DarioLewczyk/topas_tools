# Authorship:{{{
'''
Written by: Dario C. Lewczyk
Purpose:
    To convert .csv files from Yugang GIWAXS
    data to a more-crystallographically useful
    file format like .xy
'''
#}}}
# Imports: {{{
import sys, os
from glob import glob
import tqdm
import numpy as np
import re 
from useful_classes_for_data_analysis import Utils
from utils import get_time
import shutil
#}}}
# FileConvert: {{{
class FileConvert(Utils):
    # __init__: {{{
    def __init__(self,
            fileextension:str = 'csv',
            convertextension:str = 'xy',
            dest_folder:str = None,
            lmb:float = None,
            skiprows:int = 1,
            delim:str = ',',
            ):
        # Initialization of prms: {{{
        self.fileextension = fileextension
        self.convertextension = convertextension
        self.lmb = lmb
        self.skiprows = skiprows
        self.delim = delim
        Utils.__init__(self) # Initialize the utils class here.
        #}}}
        # Navigate to data: {{{
        print(f'Navigate to the directory of the .{self.fileextension} files.\nThese will be automatically converted to .{self.convertextension} files.\n')
        self._data_dir = self.navigate_filesystem()
        #}}} 
        # Navigate and create destination: {{{
        if dest_folder == None:
            t = get_time() 
            t = t.replace(':','-') # Replace the time separator for the saving. 
            dest_folder = f'GIWAXS_Conv_{t}'
        print(f'Navigate to the directory where you want to save the data. A folder will be made with the name: {dest_folder}')
        self._dest = self.navigate_filesystem()
        self._dest_folder = os.path.join(self._dest,dest_folder)
        os.mkdir(self._dest_folder) # make the destination folder
        #}}}
        # scrape files: {{{
        self.scrape_files()
        #}}}
        # convert files: {{{  
        self.convert_files()
        #}}}
    #}}} 
    # scrape_files: {{{
    def scrape_files(self):
        os.chdir(self._data_dir) # Go to the data directory
        self.files = glob(f'*.{self.fileextension}')
    #}}}
    # q_to_tth: {{{
    def q_to_tth(self,q:float = None, lmb:float = None):
        '''
        This takes the q and wavelength in angstroms. 

        You can also input an array and it will return a converted array

        This returns 2theta in degrees
        '''
        tth = 2*np.arcsin((np.abs(q)* lmb)/(4*np.pi))
        return tth * 180/np.pi
    #}}}
    # convert_files:{{{
    def convert_files(self):
        '''
        This function will convert each file scraped from the 
        data directory to the destination directory. 

        If a wavelength is given, it will convert to 2theta
        If not, it will remain as q
        '''
        conv_to_tth = False
        if self.lmb:
            conv_to_tth = True
        os.chdir(self._data_dir) # Change to the data directory
        files = tqdm.tqdm(self.files)
        for i, file in enumerate(files):
            files.set_description_str(f'converting: {file}')
            data = np.loadtxt(file,delimiter=self.delim,skiprows=self.skiprows)
            x = data[:,1] # This is where Q is located
            y = data[:,2] # This is where Intensity is located

            if conv_to_tth:
                x = self.q_to_tth(x,self.lmb) # Convert Q to tth
                firstline = 'tth\ti\n'
            else:
                firstline = 'q_A-1\tiq\n'
            with open(os.path.join(self._dest_folder,file.replace(self.fileextension,self.convertextension)),'w') as f:
                f.write(firstline)
                for i,val in enumerate(x):
                    f.write(f'{val}\t{y[i]}\n')
                f.close()
            
    #}}}

#}}}
# Run{{{ 
if __name__ == '__main__':
    selection = input('Do you want to convert Q to 2theta?\n(type y for yes or n for no, if you just press return, it will count as no)\n')
    if selection.lower() == 'y' or selection.lower() == 'yes':
        wl = input('Type your wavelength (in Angstroms):\n')
        wl = float(wl)
    else:
        wl = None
    FileConvert(lmb = wl,)

#}}}
