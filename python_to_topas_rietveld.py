#Authorship{{{
'''
topas_refinement function is inspired by Monty Cosby's code. 

The class was made by Dario Lewczyk
'''
#}}}
#Inputs{{{
import os, subprocess
import shutil
import sys
import pandas as pd
import pickle 
import pandas as pd
import matplotlib.pyplot as plt 
from tqdm import tqdm
import numpy as np
import matplotlib.ticker as mticker
#}}}
#function to send inps to topas{{{
def topas_refinement(working_directory = os.getcwd(), del_out = False):
    os.chdir(working_directory)#Moves us into the working directory. Default value is to be the original directory. 
    TOPAS6_dir = "C:\\TOPAS6" #This is where TOPAS is
    '''
    This will make an output file for all of the files generated by this code. 
    '''
    if del_out == False:
        out = 'TOPAS_Out_Files'
        if os.path.exists(out):
            os.chdir(out)
            for f in os.listdir():
                if f.endswith('.out'):
                    os.remove(f)
            os.chdir(working_directory)
        else:
            os.mkdir(out)
        os.chdir(out)
        out_dir = os.getcwd() ########### TOPAS OUTPUT FILES DIRECTORY
        os.chdir(working_directory)

    output_dir = 'TOPAS_Output' 
    if os.path.exists(output_dir):
       os.chdir(output_dir) 
       output_directory = os.getcwd()
       ################################# REMOVE DUPLICATE FILES
       for f in os.listdir():
           if f.endswith('.xy'):
               os.remove(f) #This deletes the file.els
           if f.endswith('.csv'):
               os.remove(f)    
    else: 
        os.mkdir(output_dir) 
        os.chdir(output_dir)
        output_directory = os.getcwd()
    os.chdir(output_directory) ###################### OUTPUT DIRECTORY
    output_dir = os.getcwd() #This redefines the output directory to the new output folder. 
    os.chdir(working_directory)######################changes us back to the working directory to start looping. 
    filenames = []
    files = os.listdir()
    for f in files:
        if f.endswith('.inp'): 
            filenames.append(f) 
    with tqdm(total=len(filenames)) as pbar:
        for i, inp_file in enumerate(filenames):  
            refine_cmd = 'tc '+working_directory+'\\' #This is the refinement command for TOPAS
            os.chdir(TOPAS6_dir)
            subprocess.call(refine_cmd+inp_file) #This is telling TOPAS we want to refine. 
            os.chdir(working_directory) 
            pbar.update(1)

    dir_contents = os.listdir() 
    xy_files = []
    csv_files = []
    out_files = []
    for f in dir_contents:
        if f.endswith('.xy'):
            xy_files.append(f)
        elif f.endswith('.csv'):
            csv_files.append(f)
        elif f.endswith('.out'):
            out_files.append(f)
    with tqdm(total = len(xy_files)+ len(csv_files)) as pbar:
        print('Moving .csv and .xy files...')
        for i, f in enumerate(dir_contents):
            if f.endswith('.xy') or f.endswith('.csv'): 
                os.chdir(output_dir)#checks to see if the file already exists. 
                for i2, f2 in enumerate(os.listdir()):
                    if f == f2:
                        os.remove(f2) 
                os.chdir(working_directory) 
                shutil.move(f,output_dir)#This moves the newly created .xy files to the output folder. 
                pbar.update(1)
    with tqdm(total=len(out_files)) as pbar:
        print('Moving .out files...')
        for f in out_files:
            if del_out == True:  
                os.remove(f)
            else: 
                shutil.move(f,out_dir)
            pbar.update(1)




#}}}
#Analysis_Class{{{
class Analyzer:
    def __init__(self, data_folder=os.getcwd(),col_labels = ['angle', 'y_obs','y_calc','y_diff']):
        self.data_folder = data_folder
        self.col_labels = col_labels
        self.data_dict = {} #creating a dictionary to hold our data.
        self.dict_of_data_files = {}
        self.csv_files_loaded = False ###########################Default value is false. Will change if csv files are detected. 
        os.chdir(data_folder) #Changes us to the working directory
        for i, f in enumerate(os.listdir()):
            if f.endswith('.xy'):
                filename = f 
                number = f.strip('.xy').split('_')[-1] #Grabs the number associated with the file. 
                df = pd.read_csv(filename, header=None,names=self.col_labels)
                angle =df[self.col_labels[0]]
                y_obs =df[self.col_labels[1]]
                y_calc =df[self.col_labels[2]]
                y_diff =df[self.col_labels[3]]
                max_diff = y_diff.max() #This gives us the maximum difference to use.
                modified_diff_curve = []
                for value in y_diff:
                    modified_diff_curve.append(value-max_diff*0.5) #subs 50% of the max difference. 

                self.data_dict[int(number)] = {
                    'filename': filename,
                    'df': df,
                    'angle': angle,
                    'y_obs': y_obs,
                    'y_calc': y_calc,
                    'y_diff': y_diff,
                    'modified_diff_curve': modified_diff_curve,
                    'number': number
                }
        for i,f in enumerate(os.listdir()):
            ####################
            # Has to be in a new loop in case the program doesn't encounter
            # Matching files in series. It would cause an error if this was 
            # Not done. 
            ####################
            if f.endswith('.csv'):
                self.csv_files_loaded = True ###############################################ENSURES WE KNOW THAT CSV FILE DATA ARE PRESENT FOR PLOTTING
                cols = ['Rwp', 'a', 'b', 'c', 'alpha', 'beta', 'gamma', 'volume']
                csv_df = pd.read_csv(f, header = None, sep = '\t', names=cols)
                #The format of the filename is: BiVO4_Fixed_Supercell_#_Results.csv. This just grabs the number. 
                file_number = int(f.strip('_Results.csv').split('_')[-1] )
                '''
                Create variables for Rwp, a,b,c, al,be,ga, vol
                '''
                rwp = csv_df[cols[0]]
                a = csv_df[cols[1]]
                b = csv_df[cols[2]]
                c = csv_df[cols[3]]
                al = csv_df[cols[4]]
                be = csv_df[cols[5]]
                ga = csv_df[cols[6]]
                vol = csv_df[cols[7]]
                self.data_dict[file_number].update({'csv':csv_df,
                    'rwp':rwp,
                    'a':a,
                    'b':b,
                    'c':c,
                    'alpha':al,
                    'beta':be,
                    'gamma':ga,
                    'volume':vol
                    })
    # Make Plots{{{
    def make_plots(self,save_figs = False, plot_diff = False, rietveld = False):
        with tqdm(total= len(self.data_dict)) as pbar:
            print('Working on Figures...')
            with tqdm(total = len(self.data_dict)) as pbar2:
                print('Working on Saving Figures...')
            
                for i, dict_entry in enumerate(self.data_dict.values()):
                    #This is where the xy file plots are made{{{
                    fn_no_xy = dict_entry['filename'].strip('.xy')+'_Simulated_Pattern'
                    ##################################################################
                    angle = dict_entry['angle'] 
                    y_calc = dict_entry['y_calc']
                    y_obs = dict_entry['y_obs']
                    y_diff = dict_entry['y_diff']
                    modified_diff_curve = dict_entry['modified_diff_curve'] 
                    ###################################################################
                     
                    fig,ax = plt.subplots()
                    if plot_diff == True:
                        fig2,ax2 = plt.subplots()
                        ax2.plot(angle,modified_diff_curve,'grey') #plots the fixed difference curve
                        ax2.plot(angle,y_obs,'b') #Plots observed
                        ax2.plot(angle,y_calc,'r')
                             
                        ax2.set_ylabel('Intensity')
                        ax2.set_xlabel(r'$2{\theta}^\circ$')
                        dict_entry.update({
                            'diff_fig': fig2,
                            'diff_ax': ax2
                            })
         
                         
                    dict_entry.update({
                        'fig': fig,
                        'ax': ax  
                        })
                    ax.plot(angle, y_calc, 'r')
                     
                    #Creating the plot titles. 
                    fn_list = fn_no_xy.split('_')
                    fn_list[0] = r'BiVO$_4$'
                    if rietveld == True:
                        fn_list[-2] = 'Rietveld' #This replaces the word 'simulation' with 'Rietveld'  
                    title = ' '.join(fn_list)
                    if plot_diff == True:
                        ax2.set_title(title+' Difference')
                    ax.set_title(title)
                    ax.set_ylabel('Intensity')
                    ax.set_xlabel(r'$2{\theta}^\circ$')
                    pbar.update(1) 
                    if save_figs == True:
                        figure_directory = self.data_folder+'/figures' #This gives the absolute path of the directory
                        if os.path.exists(figure_directory):
                            pass
                        else:
                            os.mkdir(figure_directory)
                        os.chdir(figure_directory)
                        #####################################################
                        if rietveld == True:
                            ###### Changes the name to rietveld. 
                            fig.savefig('BiVO4_Rietveld_{}.png'.format(dict_entry['number']))
                        elif rietveld ==False:
                            fig.savefig('BiVO4_Pattern_Sim_{}.png'.format(dict_entry['number']))
                        #####################################################
                        if plot_diff == True:
                            if rietveld == True:
                                ##### Changes the name to rieteveld
                                fig2.savefig('BiVO4_Rietveld_diff_{}.png'.format(dict_entry['number']))
                            elif rietveld == False:
                                fig2.savefig('BiVO4_Pattern_Sim_diff_{}.png'.format(dict_entry['number']))
                        #####################################################
                        pbar2.update(1)
                #}}}
            #This is where the .csv figures will be made.{{{
            if self.csv_files_loaded == True:   
                #We have csv data in out dictionary. 
                #These plots are put onto the self variable since there is only one for all files. 
                #################
                # Rwp Plot
                ################
                self.rwp_fig, self.rwp_ax = plt.subplots()
            
                self.rwp_ax.scatter(i,self.data_dict[i]['rwp'], color='b')
                self.rwp_ax.set_xlabel('Enumeration Figure')
                self.rwp_ax.set_ylabel(r'R$_{wp}$')
                self.rwp_ax.set_title(r'R$_{wp}$ Results')
                #################
                # Volume Plot
                #################
                self.vol_fig, self.vol_ax = plt.subplots()
               
                self.vol_ax.scatter(i,self.data_dict[i]['volume'], color='b')
                self.vol_ax.set_xlabel('Enumeration Figure')
                self.vol_ax.set_ylabel(r'Volume $\AA^3$') # \AA adds the angstrom symbol. 
                self.vol_ax.set_title('Volume Results')


                self.rwp_fig.savefig('BiVO4_Enumeration_Rwp_Plot.png')
                self.vol_fig.savefig('BiVO4_Enumeration_Volume_Plot.png')
            #}}} 
            os.chdir(self.data_folder)
    #}}}
    #Subplots{{{
    def subplot_creator(self, rows = 3,cols = 3,save_figs=True,show_diff = False):
        num_plots = len(self.data_dict)#This is the total number of plots to make. 
        plots_per_subplot = rows*cols #This defines the total number of plots per subplot. 
        if num_plots > plots_per_subplot:
            #print('num_plots: {}'.format(num_plots))#####################################################################
            #print('plots_per_subplot: {}'.format(plots_per_subplot))####################################################
            num_figs = num_plots//plots_per_subplot #This gives us the nearest whole number divisor
            #print('whole number divisor: {}'.format(num_figs))#########################################################
            if num_plots%plots_per_subplot != 0:
                num_figs+=1 #This adds in another figure to accommodate the whole number of figures. 
            #num_figs += num_plots % plots_per_subplot #This adds in the remainder
            #print('num_figs to be made: {}'.format(num_figs)) #######################################################################
            figure_range_intermediate = np.linspace(1,num_figs,num_figs) #This creates a range of integers that equals the number of figures. 
            figure_range = []
            for i in figure_range_intermediate:
                figure_range.append(np.int0(i))
            data_range_dictionary = {} #This creates a dictionary of the dividing points for the data for each subplot. 
            for i in figure_range:
                data_range_dictionary[i] = i*plots_per_subplot #This adds in the dividing lines. 
            #print('Data_Range_Dict: {}'.format(data_range_dictionary))############################################################
            #print('Figure_Range: {}'.format(figure_range))################################################################
        else:
            num_figs = 1
            figure_range = [1]
        self.figure_dictionary = {} #This creates a dictionary where the subplots will be kept. 
        for i in figure_range:
            subplot_fig = plt.figure(i) #Creates the figure object.
            subplot_fig.clear() #Make sure that the plot is cleared before being saved. 
            subplot_fig.set_size_inches(12,12.5) #Makes the figure a very large size (10 in. by 10 in.)
            #plt.tight_layout(w_pad = 2,h_pad = 3)
            '''
            I think that I need to add all of the axes here rather than down below. 
            This may preserve them a little bit better. I am not sure. May be worth trying. 
            '''
            self.figure_dictionary[i] = subplot_fig #we are adding each numbered figure to a dictionary of figures.
        '''
        Here is where the subplots are made. Using a progress bar. 
        '''
        with tqdm(total=len(figure_range)) as pbar:
            print('Generating {} Plots'.format(num_figs))
            for fig_num in figure_range:
                #print('Working on Figure #{}'.format(fig_num))##################################
                subplot_fig = self.figure_dictionary[fig_num] #we are calling the figure to add subplots to here.   
                x_axis = r'$2{\theta}^\circ$'
                y_axis = 'Intensity'
                subplot_fig.text(0.5,0.04, x_axis, ha = 'center')
                subplot_fig.text(0.04,0.5, y_axis, va = 'center', rotation='vertical')
             
                for i, f in enumerate(self.data_dict):
                    v =self.data_dict[i] #This ensures we go through the files in order. 
                    subplot_angle = v['angle']
                    subplot_y_obs = v['y_obs']
                    subplot_y_calc = v['y_calc']
                    subplot_y_diff = v['y_diff']
                    subplot_modified_y_diff = v['modified_diff_curve']
                    if fig_num!=1:
                        if i+1<=data_range_dictionary[fig_num] and i+1>data_range_dictionary[fig_num-1]:
                            #print('regular i: {}'.format(i))
                            #We have to do this because i becomes > the number of boxes we have in an nxm plot
                            corrected_i = i - data_range_dictionary[fig_num-1]
                            #print('corrected i:{}'.format(corrected_i)) #######################################
                            subplot_ax = subplot_fig.add_subplot(rows,cols,corrected_i+1) 
                            print('Row: {}, Col: {}, index: {}'.format(rows,cols,corrected_i+1))
                    elif fig_num == 1:
                        if i+1 <= data_range_dictionary[fig_num]:
                            #print('regular i: {}'.format(i)) #################################################3
                            subplot_ax = subplot_fig.add_subplot(rows,cols,i+1) 
                    if show_diff == True:
                        subplot_ax.plot(subplot_angle, subplot_modified_y_diff, 'grey')#This plots the difference curve. 
                    subplot_ax.plot(subplot_angle,subplot_y_obs,'b') #Plots the observed pattern
                    subplot_ax.plot(subplot_angle,subplot_y_calc,'r') #Plots the calculated pattern

                    plt.tight_layout(w_pad=3,h_pad=3)#This adds enough space between the plots so that nothing gets cut off. 
                    subplot_ax.ticklabel_format(axis='y', style='sci',scilimits=(0,0)) #This is here to force scientific notation for the y axis.
                    title = r"BiVO$_4$ {}".format(v['number'])
                 
                    subplot_ax.set_title(title)
                pbar.update(1)
        
        if save_figs == True:
            figure_directory = 'figures'
            if os.path.isdir(figure_directory):
                pass
            else:
                os.mkdir(figure_directory)
            os.chdir(figure_directory)
            with tqdm(total = len(figure_range)) as pbar2:
                print('Saving Figures...')
                for i, subplot_fig in enumerate(self.figure_dictionary.values()):
                    subplot_fig.savefig('BVO_{}_x_{}_grid_{}.png'.format(rows,cols,i))
                    pbar2.update(1)
                os.chdir(self.data_folder)
             
    #}}}
    
    #show_plots{{{
    def show_plots(self):

        plt.show()
            
    #}}}
    #Saving all of the Analysis{{{
    def save_work(self,data_name:'Input your filename to save your work.'):
        output_dir = 'Analyzed_Data' 
        if os.path.isdir(output_dir):
            pass
        else:
            os.mkdir(output_dir)
        os.chdir(output_dir)
        self.output_dir = os.getcwd()

        filename = '{}.pkl'.format(data_name)
        file_object = open(filename,'wb') #This serializes the class
        class_object = self #This is the class object 
        pickle.dump(class_object, file_object) #saves everything else.
        
        file_object.close()
    #}}}
#}}}

#Load_data{{{
def load_data(filename, folder = 'Analyzed_Data'):
    '''
    This is not something that can be run within a jupyter notebook. 
    '''
    current_directory = os.getcwd() #Saves our original place so we can return when data is loaded. 
    os.chdir(folder)
    file_object = open(filename,'rb')
    restored_class = pickle.load(file_object) #This will restore the data you saved.  
    file_object.close()
    os.chdir(current_directory) #return to the original location. 
    return restored_class
#}}} 
