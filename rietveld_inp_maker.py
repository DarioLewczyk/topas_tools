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
#khalifah_research{{{
path = python_tools_dir.split('/') #This splits the path to python_tools up. 
throw_away = path.pop(-1) #This gets rid of the python_tools folder. 
khalifah_research = '/'.join(path) #This re-assembles the path to the enclosing folder. 
#}}}
#Obtaining the template_inp_directory {{{
os.chdir(python_tools_dir) #This allows us to see all of the folders of template files are. 
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
os.chdir(khalifah_research) #This goes back to the research folder. 
choosing_cif_folder = True
next_folder = khalifah_research #################### This houses the next folder in. 
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
        '______________________________________________\n' 
        )
    if folder_selection:
        number = int(folder_selection)
        folder_selection = folders[number] #This grabs the correct folder
        current_selection = next_folder+'/'+folder_selection #This defines the new folder we are looking at. 
        os.system('clear')###### clears the output
        yes_or_no = input('______________________________________________\n' 
            'Is this the correct folder?\n'
            '{}\n'.format(current_selection)+
            'y/(n)\n'
            '______________________________________________\n' 
            )
        if yes_or_no == 'y':
            cif_directory = current_selection
            choosing_cif_folder == False #should break the loop.  
            break
        else:
            next_folder = current_selection
            os.chdir(next_folder)
            #This makes it so that we always keep advancing into the next folder. 
    else:
        sys.exit()
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
#Making the lists of lines from the inp templates{{{
os.chdir(template_inp_directory)
bvo_inp_top_half = open('top_template.inp')
bvo_inp_bottom_half = open('bottom_template.inp')

#This reads the lines of the templates to prepare for saving to the new file. 
bvo_inp_top_lines = bvo_inp_top_half.readlines() 
bvo_inp_bottom_lines = bvo_inp_bottom_half.readlines()
#}}}
#Making the Inp files{{{
cif_files = []

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
for filename in os.listdir():
    if filename.endswith('.cif'):
        cif_files.append(filename)
with tqdm(total=len(cif_files)) as pbar:
    for i, cif_file in enumerate(cif_files):
        inp_name = cif_file.replace('.cif','.inp') # This makes the inp file name the same as the cif name. 
        cur_struct = Structure.from_file(cif_file) #make a structure object. 
        no_cif_name = cif_file.strip('.cif')
        ######################
        # Obtaining the full
        # symmetry of this 
        # structure
        ######################
        space_group_analyzer = SpacegroupAnalyzer(cur_struct) #makes a space group Analyzer instance for the current structure. 
        symmetrized_struct = space_group_analyzer.get_symmetrized_structure() #This makes a new variable with the symmetry data
        symmetry_dataset = space_group_analyzer.get_symmetry_dataset() #This gives a dictionary with all the symmetry information.
        equivalent_atoms = symmetry_dataset['equivalent_atoms'] #Gives a list of equivalent atoms. (the exact length of all of the sites)
        crystal_system = space_group_analyzer.get_crystal_system().capitalize() #This gives us a capitalized name of the crystal system. 
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
                    '\t \t'+'a @ {a}'+'\n'
                    '\t \t'+'b @ {b}'+'\n'
                    '\t \t'+'c @ {c}'+'\n'

                    '\t \t'+'al @ {al}'+'\n'
                    '\t \t'+'be @ {be}'+'\n'
                    '\t \t'+'ga @ {ga}'+'\n'

                    '\t \t'+'volume @ {vol}'+'\n'
            )
        #}}}
        #Monoclinic: beta is not 90. {{{
        monoclinic = (
                    '\t \t'+'a @ {a}'+'\n'
                    '\t \t'+'b @ {b}'+'\n'
                    '\t \t'+'c @ {c}'+'\n'

                    '\t \t'+'al  {al}'+'\n'
                    '\t \t'+'be @ {be}'+'\n'
                    '\t \t'+'ga  {ga}'+'\n'

                    '\t \t'+'volume @ {vol}'+'\n'
            )
        #}}}
        #Orthorhombic: al = be = ga = 90{{{
        orthorhombic = (
                    '\t \t'+'a @ {a}'+'\n'
                    '\t \t'+'b @ {b}'+'\n'
                    '\t \t'+'c @ {c}'+'\n'

                    '\t \t'+'al  {al}'+'\n'
                    '\t \t'+'be  {be}'+'\n'
                    '\t \t'+'ga  {ga}'+'\n'

                    '\t \t'+'volume @ {vol}'+'\n'
            )
        #}}}
        #Tetragonal: a = b != c, al=be=ga=90{{{
        tetragonal = (
                '\t\tTetragonal(@ {a}, @ {c})\n'
                )
        #}}}
        #Hexagonal: a=b!=c, al = be= 90, ga = 120{{{
        hexagonal = (
                '\t\tHexagonal(@ {a}, @ {c})\n'
                )
        #}}}
        #Rhombohedral or trigonal: a=b=c, al = be = ga != 90{{{
        rhombohedral = (
                '\t\tRhombohedral(@ {a}, @ {al})\n'
                )
        #}}}
        #Cubic: a=b=c, al=be=ga=90{{{
        cubic = (
                '\t\tCubic(@ {a})\n'
            )
        #}}}
        #}}}
        ############ Lattice Params
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
            inp_file.write('\tstr\n' 
                    '\t\tspace_group \"{}\"'.format(space_group)+'\n' 
                    '\t\tscale @ 1.68165115e-005\n'
                    )
            # Crystal System Writing {{{ 
            #Triclinic{{{
            if crystal_system == 'Triclinic':
                inp_file.write(triclinic.format(
                    a = a,
                    b = b,
                    c = c,
                    al = al,
                    be = be,
                    ga = ga,
                    vol =vol
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
                    vol=vol
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
                    vol=vol
                    ))
            #}}}
            #Tetragonal {{{
            elif crystal_system == 'Tetragonal':
                inp_file.write(tetragonal.format(
                    a = a,
                    c = c
                    ))
            #}}}
            #Hexagonal{{{
            elif crystal_system == 'Hexagonal':
                inp_file.write(hexagonal.format(
                    a=a,
                    c=c
                    ))
            #}}}
            #Rhombohedral/Trigonal{{{
            elif crystal_system == 'Rhombohedral' or crystal_system == 'Trigonal':
                inp_file.write(rhombohedral.format(
                    a=a,
                    al=al
                    ))
            #}}}
            #Cubic{{{
            elif crystal_system == 'Cubic':
                inp_file.write(cubic.format(
                    a=a
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
                ##################
                for j, entry in enumerate(site.species.as_dict()):
                    ############################
                    # The species is the "entry"
                    # variable. 
                    # The occu value is the other 
                    # value within the specie dict 
                    # entry for the atom. 
                    # We also need to add in 
                    # B values here using the term: "beq"
                    ###########################
                    atom_name = entry 
                    b_value = 1 #We are going to set all b values as 1. I can make this change as I see fit later. 
                    if atom_name == 'Bi':
                        b_value = b_value_bi
                    elif atom_name == 'V' or atom_name == 'Mo':
                        b_value = b_value_v
                    
                    topas_site_text = '\t\tsite {specie}{num} \tnum_posns {num_posns} \tx {x:0.8f} \ty {y:0.8f} \tz {z:0.8f} \tocc {species} {occu} \tbeq {beq}\n'

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
                            x = site.frac_coords[0],
                            y = site.frac_coords[1],
                            z = site.frac_coords[2], 
                            species = atom_name,  
                            occu = specie_dict[entry],
                            beq = b_value
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
                '\t\t}'
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
