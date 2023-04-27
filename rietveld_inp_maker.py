#Authorship{{{
'''
This is a small program to generate input files for a large number of .cif files. 
This is not yet modularized so you have to go through and modify parameters as necessary. 
You must also have templates available (unless you want to use string formatting to generate the whole file).

Created by: Dario Lewczyk
Date: 10-25-21
V: 1.0.0
'''
#}}}
#Imports{{{
import os, subprocess
import shutil
import sys
import pandas as pd
import matplotlib.pyplot as plt
from tqdm import tqdm
from pymatgen.core.structure import Structure
from pymatgen.core.periodic_table import Specie
from pymatgen.symmetry.analyzer import SpacegroupAnalyzer# This helps us to read the equiv sites in cifs.
import numpy as np
import re #This is essential to avoid potential TOPAS errors due to charged species
from fractions import Fraction # This allows us to have more control over what the fraction converter gives us. 
#}}}
#Defining the directories we need.{{{
'''
python_tools_dir = the directory where this script is. 

khalifah_research = the directory where all of the enumeration cifs will be enclosed in. 

working_dir = directory where this script is called. 

template_inp_directory =  where you have your templates saved. 
    ##################################################
    Remember that you must save your template inp files
    as: 
        "top_template.inp"
        "bottom_template.inp"
    If this is going to work in a modular fashion. 
    ##################################################

cif_directory =  where you have your .cif files saved. 
'''
python_tools_dir = os.path.dirname(os.path.realpath(__file__)) #This grabs the location of this script. 
working_dir = os.getcwd() #lists the current directory.
#Locating My Research Folder{{{
path = python_tools_dir.split('/') #This splits the path to python_tools up. 
throw_away = path.pop(-1) #This gets rid of the python_tools folder. 
khalifah_research = '/'.join(path) #This re-assembles the path to the enclosing folder. 
#}}}
#Obtaining the template_inp_directory {{{
os.chdir(python_tools_dir) #This allows us to see all of the folders of template files are. 
os.system('clear') #Clears the output to make your eye go easier to the selections.
folders = []
for folder in os.listdir():
    if os.path.isdir(folder):
        folders.append(folder)
for i,folder in enumerate(folders):
    print('______________________________________________\n{} | {}\n'.format(i,folder))
folder_selection = input('______________________________________________\n'
    'Where are your template .inp files?\n'
    'Please type the number of your selection\n'
    '______________________________________________\n' 
    )
if folder_selection:
    number = int(folder_selection)
    template_inp_directory = python_tools_dir+'/'+folders[number] #This defines the template_inp_directory.
    print(template_inp_directory)
    os.chdir(working_dir) 
else:
    print('No Selection... Exiting.')
    sys.exit()
os.system('clear') #This clears the output
#}}}
#Choosing where the cif_directory is.{{{
############################
# Select where you want to
# Start from.
# Options are the 'Research' folder found above.
# Or the 'working directory'
############################
os.system('clear')
cif_dir_choice = input('______________________________________________\n'
        'Where do you want to work from to find the .cif files?\n'
        '0 | {}\n'.format(khalifah_research)+
        '1 | {}\n'.format(working_dir)+
        'Default is 0\n'
        '______________________________________________\n'
        )
if cif_dir_choice == str(1):
    cif_dir_choice = working_dir
    os.chdir(working_dir) #You choose to go into the current working directory to search for the cif files.
    #print('working directory')
elif cif_dir_choice == str(0) or cif_dir_choice == '':
    cif_dir_choice = khalifah_research
    os.chdir(khalifah_research) #This goes back to the research folder. 
    #print('khalifah research')
os.system('clear')
choosing_cif_folder = True
next_folder = cif_dir_choice #################### This houses the next folder in. 
while choosing_cif_folder == True:
    folders = []
    for folder in os.listdir():
        if os.path.isdir(folder):
            folders.append(folder)
    for i, folder in enumerate(folders):
        print('______________________________________________\n{} | {}\n'.format(i,folder))
    folder_selection = input('______________________________________________\n'
        'Where are your .cif files?\n'
        'Please type the number of your selection\n'
        'Or type: "b" to go back a folder\n'
        '______________________________________________\n' 
        )
    if folder_selection:
        if folder_selection.isdigit():
            number = int(folder_selection)
            folder_selection = folders[number] #This grabs the correct folder
            current_selection = next_folder+'/'+folder_selection #This defines the new folder we are looking at. 
            os.system('clear')###### clears the output
        else: 
            previous = next_folder.split('/')
            previous.pop(-1)
            current_selection = '/'.join(previous)
            os.system('clear') 
            ###################
            # Is this the right
            # folder?
            ##################
        yes_or_no = input('______________________________________________\n' 
            'Is this the correct folder?\n'
            '{}\n'.format(current_selection)+
            'y/(n)\n'
            '______________________________________________\n' 
            )
        if yes_or_no == 'y':
            cif_directory= current_selection
            os.chdir(cif_directory) #Puts us into  the excel directory.
            choosing_cif_folder= False #should break the loop.  
            #break
        else:
            next_folder = current_selection
            os.chdir(next_folder)
    else:
        exit = input('______________________________________________\n' 
                'Do you want to exit?\n'
                'y / (n)\n'
                '______________________________________________\n' 
                )
        if exit == 'y':
            sys.exit()
        else:
            pass

    os.system('clear') #Clears print statements

#}}}
#Diagnostic tools to check all directories. {{{
#print('python_tools: {}'.format(python_tools_dir))
#print('working_dir: {}'.format(working_dir))
#print('Khalifah_Research_Group: {}'.format(khalifah_research))
#print('template_inp_directory: {}'.format(template_inp_directory))
#print('cif_directory: {}'.format(cif_directory))
#sys.exit()
#}}}
#}}}
#Do you want to refine the lattice? {{{
os.system('clear')
refine_lattice = input('______________________________________________\n'
        'Do you want to refine the lattice parameters?\n'
        '[y] / n\n'
        '______________________________________________\n'
        )
if refine_lattice == 'n':
    refine_lattice == False
else: 
    refine_lattice == True
#}}}
#Do you want to refine site positions (xyz)?{{{
os.system('clear')
refine_xyz = input('______________________________________________\n'
        'Do you want to allow x,y,z to refine?\n'
        'y / (n)\n'
        '______________________________________________\n'
        )
if refine_xyz == 'y':
    refine_xyz = True
else:
    refine_xyz = False
os.system('clear') #clears the output
#}}}
# excel_file_fullpath (If you want to use an excel file for your starting point){{{
excel_file_present = False #This tells the system there is no excel file to reference.
refine_lattice = True
if refine_xyz == False:
    excel_file_template = input('______________________________________________\n'
            'Do you want to use an excel file template?\n'
            'y / (n)\n'
            '______________________________________________\n'
            )
    if excel_file_template == 'y':
        excel_file_template == True
    else:
        excel_file_template == False
if refine_xyz or excel_file_template:
    excel_reference = input('______________________________________________\n'
            'Do you have an excel file from the previous refinement?\n'
            '(y) / n\n'
            '______________________________________________\n'
            )
    os.system('clear')
    if excel_reference == 'n':
        pass
    else:
        ####################
        # Now the program 
        # knows you have an
        # excel file to work 
        # from
        ####################
        excel_file_present = True
        os.chdir(working_dir) #This sends us back to the directory where the program was called.
        searching_for_file = True
        next_folder = os.getcwd() #Stores the selection from the loops
        excel_directory = '' #This will store the directory where the excel file is.
        while searching_for_file == True:
            os.system('clear')
            folders = []
            for folder in os.listdir():
                if os.path.isdir(folder):
                    folders.append(folder)
            for i, folder in enumerate(folders):
                print('______________________________________________\n{} | {}\n'.format(i,folder))
            
            folder_selection = input('______________________________________________\n'
                'Where is your .xlsx file?\n'
                'Please type the number of your selection\n'
                'If it is back a folder, type: "b".\n'
                '______________________________________________\n' 
                )
            if folder_selection:
                if folder_selection.isdigit():
                    number = int(folder_selection) #Checks to see if this string is a number 
                    folder_selection = folders[number] #This changes the folder to the selected one.
                    current_selection = next_folder+'/'+folder_selection #This makes the full path of the new folder
                    os.system('clear') #clear output
                else:
                    previous_dir = next_folder.split('/') #Splits the path by dividing line.
                    previous_dir.pop(-1) #This gets rid of the folder you were in from the directory name.
                    current_selection= '/'.join(previous_dir) #Recombines the path into the proper name.
                ###################
                # Is this the right
                # folder?
                ##################
                yes_or_no = input('______________________________________________\n' 
                    'Is this the correct folder?\n'
                    '{}\n'.format(current_selection)+
                    'y/(n)\n'
                    '______________________________________________\n' 
                    )
                if yes_or_no == 'y':
                    excel_directory = current_selection
                    os.chdir(excel_directory) #Puts us into  the excel directory.
                    searching_for_file = False #should break the loop.  
                    #break
                else:
                    next_folder = current_selection
                    os.chdir(next_folder)
                    #This makes it so that we always keep advancing into the next folder. 
            else:
                exit = input('______________________________________________\n No Valid Selection made.\n Exit? y / (n)\n______________________________________________\n')
                if exit:
                    sys.exit()
                else:
                    pass
        os.system('clear') #Clears the output
        files = os.listdir()
        for i, filename in enumerate(files):
            print('______________________________________________\n{} | {}\n'.format(i,filename))
        file_selection = input('______________________________________________\n'
                'Please type the number of your selection\n'
                '______________________________________________\n' 
                ) 
        if file_selection.isdigit():
            number = int(file_selection)
            excel_file = files[number]
        else:
            sys.exit()
        excel_file_fullpath = excel_directory+'/'+excel_file #This gives us the full path of the excel file
        print('Excel_file_dir:\n{}'.format(excel_file_fullpath))
        os.system('clear')
if excel_file_present:
    full_df = pd.read_excel(excel_file_fullpath) #This imports the excel file.
    ref_lat = input('______________________________________________\n'
            'Do you want to allow the lattice to refine?\n'
            'y/(n)\n'
            '______________________________________________\n')
    if ref_lat == 'y':
        refine_lattice = True
    else:
        refine_lattice = False
#}}}
#b_value_refinement{{{
######################
# Do you want to 
# refine b-values?
######################
b_value_refinement = input('______________________________________________\n'
        'Do you want to refine b-values?\n'
        'y / (n)\n'
        '______________________________________________\n'
        )
refine_lattice_and_b = False
if b_value_refinement == 'y':
    b_value_refinement = True
    if refine_lattice == False:
        ref_lattice = input('______________________________________________\n'
                'Do you want to refine the lattice parameters?\n'
                'y / (n)\n'
                '______________________________________________\n'
                )
        if ref_lattice == 'y':
            refine_lattice = True
        else:
            pass
    else:
        pass
else:
    b_value_refinement = False
os.system('clear')
#}}}
#Making the lists of lines from the inp templates Also getting symmetry info{{{
os.chdir(template_inp_directory)
bvo_inp_top_half = open('top_template.inp')
bvo_inp_bottom_half = open('bottom_template.inp')

#This reads the lines of the templates to prepare for saving to the new file. 
bvo_inp_top_lines = bvo_inp_top_half.readlines() 
bvo_inp_bottom_lines = bvo_inp_bottom_half.readlines()
#}}}
#Making the Inp files{{{
cif_files = {}

os.chdir(working_dir) ################################# WORKING DIRECTORY
output_dir = os.getcwd()+'/inp_files'
if os.path.isdir(output_dir):
    #If the directory exists, this clears all the inp files from it. 
    os.chdir(output_dir)
    output_directory = os.getcwd() ######################## OUTPUT DIRECTORY DEFINED
    dir_contents = os.listdir() #######
    #for f in dir_contents:
        #if f.endswith('.inp'):
            #path = os.path.join(output_directory,f)
            #print('{} was removed'.format(path)) 
            #os.remove(path)
    os.chdir(working_dir) ############################# RE-ENTER WORKING DIRECTORY
    shutil.rmtree(output_directory)
    os.mkdir(output_dir)
else:
    os.mkdir(output_dir)
os.chdir(cif_directory) ############################## CIF DIRECTORY
filenumbers = []
for filename in os.listdir():
    if filename.endswith('.cif'):
        number = int(filename.strip('.cif').split('_')[-1]) #Make sure we can sort through these one by one so the excel sheet matches up
        filenumbers.append(number)
        cif_files[number] = filename
filenumbers.sort() #This gives us the numbers present in case we dont have a complete set of cifs.
#print(cif_files)
#print(filenumbers)
with tqdm(total=len(cif_files)) as pbar:
    for i, placeholder in enumerate(cif_files):
        i = filenumbers[i]
        cif_file = cif_files[i]
        inp_name = cif_file.replace('.cif','.inp') # This makes the inp file name the same as the cif name. 
        cur_struct = Structure.from_file(cif_file) #make a structure object. 
        no_cif_name = cif_file.strip('.cif')
        ######################
        # Obtaining the full
        # symmetry of this 
        # structure
        ######################
        #Symmetry Variables{{{
        space_group_analyzer = SpacegroupAnalyzer(cur_struct) #makes a space group Analyzer instance for the current structure. 
        symmetrized_struct = space_group_analyzer.get_symmetrized_structure() #This makes a new variable with the symmetry data
        symmetry_dataset = space_group_analyzer.get_symmetry_dataset() #This gives a dictionary with all the symmetry information.
        equivalent_atoms = symmetry_dataset['equivalent_atoms'] #Gives a list of equivalent atoms. (the exact length of all of the sites)
        crystal_system = space_group_analyzer.get_crystal_system().capitalize() #This gives us a capitalized name of the crystal system. 
        wyckoff_letters = symmetry_dataset['wyckoffs'] #This gives the wyck symbols of everything.
        wyckoff_numbers = symmetry_dataset['site_symmetry_symbols'] #This gets the associated number
        wyckoffs = [] #This will house all of the completed wyckoff symbols
        for wyck_i, letter in enumerate(wyckoff_letters):
            wyckoff = '{}_{}'.format(letter ,wyckoff_numbers[wyck_i]) #formats to look like: mult_letter_symbol
            wyckoffs.append(wyckoff) 
        axis_choice = symmetry_dataset['choice'] #This tells us where the program decided to reference in the crystal.
        #}}}
        '''
        This is the section where we write the input files automatically into a directory labeled "inp_files"
        Some notes:
            - Because of the way that TOPAS likes to see structures, a loop with an if else statement exists to remediate any issues with charges. 
            - Since there is no file with the name that we are naming our file, we have to put the "open" command into write mode with the "w" flag.
            - This is currently set up for outputting .xy files that are simulated diffraction patterns. 
        '''
        ############################
        # Defining the templates for 
        # feeding lattice params
        # to TOPAS.
        ############################
        #Lattice Param Templates{{{
        #Triclinic has no symmetry requirements. {{{

        triclinic = (
                    '\t \t'+'a {r} {a}'+'\n'
                    '\t \t'+'b {r} {b}'+'\n'
                    '\t \t'+'c {r} {c}'+'\n'

                    '\t \t'+'al {r} {al}'+'\n'
                    '\t \t'+'be {r} {be}'+'\n'
                    '\t \t'+'ga {r} {ga}'+'\n'

                    '\t \t'+'volume {r} {vol}'+'\n'
            )
        #}}}
        #Monoclinic: beta is not 90. {{{
        monoclinic = (
                    '\t \t'+'a {r} {a}'+'\n'
                    '\t \t'+'b {r} {b}'+'\n'
                    '\t \t'+'c {r} {c}'+'\n'

                    '\t \t'+'al  {al}'+'\n'
                    '\t \t'+'be {r} {be}'+'\n'
                    '\t \t'+'ga  {ga}'+'\n'

                    '\t \t'+'volume {r} {vol}'+'\n'
            )
        #}}}
        #Orthorhombic: al = be = ga = 90{{{
        orthorhombic = (
                    '\t \t'+'a {r} {a}'+'\n'
                    '\t \t'+'b {r} {b}'+'\n'
                    '\t \t'+'c {r} {c}'+'\n'

                    '\t \t'+'al  {al}'+'\n'
                    '\t \t'+'be  {be}'+'\n'
                    '\t \t'+'ga  {ga}'+'\n'

                    '\t \t'+'volume {r} {vol}'+'\n'
            )
        #}}}
        #Tetragonal: a = b != c, al=be=ga=90{{{
        tetragonal = (
                '\t\tTetragonal({r} {a}, {r} {c})\n'
                )
        #}}}
        #Hexagonal: a=b!=c, al = be= 90, ga = 120{{{
        hexagonal = (
                '\t\tHexagonal({r} {a}, {r} {c})\n'
                )
        #}}}
        #Rhombohedral or trigonal: a=b=c, al = be = ga != 90{{{
        rhombohedral = (
                '\t\tRhombohedral({r} {a}, {r} {al})\n'
                )
        #}}}
        #Cubic: a=b=c, al=be=ga=90{{{
        cubic = (
                '\t\tCubic({r} {a})\n'
            )
        #}}}
        #}}}
        ############ Lattice Params
        #Lattice parameters {{{
        if excel_file_present:
            #Reads the data from the previous refinement.
            #Can check to see if it is working by uncommenting the below. This has been checked and works.
            #print('The current i index is: {}\n The current filename is: {}\n The excel filename is: {}\n####################'.format(i,cif_file,full_df.filename[i]))
            a = full_df.a[i]
            b = full_df.b[i]
            c = full_df.c[i]
            al = full_df.alpha[i]
            be = full_df.beta[i]
            ga = full_df.gamma[i]
            vol = full_df.volume[i] 
            space_group = full_df['space group'][i]
        else:
            a = cur_struct.lattice.a
            b = cur_struct.lattice.b
            c = cur_struct.lattice.c
            al = cur_struct.lattice.alpha
            be = cur_struct.lattice.beta
            ga = cur_struct.lattice.gamma
            vol = cur_struct.lattice.volume
            space_group = cur_struct.get_space_group_info(symprec=0.01, angle_tolerance=5.0)[0]
        #####################################
        # Redefining lattice parameters for 
        # the purposes of fixing everything
        # to the same lattice constraints. 
        #####################################
        #a = 16.5352467
        #b = 11.6728038
        #c = 11.6990003
        #al = 90
        #be = 134.8779
        #ga = 90
        #vol = 1600.08650
        ####################################
        #}}}
        b_value_v = 0.2365
        b_value_bi = 0.559
        
        with open(output_dir+'/'+inp_name,'w') as inp_file:
            for line in bvo_inp_top_lines:
                inp_file.write(line) #This copies the lines present in the template.
            ## Now we need to add the structure. 
            # I am making this so that it uses TOPAS formatting to make sure we are not refining too much. 
            #####################
            # Can insert @ to 
            # Refine Parts of 
            # This model. 
            #####################
            #########################
            # These parts do not 
            # change regardless of 
            # crystal system. 
            #########################
            inp_file.write('\t\'This is the reference direction choice: {}\n'.format(axis_choice)+'\tstr\n' 
                    '\t\tspace_group \"{}\"'.format(space_group)+'\n' 
                    '\t\tscale @ 1.68165115e-005\n'
                    )
            # Crystal System Definition{{{ 
            #################
            # Check to see
            # if an excel file
            # was loaded. 
            # if so, the lattice
            # should be fixed.
            #################
            if excel_file_present:
                if refine_lattice:
                    r = '@' #Ensures the lattice is refined.
                else:
                    r = '' #This makes sure that the lattice is not refined.
            else:
                #This else statement is for when you have b-value refinement or neither b-value refinement nor xyz refinement.
                if b_value_refinement:
                    #This allows us the determine whether or not we want to refine the a,b,c when we refine b-values
                    if refine_lattice:
                        #This allows us to refine lattice parameters for the final refinement.
                        r = '@'
                    else: 
                        # Otherwise, we don't refine the lattice parameters.
                        r = ''
                else:
                    if refine_lattice:
                        r = '@' #This sets the refinement tag.
                    else:
                        r = '' #This makes sure we don't refine. 
            #Triclinic{{{
            if crystal_system == 'Triclinic':
                inp_file.write(triclinic.format(
                    a = a,
                    b = b,
                    c = c,
                    al = al,
                    be = be,
                    ga = ga,
                    vol =vol,
                    r = r
                    ))
            #}}}
            #Monoclinic {{{
            elif crystal_system == 'Monoclinic':
                inp_file.write(monoclinic.format(
                    a=a,
                    b=b,
                    c=c,
                    al=al,
                    be=be,
                    ga=ga,
                    vol=vol,
                    r = r
                    ))
            #}}}
            #Orthorhombic{{{
            elif crystal_system == 'Orthorhombic':
                inp_file.write(orthorhombic.format(
                    a=a,
                    b=b,
                    c=c,
                    al=al,
                    be=be,
                    ga=ga,
                    vol=vol,
                    r = r
                    ))
            #}}}
            #Tetragonal {{{
            elif crystal_system == 'Tetragonal':
                inp_file.write(tetragonal.format(
                    a = a,
                    c = c,
                    r=r
                    ))
            #}}}
            #Hexagonal{{{
            elif crystal_system == 'Hexagonal':
                inp_file.write(hexagonal.format(
                    a=a,
                    c=c,
                    r=r
                    ))
            #}}}
            #Rhombohedral/Trigonal{{{
            elif crystal_system == 'Rhombohedral' or crystal_system == 'Trigonal':
                inp_file.write(rhombohedral.format(
                    a=a,
                    al=al,
                    r=r
                    ))
            #}}}
            #Cubic{{{
            elif crystal_system == 'Cubic':
                inp_file.write(cubic.format(
                    a=a,
                    r=r
                    ))
            #}}}

            #}}}

            for i, site in enumerate(cur_struct.sites):
                ######################
                # Specie dict is 
                # defined here in such
                # a way that the dictionary 
                # will work whether or not 
                # there are more than 1 
                # atoms on each site. 
                ######################
                specie_dict = site.species.as_dict()

                #This if statement is required to filter those species with no specified charge.
                #These lines are not necessary.
                #TOPAS does not like seeing charges.
                if len(specie_dict) == 4:
                    ch = '+{charge:.0f}'.format(charge=specie_dict['oxidation_state'])
                else:
                    ch = ''
                ##################
                # I have modified this
                # so that the method is 
                # robust against having
                # multiple atoms within 
                # a site. 
                #######################################
                #Mixed occ atom 1 preserves the previous 
                # atom through the next loop so that if there are 
                # More than one atom on a site, so that they refine together
                #######################################
                mixed_occ_atom_number_1 = '' #This is blank but will be updated later
                for j, entry in enumerate(specie_dict):
                    ############################
                    # The species is the "entry"
                    # variable. 
                    # The occu value is the other 
                    # value within the specie dict 
                    # entry for the atom. 
                    # We also need to add in 
                    # B values here using the term: "beq"
                    ###########################
                    atom_name = re.sub(r'[\W\d]','',entry) #This searches to see if there is a charged atom and removes the charge so it doesn't mess TOPAS up.
                    
                    #Refine Atomic Position setup{{{
                    if j == 0:
                        mixed_occ_atom_number_1 = atom_name
                    elif j>1:
                        pass
                    refine_atomic_x = '{}{}_x'.format(mixed_occ_atom_number_1,i)
                    refine_atomic_y = '{}{}_y'.format(mixed_occ_atom_number_1,i)
                    refine_atomic_z = '{}{}_z'.format(mixed_occ_atom_number_1,i)
                    
                    #}}}
                    # B- Value Stuff {{{
                    b_value = 1 #We are going to set all b values as 1. I can make this change as I see fit later. 
                    if b_value_refinement:
                        ref_b = '{}{}_b'.format(mixed_occ_atom_number_1,i)
                    else: 
                        ref_b = '' #This defines the b value refinement variable
                    if atom_name == 'Bi':
                        b_value = b_value_bi 
                    elif atom_name == 'V' or atom_name == 'Mo':
                        b_value = b_value_v
                    elif atom_name == 'O':
                        #Ensures that the b values arent refined
                        ref_b = ''
                    #}}}
                    #TOPAS Text variable (Writes each atomic site) {{{
                    topas_site_text = "\t\tsite {specie}{num} \tnum_posns {num_posns} \tx {ref_x} {x:0.8f} \ty {ref_y} {y:0.8f} \tz {ref_z} {z:0.8f} \tocc {species} {occu} \tbeq {ref_b} {beq} \t'Wyckoff: {mult}_{wyckoff}\n"
                    #}}}
                    #x,y,z positions{{{
                    x = site.frac_coords[0]
                    y = site.frac_coords[1]
                    z = site.frac_coords[2] 
                    #}}}
                    # Here we are checking if x,y,z can be refined.{{{
                    '''
                    The Fraction module does the same thing as 
                        'float.as_integer_ratio'
                    But we are using the "limit_denominator" function 
                    to keep us from always getting really big numbers for fractions that are
                    close enough to an integer fraction. 
                    '''
                    fract_x = Fraction(float(x)).limit_denominator(100).as_integer_ratio()
                    fract_y = Fraction(float(y)).limit_denominator(100).as_integer_ratio()
                    fract_z = Fraction(float(z)).limit_denominator(100).as_integer_ratio()
                    #should x,y,z be refined? {{{
                    for integer in fract_x:
                        if len(str(integer)) == 1:
                            #x divisible by a single integer
                            #x should be fixed
                            refine_x = False
                        else:
                            #x refinable
                            refine_x = True
                         
                    for integer in fract_y:
                        if len(str(integer)) == 1:
                            # y is divisible by a single integer
                            # y should be fixed
                            refine_y = False
                        else:
                            #y is refinable
                            refine_y = True
                    for integer in fract_z:
                        if len(str(integer)) == 1:
                            #z is divisible by a single integer
                            # z should be fixed
                            refine_z = False
                        else:
                            #z is a refinable
                            refine_z = True
                    #}}}
                    ##############################
                    # Check for refinability
                    ##############################
                    #What happens when x,y,z are refined or not refined?{{{
                    if refine_x:
                        #print('REFINING X')
                        #print(refine_atomic_x)
                        if refine_xyz:
                            pass
                        else:
                            ref = refine_atomic_x
                            refine_atomic_x = '' #Makes this blank so it wont refine
                    else:
                        #print('FIXING X')
                        refine_atomic_x = '' #Makes this blank so it wont refine
                        #print(refine_atomic_x)
                    if refine_y:
                        #print('REFINING Y')
                        #print(refine_atomic_y)
                        if refine_xyz:
                            pass
                        else:
                            ref = refine_atomic_y
                            refine_atomic_y = '' #Makes this blank so it wont refine
                    else:
                        #print('FIXING Y')
                        refine_atomic_y = ''#Makes this blank so it wont refine
                        #print(refine_atomic_y)
                    if refine_z:
                        #print('REFINING Z')
                        #print(refine_atomic_z)
                        if refine_xyz: 
                            pass
                        else:
                            ref = refine_atomic_z
                            refine_atomic_z = '' #Makes this blank so it doesn't refine.
                    else:
                        #print('FIXING Z')
                        refine_atomic_z = '' #Makes this blank so it wont refine
                        #print(refine_atomic_z)
                    #}}}
                    #}}}
                    ##########################
                    # Here, we are filtering
                    # out the equivalent 
                    # sites
                    ######################### 
                    if i == equivalent_atoms[i]:
                        count_equiv_sites = np.count_nonzero(equivalent_atoms==i) #This gives us the count of the equivalent sites.
                        inp_file.write(topas_site_text.format(specie = atom_name,
                            num = i,
                            num_posns = count_equiv_sites,
                            ref_x = refine_atomic_x,
                            x = x,
                            ref_y = refine_atomic_y,
                            y = y,
                            ref_z = refine_atomic_z,
                            z = z,
                            species = atom_name,  
                            occu = specie_dict[entry],
                            ref_b = ref_b,
                            beq = b_value,
                            mult= count_equiv_sites,
                            wyckoff = wyckoffs[i]
                            ))
            # Now this part is for making topas give us outputs. 
            for line in bvo_inp_bottom_lines:
                inp_file.write(line) #This is writing the second half of the input file. 
            inp_file.write(
                '\tout \"{}_Results.csv\"'.format(no_cif_name)+'\n'
                '\t\tOut(Get(r_wp),'+ r'"%11.10f\t")'+'\n'
                '\t\tOut(Get(a),'+ r'"%11.10f\t")'+'\n'
                '\t\tOut(Get(b),'+ r'"%11.10f\t")'+'\n'
                '\t\tOut(Get(c),'+ r'"%11.10f\t")'+'\n'
                '\t\tOut(Get(al),'+ r'"%11.10f\t")'+'\n'
                '\t\tOut(Get(be),'+ r'"%11.10f\t")'+'\n'
                '\t\tOut(Get(ga),'+ r'"%11.10f\t")'+'\n'
                '\t\tOut(Get(cell_volume),'+ r'"%11.10f\n")'+'\n' 
                    )
            inp_file.write( 
                '\txdd_out \"{}.xy\" load out_record out_fmt out_eqn'.format(no_cif_name)+'\n'
                '\t\t{\n'
                '\t\t'+'\"%11.6f,\" = X;\n' 
		'\t\t'+'\"%11.6f,\" = Yobs;\n'	
		'\t\t'+'\"%11.6f,\" = Ycalc;\n'	
		'\t\t'+r'"%11.6f\n" = Yobs - Ycalc;'+'\n'	
                '\t\t}\n'
                    )
            inp_file.write(
                '\tOut_CIF_STR(\"Refined_{}.cif\")'.format(no_cif_name)
                    )
            inp_file.close()  
            pbar.update(1)
#}}}
#Checking for duplicates.{{{
os.chdir(working_dir)
os.chdir(output_dir)
for f in os.listdir():
    if f.endswith(' 2.inp'):
        os.remove(f)
os.chdir(working_dir)

#}}}
