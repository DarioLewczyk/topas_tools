#Authorship{{{

#}}}
from tqdm import tqdm
import os, glob,sys
import re
import time
import shutil
import pandas as pd
import pyFAI, fabio
from datetime import datetime
#System functions{{{
def clear():
    os.system('clear')

#}}}
#"get_time" function {{{
'''
This will be in the format: 
    Month-day-year_hour-minute-second
'''
def get_time():
    now = datetime.now()
    date_and_time= now.strftime("%d-%m-%Y_%H_%M_%S")
    return date_and_time
#}}}
#Convert ".dat" to ".xy"{{{
def convert_dat_to_xy(files:list):
    dat_files = glob.glob('*.dat') #get all of the .dat files
    for fn in dat_files:
        xy_file = fn.replace('.dat', '.xy')
        data = pd.read_csv(fn, skiprows=23, header=None, delim_whitespace=True)
        data.columns = ['X', 'I']
        data.to_csv(xy_file,index=False,float_format='%.8f', sep = '\t')
#}}}
#Variables to pay attention to{{{
starting_dir = os.getcwd()
poni_folder = None #Folder where poni files are stored.
poni_file = None #The PONI file you want to use
ai = None #Azimuthal integrator to integrate.
home_directory = None #Home directory where the tiff folders are.
bypass_paths = None#These are the paths to bypass when integrating
npts = None #These are the number of points for integration
#}}}
#Defining "poni_folder"{{{

selecting_poni_folder = True
clear()
stay_in_current_folder = input('Is your PONI file in this folder?\n'
        'y/(n)\n'
        '____________________________________________\n')
if stay_in_current_folder == 'y':
    selecting_poni_folder= False
    poni_folder = os.getcwd()
previous_dir = os.getcwd() #This is the previous directory for the loop.
while selecting_poni_folder:
    folders_in_cd = {}
    folder_count = 0
    for f in os.listdir():
        if os.path.isdir(f):
            folders_in_cd[folder_count]= f
            folder_count+=1
    print('Folders in current directory:\n')
    for i,f in enumerate(folders_in_cd.values()):
        print('index: {}, Name: {}\n'.format(i,f))
    print('____________________________________________\n')
    selection = input('Choose a directory by typing its number or go back by typing "b"\n'
            '____________________________________________\n')
    if selection == 'b':
        new_dir = '/'.join(starting_dir.split('/')[0:-1])#This goes back one directory. 
    elif selection == '':
        clear()
        print('Please select an option.') 
        new_dir = None
    else:
        clear()
        if re.findall(r'\d',selection):
            folder_num = int(selection) #converts to number once it is confirmed to be a number. 
            new_dir = '{}/{}'.format(previous_dir, folders_in_cd[folder_num])
        else:
            clear()
            print('Please make a valid input. Either a number or "b"\n')
            new_dir = None
    if new_dir:
        previous_dir = new_dir
        os.chdir(new_dir)
        clear()
        done_searching = input('Is {} the PONI file directory?\n'.format(new_dir)+
                'y / (n)\n'
                '____________________________________________\n')
        if done_searching == 'y':
            selecting_poni_folder = False
            poni_folder = new_dir #This sets the poni folder. 
        else:
            pass
    else: 
        pass
    
    
    
#}}}
#get variable: "poni_file"{{{
os.chdir(poni_folder) #Now we are in the PONI folder.
poni_files = glob.glob('*.poni')
poni_count = 0
clear()
print('PONI Files:\nI\t\tFile\n_________________________________________')
for i,f in enumerate(poni_files):
    print('{}\t\t{}\n'.format(i,f))
print('_________________________________________')
poni_file = False
while poni_file == False:
    poni_num = input('Please type the number of your selection\n'
                        '_________________________________________\n')     
    if re.findall(r'\d',poni_num):
        poni_file = poni_files[int(poni_num)]
        clear() 
    else:
        poni_file = False 

#}}}
#Define azimuthal integrator ("ai"){{{
ai = pyFAI.load(poni_file) #This loads the poni for integration. 
clear()
show_poni_info = input('Do you want to see what the PONI file: {}\n'.format(poni_file)+
        'looks like?\n'
        'y / (n)\n'
        '____________________________________________\n')
if show_poni_info == 'y':
    clear()
    print('Integrator:\n{}'.format(ai))
    time.sleep(3)

#}}}
#Define "home_directory"{{{
clear()
is_home = input('Is this the home directory?\n{}\n (y) / n \n_________________________________________\n'.format(starting_dir))
if is_home == 'n':
    selecting_home = True #This stays true while selecting. 
    os.chdir(starting_dir) #This brings us to the orig folder. 
    previous_dir = starting_dir #This keeps track of the folders. 
    
    while selecting_home: 
        folders = {} #will house the directories. 
        clear()
        count = 0
        for f in os.listdir():
            if os.path.isdir(f):
                folders[count]= f
                count+=1
        print('Index\t\tFolder\n_________________________________________\n')
        for i,f in enumerate(folders.values()):
            print('{}\t\t{}\n'.format(i,f))
        print('____________________________________________')
        selection = input('Select a number or enter "b" to go back.\n'
                '____________________________________________\n')
        if selection == 'b':
            new_dir = '/'.join(previous_dir.split('/')[0:-1])#gets the previous folder
        elif selection == '':
            print('Please make a valid selection.\n')
            new_dir = None
        else:
            if re.findall(r'\d',selection):
                new_dir = '{}/{}'.format(previous_dir,folders[int(selection)]) #This changes the directory.
            else:
                print('Please make a valid selection.\n')
        if new_dir:
            clear()
            correct_dir = input('Is {} the correct home directory?\ny / (n)\n_________________________________________\n'.format(new_dir))
            if correct_dir == 'y':
                home_directory = new_dir
                selecting_home = False
            else:
                previous_dir = new_dir
                os.chdir(new_dir)

else:
    home_directory = starting_dir
#}}}
os.chdir(home_directory)
#"bypass_paths" definition{{{
'''
You can change these to suit your particular needs. 
In this case, this will bypass any path that ends with:
    "Integrated","integrated", or "analysis"
or starts with:
    "Si_calib"
'''
bypass_paths = glob.glob('*Integrated')+glob.glob('*integrated')+glob.glob('Si_calib*')+glob.glob('*analysis')
#}}}
#User Defines Parms for pyFAI Integrate{{{
clear()
print('Input params for pyFAI Integration\n')
npts = input('How many points do you want? \n Default = 8000\n_________________________________________\n')
if npts:
    if re.findall(r'\d',npts):
        npts = int(npts)
    else:
        sys.exit()
else:
    npts = 8000
#}}}
#Loop for all directories in "home_directory"{{{
'''
Overview:
    This module performs the following tasks:
        1. Find all folders in the "home_directory"
        2. Change Dir to each folder
        3. Find all ".tif" files
        4. If ".tif" files are present: 
            a. Create a folder with the name of the parent dir in "home_directory"
            b. Process the files with pyFAI
            c. change the ".dat" file to ".xy"
            d. Move the processed files to the daughter directory
        
'''
t0 = time.time()
folders = {} #stores folder in home_directory
folder_count = 0 #This counts the folders in home_directory
folders_with_tiffs = [] #Stores a list of indices of folders that have tiff files. 
for f in os.listdir():
    if os.path.isdir(f):
        if f not in bypass_paths:
            folders[folder_count] = f
            folder_count+=1
integrated_folders = []#This produces a list of all integrated folders to move them later. 
pbar1 = tqdm(folders.values())
for i, path in enumerate(pbar1): 
    pbar1.set_description('Processing: {}'.format(path))
    os.chdir(path)#change into the directory to check for tiffs
    path_with_tiffs = os.getcwd() #This saves that location. 
    tif_files = glob.glob('*.tif')# This will hold all of the tiff files per dir.
    # Remove all dat files leftover {{{
    dat_files = glob.glob('*.dat')#This gets any dat files
    for dat_file in dat_files:
        os.remove(os.path.join(path_with_tiffs,dat_file))
    #}}}
    if tif_files:
        working_path = os.getcwd() #This gets our current path with the tif files
        integrated_folder = '{}/{}_integrated_{}'.format(home_directory,path,get_time())#This makes a folder in the home directory for the integrated files. It gives the time too so it never overwrites.
        integrated_folders.append(integrated_folder) #This saves the folder to our list.
        #Make the integrated_folder{{{ 
        if os.path.exists(integrated_folder):
            shutil.rmtree(integrated_folder)
            os.mkdir(integrated_folder)
        else:
            os.mkdir(integrated_folder)
        #}}} 
        pbar2 = tqdm(tif_files) 
        for j, f in enumerate(pbar2):  
            image = fabio.open(f) #This opens up the image 
            clear()
            pbar2.set_description_str('{}, dir: {}/{}'.format(f, i, len(folders)))
            #pbar2.display()
            img_array = image.data #This converts the image into usable data.
            '''
            The 'result' variable will do the integration
            It will name the file the same thing as the tif
            But will give it a ".dat" extension.
            '''
            result = ai.integrate1d(img_array,
                    npts,
                    unit = '2th_deg',
                    correctSolidAngle= False,
                    method = ['full','*','*'],
                    filename = f.replace('.tif','.dat')
                    )
            convert_dat_to_xy([f.replace('.tif','.dat')]) #This converts the current file to .xy
            shutil.move(os.path.join(path_with_tiffs,f.replace('.tif','.xy')),integrated_folder) 
            clear()
    os.chdir(home_directory)          
#Moving all of the folders to a "final_destination"{{{
final_destination = '/'.join(home_directory.split('/')[0:-1])+'/17_BM_Integrated_Files_{}'.format(get_time()) #Creates a unique end point for all of the folders
os.mkdir(final_destination)
pbar3 = tqdm(integrated_folders)
for folder in pbar3:
    pbar3.set_description('Moving "{}"'.format(folder.split('/')[-1])) #This separates the path and makes it a shorter name to display.
    shutil.move(folder,final_destination)#This moves each integrated folder to the final_destination
#}}} 
t1 = time.time()
print('Total elapsed time: {:.2f}'.format(t1-t0)) #prints the total time of this operation.
#}}}
