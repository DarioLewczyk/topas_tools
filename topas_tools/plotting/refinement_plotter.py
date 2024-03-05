# Authorship: {{{
# Written by: Dario Lewczyk
# Date: 02-20-2024
#}}}
# Imports: {{{
import copy
import numpy as np
import plotly.graph_objects as go
import re
from topas_tools.plotting.plotting_utils import PlottingUtils
from topas_tools.utils.topas_utils import UsefulUnicode
from topas_tools.utils.topas_utils import Utils
#}}}
# RefinementPlotter: {{{
class RefinementPlotter(PlottingUtils):
    '''
    This class is used to handle the plotting 
    and visualization of data collected after
    automated Rietveld Refinements have been
    accomplished.
    '''
    # __init__: {{{
    def __init__(self,rietveld_data:dict ={}):
        self.rietveld_data = rietveld_data 
        super().__init__(rietveld_data=self.rietveld_data)
    #}}} 
    # plot_pattern: {{{
    def plot_pattern(self,
            index:int = 0,  
            time_units:str = 'min', 
            rwp_decimals:int = 2,
            temp_decimals:int = 2,
            printouts:bool = True,
            run_in_loop:bool = False,
            specific_substance:str= None,
            plot_calc_patterns:bool = True,
            plot_hkli:bool = True,
            filter_hkli:bool = True,
            single_pattern_offset:float = 0,
            hkli_offset:float = -60,
            use_calc_temp:bool = True, 
            **kwargs,
        ):
        '''
        This will allow us to plot any of the loaded patterns 

        plot_hkli will allow hkl to be plotted for each phase IF the data are present

        since you run "get_data()" first, self.check_order will be in place. This will ensure the proper time is recorded.

        use *args or  **kwargs to pass through relevant plot stylings.
        1. template
        2. tth_range or xrange or x_range
        3. y_range or yrange
        4. height
        5. width
        6. show_legend
        7. legend_x 
        8. legend_y
        9. legend_xanchor
        10. legend_yanchor
        11. font_size
        12. button_xanchor
        13. button_yanchor
        14. button_x 
        15. button_y
        16. showgrid
        17. dtick
        18. ticks
        19. phase_colors # If you choose to give colors for each of the individual phases
        '''
        # assign variables from kwargs: {{{
        # default kwargs: {{{
        self._default_kwargs = {
            'template' : 'simple_white',
            'tth_range' : None,
            'yrange' :None,
            'height':800,
            'width':1000,
            'show_legend':True,
            'legend_x':None,
            'legend_y':None,
            'legend_xanchor':None,
            'legend_yanchor':None,
            'font_size':20,
            'button_xanchor':'right',
            'button_yanchor':'top',
            'button_x':1.45,
            'button_y':1.05,
            'showgrid':False,
            'dtick':1,
            'ticks':'inside',
            'phase_colors': None,
        }
        #}}}  
        # Apply any kwarg updates: {{{
        alternates = {
            'tth_range': ['tth_range', 'xrange', 'x_range'], 
            'yrange': ['yrange', 'y_range'], 
            'phase_colors': ['colors', 'phase_colors']
        }
        Utils._update_default_kwargs(self, 
            kwargs=kwargs,
            alternates=alternates,
        )
        #}}}
        # Set variables from the dictionary: {{{
        template = Utils._get_kwarg(self,'template')
        tth_range = Utils._get_kwarg(self,'tth_range')
        yrange = Utils._get_kwarg(self,'yrange')
        height = Utils._get_kwarg(self,'height')
        width = Utils._get_kwarg(self,'width')
        show_legend = Utils._get_kwarg(self,'show_legend')
        legend_x = Utils._get_kwarg(self,'legend_x')
        legend_y = Utils._get_kwarg(self,'legend_y')
        legend_xanchor = Utils._get_kwarg(self,'legend_xanchor')
        legend_yanchor = Utils._get_kwarg(self,'legend_yanchor')
        font_size = Utils._get_kwarg(self,'font_size')
        button_xanchor = Utils._get_kwarg(self,'button_xanchor')
        button_yanchor = Utils._get_kwarg(self,'button_yanchor')
        button_x = Utils._get_kwarg(self,'button_x')
        button_y = Utils._get_kwarg(self,'button_y')
        showgrid = Utils._get_kwarg(self,'showgrid')
        dtick = Utils._get_kwarg(self,'dtick')
        ticks = Utils._get_kwarg(self,'ticks')
        phase_colors = Utils._get_kwarg(self,'phase_colors')
        #}}}
            
        #}}} 
        # Check if data were collected:{{{
        if not self._data_collected:
            print('You did not yet collect data. Do that now...')
            self.get_data()
        #}}} 
        hovertemplate = f"2{self._theta}{self._degree}" + "%{x}<br>Intensity: %{y}"
        data = self.rietveld_data[index] # This gives us the entry we are interested in. 
        # Get a formatted string from csv: {{{
        self._create_string_from_csv_data(index) # This gives a variable called "self._csv_string" for us to print out. 
        #}}} 
        # Get the time the pattern was taken: {{{
        self._get_time(index,time_units,check_order=self.check_order) # This gives us "self._current_time" which is the time in the units we wanted. 
        #}}}
        # Get the plot values and labels: {{{
        tth = self.rietveld_data[index]['xy']['2theta'] # this is the array of 2 theta values
        keys = list(self.rietveld_data[index]['xy'].keys())[1:] # These are the keys we care about. 
        if use_calc_temp:
            temp = self.rietveld_data[index]['corrected_temperature'] 
            temp_label = 'Corrected Temp'
        else:
            temp = self.rietveld_data[index]['temperature']
            temp_label = 'Element Temp'
        #}}}
        # Generate the figure: {{{
        self.pattern_plot = go.Figure()
        colors = ['blue', 'red', 'grey']
        # Add the plots: {{{
        for i, key in enumerate(keys):
            self.pattern_plot.add_scatter(
                x = tth,
                y = self.rietveld_data[index]['xy'][key],
                hovertemplate = hovertemplate,
                marker = dict(
                    color = colors[i],
                ),
                name = key,
            )
        #}}}
        # plot the hkli: {{{
        if plot_hkli and self.sorted_hkli:
            hkli = data['hkli'] # This is the hkli entry but its keys are indices of the substances. 
            for i in hkli:
                # Get Data for HKLI Plot: {{{
                substance = hkli[i]['substance']
                hkli_data = hkli[i]['hkli']
                hkl = copy.deepcopy(hkli_data['hkl']) # 3-tuple of h,k,l
                hkl_tth = copy.deepcopy(hkli_data['tth'])
                hkl_i = copy.deepcopy(hkli_data['i']) # This is a list of all intensities
                hkl_d = copy.deepcopy(hkli_data['d'])
                ones = np.ones(len(hkl_tth)) 

                hkl_intensity = [hkli_offset*(i+1)]*ones # Make a list of intensities arbitrarily starting from 10.
                
                hkl_hovertemplate = []
                hkl_ht = '{}<br>hkl: {}<br>d-spacing: {} {}<br>Intensity: {}<br>' # Format: Substance, hkl, d-spacing, intensity
                hkli_indices_to_remove = [] # If you want to filter, these indices will be removed
                for idx, mi in enumerate(hkl):
                    hkli_intensity = hkl_i[idx] # This is the intensity of the current hkl
                    intermediate_hkli_ht = hkl_ht.format(substance,mi,hkl_d[idx],self._angstrom, np.around(hkl_i[idx],6))+f'2{self._theta}{self._degree}'+"%{x}"
                    if filter_hkli:
                        if hkli_intensity > 0:
                            hkl_hovertemplate.append(intermediate_hkli_ht) # Add the hovertemplate 
                        else:
                            hkli_indices_to_remove.append(idx)

                    else:
                        hkl_hovertemplate.append(intermediate_hkli_ht) # Add the hovertemplate

                #}}}
                # Remove filtered hkli indices: {{{
                if hkli_indices_to_remove:
                    hkl_intensity = list(hkl_intensity)
                    hkl = list(hkl)
                    hkl_tth = list(hkl_tth)
                    hkl_d = list(hkl_d)
                    hkli_indices_to_remove.reverse() 
                    for idx in hkli_indices_to_remove:
                   
                        hkl_intensity.pop(idx)
                        hkl.pop(idx)
                        hkl_tth.pop(idx)
                        hkl_d.pop(idx)
                  
                    hkl_intensity = np.array(hkl_intensity)
                    hkl = np.array(hkl)
                    hkl_tth = np.array(hkl_tth)
                    hkl_d = list(hkl_d)
                #}}}
                if not phase_colors:
                    hkl_color = self._get_random_color()
                else:
                    try:
                        if type(phase_colors) == list:
                            hkl_color = phase_colors[i]
                        elif type(phase_colors) == dict:
                            hkl_color = phase_colors[substance] 
                    except:
                        hkl_color = self._get_random_color()
                # Get Data for Phase Plots: {{{
                if self.sorted_phase_xy and plot_calc_patterns:
                    phase_data = data['phase_xy']
                    phase_substance = phase_data[i]['substance']
                    phase_tth= phase_data[i]['tth']
                    phase_ycalc= phase_data[i]['ycalc']
                    self.pattern_plot.add_scatter(
                            x = phase_tth,
                            y = np.array(phase_ycalc)+single_pattern_offset*(i+1), #If you give an offset, it will apply to each pattern and will offset based upon the index of the pattern
                            hovertemplate = hovertemplate,
                            marker = dict(
                                color = hkl_color,
                            ),
                            name = f'{phase_substance} phase',
                    )
                #}}}
                # Plot the Actual HKLs: {{{
                self.pattern_plot.add_scatter(
                    x = hkl_tth,
                    y = hkl_intensity,
                    hovertemplate = hkl_hovertemplate,
                    marker = dict( 
                        symbol = 'line-ns',
                        line = dict(
                            width = 2,
                            color = hkl_color,
                        ), 
                        size = 15,
                        color = hkl_color,
                    ),
                    mode = 'markers',
                    name = f'{substance} hkl',
                )

                #}}}

        #}}}
        # plot background: {{{
        if self.sorted_bkg_xy:
            bkg_data = data['bkg']
            bkg_tth = bkg_data['tth']
            bkg_ycalc = bkg_data['ycalc']
            self.pattern_plot.add_scatter(
                x = bkg_tth,
                y = bkg_ycalc,
                hovertemplate = hovertemplate,
                marker = dict(
                    color = 'black',
                ),
                name = 'Background',
            )
        #}}}
        #Update the layout: {{{
        #Get Info for Updating Layout: {{{
        if tth_range == None:
            tth_range = [min(tth), max(tth)] # plot the whole range
        
        title_text = f'Time: {np.around(self._current_time,2)} {time_units}, ({temp_label}: {np.around(temp,temp_decimals)}{self._deg_c}) Rwp: {np.around(self._rwp,rwp_decimals)}'
        xaxis_title = f'2{self._theta}{self._degree}'
        yaxis_title = 'Intensity'
        #}}}
        self._update_pattern_layout(
            fig=self.pattern_plot,
            title_text=title_text,
            xaxis_title=xaxis_title,
            yaxis_title=yaxis_title,
            tth_range=tth_range,
            yrange = yrange,
            template=template,
            font_size=font_size,
            height=height,
            width = width,
            show_legend=show_legend,
            legend_x = legend_x,
            legend_y = legend_y,
            legend_xanchor = legend_xanchor,
            legend_yanchor= legend_yanchor,
            showgrid = showgrid,
            dtick = dtick,
            ticks = ticks,
        ) 
        #}}}
        # Update buttons: {{{
        self._add_buttons(self.pattern_plot,xanchor=button_xanchor,yanchor=button_yanchor,button_x=button_x,button_y=button_y,plot_calc_patterns=plot_calc_patterns)
        #}}}
        #}}}
        # Printouts: {{{
        if printouts:
            print('Additional Refinement Information:')
            print(self._csv_string)
            el_t = np.around(self.rietveld_data[index]["temperature"],2)
            c_t = np.around(self.rietveld_data[index]["corrected_temperature"],2)
            mint = np.around(self.rietveld_data[index]["min_t"],2)
            maxt = np.around(self.rietveld_data[index]["max_t"],2)

            print(f'Element Temperature: {el_t}{self._deg_c}\n'+
                    f'Corrected Temperature: {c_t}{self._deg_c}\n'+
                    f'Min Corrected Temperature: {mint}{self._deg_c}, Max Corrected Temperature: {maxt}{self._deg_c}'
                    )
        #}}}
        # Standard Output: {{{
        if not run_in_loop:
            self.pattern_plot.show()
        #}}}
        # Loop Output: {{{
        else:
            if specific_substance == None:
                yobs = self.rietveld_data[index]['xy']['yobs']
                ycalc = self.rietveld_data[index]['xy']['ycalc']
                ydiff = self.rietveld_data[index]['xy']['ycalc']
                hovertemplate = f'{title_text}<br>Pattern Index: {index}<br>' + hovertemplate
                #title = f'Time: {np.around(self._current_time,2)} {time_units}, ({temp_label}: {np.around(temp,temp_decimals)}{self._deg_c}) Rwp: {np.around(self._rwp,rwp_decimals)}',  
            else:
                phases = self.rietveld_data[index]['phase_xy'] 
                for key in phases:
                    entry = phases[key]
                    substance = entry['substance']
                    if substance == specific_substance:
                        ycalc = entry['ycalc'] # This is the calculated y for the given substance.
                title_text = f'{title_text} {specific_substance} Series'
                yobs = None
                ydiff = None
                hovertemplate = f'{title_text}<br>Pattern Index: {index}<br>Substance: {specific_substance}<br>'+hovertemplate 
            return(tth,yobs, ycalc, ydiff, hovertemplate, title_text, xaxis_title, yaxis_title)
        #}}}
    #}}}
    # plot_csv_info: {{{
    def plot_csv_info(self, 
            plot_type:str = 'rwp',
            use_out_data:bool = False,
            plot_temp:bool = True,
            use_calc_temp:bool = True,
            time_units:str = 'min', 
            normalized:bool = False,
            time_range:list = None,
            y_range:list = None,
            height = 800,
            width = 1100,
            font_size = 20,
            yaxis_2_position = 0.15,
            additional_title_text:str = None,
            specific_substance:str = None,
            legend_x:float = 0.99,
            legend_y:float = 1.2,
            legend_xanchor:str = 'right',
            legend_yanchor:str = 'top',
            debug:bool = False,
            ticks:str = 'inside',
            ):
        ''' 
        plot_type: This can be any of the below. 
            1.) "lattice parameters" or "lattice" or "lp"
            2.) "scale factor" or "sf"
            3.) "rwp" 
            4.) "volume" or "vol"
            5.) "Rbragg" or "rb"
            6.) "Weight Percent" or "wp"
            7.) "B values" or "beq" or "bvals" 
            8.) "Size L" or "csl" or "sizel"
            9.) "Size G" or "csg" or "sizeg"
            10.) "Strain L" or "strl" or 'strainl'
            11.) "Strain G" or "strg" or 'straing'
            12.) "eta"
            13.) "stephens"


        if you want to plot data from "out" files, set the "use_calc_temp" to True

        The purpose of this function is to give the user a 
        look at the data output in csv form by TOPAS at the 
        conclusion of the refinement series. 

        This is a little complex since we do not necessarily know what we want to plot 
        the user will decide that. 

        "specific_substance": Allows you to plot only data from one substance at a time

        some things I am thinking about are: 

        Rwp:
            x = pattern number
            y = Rwp value
        lattice parameter:
            x = pattern number
            y = lattice parameter / Angstrom
        scale factor: 
            x = pattern numebr
            y = scale factor

        For each of these, we would need to know 

        '''
        if specific_substance != None and type(specific_substance) == str:
            specific_substance = [specific_substance]
        plot_type = plot_type.lower() # This ensures everything is lowercase.
        if not self._data_collected:
            print('You did not yet collect data. Do that now...')
            self.get_data()
        # Determine what to look for in the data: {{{
        yaxis_title = '' # DEfault
        yaxis2_title = '' # Default
        xaxis_title = f'Time / {time_units}'
        # Lattice Params: {{{ 
        if plot_type == 'lattice parameters' or plot_type == 'lattice' or plot_type == 'lp':
            keys = ['a','b','c', 'al','be','ga', 'alpha', 'beta', 'gamma'] # These are the 
            yaxis_title = f'Lattice Parameter / {self._angstrom}' # This is the a, b, c lattice parameter title
            yaxis2_title = f'Lattice Parameter / {self._degree}' # this is the al, be, ga lattice parameter title
            title = 'Lattice Parameters'
        #}}}
        # Scale Factor: {{{
        elif plot_type == 'scale factor' or plot_type == 'sf':
            keys = ['scale_factor', 'sf','scale factor'] # These are the variations likely to be used
            yaxis_title = 'Scale Factor'
            title = 'Scale Factor'
            normalized = True
        #}}}
        # Rwp: {{{
        elif plot_type == 'rwp':
            keys = ['rwp']
            yaxis_title = 'Rwp'
            title = 'Rwp'
        #}}}
        # Volume: {{{
        elif plot_type == 'volume' or plot_type == 'vol':
            keys = ['vol', 'volume', 'cell volume', 'cell_volume']
            yaxis_title = f'Volume / {self._angstrom}{self._cubed}'
            title = 'Volume'
        #}}}
        # R Bragg: {{{
        if plot_type == 'rbragg' or plot_type == 'rb':
            keys = ['r bragg','r_bragg'] # this tells the code what to search for
            yaxis_title = 'R Bragg'
            title = 'R Bragg'
        #}}}
        # Weight Percent: {{{
        if plot_type == 'weight percent' or plot_type == 'wp': 
            keys = ['weight percent', 'weight_percent']
            yaxis_title = 'Weight Percent'
            title = 'Weight Percent'
        #}}}
        # B-values: {{{
        if plot_type == 'b values' or plot_type == 'beq' or plot_type == 'bvals':
            keys = ['bvals', 'beq','bval', 'b value', 'b val', 'b values', 'b_value','b_val','b_values','B'] # tells the code what the likely keywords to look for are.
            yaxis_title = 'B-Values'
            title = 'B-Values'
        #}}}
        # Size L: {{{
        if plot_type == 'size l' or plot_type == 'csl' or plot_type == 'sizel':
            keys = ['size_l', 'csl','lorentzian_size','Size_L','cslv']
            yaxis_title = 'Lorentzian Size'
            title = 'Lorentzian Size'
        #}}}
        # Size G: {{{
        if plot_type == 'size g' or plot_type == 'csg' or plot_type == 'sizeg':
            keys = ['size_g', 'csg','gaussian_size','Size_G', 'csgv']
            yaxis_title = 'Gaussian Size'
            title = 'Gaussian Size' 
        #}}}
        # Strain L: {{{ 
        if plot_type == 'strain l' or plot_type == 'strl' or plot_type == 'strainl':
            keys = ['strain_l', 'strl','lorentzian_strain','Strain_L','slv']
            yaxis_title = 'Lorentzian Strain'
            title = 'Lorentzian Strain'
        #}}}
        # Strain G: {{{
        if plot_type == 'strain g' or plot_type == 'strg' or plot_type == 'straing':
            keys = ['strain_g', 'strg','gaussian_strain','Strain_G','sgv']
            yaxis_title = 'Gaussian Strain'
            title = 'Gaussian Strain' 
        #}}}
        # Lvol: {{{ 
        if plot_type.lower() == 'lvol':
            keys = ['lvol']
            yaxis_title = 'LVol'
            title = 'LVol'
        #}}}
        # Lvolf: {{{
        if plot_type.lower() == 'lvolf': 
            keys = ['lvolf']
            yaxis_title = 'Lvolf'
            title = 'LVolf'
        #}}}
        # e0: {{{ 
        if plot_type.lower() == 'e0':
            keys = ['e0']
            yaxis_title = f'e{self._subscript_zero}'
            title = f'e{self._subscript_zero}'
        #}}}
        # phase_MAC: {{{
        if plot_type.lower() == 'phase_mac':
            keys = ['phase_MAC']
            yaxis_title = 'Phase MAC'
            title = 'Phase MAC'
        #}}}
        # cell_mass: {{{
        if plot_type.lower() == 'cell_mass' or plot_type.lower() == 'cm' or plot_type.lower == 'mass':
            keys = ['cell_mass']
            yaxis_title = 'Cell Mass'
            title = 'Cell Mass'
        #}}}
        # eta: {{{
        if plot_type.lower() == 'eta':
            keys = ['eta']
            yaxis_title = 'Eta'
            title = 'Eta Values'
        #}}}
        # stephens: {{{
        if plot_type.lower() == 'stephens':
            keys = [
                's400',
                's040',
                's004',
                's220',
                's202',
                's022',
                's310',
                's103',
                's031',
                's130',
                's301',
                's013',
                's211',
                's121',
                's112',
            ]
            yaxis_title = 'Stephens Parameter'
            title = 'Stephens Parameters'
        #}}}
        #}}}
        # Update the title text: {{{
        if additional_title_text:
            title = f'{additional_title_text} {title}' # combines what the user wrote with the original title.
        #}}}
        # For the CSV Data, we need to find the data that we care about inside of self.csv_plot_data: {{{
        self._sort_csv_keys() # This gets self.csv_plot_data
        for entry in self.rietveld_data:
            if plot_temp:
                if 'temperature' not in self.csv_plot_data:
                    self.csv_plot_data['temperature'] = []
                if use_calc_temp:
                    t = self.rietveld_data[entry]['corrected_temperature']
                    temp_label = 'Corrected Temperature'
                else:
                    t = self.rietveld_data[entry]['temperature']
                    temp_label = 'Element Temperature'

                self.csv_plot_data['temperature'].append(t) # Record the temperature
            if 'time' not in self.csv_plot_data:
                self.csv_plot_data['time'] = []
            self._get_time(entry,time_units, check_order = self.check_order) # This gives us the time in the units we wanted (self._current_time)
            self.csv_plot_data['time'].append(self._current_time) # Add the time
        # IF YOU WANT TO USE THE OUTPUT, Also DEFINE plot_data : {{{
        if use_out_data:
            self._sort_out_keys() # This gets self.out_plot_dict
            self.out_plot_dict['temperature'] = self.csv_plot_data['temperature']
            self.out_plot_dict['time'] = self.csv_plot_data['time']
            plot_data = self.out_plot_dict # This local dictionary will be used to make the plot in this function. 
        else:
            plot_data = self.csv_plot_data # This is the local dictionary used to make the plot. 
        #}}}
        #}}}
        # plot the data: {{{
        fig = go.Figure()
        second_yaxis = False
        third_yaxis = False
        x = plot_data['time']
        base_ht = f'Time/{time_units}: '+'%{x}<br>' # This is the basis for all hovertemplates
        
        if keys == ['rwp']:
            hovertemplate = base_ht+'Rwp: %{y}'
            y = plot_data['rwp']
            fig.add_scatter(
                    x = x,
                    y = y,
                    hovertemplate = hovertemplate, 
                    yaxis = 'y1',
                    name = 'Rwp',
            )
            

        else:
            for substance in plot_data:
                color = self._get_random_color() # This gives us a color
                if not specific_substance:
                    usr_substance = substance.lower() # If a specific substance is not given, it is set as the current. 
                else:
                    for sub in specific_substance:
                        if sub.lower() == substance.lower():
                            usr_substance = sub.lower()
                            break
                        else:
                            usr_substance = None
                
                if substance != 'time' and substance != 'temperature' and substance != 'rwp' and substance.lower() == usr_substance:
                    entry = plot_data[substance] # This will be a dictionary entry with keys. 
                    entry_keys = list(entry.keys()) # These will be the keys for the entry. 
                    if debug:
                        print(f'ENTRY KEYS: {entry_keys}')
                    for plot_key in entry_keys:
                        try:
                            # This will be done to see if there are any matches to a value that may have a number.
                            
                            numerical_check = re.findall(r'(\w+\d*)*.',plot_key)[0] # This will match to anything that represents a formula.
                            numerical_check = numerical_check.strip(f'{substance}_')
                            if 'b_value' in numerical_check:
                                numerical_check = 'b_value'
                        except:
                            numerical_check = ''
                        if plot_key.lower() in keys or plot_key.strip(f'{substance}_') in keys or numerical_check in keys: # Need to check if the keys we are searching for are present.
                            if debug:
                                print(f'PASSED TEST: \n\tplot key: {plot_key}\n\tnumerical check: {numerical_check}\n')
                            # Handle most cases: {{{ 
                            if plot_key != 'al' or plot_key != 'be' or plot_key != 'ga' or plot_key != 'alpha' or plot_key != 'beta' or plot_key != 'gamma':
                                if specific_substance:
                                    color = self._get_random_color() # Set a specific color for each lattice parameter if only one substance plotted. 
                                # This is the default section since units should be consistent enough. 
                                # Get the data: {{{
                                if normalized:
                                    y = self._normalize(entry[plot_key]) # This will normalize the plot data
                                else:
                                    y = entry[plot_key] # This will just give us the data
                                #}}}
                                hovertemplate = base_ht +f'{yaxis_title} ({substance}, {plot_key}): '+'%{y}' # This gives us the hovertemplate for this part.
                                # Add the scatter (Y1): {{{
                                fig.add_scatter(
                                    x = x,
                                    y = y,
                                    hovertemplate = hovertemplate,
                                    name = f'{substance} {plot_key}',
                                    mode = 'lines+markers',
                                    marker = dict(
                                        color = color,
                                    ),
                                    line = dict(
                                        color = color,
                                    ),
                                    yaxis = 'y1',
                                )
                                #}}}
                             
                            #}}}
                            # Handle the case where we need to plot lattice angles: {{{
                            else:
                                # In this case, we need a second y axis for the degrees.
                                # get the data: {{{
                                if normalized:
                                    y = self._normalize(entry[plot_key])
                                else:
                                    y = entry[plot_key]
                                #}}}
                                hovertemplate = base_ht + f'{yaxis2_title} ({substance}, {plot_key}): '+'%{y}'
                                # Add the scatter (Y2):{{{
                                fig.add_scatter(
                                    x = x,
                                    y = y,
                                    hovertemplate = hovertemplate,
                                    name = f'{substance} {plot_key}',
                                    mode = 'lines+markers',
                                    marker = dict(
                                        color = color,
                                    ),
                                    line = dict(
                                        color = color,
                                    ),
                                    yaxis = 'y2',
                                ) 
                                second_yaxis = True
                                #}}}
                            #}}}
        # Plot temp data: {{{
        if plot_temp:
            yaxis3_title = f'{temp_label} /{self._deg_c}'
            hovertemplate = base_ht + f'{temp_label}/{self._deg_c}: '+'%{y}'
            fig.add_scatter(
                x = x,
                y = plot_data['temperature'],
                hovertemplate = hovertemplate,
                yaxis = 'y3',
                name = f'{temp_label}/{self._deg_c}',
                mode = 'lines+markers',
                marker = dict(color = 'red'),
                line = dict(color = 'red'),
            )
            third_yaxis = True
        #}}}
        # Update layout: {{{
        if time_range == None:
            time_range = [min(x), max(x)]
        # Update the first y axis and plot: {{{
        fig.update_layout(
            height = height,
            width = width,
            title_text = f'Plot of {title} vs. Time',
            xaxis = dict(
                title = xaxis_title,
                domain = [yaxis_2_position, 1], # the active area for x axis
                range = time_range,
                ticks = ticks,
            ), 
            yaxis = dict(
                title = yaxis_title,
                ticks = ticks,
            ),
            font = dict(
                size = font_size,
            ),
            template = 'simple_white',
            legend = dict(
                yanchor = legend_yanchor,
                xanchor = legend_xanchor,
                y = legend_y,
                x = legend_x,
            ),

        )
        #}}}
        if y_range:
            fig.update(layout_yaxis_range = y_range)
        # if second y axis: {{{
        if second_yaxis:
            fig.update_layout(
                yaxis2 = dict(
                    title = yaxis2_title,
                    anchor = 'free',
                    overlaying = 'y',
                    side = 'left',
                    position = yaxis_2_position,
                    ticks = ticks,
                ),
            )
        #}}}
        # if third axis: {{{
        if third_yaxis:
            fig.update_layout(
                yaxis3 = dict(
                    title = yaxis3_title,
                    anchor = 'x',
                    overlaying = 'y',
                    side = 'right',
                    ticks = ticks,

                ),
            )
        #}}}
        #}}}

        #}}}
        fig.show()     
    #}}}
    # plot_multiple_patterns: {{{
    def plot_multiple_patterns(self,
            indices= None, 
            waterfall:bool = False,
            fig_title:str = 'Multi Pattern Plot', 
            template:str = 'simple_white',
            offset:float = 0,
            show_ycalc:bool = True,
            show_ydiff:bool = False,
            time_units:str = 'min', 
            tth_range:list = None,
            use_calc_temp:bool = True,
            height = 800,
            width = 1000,
            show_legend:bool = True,
            legend_x:float = 0.99,
            legend_y:float = 0.99,
            legend_xanchor:str = 'right',
            legend_yanchor:str = 'top',
            font_size:int = 20,
            rwp_decimals:int = 2,
            temp_decimals:int = 2, 
            standard_colors:bool = False,
            specific_substance:str= None,
            zmin_args:tuple = (-10, 5), # The first is the minimum intensity button, the second is the number of buttons
            zmax_args:tuple = (10, 5), # The first is the minimum I for the max buttons and the second is the number of buttons
            button_layer_1_height = 1.17,
            button_layer_2_height = 1.1,
            showgrid:bool = False,
            dtick:float = 1,
            ticks:str = 'inside',
            plot_total_intensity_v_time = False,
            ):
        '''
        '
        This function will run a loop mode of "plot_pattern"
        This allows us to have multiple pattern fits overlaid on 
        one-another.

        Use the "offset" to change the spacing of the patterns.

        The "indices" can be either a list of specific files or a
        3-tuple that goes into np.linspace(low, high, number) 

        "standard_colors": If True, this will default to the standard color scheme

        using "specific_substance" you can plot the phase contribution of a single substance over time
        '''
        self._max_i = 0
        if type(indices) == tuple:
            lo,hi,num = indices
            indices= np.around(np.linspace(lo,hi,num),0) #Creates a range
        self.multi_pattern = go.Figure()
        if waterfall:
            # This necessitates a more complex list structure. 
            self.x = [] # This is going to be 2 theta range
            self.y = [] # This is the time axis
            self.z = [] # This will be a list of lists for intensity.
        if plot_total_intensity_v_time:
            self.x = [] # This will be the time range
            self.y = [] # This will be the observed intensity
            self.ycalc= [] # This will be the calculated intensity
            self.temp = [] # This holds the temp
             
        for index, i in enumerate(indices):
            # Get the data for current index: {{{ 
            tth, yobs, ycalc, ydiff, hovertemplate, title_text, xaxis_title, yaxis_title = self.plot_pattern(
                index= i, 
                template= template,
                time_units= time_units, 
                tth_range=tth_range,
                use_calc_temp=use_calc_temp,
                height =height,
                width =width,
                font_size=font_size,
                rwp_decimals= rwp_decimals,
                temp_decimals= temp_decimals,
                printouts=False,
                run_in_loop=True,
                specific_substance = specific_substance,
            )
            if not specific_substance:
                if max(yobs) > self._max_i:
                    self._max_i = max(yobs)
            else:
                if max(ycalc) > self._max_i:
                    self._max_i = max(ycalc)
            #}}}
            # If You Want a Waterfall: {{{
            if waterfall:  
                time = np.around(self.rietveld_data[i]['corrected_time']/60,4) 
                self.x = tth # This only needs to be 1 series.
                self.y.append(time) # This puts it into minutes
                if not specific_substance:
                    self.z.append(yobs) # This adds the observed intensity.
                else:
                    self.z.append(ycalc) # Adds calculated intensity
                hovertemplate = f"2{self._theta}{self._degree}" + "%{x}<br>Intensity: %{z}<br>" + "Time: %{y}<br>"
            #}}}
            # Not a waterfall: {{{
            elif not waterfall and not plot_total_intensity_v_time: 
                color1 = self._get_random_color()
                color2 = self._get_random_color()
                color3 = self._get_random_color()
                if standard_colors:
                    colors = ['blue','red','grey']
                else:
                    colors = [color1, color2, color3]
                if not specific_substance:
                    ydict = {'yobs':yobs}
                else:
                    ydict = {'ycalc':ycalc}
                if show_ycalc:
                    ydict.update({'ycalc':ycalc})
                if show_ydiff:
                    ydict.update({'ydiff':ydiff}) 
                # Add the plots: {{{ 
                for j, key in enumerate(ydict):
                    if not specific_substance:
                        self.multi_pattern.add_scatter(
                            x = tth,
                            y = np.array(ydict[key])+(offset*index),
                            hovertemplate = hovertemplate,
                            marker = dict(
                                color = colors[j],
                            ),
                            name = f'Pattern # {i}: {key}',
                        )
                    else:
                        self.multi_pattern.add_scatter(
                            x = tth,
                            y = np.array(ydict['ycalc'])+(offset*index),
                            hovertemplate = hovertemplate,
                            marker = dict(
                                color = colors[0],
                            ),
                            name = f'Pattern #{i}: {specific_substance}'
                        )
                #}}}
 
            #}}}
            # Plot the total intensity vs. Time: {{{
            elif plot_total_intensity_v_time:  
                colors = ['blue','green']
                ydict = {'yobs':sum(np.array(yobs)),'ycalc':sum(np.array(ycalc))} # sum the total intensity
                time = np.around(self.rietveld_data[i]['corrected_time']/60,4)  # Get the time that the pattern was taken at.
                try:
                    temp = np.around(self.rietveld_data[i]['corrected_temperature'],2)  #  Get the corrected_temperature
                except:
                    temp = np.around(self.rietveld_data[i]['temperature']-273.15,2) # Get the noncorrected temp
                total_i_ht = "t = %{x} min<br>Total Intensity: %{y}"
                # Collect the data: {{{
                for j, key in enumerate(ydict):
                    self.x.append(time) 
                    self.y.append(ydict['yobs'])
                    self.ycalc.append(ydict['ycalc'])
                    self.temp.append(temp) 
                #}}}
            #}}}
        # Plot the total intensity if you selected it: {{{
        if plot_total_intensity_v_time:
            hovertemplate = "%{x} min<br>Total Intensity: %{y}<br>" 
            self.multi_pattern.add_scatter(
                x = self.x,
                y = self.y,
                hovertemplate = hovertemplate,
                marker = dict(
                    color = 'blue',
                    size = 5
                ),
                mode = 'lines+markers',
                name = 'Observed Total I',
                yaxis = 'y1'
            )
            if specific_substance:
                name = f'Calculated Total I ({specific_substance})'
            else:
                name = 'Calculated Total I'
            self.multi_pattern.add_scatter(
                x = self.x,
                y = self.ycalc,
                hovertemplate=hovertemplate,
                marker = dict(
                    color = 'green',
                ),
                name = name,
                mode = 'lines+markers',
                marker_size = 5,
                yaxis = 'y1'

            )
            self.multi_pattern.add_scatter(
                    x = self.x,
                    y = self.temp,
                    marker = dict(
                        color = 'red',
                    ),
                    name = 'Temperature',
                    yaxis = 'y2'
            )
            xaxis_title = 'Time / min'
            yaxis_title = 'Total Intensity'
        # Update Layout: {{{
        self.multi_pattern.update_layout( 
            yaxis2 = dict(
                title = f'Temperature/{self._deg_c}',
                
                overlaying = 'y',
                side = 'right', 
            ),
            font = dict(
                size = 20,
            ),
        )
        #}}}
        #}}}
        # Waterfall Plot Added: {{{ 
        if waterfall: 
            self.multi_pattern.add_heatmap(
                x = self.x,
                y = self.y,
                z = self.z, 
                hovertemplate = hovertemplate,
            )
            yaxis_title = 'Time / min'
            # Get Button Args: {{{ 
            min_on_zmin, num_min_buttons = zmin_args # unpack the tuple
            min_on_zmax, num_max_buttons = zmax_args # unpack the tuple
            min_steps = (0 -min_on_zmin)/(num_min_buttons -1)
            max_steps = (self._max_i -min_on_zmax)/ (num_max_buttons-1)
  
            zmin_arange = np.arange(min_on_zmin, 0+min_steps,min_steps)
            zmax_arange = np.arange(min_on_zmax, self._max_i+max_steps, max_steps)
            #}}}
            # Make buttons to change scaling: {{{
            zmin_buttons = [
                dict(
                    label = f'I_min: {np.around(v,2)}',
                    method = 'restyle',
                    args = [
                        {'zmin': v},
                    ]
                ) for v in zmin_arange
            ]
            zmax_buttons = [
                dict(
                    label = f'I_max: {np.around(v,2)}',
                    method = 'restyle',
                    args = [
                        {'zmax': v},
                    ]
                ) for v in zmax_arange
            ]
            #}}}
        #}}}
        # Update Layout: {{{
        
        self._update_pattern_layout(
                fig = self.multi_pattern,
                title_text=fig_title,
                xaxis_title=xaxis_title,
                yaxis_title=yaxis_title,
                tth_range=tth_range,
                template=template,
                font_size=font_size,
                height=height,
                width=width,
                show_legend=show_legend,
                legend_x = legend_x,
                legend_y=legend_y,
                legend_xanchor=legend_xanchor,
                legend_yanchor=legend_yanchor,
                showgrid = showgrid,
                dtick = dtick,
                ticks = ticks,
        )
        # Waterfall Update: {{{
        if waterfall:
            self.multi_pattern.update_layout( 
                    margin = dict(t=200,b=0,l=0,r=0),
                    autosize = False,
                    updatemenus = [
                    dict(
                        buttons = zmax_buttons,
                        yanchor = 'top',
                        type = 'buttons',
                        y = button_layer_1_height,
                        x = 0,
                        xanchor = 'left',
                        pad = {'r':10, 't':10},
                        direction = 'right',
                    ),
                    dict(
                        buttons = zmin_buttons,
                        yanchor = 'top',
                        type = 'buttons',
                        y = button_layer_2_height,
                        x=0,
                        xanchor = 'left',
                        pad = {'r':10,'t': 10},
                        direction = 'right',
                    )
                ],
                
            )
        #}}} 
        #}}} 

        self.multi_pattern.show()
    #}}}
    # plot_mole_fraction: {{{
    def plot_mole_fraction(self,
            plot_type:'wp',
            formulas:list = None,
            fu_element:list = None,
            element_name:str = None,
            xaxis_title:str = 'time / min',
            width = 1200,
            height = 800,
            template:str = 'simple_white',
            xrange:list = None,
            yrange:list = None,
            show_legend:bool = True,
            font_size:int = 20,
            marker_size:int = 5,
            mode:str = 'markers+lines',
            color:str = None,
            legend_xanchor:str = 'right',
            legend_yanchor:str = 'top',
            legend_x:float = 1.55,
            legend_y:float = 0.99,

        ):
        '''
        This function will plot mole fractions for a given substance. 
        based on what you provide.
        ''' 
        self._get_mol_fraction_data(formulas,fu_element,element_name)
        if plot_type == 'wp':
            plot_title = f'Weight Percent - Derived Mole Fraction {element_name}'
            key = 'norm_mf_from_wp'
        elif plot_type == 'sf':
            plot_title = f'Scale Factor - Derived Mole Fraction {element_name}'
            key = 'mf_from_sf'
        yaxis_title = f'mole fraction ({element_name})'
        # Get important plot prms: {{{
        time = np.array(self.csv_plot_data['time'])
        temp = np.array(self.csv_plot_data['temperature'])
        #}}}
        # Make Plots: {{{
        for i, formula  in enumerate(formulas):
            entry = self.mol_fraction_data[formula]
            mf = entry[key]
            if i == 0:
                self.plot_data(
                    x = time,
                    y =mf,
                    name = f'{formula} Mole Fraction',
                    mode = mode,
                    title_text=plot_title,
                    xaxis_title=xaxis_title,
                    yaxis_title=yaxis_title,
                    template=template,
                    xrange=xrange,
                    yrange=yrange,
                    height=height,
                    width=width,
                    show_legend=show_legend,
                    font_size=font_size,
                    marker_size=marker_size, 
                    color=color,
                )
            else:
                self.add_data_to_plot(
                    x = time,
                    y = mf,
                    name = f'{formula} Mole Fraction',
                    mode = mode,
                    xrange = xrange,
                    yrange = yrange,
                    marker_size=marker_size,
                    color = color,
                
                )
        #}}}
        # Finish off with the temperature curve: {{{
        self.add_data_to_plot(
            x = time,
            y = temp,
            name = f'Temperature',
            mode = mode,
            marker_size=marker_size,
            show_figure=True,
            y3 = True,
            y3_title = f'Temperature / {self._deg_c}',
            color = 'red',
            legend_xanchor=legend_xanchor,
            legend_yanchor=legend_yanchor,
            legend_x = legend_x,
            legend_y = legend_y,
        )
        #}}} 
    #}}}
    # plot_times: {{{ 
    def plot_times(self,):
        if not self._data_collected:
            print('You did not yet collect data. Do that now...')
            self.get_data()
        fig = go.Figure()
        # Get the data to plot: {{{
        readable_times = list(self.metadata_data.keys())
        if self.check_order:
            ys = np.linspace(1, len(self.corrected_range), len(self.corrected_range))
            xs = [np.around(entry['corrected_time']/60, 4) for idx, entry in self.rietveld_data.items()] 

        else:
            xs = [np.around((self.metadata_data[rt]['epoch_time'] - self.metadata_data[readable_times[0]]['epoch_time']) / 60, 4) for rt in self.metadata_data] # Creates a list of the real times
            ys = np.linspace(1, len(readable_times), len(readable_times)) # Create a line with the total number of patterns. 
        #}}}
        # Plot the data: {{{
        fig.add_scatter(
            x = xs,
            y = ys,
            mode = 'lines+markers', # Shows the markers with a line going through them.
        )
        #}}}
        # Update Layout: {{{
        fig.update_layout(
            height = 800,
            width = 1100,
            title_text = 'Plot of Times',
            xaxis_title = 'Time/min',
            yaxis_title = 'Plot Number',
            font = dict(
                size = 20,
            ),
            template = 'simple_white',
        )
        #}}}
        fig.show() 
    #}}}
#}}}
