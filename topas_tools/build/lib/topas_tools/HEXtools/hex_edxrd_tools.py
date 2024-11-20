# Authorship: {{{
# Written by: Dario Lewczyk
# Date: 03/13/2024
#}}}
# Imports: {{{
import os
from glob import glob
from tqdm import tqdm
import xraydb
import pandas as pd
import numpy as np
import algotom.io.loadersaver as losa
#}}}
# EDXRDTools: {{{
class EDXRDTools:
    '''
    EDXRDTools provides us some utilities 
    that will be useful for importing data from the beamline
    '''
    # __init__: {{{
    def __init__(self,):
        self._i_dat = None
        self._q_dat = None
        self._home = os.getcwd()
        self._bad_strips = [] # Track strips with Q = 0 for all channels
    #}}}
    # write_xys_for_strips: {{{
    def write_xys_for_strips(self,
            save_dir:str = None,
            q_file:str = None,
            i_file:str = None,
            extension:str = 'xy',
            strips:range = range(0, 192),
            mode = 0,
        ):
        '''
        q_file = file path of an q file
        i_file = file path of an i file

        Mode0: Q, I files are made
        Mode1: Channel (B), I files made
        '''
        require_q = True 
        # Check Mode: {{{
        if mode == 0:
            header = '\'Q\tI\n'
            fn = 'QI_strip'
        elif mode == 1:
            header = '\'B\tI\n'
            fn = 'BI_strip'
            require_q = False
        #}}}
        # Image Opener: {{{
        self._i_dat = losa.load_image(i_file)
        if require_q:
            self._q_dat = losa.load_image(q_file)
        #}}}
        # Create the new directory to save the output files:{{{
        if not os.path.isdir(save_dir):
            os.mkdir(save_dir)
        os.chdir(save_dir)
        #}}} 
        # Loop through strips: {{{
        pbar = tqdm(strips, desc = 'Writing strips:')
        for strip in pbar:
            strip_i = self._i_dat[strip] #Give the intensities for all channels of a strip
            with open(f'{fn}_{strip}.{extension}','w') as f:
                f.write(header)
                if require_q: 
                    strip_q = self._q_dat[strip] # Give the q vals for all channels on a strip
                    if np.array(strip_q).all() == np.zeros(len(strip_q)).all():
                        self._bad_strips.append(strip)
                # Add the data to the file: {{{
                for j, i in enumerate(strip_i):
                    if mode == 0:
                        f.write(f'{strip_q[j]}\t{i}\n')
                    elif mode == 1:
                        f.write(f'{j}\t{i}\n')
                #}}}
                f.close()
        #}}} 
        # Inform the user of bad strips: {{{
        if self._bad_strips and require_q:
            print(f'The strips: {self._bad_strips} had Q=0 for all Q vals.')
        #}}}
        os.chdir(self._home)
        
    #}}}
    # write_matrices: {{{ 
    def write_image_matrices(
            self, 
            fn:str = None,
            target:str = 'q', 
            save_dir:str = None,
            extension:str = 'txt', 
        ):
        '''
        Allows you to save a matrix of the Q or I values easily

        target = q or i
        '''
        if save_dir:
            if not os.path.isdir(save_dir):
                os.mkdir(save_dir)
            os.chdir(save_dir)
        if target.lower() == 'q':
            try:
                df = pd.DataFrame(self._q_dat)
            except:
                raise ValueError('q_dat == None!')
        elif target.lower() == 'i':
            try:
                df = pd.DataFrame(self._i_dat)
            except:
                raise ValueError('i_dat == None!')
        else:
            raise ValueError(f'{target} is invalid for "target"')
        df.to_csv(f'{fn}.{extension}', header=False,index=False)
        os.chdir(self._home)
    #}}}
    # get_line_energies: {{{ 
    def get_line_energies(
            self,
            elements:list = None, 
            units:str = 'keV',
            i_threshold:float = 0.01,
            show_data:bool = False,
            save:bool = True,
            fn:str = None,
            extension:str = 'xlsx',
            save_dir:str = None, 
            ):
        '''
        This function leverages the xraydb to get 
        the energies of lines in an X-ray spectrum for that element.
        '''
        # Energy conversion definitions: {{{
        if units.lower() == 'kev':
            en_fac = 1000
        elif units.lower() == 'ev':
            en_fac = 1
        else:
            raise ValueError(f'Units: {units} are invalid!')
        #}}}
        data = []
        row_names = []
        col_names = [f'Energy/{units}','Unnormalized I', 'Normalized I']
        # Get the energies: {{{
        for element in elements:
            for name, line in xraydb.xray_lines(element, 'K').items():
                energy = line.energy / en_fac
                intensity = line.intensity
                if intensity> i_threshold:
                    row_names.append(f'{element}_{name}')
                    data.append([energy,intensity, 0]) #cols will be energy, intensity, norm int
        #}}}
        data = np.asarray(data)
        data[:,2] = data[:,1]/max(data[:,1])
        energy_df = pd.DataFrame(data, index = row_names, columns = col_names)
        # write the file: {{{
        if save:
            if not os.path.isdir(save_dir):
                os.mkdir(save_dir)
            os.chdir(save_dir)
            if extension == 'xlsx' or extension == 'xls':
                with pd.ExcelWriter(f'{fn}.{extension}') as writer:
                    energy_df.to_excel(writer)
            else:
                # both header and index are relevant here.
                energy_df.to_csv(f'{fn}.{extension}', header=True,index=True)  
        #}}}
        os.chdir(self._home)
        if show_data:
            return energy_df
        
    #}}}
#}}}
