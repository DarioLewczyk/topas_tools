#Imports{{{
import sys,os
import pandas as pd
import re
from tqdm import tqdm
#}}}
#Output_Analyzer Class{{{
class Output_Analyzer:
    def __init__(self, working_dir=os.getcwd()):
        self.working_dir = working_dir
        self.out_files = {}
        for f in os.listdir():
            if f.endswith('.out'):
                num = f.strip('.out').split('_')[-1]
                if num.isnumeric:
                    num = int(num)
                self.out_files[num] = f #This organizes the output files by number
        for number in tqdm(self.out_files.keys(),desc='Output_files',total=len(self.out_files)):
            curr_file = self.out_files[number]#This grabs the current output file

            full_dict = {}
            r_vals_dict = {}
            bkg_dict = {}
            coord_dict = {}
            #Coord dictionary labels{{{
            coord_dict['x'] = {}
            coord_dict['xlim'] = {}
            coord_dict['y'] = {}
            coord_dict['ylim'] = {}
            coord_dict['z'] = {} 
            coord_dict['zlim'] = {}
            coord_dict['B-values'] ={}
            coord_dict['Blim'] = {}
            coord_dict['Wyckoff'] = {}
            #}}}
            list_of_items_to_look_for = []
            lines_for_coords = []
            # Short Functions for the module {{{
            def is_refined(string:str):
                if re.findall('@',string):
                    return True
                else:
                    return False
            def strings_to_floats(lst:list):
                return[float(x) for x in lst]
            def get_words(string:str):
                words = re.findall(r'(\D+\d?\D+)\s', string.strip('\t')) #This will match with words even if they have numbers in them. But will exlude numbers separated by a space
                return words
            def get_numbers(string:str):
                if re.search(r'e\W+',string):
                    numbers = strings_to_floats(re.findall(r'\-?\d+\.?\d+\D+?\d+',string))#This ensures if scientific notation, it still works.
                else:
                    numbers = strings_to_floats(re.findall(r'\-?\d+\.?\d+',string)) #This searches for any number
                if len(numbers) == 1:
                    numbers = numbers[0]
                return(numbers)
            #}}}
            with open(curr_file) as f:
                for i, line in enumerate(f.readlines()):
                    #print(i, line)
                    # r value lines {{{
                    if re.search('r_exp',line):
                        '''
                        This if statement finds the line that gives information on the r values
                        and searches for words and associated decimal values. 
                        It will then pair the two up in a dictionary. 
                     
                        When the decimal is paired with the key, 
                        it is converted to a floating point number from a string. 
                        '''
                        words = get_words(line)
                        numbers = get_numbers(line)
                        for i, word in enumerate(words):
                            word = word.strip(' ')
                            r_vals_dict[word] = numbers[i]
                    #}}}
                    # Background {{{
                    elif re.search('bkg' ,line):
                        bkg_dict['ref_bkg'] = is_refined(line) #Checks if this is refined
                        values = get_numbers(line)
                        bkg_dict['chebychev_values']= values
                        bkg_dict['num_chebychev'] = len(values)
                    elif re.search('One_on_X',line):
                        one_on_x = True
                        values = get_numbers(line)
                        bkg_dict['ref_one_on_x'] = is_refined(line)
                        bkg_dict['one_on_x'] = values
                    #}}}
                    # Sample displacement{{{
                    elif re.search('Specimen_Displacement',line):
                        full_dict['specimen_displacement_ref'] = is_refined(line)
                        full_dict['specimen_displacement'] = get_numbers(line)
                    #}}}
                    # Scale factor{{{
                    elif re.search('scale',line):
                        full_dict['scale_refined'] = is_refined(line)
                        full_dict['scale']= get_numbers(line)
                     
                    #}}}
                    # Lattice {{{
                    elif re.search('site',line):
                        refined_line = re.findall(r'\S+',line)
                        lines_for_coords.append(refined_line)
                        site_label = refined_line[1]
                        num_posns = refined_line[3]
                        if len(refined_line)<21:
                            ###################
                            # This finds the 
                            # sites that are 
                            # not refined. 
                            ###################
                            # FInding the not refined things and correcting the cols. {{{
                            not_refined = re.findall(r'\t\w\s\D\d\.\d+',line)#Checks for the format: x number
                            for i, site in enumerate(not_refined):
                                if re.search('x',site):
                                     refined_line.insert(5,'Not_Refined') #This adds a Col 
                                    #print(site)
                                elif re.search('y',site):
                                    #print(site)
                                    refined_line.insert(8,'Not_Refined') # Adds a Col
                                elif re.search('z',site):
                                    #print(site)
                                    refined_line.insert(11,'Not_Refined') #Adds a Col
                                #########
                                #B-values
                                #########
                                not_ref_bvals = re.findall(r'b\S+\s+\d',line)
                                if not_ref_bvals:
                                    refined_line.insert(17, 'Not_Refined')#adding in a line here
                            #}}}
                        ## This finds the x coords (may also pick up the LIMIT flags)
                        x = re.findall(r'-?\d+\.\d+',refined_line[6])
                        ## This finds the y coords (may also pick up the LIMIT flags)
                        y = re.findall(r'-?\d+\.\d+',refined_line[9])
                        ## This finnds the z coords (may pick up the LIMIT flags)
                        z = re.findall(r'-?\d+\.\d+',refined_line[12])
                        # This finds the b-values (may pick up LIMIT flags)
                        bvals = re.findall(r'-?\d+\.?\d*',refined_line[18])
                        #X values{{{
                        if x:
                            #print('This is the original x: {}'.format(x))
                            if len(x)==2:
                                limit = x[1]
                                x.pop(1)#Ensures this stays as a single value
                            else:
                                limit = '0'
                            x = x[0]
                            coord_dict['x'].update({'{}'.format(site_label):float(x)})
                            coord_dict['xlim'].update({'{}'.format(site_label):float(limit)})
              
                            #coord_dict['{}_x_limit'.format(site_label)] = float(limit)
                            #print(x)
                        #}}}
                        #Y values{{{
                        if y:
                            #print('This is the original y: {}'.format(y))
                            if len(y)==2:
                                limit = y[1]
                                y.pop(1) #This ensures this stays as a single value. 
                            else:
                                limit = '0'
                            y = y[0]
                            coord_dict['y'].update({'{}'.format(site_label):float(y)})
                            coord_dict['ylim'].update({'{}'.format(site_label):float(limit)})
                            #coord_dict['{}_y'.format(site_label)] = strings_to_floats(y)
                            #coord_dict['{}_y_limit'.format(site_label)] = float(limit)
                            #print(y)
                        #}}}
                        #Z values{{{
                        if z:
                            #print('This is the original z: {}'.format(z))
                            if len(z)==2:
                                limit = z[1]
                                z.pop(1)#Ensures this stays as a single value
                            else:
                                limit = '0'
                            z = z[0]
                            coord_dict['z'].update({'{}'.format(site_label):float(z)})
                            coord_dict['zlim'].update({'{}'.format(site_label):float(limit)})
                        #}}}
                        #B-values{{{
                        if bvals:
                            if len(bvals)==2:
                                limit = bvals[1]
                                bvals.pop(1)
                            else:
                                limit = '0'
                            bvals = bvals[0]
                            coord_dict['B-values'].update({site_label:float(bvals)})
                            coord_dict['Blim'].update({site_label:float(limit)})
                        #}}}
                        #Wyckoff symbols{{{
                        coord_dict['Wyckoff'].update({site_label:refined_line[-1]}) #Wyckoff symbol is the last line.
                        #}}}
                 
                        #print(refined_line[12])
                        #print(line)
                    #}}}
            full_dict.update(r_vals_dict)
            full_dict.update(bkg_dict)
            full_dict.update(coord_dict)
            
            #Creating the tables{{{
            #columns=['','Site','','Num Positions', '', '', 'x', '', '', 'y', '', '', 'z', '', 'Atom', 'Occupancy', '', '', 'B', '', 'Wyckoff']
            #coordinate_table = pd.DataFrame(lines_for_coords,columns = columns)#This compiles a table of all of the atomic coordinates
            coordinate_table = pd.DataFrame(coord_dict)
            background_table = pd.DataFrame(bkg_dict) #This creates the table with all of the background items.
            r_value_table = pd.DataFrame(r_vals_dict,index = [0]) #The index on this table is to tell pandas that it only needs to print one row for the table. 

            #}}}
            # Writing the Excel File {{{
            dir_name = 'Output_File_Excel_Sheet'
            if os.path.exists('{}/{}'.format(os.getcwd(),dir_name)):
                pass
            else:
                os.mkdir(dir_name)
            os.chdir('{}/{}'.format(os.getcwd(),dir_name))
            writer = pd.ExcelWriter('{}.xlsx'.format(curr_file.strip('.out'))) #This sets the excel file to the name of the output file.
            coordinate_table.to_excel(writer, 'Site Information')
            background_table.to_excel(writer, 'Background')
            r_value_table.to_excel(writer, 'R-value Information')
            writer.save()
            #}}}
            os.chdir(self.working_dir) #This ensures we always get back to the working directory after each loop.
 #}}}
