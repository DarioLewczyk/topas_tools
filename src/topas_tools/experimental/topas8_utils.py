# Authorship: {{{
''' 
Written by: Dario C. Lewczyk
Date: 01-22-25
Purpose: Parse Peter's output and ingest and process data from TOPAS8 through python

Since TOPAS8 is not fully released at this time and these things are subject to change, they will remain in the experimental 
module of topas_tools
'''
#}}}
# imports: {{{
from topas_tools.plotting.plotting_utils import GenericPlotter as gp
import os
import bisect
from glob import glob
import shutil
from shutil import copyfile
import re
import numpy as np
import plotly.graph_objects as go
import pandas as pd
from scipy.optimize import minimize
from math import gcd
from functools import reduce
from topas_tools.utils.topas_utils import Utils 
utils = Utils()
plt = gp()
#}}}
# Basic functions{{{ 
#go_to_dir: {{{
def go_to_dir(base_folder, subfolder_idx, subfolders:list = ['IPS', 'xPS', 'xPx', 'IPx']):
    
    new_dir = os.path.join(base_folder, subfolders[subfolder_idx])
    if os.path.exists(new_dir):
        os.chdir(new_dir)
    else:
        print(f'No path: {new_dir}')
#}}}
# go_to_dir_and_get_xy: {{{
def go_to_dir_and_get_xy(base_folder, subfolder_idx, subfolders:list = ['IPS', 'xPS', 'xPx', 'IPx']):
    go_to_dir(base_folder, subfolder_idx, subfolders)
    xy_file = glob('*.xy')[0] # Get the xy file
    return parse_xy(xy_file)
#}}}
# fit_to_line: {{{
def fit_to_line(x, y,  artificial_x = None):
    ''' 
    This performs a fast fit to data you provide.
    If you want to modify the xaxis you are fitting, pass np.linspace to artificial_x

    returns m, x, fit
    '''
    if type(artificial_x ) == type(None):
        artificial_x = np.linspace(0, 20, 20)
    try:
        m, b = np.polyfit(x, y, 1)
        fit = [m*s + b for s in artificial_x]
    except:
        m, b = (0,0)
        fit = np.zeros_like(artificial_x)
    return m, b, fit
#}}}
# convert_str_hkl_to_tuple{{{
def convert_str_hkl_to_tuple(hkl_str:str):
    return  tuple(int(v) for v in hkl_str.split('_'))
#}}}
#}}}
# Optimization Functions: {{{
#}}}
# Plotting functions: {{{
# basic_xy_file_plot: {{{
def basic_xy_file_plot(tth, yobs, ycalc, ydiff, title = ''):
    # initial plot: {{{
    plt.plot_data(
        tth, 
        yobs, 
        title_text=title,
        xaxis_title= f'2{plt._theta}{plt._degree}',
        yaxis_title='Intensity',
        mode = 'lines',
        color = 'blue',
        name = 'yobs',
        height = 450
    )
    #}}}
    # ycalc: {{{
    plt.add_data_to_plot(
        tth, 
        ycalc,
        mode = 'lines',
        color = 'red',
        name = 'ycalc',
    )
    #}}}
    # diff: {{{
    plt.add_data_to_plot(
        tth, 
        ydiff, 
        mode = 'lines',
        color = 'grey', 
        name = 'ydiff',
    )
    #}}}
    plt.show_figure()
#}}}
# plot_ib_data: {{{
def plot_datasets_with_error(
        datasets:list= None, 
        title_text:str = 'Williamson-Hall Plot',
        xaxis_title = 's (nm^-1)',
        yaxis_title = 'IZTF IB (s, nm)',
        yaxis_range = None,
        height = 400,
        width = 800,
        marker_size = 5,
        legend_x = 0.95,
        legend_y = 0.95,
        x_for_fit = np.linspace(0,20,20)
    ):
    ''' 
    This function will take a dictionary of the data you want to plot
    Expected entries are: 
        x, y, yerr, name, hovertemplate, color
    '''
    print('#'*45)
    fig = go.Figure()
    # Loop through the datasets: {{{
    for dataset in datasets:
        x = dataset['x']
        y = dataset['y']
        yerr = dataset['yerr']
        color = dataset['color']
        name = dataset['name']
        ht = dataset['hovertemplate']
        m, b, fit = fit_to_line(x, y, artificial_x=x_for_fit)
        # Plot the base data: {{{
        fig.add_scatter(
            x = x,
            y = y,
            error_y = dict(
                type = 'data',
                array = yerr,
                visible = True,
            ),
            marker = dict(color = color),
            name = name,
            mode = 'markers',
            hovertemplate = ht,
            marker_size = marker_size,

        )
        #}}}
        # Plot the fit to the data: {{{
        fig.add_scatter(
            x = x_for_fit,
            y = fit,
            line = dict(color = color),
            name = f'{name}_fit',
            hovertemplate = f'm= {m}* x + {b}',
            mode = 'lines',
        )
        #}}}
        # Print Useful info: {{{
        print(f'slope ({name}): {np.around(m, 6)}, intercept ({name}): {np.around(b, 6)}')
        #}}}
    #}}}
    print('#'*45)
    fig.update_layout(
        title = title_text,
        xaxis_title = xaxis_title,
        yaxis_title = yaxis_title,
        template = 'simple_white',
        legend = dict(
            x = legend_x,
            y = legend_y,
        ),
        yaxis = dict(range = yaxis_range),
        height = height,
        width = width
    )
    fig.update_xaxes(ticks = 'inside')
    fig.update_yaxes(ticks = 'inside')
    fig.update_xaxes(mirror= True)
    fig.update_yaxes(mirror= True)
    fig.show()
#}}}
#}}}
# IO functions: {{{
# get_igor_compatible_out_files:{{{ 
def get_igor_compatible_out_files(directories:list = None, profile_data:dict=None, num_subdirs:int = 4,subdirs:list = ['IPS', 'xPS', 'xPx', 'IPx']):
    ''' 
    This function will rename the columns of one of the 
    "..._profiles.out" files so that there are no duplicates
    This ensures that when loaded into IGOR, the columns are distinguishable

    make sure the directories are absolute paths
    '''
    for base_dir in directories:
        for idx in range(num_subdirs):
            try:
                go_to_dir(base_dir, idx, subdirs)
            except:
                break
            method = os.path.basename(os.getcwd())
            base = os.path.basename(base_dir)
            identifier = '_'.join([base,method]) # This is the identifier that gets added to the name of the file and the column headers. 

    
            out_files = glob('*.out')
            profile = [f for f in out_files if '_profiles.out' in f][0]
            with open(profile, 'r') as f:
                lines = f.readlines()
                with open(f'{profile.strip(".out")}_{identifier}.out', 'w') as f2:
                    for i, line in enumerate(lines):
                        if i == 0:
                            label_line = lines[0].split(',')
                            updated_label_list = []
                            for j, label in enumerate(label_line):
                                stripped_label = label.strip("\n").strip("").strip(" ")
                                if j < len(label_line)-1:
                                    new_label = f'{stripped_label}_{identifier}'
                                else:
                                    new_label = f'{stripped_label}_{identifier}\n'
                                updated_label_list.append(new_label)
                            updated_label_line = ','.join(updated_label_list)
                            f2.write(updated_label_line)
                        else:
                            lne = []
                            entry = profile_data[identifier]
                            for key, arr in entry.items():
                                lne.append(str(arr[i-1])) # Because the first line is 0, we need to do i-1
                            newline = ','.join(lne)
                            if i+1 < len(lines):
                                newline = newline+'\n'
                            f2.write(newline)
                            #f2.write(line)
                    f2.close()
                f.close()


#}}}
# write_profile_data_to_excel: {{{
def write_profile_data_to_excel(
        profile_data:dict = None, 
        filter_key:str = 'filtered_10',
        excel_fn_prefix:str = 'IrBCN',
        output_dir:str = None,
        include_entries = None,
        modify_keys = True,
    ):
    '''  

    ''' 
    # Write to an excel file
    home = os.getcwd()
    dataframes = [] # these are the dataframes generated from profile_data
    identifiers = [] # The list of identifiers from each profile data entry
    
    try:
        filtered_dict = profile_data[filter_key]
    except:
        filtered_dict = profile_data # This is in the case where you don't need a filter
    for identifier, entry in filtered_dict.items():
        keys = list(entry.keys())
        if len(keys) >1:
            identifiers.append(identifier)
            new_keys = []
            arrs = []
            for key, arr in entry.items():
                include = True
                #  If you want only certain entries: {{{
                if type(include_entries) != type(None):
                    if key in include_entries:
                        include = True
                    else:
                        include = False 
                #}}}
                if include:
                    if modify_keys:
                        new_keys.append(f'{key}_{filter_key}_{identifier}') 
                    else:
                        new_keys.append(key)
                    arrs.append(arr) # add the array data to a list
            df = pd.DataFrame(arrs,index=new_keys).T # Create the dataframe. Must be created like this to have the custom header labels
            dataframes.append(df)
    excel_file = f'{excel_fn_prefix}_{filter_key}.xlsx'
    if os.path.exists(output_dir):
        os.chdir(output_dir)
    else:
        os.mkdir(output_dir)
        os.chdir(output_dir)
    with pd.ExcelWriter(excel_file) as writer:
        for i, df in enumerate(dataframes):
            df.to_excel(writer, sheet_name = identifiers[i], index = False)
    os.chdir(home)
    print(f'Wrote {excel_file} to:\n{output_dir}')
#}}}
# write_output_data_to_excel: {{{
def write_output_data_to_excel(
        all_output_pd:list = None,
        all_epsilons:list = None,
        capillaries:list = ['kapton', 'glass'],
        distances:list = [220, 600, 900, 1200],
        excel_dir:str = os.getcwd(),
    ):
    ''' 
    This function allows you to quickly output large amounts of data to excel
    using the "profile_output" dictionary created by this code in a sequential fashion. 

    all_output_pd: list of profile_output dictionaries
    all_epsilons: list of the epsilon values you want to use in order
    capillaries: list of the unique capillary types in your output. Must be in order of the repeat.
        ex: capillaries = ["kapton", "glass"]
        data: [220_kap, 220_glass, 500_kap, 500_glass]
    distances: list of distances as above
    '''
    if not os.path.exists(excel_dir):
        os.mkdir(excel_dir)
    # Loop through each profile_output: {{{
    for i, pd_out in enumerate(all_output_pd):
        # Make useful string arguments: {{{
        if len(capillaries) == 2:
            curr_capillary = capillaries[i%2]
            dist_idx = (i//2)%len(distances)
            curr_dist = distances[dist_idx]
        else:
            curr_capillary = capillaries[0]
            curr_dist = distances[i]
        curr_epsilon = all_epsilons[i]
        curr_epsilon = str(np.format_float_scientific(curr_epsilon,2)).replace('.','p')
        excel_file = f'{curr_capillary}_{curr_dist}mm_eps_{curr_epsilon}.xlsx'


        cap_letter_id = curr_capillary[0] # Gives either a k or a g for labeling
        dist_id = f'{curr_dist}{cap_letter_id}'
        #}}} 
        dfs = []
        special_entries = ['compositions', 'avg_mcl_sizes', 'avg_mcl_sizes_e'] # These are specifically defined in the profile_output
        # Loop through the dictionary: {{{
        for comp, pd_entry in pd_out.items():
            if comp not in special_entries:
                key_prefix = f'{dist_id}_{comp}'
                new_keys = []
                keys = list(pd_entry.keys())
                for key in keys: 
                    new_keys.append(f'{key_prefix}_{key}_eps_{curr_epsilon}')
                updated_entry = {new_keys[i]:value for i, (key, value) in enumerate(pd_entry.items())}
                df = pd.DataFrame(updated_entry)
                dfs.append(df)
        
        df = pd.DataFrame([pd_out[special_entries[0]], pd_out[special_entries[1]], pd_out[special_entries[2]]], index=[f'{dist_id}_{df_lbl}' for df_lbl in special_entries]).T
        dfs.append(df)
        #}}} 
        # Now we want to write the file
        with pd.ExcelWriter(os.path.join(excel_dir,excel_file)) as writer:
            start_col = 0
            for df in dfs:
                df.to_excel(writer, sheet_name=dist_id, startcol=start_col, index=False)
                start_col+=len(df.T)
    #}}}
#}}}
# write_harmonics_to_excel: {{{
def write_harmonics_to_excel(
        harmonics:dict,
        filename:str,
        out_dir,
    ):
    '''
    This uses the harmonics dictionary to output data to excel

    '''
    current_dir = os.getcwd()
    os.chdir(out_dir)
    with pd.ExcelWriter(f'{filename}.xlsx') as writer:
        for key, entry in harmonics.items():
            num_entries = len(entry['s_nm'])
            if num_entries > 1:
                new_entry = {} # We need to reformat some things for using IGOR.
                # Get sheet name: {{{
                sheet_name = str(key).strip('()')
                sheet_name = sheet_name.split(' ')
                sheet_name = ''.join(sheet_name)
                sheet_name = sheet_name.replace(',','_')
                #}}}
                #print(sheet_name)
                for col, v in entry.items():
                    col = str(col)
                    col = col.strip('()')
                    col = col.replace(',', '_')
                    if 'hkl' in col:
                        new_hkl = []
                        for hkl in v:
                            hkl = str(hkl).strip('()')
                            hkl = hkl.replace(',','_')
                            new_hkl.append(hkl)
                        new_entry[f'{col}_{sheet_name}'] = new_hkl
                    if 'ht' not in col and 'hkl' not in col:
                        new_entry[f'{col}_{sheet_name}'] = v 
                entry_df = pd.DataFrame(new_entry ) 
                entry_df.to_excel(writer, index = False, sheet_name = sheet_name)
    full_path_written = os.path.join(out_dir, f'{filename}.xlsx')
    print(f'Excel file written to: {full_path_written}')
    os.chdir(current_dir)
#}}}
#}}}
# inp_generator_for_auto_ixpxsx: {{{
def inp_generator_for_auto_ixpxsx(
        template_dir:str = None,
        data_dir:str = None,
        data_extension:str = 'xy',
        output_dir:str = None,
        IxPxSx_dirs = ['IPS', 'xPS', 'xPx', 'xxx'],
        new_inp_basename = 'Si_Al2O3',
        starting_idx = 0,
        delete_old_dir:bool = False,
    ):
    ''' 
    This generates input files in directories for you to run automated refinements on
    # Uses a template INP to make all the files
    
    starting_idx: This is the index that comes before the temperature in the dirname for sorting
    '''
    if delete_old_dir:
        if os.path.exists(output_dir):
            print(f'Removing: {os.path.basename(output_dir)}')
            shutil.rmtree(output_dir)
    home = os.getcwd()
    os.chdir(template_dir)
    template = glob('*.inp')[0]

    # starting_idx = 34
    os.chdir(data_dir)
    xy_files = glob(f'*.{data_extension}')
    
    xy_files.sort()
    for i, xy in enumerate(xy_files):
        if starting_idx:
            i += starting_idx # This adds an offset so that the numbering coninues as normal after the IOC reboot
        os.chdir(data_dir)
        m = re.search(r'(\d+)C', xy)
        if m:
            temp = int(m.group(1))
            os.chdir(template_dir)
            new_inp = f'{new_inp_basename}_{temp}C_MTF.inp'
            print(f'Making INP: {new_inp}')
            with open(template) as fin, open(new_inp, 'w') as fout:
                for line in fin:
                    if line.lstrip().startswith('xdd'):
                        fout.write(f'xdd {xy}\n') # Write the new xy file to the name
                    else:
                        fout.write(line)
            # Now that we have the new input file, let's move it to it's new home.
            inp_dest = os.path.join(output_dir, f'{i}_{temp}C') # This is the directory where we will be sending things
            inp_dest = utils.make_unique_dir(inp_dest) # This ensures that the directory is always updated to be the correct one (if there are duplicate temps)
         
            for dirname in IxPxSx_dirs:
                os.mkdir(os.path.join(inp_dest, dirname))
            shutil.move(new_inp, inp_dest)
            print(f'\tMoving {new_inp} to {os.path.basename(inp_dest)}')
            os.chdir(data_dir)
            copyfile(xy, os.path.join(inp_dest, xy))
            print(f'\tCopying {xy} to {os.path.basename(inp_dest)}')


#}}}
