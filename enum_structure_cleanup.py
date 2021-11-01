#Imports{{{
import os
import sys
import time
from tqdm import tqdm
from pymatgen.core.structure import Structure
from pymatgen.io.cif import CifWriter
from pymatgen.core.periodic_table import Specie
import numpy as np
#}}}
#Directory Choice Module{{{
dir_list = os.listdir() # This function will return a list of all directories.
directory = input('Please write the absolute path of the enumeration output file.: \n'
        'If you want to use the current directory, enter "0".\n'
        'or press "q" to quit. \n'
        '------------------------------------------------------------------------ \n'
        )
if directory == 'q':
    print('You have successfully quit. No changes have been made.')
    sys.exit()
elif directory == False:
    print('Please write your directory name')
elif directory == '0':
    dir_dict = {}
    print('i | Directory Name\n_____________________________________________________')
    for i, dir_name in enumerate(dir_list): 
        if os.path.isdir(dir_name):
            print('\n{} | {}\n_____________________________________________________'.format(i,dir_name))
            dir_dict[i] = dir_name #This adds the directory names into a dictionary
    dir_num = input('Please type the number of the directory where your files are.\n'
            '------------------------------------------------------------------------ \n'
            )
    dir_int = int(dir_num) #This casts the string from the above as an integer.
    directory = os.path.abspath(dir_dict[dir_int]) #This provides the absolute path for the folder specified above
    os.chdir(directory)
elif directory:
    os.chdir(directory)
#}}}
#Inputs for function params{{{
#############################
# Atom for Removal
#############################
atom_for_removal = input('What atom should be removed by this program? (Default is Pb): \n'
        '------------------------------------------------------------- \n')
if atom_for_removal:
   atom_for_removal = atom_for_removal 
else:
    atom_for_removal = 'Pb'
#print('You selected {} for removal. Input type: {}'.format(atom_for_removal,type(atom_for_removal)))
#############################
# Atom for Replacement
#############################
atom_for_replacement = input('What atom do you want to have replaced? (Default is Fe): \n'
        'If you do not want to replace an atom, input: "0". \n'
        'If you want to replace multiple atoms, input: "1".\n'
        '------------------------------------------------------------ \n')
##########################
# Atom explicitly assigned
##########################
if atom_for_replacement != '0' and atom_for_replacement != '1' and atom_for_replacement != '':
    atom_for_replacement = atom_for_replacement
#########################
# If we want to assign
# multiple atoms to 
# replace
#########################
elif atom_for_replacement == '1': 
    atoms_for_replacement = input('Please type the atoms to replace, separated by: ",".\n'
            '------------------------------------------------------------ \n')
    atoms_for_replacement =atoms_for_replacement.split(',')
########################
# This is the default
#######################
elif atom_for_replacement == '':
    atom_for_replacement = 'Fe'
########################
# This will not replace 
# Any atom. 
#######################
elif atom_for_replacement == "0":
    atom_for_replacement = ''
   
#print('You selected {} for replacement. Input type: {}'.format(atom_for_replacement,type(atom_for_replacement)))

if atom_for_replacement:
    if atom_for_replacement != '1':
        replacement = input('What atom should {} be replaced with? \n------------------------------------------------------------ \n'.format(atom_for_replacement)) 
        print('---------------------------------------------------- \n') 
    elif atom_for_replacement == '1':
        replacement = input('What atom should these atoms:\n{}\nbe replaced with? \n------------------------------------------------------------ \n'.format(atoms_for_replacement)) 
        print('---------------------------------------------------- \n') 
else: 
    replacement = ''
#print(replacement,type(replacement))
symprec_choice = input('Do you want to require symmetry when saving the .cif files?\n'
        'y / n\n'
        'Default choice is ("n").\n'
        '------------------------------------------------------------ \n')
if symprec_choice == 'y': 
    print('I see you selected yes')
    symprec_value = input('What precision do you want to use?\n'
            'Default value is: 0.01\n'
            '------------------------------------------------------------ \n')
    if symprec_value == '': 
        symprec_value = 0.01
    else: 
        symprec_value = float(symprec_value) 

elif symprec_choice == '': 
    symprec_choice = 'n'
#}}}
#Function to do replacement/removal of sites. {{{
cif_files = []
for filename in os.listdir():
    if filename.endswith('.cif'):
        #print(filename)
        cif_files.append(filename)
with tqdm(total=len(cif_files)) as pbar:
    for filename in os.listdir():
        if filename.endswith('.cif'):
            no_cif_name = filename.strip('.cif') #Removes .cif from this name
            split_name = no_cif_name.split('_') #Splits the name into a list by the delimeter
            nums = [2,2] #creates a list of 1 to iterate over to remove words from filenames
            for i in nums:
                split_name.pop(i)#removes the extraneous words
            split_name.insert(1,'Fixed') 
            short_name = '_'.join(split_name)#This puts the name in the form: 'Li7RuO6_SG2_#'
            #print(short_name)
 
            struct = Structure.from_file(filename)#this reads the current cif file
            #print(struct)
            ###
            #Removing all of the Pb and Fe
            ###
            orig_len = len(struct.species) #this is the original length to compensate for loss of positions.
            #print('The number of species in the structure is: {}'.format(orig_len))
            for i, species in enumerate(struct.species):
                corrected_i = i #This is here to ensure that the correct index is removed or replaced since the list of positions will shorten as the code loops.
                #print('Current species = {}. Species for removal: {}. Species for Replacement: {}'.format(species, atom_for_removal, atom_for_replacement))
                if species.name == atom_for_removal or species.name == atom_for_replacement or atom_for_replacement == '1':
                    #print('We made it through the species check')
                    '''
                    Corrected_i accounts for the fact that the number of species changes as
                    Pb is removed, so the index needs to adapt in real time.
                    '''
                    corrected_i = i - (orig_len - len(struct.species)) #This corrects the index to land us on the right element of the positions list.
                    #print(corrected_i)
                    if species.name == atom_for_removal:
                        #print('{} is at position: {} in file: {}'.format(struct.species[corrected_i].name,corrected_i, short_name))
                        #print('{} is being removed. Its position was: {}'.format(struct.species[corrected_i].name,corrected_i))
                        struct.pop(corrected_i) #This will remove the target atoms from the structure
                    elif species.name == atom_for_replacement:
                        #print('{} is at position: {} in file: {}'.format(struct.species[corrected_i].name,  corrected_i, short_name))
                        #print('{} is being replaced. Its position was: {}'.format(struct.species[corrected_i].name, corrected_i))
                        struct.replace(corrected_i,replacement) #This will replace the Fe atoms with Li0+ atoms
                        #print(struct)
                    if atom_for_replacement == '1':
                        #print('Starting to replace the following atoms: {}'.format(atoms_for_replacement))
                        for i, atom in enumerate(atoms_for_replacement):
                            if atom == species.name:
                                struct.replace(corrected_i, replacement)
                        
#}}}
# Writing the file/ Creating output directory {{{
            dir_name = 'Fixed_Output' #This is going to be the directory that we are going to put the corrected cifs into. 
            '''
            The symprec choice basically 
            tells us if we need to account for symmetry 
            when saving the cif file or not. 
            This is important to note. 
            '''
            if symprec_choice == 'y':
                cif = CifWriter(struct,symprec=symprec_value)
            elif symprec_choice == 'n':
                cif = CifWriter(struct) 
            if os.path.isdir(dir_name):
                pass 
            else:
                os.mkdir(dir_name)
            
            cif.write_file(dir_name+'/'+short_name + '.cif')
        pbar.update(1)
    
#}}}
