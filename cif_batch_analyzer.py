#Imports{{{
import os
from pymatgen.core.structure import Structure
from pymatgen.io.cif import CifWriter
import numpy as np
import crystal_toolkit
import math as mth
import matplotlib.pyplot as plt
from pymatgen.analysis.chemenv.utils.coordination_geometry_utils import vectorsToMatrix
from pymatgen.electronic_structure.plotter import plot_lattice_vectors
from pymatgen.core import Lattice
from pymatgen.core.surface import SlabGenerator
from pymatgen.io.cif import CifWriter
import pandas as pd
from pymatgen.symmetry.analyzer import SpacegroupAnalyzer
from collections import Counter
#}}}
#BatchAnalyzer{{{
class BatchAnalyzer:
    def __init__(self, doc_list:list):
        self.doc_list = doc_list #This is initializing. 
    #Document Dictionary Creator{{{
    '''
    This function takes a list of filenames. 
    It is assumed that: 
        1. Your filename contains a .cif extension
        2. Your filename is separated by '_'
        3. Your filename contains an index starting with 0 as the last thing before the extension. 
    '''
    def doc_dict_creator(self):
        self.doc_dict = {} #This is the dictionary where the information is written. 
        for i,name in enumerate(self.doc_list):
            if name.endswith('.cif'):
                no_cif = name.strip('.cif') #This will remove the extension from the name
                split_name = no_cif.split('_') #This makes a list of words from the filename
                self.doc_dict[int(split_name[-1])] = name # This creates a dict entry with the number of the file being read so it can be parsed through in order.  
    #}}}
    #Symmetry Analyzer{{{
    '''
    This function requires a dictionary of filenames to be presented. 
    It is necessary that the filenames are in the directory you are working out of. 
    It is also necessary that the files are all .cif files so that pymatgen can read them. 
    '''
    def symmetry_analyzer(self, wyckoff_cutoff = 40): 
        self.wyckoff_cutoff = wyckoff_cutoff
        self.results = {}
        cols = []
        for i,file in enumerate(self.doc_dict):
            filename = self.doc_dict[i]
            cols.append(filename.strip('.cif'))
            struct = Structure.from_file(filename)
            analyzed_struct = SpacegroupAnalyzer(struct) # This will analyze the symmetry of the structure. 
            '''
            Here we are extracting important parameters that we need. 
            '''
            symmetrized_struct = analyzed_struct.get_symmetrized_structure() 
            counter_object = Counter(symmetrized_struct.as_dict()['equivalent_positions']) #Allows us to count equiv positions
            unique_sites = counter_object.keys() #Creates a list of all the unique sites. 
            num_unique_sites = len(unique_sites) #This counts all of the unique sites.
            abc = struct.lattice.abc
            angles = struct.lattice.angles
            wyck = symmetrized_struct.wyckoff_symbols# This function will create a list of symbols
            self.results[filename.strip('.cif')] = {'structure':symmetrized_struct, 
                                                        'a': abc[0], 
                                                        'b': abc[1], 
                                                        'c': abc[2], 
                                                        'alpha': angles[0], 
                                                        'beta': angles[1],
                                                        'gamma':angles[2],
                                                        'volume': struct.lattice.volume,
                                                        'space group': struct.get_space_group_info()[0],
                                                        'unique sites': num_unique_sites 
                                                        }
            if len(wyck) <= self.wyckoff_cutoff:  
                for idx, symbol in enumerate(wyck):
                    pos = idx+1
                    self.results[filename.strip('.cif')]['wyckoff symbol {}'.format(pos)] = symbol #This will make as many entries as necessary for the wyckoff symbols.  
    #}}}
    #Table Generator{{{
    def table_generator(self): 
        self.results_dict = self.results
        self.files_with_wyckoff = {} #Make a dictionary to store files with wyckoff symbols
    
        self.df_with_wyckoff = pd.DataFrame(self.results_dict).drop('structure')
        self.cols_to_drop = []
        for i, column_name in enumerate(self.df_with_wyckoff.T.columns):
            if column_name.startswith('wyckoff'):
                self.cols_to_drop.append(column_name)
            else:
                pass

        for i,name in enumerate(self.results_dict):
            for i2,col in enumerate(self.cols_to_drop):
                if col in self.results_dict[name]:
                    self.files_with_wyckoff[i] = self.results_dict[name] #This adds each file containing wyck to a dictionary. 

        self.df = self.df_with_wyckoff.drop(self.cols_to_drop)#This generates the dataframe with samples as cols. But removes wyckoff
        #self.df = self.df.drop(labels=['structure'])#This redefines df as a dataframe without structure since it is a waste of space.
        self.df_no_unique_sites = self.df.drop(labels = ['unique sites']) #This generates another table without unique sites.
        self.df_transposed = self.df.T #Puts names as rows 
        self.df_transposed_no_us = self.df_no_unique_sites.T #Puts names as rows.
        self.space_group_table = pd.DataFrame(self.df_transposed['space group'].value_counts())#This creates the space group count table.
        self.unique_sites_table = pd.DataFrame(self.df_transposed['unique sites'].value_counts())#Thic creates the unique site count table.  

        self.all_counts = self.df_transposed_no_us.apply(pd.Series.value_counts)
        self.all_counts.fillna('',inplace=True)
    def table_dictionary_generator(self, labels_to_remove_from_df=['a','b','c','alpha','beta','gamma','volume']):
        self.labels_to_remove_from_df = labels_to_remove_from_df
        '''
        This function serves to generate a dictionary full of tables that provide easy-to-read
        information.
        ''' 
        self.df_cleaned = self.df.drop(labels_to_remove_from_df) #This will remove the columns of data in the original dataset.
        self.df_transposed_cleaned = self.df_cleaned.T #transposes the table as before. 

        self.df_wyckoff_cleaned= self.df_with_wyckoff.drop(labels_to_remove_from_df)#This cleans up the wyckoff table 
        #self.df_wyckoff_cleaned.fillna('',inplace=True)
        self.df_wyckoff_cleaned_transposed = self.df_wyckoff_cleaned.T #transposes it

        self.unique_sites_dict = {} #This dictionary does not care about the wyckoff sites
        self.unique_sites_dict_with_wyckoff = {} #This dictionary cares about wyckoff sites. 

        self.cols_dict = {} #This houses the columns to be dropped so there aren't extraneous columns. 
        self.columns_count = {} #keeps track of columns so that the excel sheet can be made. 
        self.rows_count = {} #keeps track of the cols so that excel sheet can be made.
        '''
        This is the dictionary that cares about wyckoff sites. 
        '''
        for i, unique_sites in enumerate(self.unique_sites_table.to_dict()['unique sites']):
            if int(unique_sites) <= self.wyckoff_cutoff:  
                cols_to_drop = [] #This is a temporary variable that gets added to the cols_dict. 
                for i2, col_name in enumerate(self.df_wyckoff_cleaned_transposed.columns):
                    if col_name.startswith('wyckoff'):
                        column_split = col_name.split(' ')#This makes a list of strings. 
                        column_number = int(column_split[-1]) #The last string in the list is always a number. 
                        if column_number > unique_sites:
                            cols_to_drop.append(col_name)
                    self.cols_dict[unique_sites] = cols_to_drop #This makes it so that when we reach the unique sites number, the program knows how many cols to drop. 
                temp_table = self.df_wyckoff_cleaned_transposed.copy() #Protects this table by making a tmp
                dropped = temp_table.drop(columns=self.cols_dict[unique_sites]) #the temp table has extraneous cols dropped
                self.columns_count[i] = len(dropped.columns)+1 #adds the length of the columns. +1 since doesnt count the first column
                
                self.unique_sites_dict_with_wyckoff[i] =dropped[dropped['unique sites'] == unique_sites] 
                self.rows_count[i] = len(self.unique_sites_dict_with_wyckoff[i].index)+1 # adds the length of rows +1.
            else:
                self.unique_sites_dict_with_wyckoff[i] = self.df_transposed_cleaned[self.df_transposed_cleaned['unique sites'] == unique_sites]
                self.columns_count[i] = len(self.df_transposed_cleaned.columns)+1 #adds the length of the columns. Again, doesnt count the first column. 
                self.rows_count[i] = len(self.unique_sites_dict_with_wyckoff[i].index) +1 #adds the length of the rows +1
        '''
        This dictionary does not care about wyckoff sites. 
        '''
        for i, unique_sites in enumerate(self.unique_sites_table.to_dict()['unique sites']):
            self.unique_sites_dict[i] = self.df_transposed_cleaned[self.df_transposed_cleaned['unique sites'] == unique_sites] 

    #}}}
    #}}}


