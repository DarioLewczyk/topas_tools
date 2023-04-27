# Authorship: {{{
'''
Written by Dario Lewczyk
Date: 04/19/2023
Purpose:
    The goal of this function is to be able to 
    go through all directories located within a "call" directory
    and read all of the .xy files present and perform background subtraction
    on them. 
    The program will then create a new folder in the main directory called "bkg_sub"
    where it will create separate folders for each folder it goes through and will dump
    abbreviated filenames with the background subtracted data in the correct folders.
'''
#}}}
# Imports: {{{
import glob # File collection
import re # Filename Parsing
import os # Navigation 
import numpy as np
from skimage import restoration # This will allow us to background subtract.
from tqdm import tqdm
#}}}
# Customizable Params: {{{
relevant_radii = [
    7.5, 
    21.5, 
    45.7, 
    250, 
    31.25, 
    1000,
] # These are the "ball" radii. smaller means more propensity for overfitting (use cautiously)
regions = [
    2.390699,
    2.963193, 
    4.963193, 
    7.800922, 
    8.841004, 
    180
] #These are the regions of the patterns that we might care about. If you dont want multi fitting, just leave 180
#}}}
# Script begins: {{{
working_dir = os.getcwd() 
relevant_folders = [] # This will be a list of folders. 
xy_files_in_folders = [] # This will be a list of lists (each entry is a folder in the order above)
new_folders = [] # This will hold the new names of the folders
# Initial Setup: {{{
for i, item in enumerate(os.listdir()):
    if os.path.isdir(item) and item != 'bkg_sub':
        '''
        This is done so that we only record folders and if we choose to run this function again
        in the same folder, that we do not need to worry about subtracting background subtracted
        files.
        '''
        os.chdir(item)
        xy_files = glob.glob('*.xy') 
        if xy_files:
            # The below is searching for items that contain capital/lower letters
            # and digits together or simply digits. 
            # Where there is a "*" it means that is optional but can be as many instances in a row
            # as necessary
            # The "|" separates possibilities
            relevant_words_from_fn = re.findall(r'[A-Za-z]*\d+[A-Za-z]*\d*|\d+|cool|[a-z]*RT|integrated',item)
            relevant_words_from_fn.extend([
                'background',
                'subtracted'
            ]) 
            new_folder_name = '_'.join(relevant_words_from_fn)
    
            new_folders.append(new_folder_name) # Add the new dir name
            relevant_folders.append(os.path.join(working_dir,item)) # Add the full path to the original folder
            xy_files_in_folders.append(xy_files) #store the filenames
    os.chdir(working_dir)# Return home when done.
        
#}}}
if not os.path.exists(os.path.join(working_dir,'bkg_sub')):
    # WE will create the home folder for the final folders and their files.
    os.mkdir('bkg_sub')
destination_home = os.path.join(working_dir,'bkg_sub') # Make the path variable. 
# Loop through new folders to make them: {{{
print(f'New Folders to Make: {len(new_folders)}')
pbar1 = tqdm(iterable = new_folders) # Create a progress bar for the new folders. 
os.chdir(destination_home) # Move to the new home directory.
for i, new_folder in enumerate(pbar1):
    pbar1.set_description(f'Creating dict: {new_folder}')
    destination = os.path.join(destination_home,new_folder)
    if not os.path.exists(destination):
        os.mkdir(destination) # Make the current destination directory
    source = relevant_folders[i] # This is the source directory
    xy_files = xy_files_in_folders[i] # These are the files in the source.
    pbar2 = tqdm(iterable= xy_files) # Make a second progress bar to work through. 
    # Loop through the files: {{{
    for j, xy_file in enumerate(pbar2):
        # DEFINE DICT AND LIST FOR BKG: {{{
        combined_bkg = [] # This is where the total background is stored
        bkgs = {} # Dictionary holding all of the backgrounds. 
        #}}} 
        # Make the new filename: {{{
        splitname = re.findall(r'[A-Za-z]*\d+[A-Za-z]*\d*|\d+',xy_file)
        final_name = []
        for part in splitname:
            if not part.isnumeric():
                if 'NH3' not in part and 'pctV' not in part:
                    final_name.append(part)
            else:
                if part != '0':
                    final_name.append(part)
        newname = '_'.join(final_name)
        new_xy_file = f'{newname}.xy'
        #}}}
        pbar2.set_description(f'BKG Sub: {new_xy_file}')

        # Read the data: {{{
        orig_xs = []
        orig_ys = []
        xy_filepath = os.path.join(source,xy_file) # Get the fullpath of the file
        new_xy_filepath = os.path.join(destination,new_xy_file) # Get the fullpath of final file

        with open(xy_filepath,'r') as orig:
            with open(new_xy_filepath,'w') as new:
                new_header = 'tth\tI\n'
                lines = orig.readlines() # Gives the lines of the file
                for line in lines:
                    numbers = re.findall(r'\d*\.?\d+',line) # Get the values only. 
                    if len(numbers) == 2:
                        orig_xs.append(float(numbers[0]))
                        orig_ys.append(float(numbers[1]))
                orig.close() # We do not need the original data anymore
                # Create the combined background: {{{
                for l, region in enumerate(regions):
                    bkgs[region] = restoration.rolling_ball(orig_ys, radius=relevant_radii[l])
                for l, tth in enumerate(orig_xs):
                    region0 = regions[0]
                    region1 = regions[1]
                    region2 = regions[2]
                    region3 = regions[3]
                    region4 = regions[4]
                    region5 = regions[5]
                    if tth <= region0:
                        combined_bkg.append(bkgs[region0][l]) # Add the lth index of the bkg
                    elif tth <= region1:
                        combined_bkg.append(bkgs[region1][l]) # Add the lth index of the bkg
                    elif tth <= region2:
                        combined_bkg.append(bkgs[region2][l]) # Add the lth index of the bkg
                    elif tth <= region3:
                        combined_bkg.append(bkgs[region3][l]) # Add the lth index of the bkg
                    elif tth <= region4:
                        combined_bkg.append(bkgs[region4][l]) # Add the lth index of the bkg
                    elif tth <= region5:
                        combined_bkg.append(bkgs[region5][l]) # Add the lth index of the bkg
                #}}}

                #background = restoration.rolling_ball(orig_ys, radius = 25) # Creating background with best radius from testing.
                
                bkg_sub_ys = orig_ys- np.array(combined_bkg)# This gives us the background subtracted data
                new.write(new_header) # This writes the first line
                for i, x in enumerate(orig_xs):
                   new.write(f'{x}\t{bkg_sub_ys[i]}\n') # Write the next line.  
                new.close()
        #}}} 
    #}}}
#}}}
#}}}
