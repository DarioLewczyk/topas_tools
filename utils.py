#Authorship{{{
'''
Written by Dario Lewczyk
'''
#}}}
#Imports{{{
from tqdm import tqdm
import os, glob,sys
import re
import time
import texttable
import shutil
import pandas as pd
import numpy as np #Needed to load in the mask file.
from datetime import datetime
import pickle
from itertools import combinations # needed to generate polyhedra. 
from scipy.spatial.distance import euclidean
import plotly.graph_objects as go # Needed for graphing. 
#import math as mth
import numpy as np
#import pandas as pd
#from scipy.spatial.distance import euclidean
#import pymatgen
#from pymatgen.core import Structure
#import crystal_toolkit
#import re
#}}}
#"get_time" function {{{
'''
This will be in the format: 
    Month-day-year_hour-minute-second
'''
def get_time():
    now = datetime.now()
    date_and_time= now.strftime("%d-%m-%Y_%H:%M:%S")
    return date_and_time
'''
This function gives us a printout of hours:mins:seconds for elapsed time in seconds
'''
def get_readable_time(time):
    hrs = time // 60**2
    mins = time // 60
    if mins >59:
        mins_already_accounted_for = hrs *60
        mins = mins - mins_already_accounted_for
    sec = time % 60
    final_time = ('{:.0f}h:{:.0f}m:{:.2f}s'.format(hrs,mins,sec))#This gives us a nice printout with not too many figures.
    return final_time
    

#}}}
#collect_data{{{
def collect_data(directory):
    working_dir = os.getcwd()
    os.chdir(directory) #Change to the directory where the data is located.
    data_dir = os.getcwd() #If you put in a relative path, this gives the absolute path
    pickle_file = None
    for f in os.listdir():
        if f.endswith('.pkl'):
            pickle_file = f
            if pickle_file:
                with open(pickle_file,"rb") as filename:
                    read_data=pickle.load(filename)#This loads our data to the "self.read_data" var.
            else:
                print('There are no ".pkl" files in this directory!\n"%s"'%data_dir)
            os.chdir(working_dir) 
        else:
            os.chdir(working_dir)
    return read_data
#}}}
#parse_zhuoying_output{{{
def parse_zhuoying_output(read_data):
    parsed_data = {} #This creates our dictionary to hold the data from Zhuoying's code
    for i, struct in enumerate(read_data):
        metals = []
        x_atoms = []
        ligands = []
        formula = struct['structure'].formula
        if 'mp_id' in list(struct.keys()):
            mp_id = struct['mp_id'] # Gets the MP ID
        else:
            mp_id = '' # If there is no mp id, skip this.
        site_index = struct['site_index'] # This will get the index of the center site in the structure.
        center_atoms = struct['center_coords']
        metals.append(center_atoms) #This makes sure the centroid is always first.
        other_atoms = struct['other_coords']
        parsed_data['struct_%s'%i] = {'formula': formula, 'mp_id':mp_id, 'site_index':site_index}
        for j, coords in enumerate(other_atoms):
            nn = coords['nn'] #These are the X atoms
            nnn = coords['nnn'] #These are the M2 atoms
            ligand = coords['ligands']#This retrieves the array of ligands from the dict.
            metals.append(nnn) #This adds m2 to the metals list.
            x_atoms.append(nn) #This adds the nonmetals ot the nonmetals list
            ligands.append(ligand)#Add the list of ligands to the dict.
        m = np.array(metals)#makes an array of the metals
        o = np.array(x_atoms)#makes an array of the nonmetals.
        l = np.array(ligands)#Makes an array of the ligands attached to NNN
        parsed_data['struct_%s'%i].update({'metals':m, 'x_atoms':o, 'ligands':l}) #updates the dictionary.
    return parsed_data
#}}}
# Original 2D Plotter Functions {{{
# get_position_of_max_and_min_points_of_a_plane {{{
def get_position_of_max_and_min_points_of_a_plane(points, plane,metals = False):
    '''
    Find the max and min points of a particular plane. 
    This will return a 2-tuple that gives:
        1. indexes of points. 
        2. Coordinates of points. 
    '''
    x = points[:,0]
    y = points[:,1]
    z = points[:,2]
    max_x = max(x)
    min_x = min(x)
    max_y = max(y)
    min_y = min(y)
    max_z = max(z)
    min_z = min(z)
    max_x_idx = np.where(x == max_x)[0][0]
    min_x_idx = np.where(x == min_x)[0][0]
    max_y_idx = np.where(y == max_y)[0][0]
    min_y_idx = np.where(y == min_y)[0][0]
    max_z_idx = np.where(z == max_z)[0][0]
    min_z_idx = np.where(z == min_z)[0][0]
    
    if metals:
        xy_idx = [0,max_x_idx, min_x_idx, max_y_idx, min_y_idx]
        xz_idx = [0,max_x_idx, min_x_idx, max_z_idx, min_z_idx]
        yz_idx = [0,max_y_idx, min_y_idx, max_z_idx, min_z_idx]


        xy = (np.array([[x[0], y[0]], [max_x, points[max_x_idx][1]],[min_x, points[min_x_idx][1]], [points[max_y_idx][0],max_y],[points[min_y_idx][0],min_y]])) #This will pair up the x and y coords
        xz = (np.array([[x[0], z[0]], [max_x, points[max_x_idx][2]],[min_x, points[min_x_idx][2]], [points[max_z_idx][0],max_z],[points[min_z_idx][0],min_z]])) #This will pair up the x and z coords
        yz = (np.array([[y[0], z[0]], [max_y, points[max_y_idx][2]],[min_y, points[min_y_idx][2]], [points[max_z_idx][1],max_z],[points[min_z_idx][1],min_z]])) #This will pair up 
    else:
        xy_idx = [max_x_idx, min_x_idx, max_y_idx, min_y_idx]
        xz_idx = [max_x_idx, min_x_idx, max_z_idx, min_z_idx]
        yz_idx = [max_y_idx, min_y_idx, max_z_idx, min_z_idx]


        xy = (np.array([[max_x, points[max_x_idx][1]],[min_x, points[min_x_idx][1]], [points[max_y_idx][0],max_y],[points[min_y_idx][0],min_y]])) #This will pair up the x and y coords
        xz = (np.array([[max_x, points[max_x_idx][2]],[min_x, points[min_x_idx][2]], [points[max_z_idx][0],max_z],[points[min_z_idx][0],min_z]])) #This will pair up the x and z coords
        yz = (np.array([[max_y, points[max_y_idx][2]],[min_y, points[min_y_idx][2]], [points[max_z_idx][1],max_z],[points[min_z_idx][1],min_z]])) #This will pair up  
    
    if plane == 'xy':
        return (xy_idx,xy)
    elif plane == 'xz': 
        return (xz_idx,xz)
    elif plane == 'yz':
        return (yz_idx,yz)
#}}}
# plot_2d_given_plane {{{
'''
This function will add plots to a figure that has already been generated. 
It will return the true statements required to successfully alter the figure and add the buttons to the figure.
'''
def plot_2d_given_plane(figure_object:go.Figure, metals, x_atoms, ligands, plane, visible = True):
    '''
    This function will plot in-plane data given a plane on which to plot. 
    It will return a list of "True" statements that can be used to add buttons to an interactive plot. 
    '''
    true_statements_generated = [] # This will generate a list of "True" items so that we can do the buttons easily. 
    # Hover template {{{
    if plane == 'xy':
        hover_template = '<i>x</i>: %{x:.2f}<br>'+'<i>y</i>: %{y:.2f}<br>'+'<b>Atom</b>: %{text}'
    elif plane == 'xz':
        hover_template = '<i>x</i>: %{x:.2f}<br>'+'<i>z</i>: %{y:.2f}<br>'+ '<b>Atom</b>: %{text}'
    elif plane == 'yz':
        hover_template = '<i>y</i>: %{y:.2f}<br>'+'<i>z</i>: %{y:.2f}<br>'+ '<b>Atom</b>: %{text}'
    #}}}
    # Define metals and x_atoms{{{
    '''
    Specific vars defined here: 
        1) metal_idx
        2) metal_coords
        3) x_atom_idx
        4) x_atom_coords
        5) metal_labels
        6) x_atom_labels
    '''
    
    metal_idx, metal_coords = get_position_of_max_and_min_points_of_a_plane(metals,plane,True)
    x_atom_idx, x_atom_coords = get_position_of_max_and_min_points_of_a_plane(x_atoms, plane)
    
    metal_labels = []
    x_atom_labels = []
    
    for i in metal_idx:
        metal_labels.append('M%s'%i)
    for i in x_atom_idx:
        x_atom_labels.append('X%s'%i)
    #}}}
    '''
    I need to add the polyhedra first because if i do not. Then I can't really see the atoms. 
    '''
    # Coordination polyhedra {{{
    # Add the coordination polyhedra about the central metal.{{{
    '''
    This does the same thing as the 3d version and allows the coordination polyhedra to be filled in. (just in 2d).
    '''
    x_atom_combs = list(combinations(x_atom_coords,3)) #This gets us combinations of 3 points for the x atoms shown. It allows us to fully fill in the square. 
    for arr in x_atom_combs:
        x = np.array(arr)[:,0] #This gives us all the x coords for the combinations. 
        y = np.array(arr)[:,1] # This gives all the y coords for the comnination
        figure_object.add_trace(
            go.Scatter(
                x = x,
                y = y, 
                visible = visible,
                mode = 'markers',
                marker = dict(
                    size = 0,
                    #color = 'rgba(0,0,0,0)'
                    ),
                fill = 'toself',
                fillcolor = 'rgba(5,20,70,0.3)',
                showlegend = False,
                hovertext = False,
                )
            )
        true_statements_generated.append(True)
    
    #}}}
    # Ligand Polyhedra{{{
    for i, ligand in enumerate(ligands):
        nums, coords = get_position_of_max_and_min_points_of_a_plane(ligand,plane) #This is the data we need to plot the polyhedra
        for j in nums:
            ligand_combs = list(combinations(coords,3)) #This generates the list of points for filling in the polyhedra
            for arr in ligand_combs:
                x = np.array(arr)[:,0]
                y = np.array(arr)[:,1]
                figure_object.add_trace(
                    go.Scatter(
                        x = x,
                        y = y, 
                        visible = visible,
                        mode = 'markers',
                        marker = dict(
                            size = 0,
                            #color = 'rgba(0,0,0,0)',
                        ),
                        fill = 'toself',
                        fillcolor = 'rgba(70,5,20,0.1)',
                        showlegend = False,
                        hovertext = False,
                    )
                )
                true_statements_generated.append(True)
    #}}}
    
    #}}} 
    # Add metals (in plane): {{{
    figure_object.add_trace(
        go.Scatter(
            x = metal_coords[:,0],
            y = metal_coords[:,1],
            text = metal_labels,
            visible = visible,
            mode = 'markers',
            marker = dict(
                size = 15,
                ),
            hovertemplate=hover_template,
            name = 'Metals'
            )
        )
    true_statements_generated.append(True)
    #}}}
    
    # X Atoms Plotted: {{{
    figure_object.add_trace(
        go.Scatter(x=x_atom_coords[:,0],
                   y=x_atom_coords[:,1],
                   text=x_atom_labels,
                   visible = visible,
                   mode = 'markers',
                   marker = dict(
                       size = 10,
                   ),
                   #fill = 'toself',
                   #fillcolor = 'rgba(5,20,70, 0.3)',
                   hovertemplate = hover_template,
                   name = 'X Atoms'
                  )
            )
    true_statements_generated.append(True)
    #}}}
    # Add the ligands (the ligands for metals above and below the plotting plane): {{{
    for i, ligand in enumerate(ligands):
        
        #if (i+1) not in metal_idx:
        nums,coords = get_position_of_max_and_min_points_of_a_plane(ligand,plane) # This will get the coords associated with each ligand in the plane of interest.  
        
        # Now, we plot the points of the ligands. 
        ligand_text = []
        for j in nums:
            ligand_text.append('M{}, L{}'.format(i+1,j+1)) # These labels will associate the in-plane ligands with the metal centers they belong to. 
        figure_object.add_trace(
            go.Scatter(x=coords[:,0],
                        y=coords[:,1],
                        text=ligand_text,
                        visible=visible,
                        #line=dict(color="#F06A6A", dash="dash")
                        mode = 'markers',
                        marker = dict(
                            size = 10,
                        ),
                        #fill = 'toself',
                        #fillcolor = 'rgba(70,5,20,0.3)',
                        hovertemplate = hover_template,
                        name = 'Ligands for M%s'%(i+1)
                        )
                    )
        true_statements_generated.append(True)
    #}}}
    return true_statements_generated
#}}}
# plot_2d {{{
'''
This function will plot projections onto the following planes: 
xy, xz, yz
The plot generated will have buttons to cycle through the plots. 
'''
def plot_2d(parsed_data,index):
    '''
    This will make a 2d plot of the metals, x_atoms, and ligands under the assumption they are defined
    as they are in zhuoying's code. 
    This function will also make the plot interactive so that you can quickly cycle between "xy," "xz," and "yz" plane views easily. 
    '''
    key = 'struct_%s'%index
    # Defining things we need: {{{
    fig = go.Figure() # This is the figure object that we will add plots to.
    metals = parsed_data[key]['metals']
    x_atoms = parsed_data[key]['x_atoms']
    ligands = parsed_data[key]['ligands']
    formula = parsed_data[key]['formula']
    #}}}
    # Add plots: {{{
    xy_true_statements = plot_2d_given_plane(figure_object=fig,
                                            metals=metals,
                                            x_atoms=x_atoms,
                                            ligands=ligands,
                                            plane = 'xy')
    xz_true_statements = plot_2d_given_plane(figure_object=fig,
                                            metals=metals,
                                            x_atoms=x_atoms,
                                            ligands=ligands,
                                            plane = 'xz',
                                            visible=False)
    yz_true_statements = plot_2d_given_plane(figure_object=fig,
                                            metals=metals,
                                            x_atoms=x_atoms,
                                            ligands=ligands,
                                            plane = 'yz',
                                            visible=False)
    #}}}
    # Get arguments for buttons: {{{
    xy_proj_args = []
    xz_proj_args = []
    yz_proj_args = []

    for t in xy_true_statements:
        xy_proj_args.append(t)
        xz_proj_args.append(False)
        yz_proj_args.append(False)
    for t in xz_true_statements:
        xy_proj_args.append(False)
        xz_proj_args.append(t)
        yz_proj_args.append(False)
    for t in yz_true_statements:
        xy_proj_args.append(False)
        xz_proj_args.append(False)
        yz_proj_args.append(t)
    #}}}
    # Buttons {{{
    fig.update_layout(
        updatemenus=[
            dict(
                type="buttons",
                direction="right",
                active=0,
                buttons=list([
                    dict(label="XY Projection",
                         method="update",
                         args=[{"visible": xy_proj_args},
                               {"title": "{} – XY Projection".format(formula), 'xaxis':{'title': 'x'}, 'yaxis':{'title': 'y'}},
                              ]),
                    dict(label="XZ Projection",
                         method="update",
                         args=[{"visible": xz_proj_args},
                               {"title": "{} – XZ Projection".format(formula), 'xaxis':{'title': 'x'}, 'yaxis':{'title': 'z'}},
                              ]),
                    dict(label="YZ Projection",
                         method="update",
                         args=[{"visible": yz_proj_args},
                               {"title": "{} – XZ Projection".format(formula), 'xaxis':{'title': 'y'}, 'yaxis':{'title': 'z'}},
                              ])

                ]),
            )
        ])
    #}}}
    # Set title and other visual stuff. {{{
    fig.update_layout(
        title_text="{} – XY Projection".format(formula),
        autosize = False,
        height = 900,
        width = 1300,
        xaxis_title = 'x',
        yaxis_title = 'y',
    )
    #}}}

    fig.show()
#}}}
#}}}
#Better_2d_plotter{{{
#get_plane_dictionary{{{
def get_plane_dictionary (metals:list, directions_dict:dict, key):
    '''
    Need to give list of metals as well as dict of directions
    This function will provide the user with a dictionary consisting of all unique planes present within the structure (for our cases 3 planes)
    For each plane: 
        The 3 coordinate points required to define 2 vectors,  𝑢⃗,𝑣⃗ 
        which define the plane are included. 
        Finally, the normal vector:  𝑛⃗
        is also included
    '''
    directions = directions_dict[key]
    plane_dictionary = {} # This will be a dictionary to hold plane info. 
    for i, dir_key in enumerate(directions):

        cm_coords = metals[0] #This gives us the coords of the center metal. 
        direction = directions[dir_key] # This gives us the direction a,b,c with a sign. 
        letter = re.findall(r'\w',direction)[0]
        dir_index = int(re.findall(r'\d',key)[0]) # This gives us the integer index
        metal_at_current_direction = metals[dir_index] # This gives us the metal coords we are currently at.
        sign = re.findall(r'\+|\-', direction)[0]  #This will find the + or minus
        #print(sign)
        #print('Metal: {} = {}\n\tDirection: {}\n\tLetter: {}'.format(dir_key, metal_at_current_direction, direction, letter))
        if sign == '+':
            other_directions = [] # This will give a list of the other directions that pass. 
            other_metal_labels = [] # This will give us the labels 
            other_metal_coords = [] # This will give us the coords. 
            '''
            We are looking for the + directions to create our vectors to get a plane since in order to be defined as a perovskite, we need 3 orthogonal directions. 
            '''
            for j, second_dir_key in enumerate(directions):
                next_direction = directions[second_dir_key] # This will give us another direction in the form "+/-letter"
                next_letter = re.findall(r'\w',next_direction)[0] #This will give us the letter of the next direction
                next_sign = re.findall(r'\+|\-',next_direction)[0] # This will match with + or -. 
                if next_sign == '+' and next_letter != letter:
                    other_directions.append(next_letter) # Add the next letter to the other directions (so that we can name the plane)
                    other_metal_labels.append(second_dir_key) # This will give us the label. 
                    next_dir_index = int(re.findall(r'\d',second_dir_key)[0]) #This is the number 
                    next_metal_coords = metals[next_dir_index] # This is the new set of coords. 
                    other_metal_coords.append(next_metal_coords)
            if len(other_directions) == 2:
                #print('{}{} Plane'.format(other_directions[0],other_directions[1]))
                #print('Plane consists of points: {}, {}, and {}'.format('M0', other_metal_labels[0], other_metal_labels[1]))
                #print('Coords: \n\tM0: {}\n\t{}: {}\n\t{}: {}'.format(cm_coords, other_metal_labels[0],other_metal_coords[0], other_metal_labels[1], other_metal_coords[1]))
                p0 = np.array(cm_coords)
                p1 = np.array(other_metal_coords[0])
                p2 = np.array(other_metal_coords[1])
                u = p1 - p0
                v = p2 - p0
                #print('Len(u): {}'.format(euclidean(p0,p1)))
                #print('Len(v): {}'.format(euclidean(p0,p2)))
                cross_p = np.cross(u,v)
                dot_p = np.dot(u,v)
                #print('\tCross Product: {}'.format(cross_p))
                #print('\tDot Product: {}'.format(dot_p))
                plane_name = '{}{}'.format(other_directions[0],other_directions[1])
                plane_dictionary[plane_name] = {
                    'M0': cm_coords,
                    '{}'.format(other_metal_labels[0]): other_metal_coords[0],
                    '{}'.format(other_metal_labels[1]): other_metal_coords[1],
                    'N': cross_p
                }
                #print(plane_dictionary)
    return plane_dictionary
            
#}}}
#transform_2d{{{
def transform_2d(p0,p1,p2,n, point):
    u = p1 - p0 # This is essentially the new 'x' direction
    v = p2 - p0 # This is essentially the new 'y' direction
    norm_u = u/euclidean(p1,p0) # This will take the vector and divide it by the magnitude of the vector
    norm_v = v/euclidean(p2,p0) # This will take the vector, v and divide it by the magnitude of v. 

    x = np.dot(norm_u, point - p0)
    y = np.dot(norm_v, point - p0)
    #x = np.dot(u, point-p0) 
    #y = np.dot(v, point-p0)
    return(x,y)
#}}}
#transform_3d_to_2d{{{
def transform_3d_to_2d(plane_dictionary, metals, x_atoms, ligands):
    '''
    This takes a dictionary with the info necessary for transformation
    and performs the transformation and throws each value into its own dictionary. 
    It will generate 3 dicts, 1 for each of the metals, x atoms, and ligands. 

    The dictionaries have keys for each of the planes within them. 
    Inside of each plane, the key will be 'metals' for metals, 
    'x_atoms' for x atoms, 
    and 'ligands' for ligands. 

    These house the 2D data in the same format as the original 3D data. 
    '''
    metals_dict = {}
    x_atoms_dict = {}
    ligands_dict = {}
    for key in plane_dictionary:
        metals_dict[key] = {} # Initialize all of the keys
        x_atoms_dict[key] = {}
        ligands_dict[key] = {}
    
   
    for plane_label in plane_dictionary:
        transposed_metals = []# Should be defined here so that we cap the length at the number of metals. 
        for i, metal in enumerate(metals):
        #for plane_label in plane_dictionary:
            x_axis_label = plane_label[0] 
            y_axis_label = plane_label[1]
            current_dict = plane_dictionary[plane_label]
            list_of_keys = list(current_dict.keys())
            p0 = current_dict[list_of_keys[0]] # This will get our center point on the plane
            p1 = current_dict[list_of_keys[1]] # This will get our second point on the plane
            p2 = current_dict[list_of_keys[2]] # This gets the 3rd point on the plane
            n = current_dict[list_of_keys[3]] # This gets the normal vector. 

            x,y =transform_2d(p0,p1,p2,n,metal) # This will transform the given point. 
            transposed_metals.append([x,y]) # Put these values into an array so that we have an easier time getting the values out later. 
        metals_dict[plane_label].update({
            'metals': np.array(transposed_metals) # This will add the array of metals to the dictionary. 
        })
    for plane_label in plane_dictionary:
        transposed_x_atoms = []# Should be defined here so that we cap the length at the number of metals. 
        for i, x_atom in enumerate(x_atoms):
        #for plane_label in plane_dictionary:
            x_axis_label = plane_label[0] 
            y_axis_label = plane_label[1]
            current_dict = plane_dictionary[plane_label]
            list_of_keys = list(current_dict.keys())
            p0 = current_dict[list_of_keys[0]] # This will get our center point on the plane
            p1 = current_dict[list_of_keys[1]] # This will get our second point on the plane
            p2 = current_dict[list_of_keys[2]] # This gets the 3rd point on the plane
            n = current_dict[list_of_keys[3]] # This gets the normal vector. 

            x,y = transform_2d(p0,p1,p2,n,x_atom) # This will transform the given point. 
            transposed_x_atoms.append([x,y]) # Put these new coords into a list 
        x_atoms_dict[plane_label].update({
            'x_atoms': np.array(transposed_x_atoms) # This will add the array of x atoms to the dictionary. 
        }) 
    for plane_label in plane_dictionary:
        transposed_ligands = [] # Should be defined here so that we cap the length at the number of metals. 
        for i, ligandss in enumerate(ligands):
            transposed_ligandss = []
            for j, ligand in enumerate(ligandss):
                #for plane_label in plane_dictionary:
                x_axis_label = plane_label[0] 
                y_axis_label = plane_label[1]
                current_dict = plane_dictionary[plane_label]
                list_of_keys = list(current_dict.keys())
                p0 = current_dict[list_of_keys[0]] # This will get our center point on the plane
                p1 = current_dict[list_of_keys[1]] # This will get our second point on the plane
                p2 = current_dict[list_of_keys[2]] # This gets the 3rd point on the plane
                n = current_dict[list_of_keys[3]] # This gets the normal vector. 

                x,y = transform_2d(p0,p1,p2,n,ligand) # This will transform the given point. 
                transposed_ligandss.append([x,y])
                #ligands_dict[plane_label].update({
                #    'M{},L{}'.format(i+1,j+1): (x,y)
                #})  
            transposed_ligands.append(transposed_ligandss)
        ligands_dict[plane_label].update({
            'ligands': np.array(transposed_ligands)
        })
    return ((metals_dict,x_atoms_dict,ligands_dict))

#}}}
#add_transformed_2d_plot{{{
def add_transformed_2d_plot(figure_object:go.Figure, metals_dict, x_atoms_dict, ligands_dict, plane_index, directions:dict, visible = True):
    '''
    This function will plot in-plane data given a plane on which to plot. 
    It will return a list of "True" statements that can be used to add buttons to an interactive plot. 
    '''
    plane_keys = []  # This will hold the plane names generated. 
    for key in metals_dict:
        plane_keys.append(key) # This will add each key to the list. 
    
    plane = plane_keys[plane_index] # This grabs the desired plane by index. 
    first_letter_in_plane_name = plane[0]
    second_letter_in_plane_name = plane[1]
    
    
    true_statements_generated = [] # This will generate a list of "True" items so that we can dothe buttons easily. 
    
    # Hover template {{{
    if plane == 'bc':
        hover_template = '<i>b</i>: %{x:.2f}<br>'+'<i>c</i>: %{y:.2f}<br>'+'<b>Atom</b>: %{text}'
    elif plane == 'ac':
        hover_template = '<i>a</i>: %{x:.2f}<br>'+'<i>c</i>: %{y:.2f}<br>'+ '<b>Atom</b>: %{text}'
    elif plane == 'ab':
        hover_template = '<i>a</i>: %{y:.2f}<br>'+'<i>b</i>: %{y:.2f}<br>'+ '<b>Atom</b>: %{text}'
    elif plane == 'ba':
        hover_template = '<i>b</i>: %{y:.2f}<br>'+'<i>a</i>: %{y:.2f}<br>'+ '<b>Atom</b>: %{text}'
    elif plane == 'ca':
        hover_template = '<i>c</i>: %{y:.2f}<br>'+'<i>a</i>: %{y:.2f}<br>'+ '<b>Atom</b>: %{text}'
    elif plane == 'cb':
        hover_template = '<i>c</i>: %{y:.2f}<br>'+'<i>b</i>: %{y:.2f}<br>'+ '<b>Atom</b>: %{text}'
        
    #}}} 
    # Define metals and x_atoms{{{
    '''
    Specific vars defined here: 
        1) metal_idx
        2) metal_coords
        3) x_atom_idx
        4) x_atom_coords
        5) metal_labels
        6) x_atom_labels
    '''
    '''
    These 2 are both dictionaries of dictionaries. Need to specify "metals" for the metals and "x_atoms" for the x atoms
    to get the coordinates. A quirk of how the dictionary was created. 
    '''
    metal_coords = metals_dict[plane]['metals'] # This will get the transformed x,y coords of the metals  
    x_atom_coords = x_atoms_dict[plane]['x_atoms'] #This will get the transformed x,y coords of the x_atoms. 
    #print('Metal Coords:\n\t{}'.format(metal_coords))
    #print('X Atom Coords:\n\t{}'.format(x_atom_coords))
    
    metal_idx = []
    x_atom_idx = []
    for i, coord in enumerate(metal_coords):
        metal_idx.append(i)
    for i, coord in enumerate(x_atom_coords):
        x_atom_idx.append(i+1) #Adding 1 here so these line up. 
    
    #metal_idx, metal_coords = get_position_of_max_and_min_points_of_a_plane(metals,plane,True)
    #x_atom_idx, x_atom_coords = get_position_of_max_and_min_points_of_a_plane(x_atoms, plane)
    
    metal_labels = []
    x_atom_labels = []
    
    for i in metal_idx:
        if i == 0:
            metal_labels.append('M%s'%i) # Center metal has no direction, so it is left as just the metal label. 
        else:
            metal_labels.append('M{}, {}'.format(i, directions['M%s'%i])) #This will add the associated direction to the metal 
    for i in x_atom_idx:
        x_atom_labels.append('X%s'%(i)) # Now we add the x labels so that they match with the metals. 
    #}}} 
    '''
    I need to add the polyhedra first because if i do not. Then I can't really see the atoms. 
    '''
    # Coordination polyhedra {{{
    # Add the coordination polyhedra about the central metal.{{{
    '''
    This does the same thing as the 3d version and allows the coordination polyhedra to be filled in. (just in 2d).
    '''
    x_atom_combs = list(combinations(x_atom_coords,3)) #This gets us combinations of 3 points for the x atoms shown. It allows us to fully fill in the square. 
    for arr in x_atom_combs:
        x = np.array(arr)[:,0] #This gives us all the x coords for the combinations. 
        y = np.array(arr)[:,1] # This gives all the y coords for the comnination
        figure_object.add_trace(
            go.Scatter(
                x = x,
                y = y, 
                visible = visible,
                mode = 'none',
                #marker = dict(
                #    size = 0,
                #    #color = 'rgba(0,0,0,0)'
                #    ),
                fill = 'toself',
                fillcolor = 'rgba(5,20,70,0.3)',
                showlegend = False,
                hovertext = False,
                hoverinfo = 'skip',
                )
            )
        true_statements_generated.append(True)
    
    #}}}
    # Ligand Polyhedra{{{
    '''
    As in the case of the x atoms/metals, the ligands were defined in such a way that
    you need to actually input a key to get the list of lists. 
    '''
    ligands = ligands_dict[plane]['ligands'] # This gives us the coords of the transformed ligands. 
    for i, ligand in enumerate(ligands):
        #nums, coords = get_position_of_max_and_min_points_of_a_plane(ligand,plane) #This is the data we need to plot the polyhedra
        #for j, coords in enumerate(ligand):
        '''
        "ligand" is a list of all the ligands around a metal center. 
        '''
        ligand_combs = list(combinations(ligand,3)) #This generates the list of points for filling in the polyhedra
        for arr in ligand_combs:
            true_statements_generated.append(True)
            x = np.array(arr)[:,0]
            y = np.array(arr)[:,1]
            figure_object.add_trace(
                go.Scatter(
                    x = x,
                    y = y, 
                    visible = visible,
                    mode = 'none',
                    #marker = dict(
                    #    size = 0,
                    #    #color = 'rgba(0,0,0,0)',
                    #),
                    fill = 'toself',
                    fillcolor = 'rgba(70,5,20,0.1)',
                    showlegend = False,
                    hovertext = False,
                    hoverinfo = 'skip',
                    )
                )
    #}}}
    
    #}}} 
    # Add metals (in plane): {{{
    figure_object.add_trace(
        go.Scatter(
            x = np.array(metal_coords)[:,0],
            y = np.array(metal_coords)[:,1],
            text = metal_labels,
            visible = visible,
            mode = 'markers',
            marker = dict(
                size = 15,
                ),
            hovertemplate=hover_template,
            name = 'Metals'
            )
        )
    true_statements_generated.append(True)
    #}}} 
    # X Atoms Plotted: {{{
    figure_object.add_trace(
        go.Scatter(x=x_atom_coords[:,0],
                   y=x_atom_coords[:,1],
                   text=x_atom_labels,
                   visible = visible,
                   mode = 'markers',
                   marker = dict(
                       size = 10,
                   ),
                   #fill = 'toself',
                   #fillcolor = 'rgba(5,20,70, 0.3)',
                   hovertemplate = hover_template,
                   name = 'X Atoms'
                  )
            )
    true_statements_generated.append(True)
    #}}}
    # Add the ligands (the ligands for metals above and below the plotting plane): {{{
    for i, ligand in enumerate(ligands):
        true_statements_generated.append(True)
        #if (i+1) not in metal_idx:
        #nums,coords = get_position_of_max_and_min_points_of_a_plane(ligand,plane) # This will get the coords associated with each ligand in the plane of interest.  
        
        # Now, we plot the points of the ligands. 
        ligand_text = []
        for j, placeholder in enumerate(ligand):
            '''
            Again, the ligand is all the coords of the ligands about a metal. 
            '''
            ligand_text.append('M{}, L{}'.format(i+1,j+1)) # These labels will associate the in-plane ligands with the metal centers they belong to. 
        figure_object.add_trace(
            go.Scatter(x=ligand[:,0],
                        y=ligand[:,1],
                        text=ligand_text,
                        visible=visible,
                        #line=dict(color="#F06A6A", dash="dash")
                        mode = 'markers',
                        marker = dict(
                            size = 10,
                        ),
                        #fill = 'toself',
                        #fillcolor = 'rgba(70,5,20,0.3)',
                        hovertemplate = hover_template,
                        name = 'Ligands for M%s'%(i+1)
                        )
                    )
    #}}}
    return (true_statements_generated, plane)
#}}} 
# plot_2d_transformed{{{
'''
This function will plot projections onto the following planes: 
xy, xz, yz
The plot generated will have buttons to cycle through the plots. 
'''
def plot_2d_transformed(parsed_data:dict,directions:dict,index:int):
    '''
    This will make a 2d plot of the metals, x_atoms, and ligands under the assumption they are defined
    as they are in zhuoying's code. 
    This function will also make the plot interactive so that you can quickly cycle between "xy," "xz," and "yz" plane views easily. 
    '''
    
    key = 'struct_%s'%index
    # Defining things we need: {{{
    fig = go.Figure() # This is the figure object that we will add plots to.
    metals = parsed_data[key]['metals']
    x_atoms = parsed_data[key]['x_atoms']
    ligands = parsed_data[key]['ligands']
    formula = parsed_data[key]['formula']
    
    '''
    Here, we need to get the dictionaries necessary to plot the data. 
    '''
    plane_dictionary = get_plane_dictionary(metals, directions,key) # This will get the plane dictionary
    metal_dict, x_atom_dict, ligand_dict = transform_3d_to_2d(plane_dictionary, metals, x_atoms, ligands) #This returns 3 dictionaries that contain the x,y coords of the transformed points.
    
    
    #}}}
    # Add plots: {{{
    plane_1_true_statements,plane1 = add_transformed_2d_plot(figure_object = fig, 
                                                     metals_dict = metal_dict, 
                                                     x_atoms_dict = x_atom_dict, 
                                                     ligands_dict = ligand_dict, 
                                                     plane_index = 0, 
                                                     directions= directions[key],
                                                     visible = True
                                                    )
    plane_2_true_statements,plane2 = add_transformed_2d_plot(figure_object = fig, 
                                                     metals_dict = metal_dict, 
                                                     x_atoms_dict = x_atom_dict, 
                                                     ligands_dict = ligand_dict, 
                                                     plane_index = 1, 
                                                     directions= directions[key],
                                                     visible = False
                                                    )
    plane_3_true_statements,plane3 = add_transformed_2d_plot(figure_object = fig, 
                                                     metals_dict = metal_dict, 
                                                     x_atoms_dict = x_atom_dict, 
                                                     ligands_dict = ligand_dict, 
                                                     plane_index = 2, 
                                                     directions= directions[key],
                                                     visible = False
                                                    )
    #print('Plane 1: {}'.format(len(plane_1_true_statements)))
    #print('Plane 2: {}'.format(len(plane_2_true_statements)))
    #print('Plane 3: {}'.format(len(plane_3_true_statements)))
  
    #}}}
    # Get arguments for buttons: {{{
    plane_1_proj_args = []
    plane_2_proj_args = []
    plane_3_proj_args = []

    for t in plane_1_true_statements:
        plane_1_proj_args.append(t)
        plane_2_proj_args.append(False)
        plane_3_proj_args.append(False)
    for t in plane_2_true_statements:
        plane_1_proj_args.append(False)
        plane_2_proj_args.append(t)
        plane_3_proj_args.append(False)
    for t in plane_3_true_statements:
        plane_1_proj_args.append(False)
        plane_2_proj_args.append(False)
        plane_3_proj_args.append(t)
    #print('Plane 1 Proj Args: {}'.format(len(plane_1_proj_args)))
    #print('Plane 2 Proj Args: {}'.format(len(plane_2_proj_args)))
    #print('Plane 3 Proj Args: {}'.format(plane_3_proj_args))
    #}}}
    # Update Layout {{{
    fig.update_layout(
        updatemenus=[
            dict(
                type="buttons",
                direction="right",
                active=0,
                buttons=list([
                    dict(label="{} Projection".format(plane1),
                         method="update",
                         args=[{"visible": plane_1_proj_args},
                               {"title": "{} – {} Projection".format(formula,plane1), 'xaxis':{'title': '%s'%plane1[0]}, 'yaxis':{'title': '%s'%plane1[1]}},
                              ]),
                    dict(label="{} Projection".format(plane2),
                         method="update",
                         args=[{"visible": plane_2_proj_args},
                               {"title": "{} – {} Projection".format(formula,plane2), 'xaxis':{'title': '%s'%plane2[0]}, 'yaxis':{'title': '%s'%plane2[1]}},
                              ]),
                    dict(label="{} Projection".format(plane3),
                         method="update",
                         args=[{"visible": plane_3_proj_args},
                               {"title": "{} – {} Projection".format(formula,plane3), 'xaxis':{'title': '%s'%plane3[0]}, 'yaxis':{'title': '%s'%plane3[1]}},
                              ])

                ]),
            )
        ])
    #}}}
    # Set title {{{
    fig.update_layout(
        title_text="{} – {} Projection".format(formula,plane1),
        autosize = False,
        height = 900,
        width = 1300,
        xaxis_title = '%s'%plane1[0],
        yaxis_title = '%s'%plane1[1],
    )

    fig.show()
    #}}}
#}}} 
#}}}
# Utils: {{{
class Utils:
    def __init__(self):
        pass
    #"_get_time" {{{
    '''
    This will be in the format:
    Month-day-year_hour-minute-second
    '''
    def _get_time(self):
        now = datetime.now()
        date_and_time= now.strftime("%d-%m-%Y_%H:%M:%S")
        return date_and_time
    #}}}
    # _get_readable_time: {{{
    def _get_readable_time(self,time):
        '''
        This function gives us a printout of hours:mins:seconds for elapsed         time in seconds
        '''
           
        hrs = time // 60**2
        mins = time // 60
        if mins >59:
            mins_already_accounted_for = hrs *60
            mins = mins - mins_already_accounted_for
            sec = time % 60
            final_time = ('{:.0f}h:{:.0f}m:{:.2f}s'.format(hrs,mins,                sec))#This gives us a nice printout with not too many figures.
        return final_time
    #}}}
    # generate_table: {{{
    def generate_table(self,
        iterable:list = None,
        header= None,
        index_list:list = None,
        cols_align:list = ['c','l'],
        cols_dtype:list = ['i', 't'],
        cols_valign:list = ['b','b'],
        ):
        '''
        This function allows us to generate clean looking tables
        in a text format.
        Now, you can actually generate tables with more than just 2 columns
        '''
        if isinstance(header,str):
            header = ['Index', header] # If you just give a string, then this will make a list for you.
        if index_list:
            if len(iterable) != len(index_list):
                print('Your index_list must be equal to your iterable!')
                print('len iterable: {}\nlen index_list: {}'.format(len(iterable),len(index_list)))
 
        table = texttable.Texttable()
        table.set_cols_align(cols_align) #This sets alignment of cols to center for the index and left for the             vals.
        table.set_cols_dtype(cols_dtype) #This sets the d type of the first column as integers and the second as           text.
        table.set_cols_valign(cols_valign) # This sets the values to be bottom aligned in the cells.
        table.add_row(header) #This adds the header to the table.
        for i, v in enumerate(iterable):
            if index_list and cols_align == ['c','l']:
                table.add_row([index_list[i], v]) # Add your custom labels with the values.
            elif cols_align != ['c','l']:
                # This means that we are trying to add more columns.
                table.add_row(v) # This will just contain all of the index and value information
            else:
                table.add_row([i,v])
        print(table.draw())
    #}}}
#}}}
