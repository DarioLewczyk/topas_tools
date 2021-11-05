#Imports{{{
from tqdm import tqdm
from pymatgen.core.structure import Structure
from pymatgen.io.cif import CifWriter
import os
import sys
#}}}
#This is where the inputs are {{{
####################
#
###################
atom_for_replacement = input('______________________________________________________\n'
        'What atom do you want to replace?\n'
        'Default is "V".\n'
        '______________________________________________________\n'
        )
if atom_for_replacement:
    pass
else:
    atom_for_replacement = 'V' #This sets the default atom as V.
##################
#
##################
atom_replacements = input('______________________________________________________\n'
        'What atoms do you want to replace?\n'
        'The default is: "[V, Mo]".\n'
        'Remember, this must be a list\n'
        '______________________________________________________\n'
        )
if atom_replacements:
    pass
else:
    atom_replacements = ['V','Mo']
###################
#
###################
occupancies = input('______________________________________________________\n'
        'What are the occupancies for: {}?\n'.format(atom_replacements)+
        'Default is: "[2/5,3/5]"\n'
        "Type these separated by a comma.\n"
        '______________________________________________________\n'
        )
if occupancies: 
    floats= []
    occupancies = occupancies.split(',') #This makes a list separated by commas. 
    for i in occupancies:
        numbers = i.split('/')
        integers = []
        for j in numbers:
            integers.append(int(j)) 
        floats.append(integers[0]/integers[1])  
    occupancies = floats 
else:
    occupancies = [2/5, 3/5]

#}}}
#Define_Directories{{{
working_dir = os.getcwd() #This is where the cifs are. 
output_dir = working_dir+'/Mixed_Occ_Output' #This defines where the output stuff will be. 
if os.path.isdir(output_dir):
    pass
else:
    os.mkdir(output_dir)
#}}}
#Performing structure modifications. {{{
cif_files = []
for i, f in enumerate(os.listdir()):
    if f.endswith('.cif'):
        cif_files.append(f)
with tqdm(total = len(cif_files),desc='Altering Cif Files') as pbar:
    for i, cif in enumerate(cif_files):
        struct = Structure.from_file(cif) #This makes a pymatgen struct. 
        split_name = cif.split('_') # splits the name by "_"
        split_name.insert(-1,'Mixed_Occupancy') #adds this title component before the number.cif
        name = '_'.join(split_name) #Recombine the name
        species = struct.species 
        for i, site in enumerate(species):
            atom = site.name #This obtains the string of the element. 
            if atom == atom_for_replacement: 
                struct[i] = {atom:occupancies[idx] for idx,atom in enumerate(atom_replacements)}
        os.chdir(output_dir)
        cif_to_write = CifWriter(struct, symprec = 0.01)
        cif_to_write.write_file(name) #writes the file. 
        os.chdir(working_dir)
        pbar.update(1)

#}}}
