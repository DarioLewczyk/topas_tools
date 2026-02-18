# Authorship: {{{
# Written by: Dario Lewczyk
# Date: 02-20-2024
#}}}
# Imports: {{{
import os
import re
import glob
import numpy as np
import texttable
from scipy.optimize import fsolve
#from PIL import Image
import fabio
from scipy.signal import savgol_filter
from topas_tools.IO import IO
#}}}
# Utils: {{{
class Utils: 
    # generate_table: {{{
    def generate_table(self,
        iterable:list = None,
        header = None,
        index_list:list = None,
        cols_align:list = ['c','l'],
        cols_dtype:list = ['i','t'],
        cols_valign:list = ['b','b'],
        ):
        '''
        This allows us to generate clean text-based tables
        for user selection printouts.
        '''
        # Pre-checks: {{{
        if isinstance(header,str):
            header = ['Index',header]
        else:
            header = ['Index','Item']
        if index_list:
            if len(iterable) != len(index_list):
                print('Incompatible index list for iterable given.')
        #}}}
        # Generate the table: {{{
        table = texttable.Texttable()
        table.set_cols_align(cols_align)
        table.set_cols_dtype(cols_dtype)
        table.set_cols_valign(cols_valign)
   
        table.add_row(header) 
        for i, v in enumerate(iterable):
            if index_list and cols_align == ['c', 'l']:
                table.add_row([index_list[i], v]) 
            elif cols_align != ['c', 'l']:
                table.add_row(v) 
            else:
                table.add_row([i,v]) 
        print(table.draw())
        #}}}
#}}}
    # clear: {{{
    def clear(self):
        if os.name == 'nt':
            os.system('cls') # This is for Windows
        else:
            os.system('clear') # This is for mac and linux
    #}}}
    # prompt_user: {{{
    def prompt_user(self, iterable:list = None,header:str = None):
        '''
        This function will prompt the user to make a selection 
        from a list given.
        The function will return the value selected.
        '''
        # Loop for user selection: {{{
        selecting = True
        result = None
        self.generate_table(iterable,header = header) 
        while  selecting:
            selection = input('Please select the number of your choice.\nIf you want to quit, simply press return or type none.\nIf you want to go back a directory, you can type "b".\n')
            # Check if the selection was valid: {{{
            if selection.isdigit():
                selection = int(selection)
                result = iterable[selection]
                selecting = False
            
            elif selection == 'b': 
                selection = iterable.index('back_directory') # Get the index of the back
                result = iterable[selection]
                selecting = False 
            #}}}
            # Check for quit: {{{
            elif selection.lower() == 'none' or selection == '':
                selecting = False
            #}}}
            # Check for Fragment of Dir Name: {{{
            else:
                possibilities = []
                for i, dirname in enumerate(iterable):
                    tmp_dirname = dirname.lower() 
                    if re.findall(selection.lower(),tmp_dirname):
                        possibilities.append(dirname) # Add the possible choice 
                if len(possibilities) > 1:
                    print()
                    self.generate_table(possibilities,header=header)
                    selection = input('Please select the directory you meant\n')
                    if selection.isdigit():
                        result = possibilities[int(selection)]
                        selecting = False
                elif len(possibilities) == 1:
                    result = possibilities[0] # This was what was meant 
                    selecting = False
            #}}} 
    
        #}}}
        return result
    #}}}
    # navigate_filesystem: {{{
    def navigate_filesystem(self):
        '''
        The purpose of this is to navigate the filesystem of your computer
        to get to a directory if you aren't already where you want to be
        '''
        navigating = True
        # while loop: {{{
        while navigating:
            current_directory = os.getcwd()
            current_directory_contents = os.listdir()
            cd_folders = []
            for f in current_directory_contents:
                if os.path.isdir(f):
                    cd_folders.append(f) 
            cd_folders.extend(['back_directory','done_selecting'])
            
            #self.generate_table(cd_folders,header = 'Directories')
            selection = self.prompt_user(cd_folders)
            
    
            if selection == None or selection == 'done_selecting':
                navigating = False
            elif selection == 'back_directory':
                os.chdir(os.path.dirname(current_directory)) # This goes back a directory.
            else:
                os.chdir(selection) # Change directory to the new one.
            self.clear()
        #}}}
        return os.getcwd() #Final directory is returned
        
    #}}}
    # find_a_file: {{{
    def find_a_file(self, dirname:str = None, fileextension:str = None):
        '''
        This function is built to simplify the process of finding a file 
        given a filetype. 

        If called without an explicit directory name (dirname) the function will 
        start by searching the current directory. If no files matching the descriptor exist
        it will prompt the user to search for another directory 

        returns: (file, directory)
        '''
        home = os.getcwd()
        files = None
        # no dirname specified: {{{
        if not dirname:
            files = glob.glob(f'*.{fileextension}')
            if len(files) == 0:
                print(f'No files matching the fileextension: "{fileextension}" were found')
            else:
                dirname = home

        #}}}
        # dirname specified: {{{
        else:
            if os.path.isdir(dirname):
                os.chdir(dirname)
                files = glob.glob(f'*.{fileextension}')
                if len(files) == 0:
                    print(f'No files matching the fileextension: "{fileextension}" were found')
            else:
                print(f'The directory: {dirname} does not exist, navigate to the right directory:')
        #}}}
        # if need to navigate filesystem: {{{
        if not files:
            while not files:
                dirname = self.navigate_filesystem()
                files = glob.glob('*.{fileextension}')
                if not files: 
                    print(f'No files matching extension: "{fileextension}"')
        #}}}
        # with files, determine if user needs to select a file from a list: {{{
        if len(files) == 1:
            file = files[0]
        else:
            file = self.prompt_user(files, f'{fileextension} files')
        #}}}
        return (file, dirname)

    #}}}
    # get_min_max: {{{
    def get_min_max (
            self, 
            vals:list = None, 
            custom_labels:list = None,
            pct:float = 0.5,
            decimals:int = 5, 
        ):
        '''
        This function serves to quickly get the lattice parameters 
        for a single or series of values varying by a percentage ±
        '''
        fract = pct/100
        try:
            print('-'*10)
            for i, v in enumerate(vals):
                minv = np.around(v - v*fract, decimals)
                maxv = np.around(v + v*fract, decimals)
                if custom_labels == None:
                    custom_labels = ['']*len(vals)
                print(f'Min {custom_labels[i]}: {minv}\nMax {custom_labels[i]}: {maxv}')
            print('-'*10)
        except: 
            minv = np.around(vals-vals*fract,decimals)
            maxv = np.around(vals+vals*fract,decimals)
            if not custom_label:
                custom_label = ''
            print(f'Min {custom_label}: {minv}\nMax {custom_label}: {maxv}')
    #}}}
    # get_time_range: {{{ 
    def _get_time_range(self, metadata_data:dict = None, time_range:list = None,max_idx:int = None):
        '''
        This function serves to define a new range for the automated refinement tool 
        to work from. 
        One thing to note is that the indices are always 1 higher than pythonic indices. 
        e.g. 1 == 0 because we use len(range) to get the last data point. 
        '''
        mdd_keys = list(metadata_data.keys())
        t0 = metadata_data[mdd_keys[0]]['epoch_time'] # This is the first time in the series. This will be shown to user
        start = 1
        end = max_idx
        print(f'Starting epoch time: {t0} s')

        found_start = False
        found_end = False
        for i, (rt, entry) in enumerate(metadata_data.items()): 
            ti = entry['epoch_time']
            time = (ti - t0)/60
            # Handle the start case: {{{
            if time >= time_range[0] and not found_start:
                start = i+1 # make the index +1 because we subtract later. 
                print(f'Starting time: {time*60} s')
                found_start = True
            #}}}
            # Handle the end case: {{{
            elif  time >= time_range[1] and not found_end:
                if i+1 < max_idx:
                    end = i+1 # make the index +1 because we subtract later.
                else:
                    end = max_idx
                found_end = True
                break
            #}}}
        return (start,end)
    #}}}
    # convert_to_q: {{{
    def convert_to_q(self, tth = None, d = None,  lambda_angstrom:float = None, mode = 0):
        '''
        This function serves to convert 2theta to q space
        It can also convert d to q
        
        mode = 0: gives q in angstrom
        mode = 1: gives q in nm

        REMEMBER that the mode switch will only do what is expected if you are working with 2theta and a wavelength.

        Can work with either a single value or a list of values
        '''
        # If using 2THETA: {{{
        if lambda_angstrom:
            lambda_nm = lambda_angstrom * 10

            # unit selection: {{{
            if mode == 0:
                lam = lambda_angstrom
            elif mode == 1:
                lam = lambda_nm
            #}}}
        # If a list of TTH values is passed: {{{
        try:
            qs = []
            for tth_val in tth:
                tth_rad = np.radians(tth_val)
                q = 4*np.pi/lam * np.sin(tth_rad/2)
                qs.append(q)
            return qs
        #}}} 
        # If only one value passed: {{{
        except:
            try:
                tth_rad = np.radians(tth)
                q = 4*np.pi/lam * np.sin(tth_rad/2)
                return q
            except:
                pass # This kicks it to the d spacing version
        #}}}
        #}}}
        # d-spacing to q: {{{
        # If passing a list of values: {{{
        try:
            qs = []
            for dval in d:
                q = (2*np.pi)/dval
                qs.append(q)
            return qs
        #}}} 
        # If passing only a single value: {{{
        except:
            q = (2*np.pi)/d
            return q
        #}}}
        #}}}
    #}}}
    # convert_to_s: {{{
    def convert_to_s(self, d): 
        '''
        This function takes a d spacing as input. 

        It can either convert a single value of d to s
        OR
        It can convert a list of values of d to s
        '''
        s_vals = []
        # If a list of values passed: {{{
        try:
            for dval in d:
                s_vals.append(1/dval)
            return s_vals
        #}}}
        # If only one passed: {{{
        except:
            return 1/d
        #}}}
    #}}}
    # convert_d_to_tof: {{{
    def convert_d_to_tof(self, d = None, zero:float = None, difa:float = None, difb:float = None, difc = None):
        ''' 
        This allows us to back-calculate from d-spacing to TOF if we want
        This can be helpful when you double check peak positions from JANA with a python figure.

        This can either convert a single value of d 
        OR 
        a list of ds to TOF
        '''
        # If user passes a list of ds: {{{
        try:
            tofs = []
            for dval in d:
                tof = (zero+difc*dval + difa*dval**2 + difb/dval)/1000
                tofs.append(tof)
            return tofs
        #}}}
        # If user passes a single d: {{{
        except:
            tof = (zero+difc*d+ difa*d**2 + difb/d)/1000
            return tof
        #}}}
    #}}}
    # _tof_eqn: {{{
    def _tof_eqn(self, d, tof, zero, difa, difb, difc):
        return zero + difc * d + difa * d**2 + difb/d - tof*1000
    #}}}
    # convert_tof_to_d: {{{
    def convert_tof_to_d(self, tof = None, zero:float = None, difa:float = None, difb:float = None, difc:float = None, debug:bool=False):
        '''
        Uses the calibration parameters obtained from the TOF diffractometer team to calculate the d-spacing of your data.

        This can either use a list of TOF values 
        OR
        A singular TOF value
        '''

        if debug:
            print(f'zero: {zero}\ndifa: {difa}\ndifb: {difb}\ndifc: {difc}')
        # If using a list of TOFs: {{{
        try:
            ds = []
            for i, tof_val in enumerate(tof):
                # Initial guess for d
                d_guess = 0.5
                #solve for d
                d = fsolve(self._tof_eqn, d_guess, args = (tof_val, zero, difa, difb, difc)) # Solve the quadratic function for d
                if debug:
                    print(f'd (calc {i}): {d}') 
                ds.append(d[0])
            return ds
        #}}}
        # If using a singular TOF: {{{
        except:
            # Initial guess for d
            d_guess = 0.5
            #solve for d
            d = fsolve(self._tof_eqn, d_guess, args = (tof, zero, difa, difb, difc)) # Solve the quadratic function for d
            if debug:
                print(f'd (calc {i}): {d}') 
            return d[0]
        #}}}
    #}}}
    # convert_d_to_tth: {{{
    def convert_d_to_tth(self, d = None, lam:float = 0.1665):
        ''' 
        This function allows you to calculate either a single d spacing to 2theta 
        OR
        a whole list of d spacings to 2theta
        
        This is just a proxy function because i like the "convert" scheme a bit better for these calculations
        now. 
        '''
        return self.calc_tth_from_d(lam= lam, d= d)
       
    #}}}
    # calc_tth_from_d: {{{
    def calc_tth_from_d(self, lam:float = 0.1665, d:float = 0.1):
        '''
        Uses Bragg's law to convert from d spacing to 2theta
        returns in degrees
        This will work for either a single value or multiple values

        if you have given a value that is not possible, then it will default to 180
        '''
        try:
            len(d)
            ds = d
            tths = []
            for d in ds:
                angle = lam/(2*d) 
        
                if angle <= 1:
                    tth = np.degrees(2*np.arcsin(angle)) 
                else:
                    tth = np.degrees(2*np.arcsin(1))
                tths.append(tth)
            return(np.array(tths))
        except:  
            angle = lam/(2*d) 
        
            if angle <= 1:
                tth = np.degrees(2*np.arcsin(angle)) 
            else:
                tth = np.degrees(2*np.arcsin(1))
            return tth
    #}}}
    # convert_tth_to_d: {{{
    def calc_d_from_tth(self, lam:float = 0.1665, tth:float = 0.8):
        '''
        n lam = 2d sin(theta)

        make sure that you give the tth in degrees.
        '''
        th = tth/2 # Convert 2theta into theta
    
        return lam/(2 * np.sin(np.deg2rad(th)))
    #}}}
    # calculate_d_from_hklm: {{{
    def calculate_d_from_miller_indices(self, miller_indices, a, b, c, qa:float = 0, qb:float = 0, qc:float = 0):
        '''
        miller_indices: a list of tuples of either: (h,k,l) or (h, k, l, m)
        This calculates the d-spacing in a general way for either 3D or (3+d)D miller indices
        if you are doing the (3+d)D case, you MUST ensure that you input your q vector
        '''
        ds = []
        try:
            for h, k, l, m in miller_indices:
                d = 1/np.sqrt(((h+qa*m)/a)**2 + ((k +qb*m)/b)**2 + ((l + qc*m)/c)**2)
                ds.append(d)
        except:
            for h, k, l in miller_indices:
                d = 1/np.sqrt((h/a)**2 + (k/b)**2 + (l/c)**2)
                ds.append(d)
        return ds 
    #}}}
    # calculate_rmse: {{{
    def calculate_rmse(self,data, fit, precision = 4):
        ''' 
        data is your actual data
        fit is the fit to the data
        '''
        resid = np.array(fit - data)
        sq_resid = resid**2
        avg = np.average(sq_resid)
        return np.around(np.sqrt(avg), precision)
    #}}}
    # calculate_rsq: {{{
    def calculate_rsq(self, data, fit, precision = 4):
        ''' 
        data is the actual data
        fit is the fit to the data
        '''
        dat_avg = np.average(data)
    
        sst = np.sum((np.array(data) - dat_avg)**2)
        ssr = np.sum((np.array(data) - np.array(fit))**2)
        rval = 1 - (ssr/sst)
        return np.around(rval, precision)
    #}}}
    # calculate_derivative: {{{
    def calculate_derivative(self, x, y, step_size = 1, mode = 0, polyorder:int = 1):
        '''
        mode: 0 = moving average
        mode: 1 = no smoothing
        mode: 2 = use savgol filter

        If you use mode 2: 
            step_size is the window size
            polyorder is the order of the polynomial for smoothing
        '''
     
        x = np.array(x)
        y = np.array(y)
        step_size = int(step_size)
        # No Smoothing: Mode 1: {{{
        if mode == 1:
            dydx = np.gradient(y, x)
            new_x = x[::step_size]
            dydx = dydx[::step_size]
        #}}}
        # Moving average: Mode 0:  {{{
        elif mode == 0:
            # Smooth the data using a moving average with a specified step size
            y_smooth = np.convolve(y, np.ones(step_size)/step_size, mode = 'valid')
            new_x = x[:len(y_smooth)]
            # Calculate the derivative
            dydx = np.gradient(y_smooth, new_x)
        #}}}
        # Savgol Filter: Mode 2: {{{
        elif mode == 2:
            y_smooth = savgol_filter(y, step_size, polyorder)
            # Calculate differences between consecutive points
            dx = np.diff(x)
            dy_smooth = np.diff(y_smooth)

            new_x = x[1:] # The new x should be one shorter than the original 
            dydx = dy_smooth/dx

        #}}}
        
        return new_x, dydx
    #}}}
    # calculate_toffset_for_isotherm: {{{
    def calculate_toffset_for_isotherm(self, x, y, tolerance:float = 0.1, start_idx:int = 0,  print_delta_x:bool = False):
        ''' 
        This function will print out a time offset placing the start of your isotherm at 
        t = 0. It will  also return the corrected time range. 

        currently, this only matches a value in the range 
        This uses the derivative to determine when the temperature has settled
        
        If you are working with some datasets, you may need to exclude some indices. 
        If this is the case, then use start_idx to change that. 
        '''
        tmp_x = np.array(x[start_idx:])
        tmp_y = np.array(y[start_idx:])
        newx, dydx = self.calculate_derivative(tmp_x,tmp_y, 1, mode = 1)
        settling_idx = np.where(np.abs(dydx) <= tolerance)[0][0]
        settling_x = tmp_x[settling_idx]

        x = np.array(x)
        if print_delta_x:
            print(f'∆x = {np.around(settling_x - x[0],2)}')
        return x - settling_x

    #}}}
    # fit_linear: {{{ 
    def fit_linear(self, x, y, start_idx:int = None, end_idx:int = None, print_results:bool = True, print_precision:int = 2, print_idx:int = 1):
        ''' 
        This function allows you to quickly fit data to a line
        and also receive feedback on how the fit quality is

        returns a tuple: 

        (slope, intercept, fit_line)

        IMPORTANT: Since we are using slices, the end index is the human readable item number 
        This is since slices are exclusive of the end index given. 
        '''
        if not start_idx:
            start_idx = 0
        if not end_idx:
            end_idx = len(y)
        fitx = x[start_idx:end_idx]
        fity = y[start_idx:end_idx]

        m, b = np.polyfit(fitx, fity, deg = 1)
        fit = np.array([m*x + b for x in x])
        
        # Printout: {{{
        if print_results:
            rsq = self.calculate_rsq(fity, fit[start_idx:end_idx], print_precision)
            rmse = self.calculate_rmse(fity, fit[start_idx:end_idx], print_precision)
            print(f'Region {print_idx}:')
            print(f'\tRMSE: {rmse}')
            print(f'\tR^2: {rsq}')
            print(f'\tFit parameters: slope: {np.format_float_scientific(m, print_precision)}, intercept: {np.format_float_scientific(b, print_precision)}')

        #}}}
        return m, b, fit
    #}}}
    # calculate_snr: {{{
    def calculate_snr(self, y):
        ''' 
        This function calculates the mean of intensity data divided by the standard deviation
        Generally I have found that if the ratio is low (e.g. < 2) the pattern is good

        If the ratio is larger (e.g. 10, 26, etc.) the pattern is unusable
        '''
        signal = np.mean(y)
        noise = np.std(y)
        return signal/noise if noise !=0 else 0
    #}}}
    # _load_raw_xy: {{{
    def _load_raw_xy(self,fn:str = None, data_dir:str = None):
        """ 
        This function simply loads an XY file generated by 
        pyFAI. 
        """
        home = os.getcwd()
        os.chdir(data_dir)
        data = np.loadtxt(fn, skiprows=1)
        x = data[:,0]
        y = data[:,1]
        os.chdir(home)
        return x,y
    #}}}
    # load_output_xy: {{{
    def load_output_xy(self, fn):
        """ 
        Simple function to load an xy file
        produced as output from TOPAS using my macro
        Out_X_Yobs_Ycalc_Ydiff()
        """
        xy = np.loadtxt(fn,delimiter=',')
        tth = xy[:,0]
        yobs = xy[:,1]
        ycalc = xy[:,2]
        ydiff = xy[:,3]
        return tth, yobs, ycalc, ydiff
#}}}
    # _filter_csv_dict: {{{
    def _filter_csv_dict(self, csv_plot_data:dict = None, plot_type:str = None, debug:bool = False):
        ''' 
        This function is used to generate a new dictionary with only the values you care about for the specific plot.

        '''
        pattern = None
        yaxis_title = ''
        yaxis2_title = ''
        title = ''
        new_csv_dict = {} # This is the output dictionary
        # Determine the pattern and the labels: {{{
        # Lattice Params: {{{ 
        if plot_type == 'lattice parameters' or plot_type == 'lattice' or plot_type == 'lp':
            pattern = r'^(a|b|c|al|be|ga|alpha|beta|gamma)$' # This is a pattern to match only lattice parameter entries 
            yaxis_title = f'Lattice Parameter / {self._angstrom}' # This is the a, b, c lattice parameter title
            yaxis2_title = f'Lattice Parameter / {self._degree}' # this is the al, be, ga lattice parameter title
            title = 'Lattice Parameters'
        #}}}
        # Scale Factor: {{{
        elif plot_type == 'scale factor' or plot_type == 'sf': 
            pattern = r'^(scale_factor|sf|scale factor)$'
            yaxis_title = 'Scale Factor'
            title = 'Scale Factor'
            #normalized = True
        #}}}
        # Volume: {{{
        elif plot_type == 'volume' or plot_type == 'vol': 
            pattern = r'^vol$|^volume$|^cell_volume$|^cell volume$'
            yaxis_title = f'Volume / {self._angstrom}{self._cubed}'
            title = 'Volume'
        #}}}
        # R Bragg: {{{
        if plot_type == 'rbragg' or plot_type == 'rb':
            pattern = r'^r bragg$|^r_bragg$' 
            yaxis_title = 'R Bragg'
            title = 'R Bragg'
        #}}}
        # Weight Percent: {{{
        if plot_type == 'weight percent' or plot_type == 'wp': 
            pattern = r'^weight_percent$|^weight_percent$' 
            yaxis_title = 'Weight Percent'
            title = 'Weight Percent'
        #}}}
        # B-values: {{{
        if plot_type == 'b values' or plot_type == 'beq' or plot_type == 'bvals':
            pattern = r'^(bvals|beq|bval|b value|b val|b values|b_value|b_val|b_values)_\w+$' 
            yaxis_title = 'B-Values'
            title = 'B-Values'
        #}}}
        # Size L: {{{
        if plot_type == 'size l' or plot_type == 'csl' or plot_type == 'sizel':
            pattern = r'^(size_l|csl|lorentzian_size|Size_L|cslv)$' 
            yaxis_title = 'Lorentzian Size'
            title = 'Lorentzian Size'
        #}}}
        # Size G: {{{
        if plot_type == 'size g' or plot_type == 'csg' or plot_type == 'sizeg':
            pattern = r'^(size_g|csg|gaussian_size|Size_G|csgv)$'  
            yaxis_title = 'Gaussian Size'
            title = 'Gaussian Size' 
        #}}}
        # Strain L: {{{ 
        if plot_type == 'strain l' or plot_type == 'strl' or plot_type == 'strainl':
            pattern = r'^(strain_l|strl|lorentzian_strain|Strain_L|slv)$' 
            yaxis_title = 'Lorentzian Strain'
            title = 'Lorentzian Strain'
        #}}}
        # Strain G: {{{
        if plot_type == 'strain g' or plot_type == 'strg' or plot_type == 'straing':
            pattern = r'^(strain_g|strg|gaussian_strain|Strain_G|sgv)$'   
            yaxis_title = 'Gaussian Strain'
            title = 'Gaussian Strain' 
        #}}}
        # Lvol: {{{ 
        if plot_type.lower() == 'lvol':
            pattern = r'^lvol$'
            yaxis_title = 'LVol'
            title = 'LVol'
        #}}}
        # Lvolf: {{{
        if plot_type.lower() == 'lvolf': 
            pattern = r'^lvolf$' 
            yaxis_title = 'Lvolf'
            title = 'LVolf'
        #}}}
        # e0: {{{ 
        if plot_type.lower() == 'e0':
            pattern = r'^e0$' 
            yaxis_title = f'e{self._subscript_zero}'
            title = f'e{self._subscript_zero}'
        #}}}
        # phase_MAC: {{{
        if plot_type.lower() == 'phase_mac':
            pattern = r'^(phase_mac|phase_MAC)$' 
            yaxis_title = 'Phase MAC'
            title = 'Phase MAC'
        #}}}
        # cell_mass: {{{
        if plot_type.lower() == 'cell_mass' or plot_type.lower() == 'cm' or plot_type.lower == 'mass':
            pattern = r'^cell_mass$' 
            yaxis_title = 'Cell Mass'
            title = 'Cell Mass'
        #}}}
        # eta: {{{
        if plot_type.lower() == 'eta':
            pattern = r'^eta$' 
            yaxis_title = 'Eta'
            title = 'Eta Values'
        #}}}
        # stephens: {{{
        if plot_type.lower() == 'stephens':
            pattern = r'^(eta|s400|s040|s004|s220|s202|s022|s310|s031|s130|s301|s013|s211|s121|s112)$'
            yaxis_title = 'Stephens Parameter'
            title = 'Stephens Parameters'
        #}}}
        # Occupancies: {{{
        if plot_type.lower() == 'occupancies' or plot_type.lower() == 'occ':
            pattern = r'^(occupancy|occ)_\w+$|^\w+_(occupancy|occ)$'
            yaxis_title  = 'Occupancy'
            title = 'Occupancy Evolution'
        #}}}
        #}}}
        # Return the data: {{{
        if pattern != None: 
            for key, old_csv in csv_plot_data.items():
                if debug:
                    try:
                        print(f'Old CSV: {old_csv.keys()}')
                    except:
                        print(f'key: {key} does not have a dict entry!')
                try: 
                    pattern = re.compile(pattern) # Compile the regex
                    filtered_dict = {k:v for k, v in old_csv.items() if pattern.match(k.lower())} # Create a copy dict with only relevant entries
                    if debug:
                        print(f'{key}\n\t{pattern}: {filtered_dict.keys()}')
                    new_csv_dict[key] = filtered_dict # Add the filtered dictionary to the 
                except:
                    pass
            return new_csv_dict, yaxis_title, yaxis2_title, title
        else:
            print(f'The plot type: {plot_type} is not defined!')
        #}}}
    #}}}
    # export_xy_with_hkl: {{{
    def export_xy_with_hkl(self, idx, rietveld_data, excel_dir, fn):
        return IO.export_xy_with_hkl(idx, rietveld_data, excel_dir, fn)
    #}}}
    # get_dirs_for_ixpxsx_automations: {{{
    def get_dirs_for_ixpxsx_automations(
        self,
        home_dir: str = None,
        data_extension: str = 'xy',
        ixpxsx_types: list = ['IPS', 'xPS', 'xPx', 'xxx']
    ):
        """
        Return a list of directories under home_dir that contain:
            - at least one .inp file
            - at least one data file with the given extension
            - all required IxPxSx subdirectories
        """
        valid_dirs = []
    
        # Loop through entries without changing directories
        for entry in os.scandir(home_dir):
            if not entry.is_dir():
                continue
    
            entry_path = entry.path
            files = os.listdir(entry_path)
    
            has_inp = any(f.endswith('.inp') for f in files)
            has_data = any(f.endswith(f'.{data_extension}') for f in files)
    
            if not (has_inp and has_data):
                continue
    
            # Check required IxPxSx subdirectories
            all_subdirs_exist = True
            for sub in ixpxsx_types:
                sub_path = os.path.join(entry_path, sub)
                if not os.path.isdir(sub_path):
                    all_subdirs_exist = False
                    break
    
            if all_subdirs_exist:
                valid_dirs.append(entry_path)
        # Because now we have full paths, need to sort with a lambda func
        valid_dirs = sorted(
                valid_dirs,
                key = lambda p: int(os.path.basename(p).split('_')[0])
        )
        return valid_dirs
    #}}}
    # clean_directory: {{{
    def clean_directory(self, exclude:list = None, path = "."):
        ''' 
        This function will clean a directory so it is properly prepared
        This may be particularly useful for running TOPAS automations since 
        it ensures that the directory is always in a pristine state each time
        the automation is run

        exclude: What files would you like to exclude? 
        path: path to the directory
        '''
        exclude = set(exclude or [])

        with os.scandir(path) as entries: 
            for entry in entries: 
                if entry.is_file():
                    if entry.name not in exclude: 
                        os.remove(entry.path)
            
            # entry.is_dir() → ignored automatically
    #}}}
    # make_unique_dir: {{{
    def make_unique_dir(self,base):
        if not os.path.exists(base):
            os.makedirs(base)
            return base
        i = 1
        while True:
            new_name = f'{base}_{i}'
            if not os.path.exists(new_name):
                os.makedirs(new_name)
                return new_name
            i+=1
        
    #}}}
    # get_dict_entry: {{{ 
    def get_dict_entry(self, d:dict, *keys):
        """ 
        helps to quickly get an entry from a large 
        nested dictionary. 
        Can use as many keys as you want
        keys are applied sequentially

        e.g. 

            d[key1][key2][key3]...[keyn]
        """
        for k in keys:
            if not isinstance(d, dict) or k not in d:
                return None
            d = d[k]
        return d
    #}}}
#}}}
# UsefulUnicode: {{{
class UsefulUnicode: 
    '''
    This is a class because these symbols do not need to be
    visible to the end user in a generic sense. 
    '''
    def __init__(self,): 
        self._degree = u'\u00B0' # Degree symbol
        self._deg_c = u'\u2103' # Degree C symbol
        self._subscript_zero = u'\u2080' # Subscript zero
        self._subscript_one =   u'\u2081'
        self._subscript_two =   u'\u2082'
        self._subscript_three = u'\u2083'
        self._subscript_four =  u'\u2084'
        self._subscript_five =  u'\u2085'
        self._subscript_six =   u'\u2086'
        self._subscript_seven = u'\u2087'
        self._subscript_eight = u'\u2088'
        self._subscript_nine =  u'\u2089'
        self._angstrom = u'\u212b' # Angstrom symbol
        self._cubed = u'\u00b3' # Cubed (superscript 3)

        self._angstrom_symbol = u'\u212b'
        self._degree_symbol = u'\u00b0'
        self._degree_celsius = u'\u2103'
        self._theta = u'\u03b8'
        self._phi = u'\u1D719'
        self._lambda = u'\u03BB'
        self._alpha = u'\u03B1'
        self._beta = u'\u03B2'
        self._gamma = u'\u03B3'


        self._sub_a = u'\u2090'
        self._sub_b = u'\u1D47'
        self._sub_c = u'\u1D9c'
        self._sub_d = u'\u1D48'
        self._sub_e = u'\u2091'
        self._sub_f = u'\u1DA0'
        self._sub_g = u'\u1D4D'
        self._sub_h = u'\u2095'
        self._sub_i = u'\u1D62'
        self._sub_j = u'\u2C7C'
        self._sub_k = u'\u2096'
        self._sub_l = u'\u2097'
        self._sub_m = u'\u2098'
        self._sub_n = u'\u2099'
        self._sub_o = u'\u2092'
        self._sub_p = u'\u209A'
        #self._sub_q = u'\u2090'
        self._sub_r = u'\u1D63'
        self._sub_s = u'\u209B'
        self._sub_t = u'\u209C'
        self._sub_u = u'\u1D64'
        self._sub_v = u'\u1D65'
        #self._sub_w = u'\u2090'
        self._sub_x = u'\u2093'
        #self._sub_y = u'\u2090'
        #self._sub_z = u'\u2090'
#}}}
# DataCollector: {{{
class DataCollector: 
    '''
    This class gives us the tools necessary to allow us to import
    data that we are interested in - given a fileextension 
    Additionally, dependent upon what we are looking at.
    e.g. data, metadata, etc.
    '''
    # __init__: {{{
    def __init__(
            self, 
            fileextension:str = 'xy',
            position_of_time = 1,
            len_of_time = 6,
            time_units:str = 'min',
            file_time_units:str = 'sec',
            skiprows = 1, 
            metadata_data:dict = {},
            mode = 0,
        ):
        '''
        1. fileextension: The extension (without a .)
        2. position_of_time: the index in the filenname where time is located (assuming you have time in your filename)
        3. len_of_time: The number of digits you have in your file's time code
        4. time_units: The time units you want at the end of processing
        5. file_time_units: The units of time recorded in the filenname
        6. skiprows: The number of rows to skip when reading the data (necessary when using numpy and headers are present).

        mode: 
            The mode is 0 by default. This means that the program will expect to see time stamps in your xy files
            If you want to just get all files of a particular extension without that requirement, use "1"

        '''
        # Initialize values: {{{
        self._fileextension = fileextension
        self.position_of_time = position_of_time 
        self.len_of_time = len_of_time 
        self.time_units = time_units 
        self.file_time_units = file_time_units 
        self.skiprows = skiprows  
        self.metadata_data = metadata_data # Transfer the metadata or start fresh 
        self._datacollector_mode = mode
        #}}}
        # Determine if working with images: {{{
        if self._fileextension == 'tif' or self._fileextension == 'tiff':
            self.image = True# get_arrs uses this to determine to treat an image or data
        else:
            self.image = False # Treats the data as CSV type
        #}}}
        self.file_dict = {} # This will be initialized as empty 
    #}}}
    # scrape_files: {{{
    def scrape_files(self, fileextension:str = None):
        '''
        This function finds all files with the extension selected
        and sorts them based on the timecode embedded in their filenames.
        '''
        if fileextension:
            self._fileextension = fileextension
        self.files = glob.glob(f'*.{self._fileextension}')
        tmp = {}
        for i, f in enumerate(self.files):
            if self._datacollector_mode == 0:
                numbers = re.findall(r'\d{'+str(self.len_of_time)+r'}',f) 
                number = int(numbers[self.position_of_time])
                if number:
                    tmp[number] = f # The files will be indexed by their timecode
            elif self._datacollector_mode == 1:
                 tmp[i] = f
            # We now sort the dictionary entries by their number (least to greatest.) 
        self.file_dict = dict(sorted(tmp.items())) 
    #}}}
    # _resort_with_metadata: {{{
    def _resort_with_metadata(self, file_dict:dict = None, metadata_data:dict = None, ):
        '''
        Sometimes, the readable times fail horribly and you need to fall back on metadata to determine the 
        ordering of filenames. 

        In these cases, you use this function which will reorder the file dictionary for you based off of 
        a correctly sorted metadata dictionary.
        ''' 
        #print(len(file_dict), len(metadata_data))
        #print(list(file_dict.keys()))
        #print(list(metadata_data.keys()))
        correctly_sorted_readable_times = list(metadata_data.keys()) # These are correctly sorted by epoch time
        # Create a new dictionary with the sorted keys from the metadata dictionary:
        sorted_file_dict = {key: file_dict[key] for key in correctly_sorted_readable_times if key in file_dict}
 
        return sorted_file_dict
    #}}}
    # get_data_for_waterfall: {{{
    def get_data_for_waterfall(self,metadata_data:dict = None, 
            start_time:int = None, 
            end_time:int = None, 
            num_patterns:int = None,
            ):
        '''
        This function allows you to quickly get a range over which to plot data
        in a waterfall plot.  
        '''
        times = self._get_time_arr(metadata_data, self.time_units)
        # Go through input: {{{
        if not start_time and not end_time and not num_patterns:
            selecting = True
            while selecting:
                # Gather the information we need to progress: {{{ 
                first_time, idx_first_time, key_first_time, fn_first_time = self._get_first_time(metadata_data)
                first_time = key_first_time # This uses the readable time which will be the key
                last_time = max(metadata_data, key = lambda k: metadata_data[k]['epoch_time'])

                timecodes = list(self.file_dict.keys())
                min_index = timecodes.index(first_time)
                max_index = timecodes.index(last_time)
                
                min_time = np.around(min(times),1)
                max_time = np.around(max(times),1)
                #}}}
                print(f'You have {len(timecodes)} patterns in this directory.\nThe time ranges from: {min_time} {self.time_units} to {max_time} {self.time_units}')
                print('#'*80)
                selection = input('Enter the time range over which you want to plot along with the number of plots you want. (3 values)\nIf you just want to plot everything, press return\n')
                numbers = selection.split(',')
                
                # If the length of the user input is appropriate (len == 2): {{{
                if len(numbers) == 3:
                    time_range = [float(v.strip()) for v in numbers[:2]]
                
                    self._first_pattern_idx = self.find_closest(times, time_range[0], mode = 1) # This gives the index of the time 
                    self._last_pattern_idx = self.find_closest(times, time_range[1], mode = 1) # This gives the index of the last pattern
                    self._num_patterns = int(numbers[-1])
                    
                    selecting = False
                #}}}
                # No input is given and thus, all files are loaded: {{{
                else:
                    self._first_pattern_idx = min_index
                    self._last_pattern_idx = max_index
                    self._num_patterns = len(timecodes)
                    selecting = False
                #}}}
        #}}}
        # If given a starting and ending idx: {{{
        else:
            self._first_pattern_idx = self.find_closest(times, start_time, mode = 1)
            self._last_pattern_idx = self.find_closest(times, end_time, mode = 1)
            self._num_patterns = num_patterns
        #}}}
        self._get_arrs(metadata_data=metadata_data)
    #}}} 
    # get_arrs: {{{
    def _get_arrs(self, metadata_data:dict = None):
        '''
        This function is used to obtain the data from the files that fall within the time
        frame selected.
  
   
        The time recorded in the filename will work to sort but will not work to plot.
        '''
        ys = []
        files = []
        temps = []
        #first_time = min(list(self.file_dict.keys())) 
        keys = list(metadata_data.keys())
        #all_times = self._get_time_arr(metadata_data=metadata_data, time_units=self.time_units) # All the times
        readable_time_keys = list(metadata_data.keys())

        tmp_rng = np.linspace(self._first_pattern_idx, self._last_pattern_idx, self._num_patterns) 
        tmp_rng = self.check_order_against_time(tmp_rng, readable_time_keys, metadata_data, )
        rng = [int(fl) for fl in tmp_rng]

        # Get the times: {{{
        t0 = metadata_data[readable_time_keys[rng[0]]]['epoch_time'] # The  initial time
        for i in rng:
            time = readable_time_keys[i] # Gives us the current readable time key
            temps.append(metadata_data[time]['temperature']) # Add the celsius temp
            f = self.file_dict[time]
            t1 = metadata_data[time]['epoch_time'] # Gives the current metadata
            # convert the time to selected units: {{{
            if self.time_units == 'min':
                current_time = (t1-t0)/60
            elif self.time_units == 'h':
                current_time = (t1-t0)/(60**2)
            elif self.time_units == 'sec':
                current_time == t1-t0
            #}}}
            # Get the times and files: {{{
            ys.append(current_time)
            files.append(f)
            #}}}
        #}}}

        # Get the tth and I vals {{{ 
        zs = [] # This will be the length of the files but will hold lists of intensities for each.
        self.max_i = 0
        self.min_i = 0
        min_tth = None
        max_tth = None
        max_len = None
        for f in files:
            data = np.loadtxt(f,skiprows=self.skiprows)
            tth = data[:,0]
            iau = data[:,1]
            # Record max angle: {{{
            if max_tth:
                if max_tth < max(tth):
                    max_tth = max(tth)
            else:
                max_tth = max(tth)
            #}}}
            # Record min angle: {{{
            if min_tth:
                if min_tth > min(tth):
                    min_tth = min(tth)
            else:
                min_tth = min(tth)
            #}}}
            # Record datapoints: {{{
            if max_len:
                if max_len < len(tth):
                    max_len = len(tth)
            else:
                max_len = len(tth)
            #}}}
            zs.append(iau) # Record the intensities for the current pattern.
            # Record the max and min intensities: {{{
            if max(iau) > self.max_i:
                self.max_i = max(iau)
            if min(iau) < self.min_i:
                self.min_i = min(iau)
            #}}}
        print(min_tth, max_tth, max_len)
        self.tth_arr = np.linspace(min_tth, max_tth, max_len)
        self.time_arr = np.array(ys)
        self.i_arr = np.array(zs)
        if temps:
            self.temp_arr = np.array(temps)
        else:
            self.temp_arr = None
        #}}}
        
    #}}}
    # _parse_imarr: {{{
    def _parse_imarr(self,im_arr = None):
        '''
        The goal of this function is to lighten up the get_imarr function  
        It will just parse an image array regardless of where its origin 
        The function will then return a tuple of: 

        (xs, ys, zs, max_z)
        '''
        # Define vars: {{{
        xs = []
        ys = []
        zs = [] 
        max_z = 0
        #}}}
        # Parse the image: {{{
        for y, zarr in enumerate(im_arr):
            inner_z = [] # This holds the zs for each row of the array
            ys.append(y)
            for x, z in enumerate(zarr): 
                if y == 0:
                    xs.append(x) # This only needs to happen once since the number should not change. 
                inner_z.append(z) 
                if z > max_z:
                    max_z = z
            zs.append(inner_z)
        #}}}
        # convert lists to arrays: {{{
        xs = np.array(xs)
        ys = np.array(ys)
        zs = np.array(zs)
        #}}}
        return (xs, ys, zs, max_z)
    #}}}
    # get_imarr: {{{
    def get_imarr(self,fileindex:int = 0):
        # Get X, Y, Z Data (IF Image): {{{        
        '''
        Now, we know that we are dealing with an image file. 
        This means that we should first load it using the Image class
        Then We convert to an array with numpy. 
        Xs are represented by each of the indices in the arrays in the primary array
        Ys are represented by each of the indices of arrays in the primary array
        Zs are stored as values in each of the arrays within the primary array.
        ''' 
        # Load information: {{{ 
        keys = list(self.file_dict.keys())
        image_time_key = keys[fileindex] # This is the time in seconds
        file = self.file_dict[image_time_key] # Get the filename you wanted
        self.image_time = image_time_key - keys[0] # Get relative from the first time.
        self.image_time_min = np.around(self.image_time/60,2)
        self.image_time_h = np.around(self.image_time/(60**2),2)
        #}}}
        # Handle the image: {{{
        self.im_arr = fabio.open(file).data # Using fabio instead of PIL.Image, we can get the exact same array in one line
        self.im_x, self.im_y, self.im_z, self.max_im_z = self._parse_imarr(self.im_arr)
        #}}} 
        #}}}
    #}}}
    # find_closest: {{{
    def find_closest(self,sorted_array, target, mode:int = 0):
        '''
        sorted_array: 
            an array where the values are sorted and not randomly distributed
        target: 
            the value you are looking for.
        mode: 
            0: returns the element from the list
            1: returns the index of the element in the list
        '''
        # Simple cases where you want the first or last element: {{{
        if target <= sorted_array[0]:
            if mode == 0:
                return sorted_array[0]
            elif mode == 1:
                return 0
        if target >= sorted_array[-1]:
            if mode == 0:
                return sorted_array[-1]
            elif mode == 1:
                return -1
        #}}}
        # Finding an exact match: {{{
        start, end = 0, len(sorted_array) - 1
        while start <= end:
            mid = (start + end) // 2
            if sorted_array[mid] == target:
                if mode== 0:
                    return sorted_array[mid]
                elif mode == 1:
                    return mid
            elif sorted_array[mid] < target:
                start = mid + 1
            else:
                end = mid - 1
        #}}} 
        #  Approximate matches: {{{
        # At this point, start is the smallest number greater than target
        # and end is the largest number less than target.
        # Return the closest of the two
        if start < len(sorted_array) and sorted_array[start] - target < target - sorted_array[end]:
            if mode == 0:
                return sorted_array[start]
            elif mode == 1:
                return start
        if mode == 0:
            return sorted_array[end]
        elif mode == 1:
            return end
        #}}}  
    #}}}
    # _get_time_arr: {{{
    def _get_time_arr(self, metadata_data:dict = None, time_units:str = 'min'):
        ''' 
        This function enables the fast acquisition of an array of 
        times for determining the range over which you would like to 
        collect data for making a waterfall plot or other useful functionality of this code. 
        '''
        first_time = min(entry['epoch_time'] for entry in metadata_data.values())
        if time_units == 's':
            times = [entry['epoch_time'] - first_time for entry in metadata_data.values()]
        elif time_units == 'min':
            times = [(entry['epoch_time'] - first_time)/60 for entry in metadata_data.values()]
        elif time_units == 'h':
            times = [(entry['epoch_time'] - first_time)/3600 for entry in metadata_data.values()]
        return times
    #}}}
    # _get_first_time{{{ 
    def _get_first_time(self,metadata_data:dict = None, debug = True):
        md_keys = list(metadata_data.keys()) # These are the timecodes pulled from the filenames
        epoch_times = [] # List of the epoch times for the dataset
        for key, entry in metadata_data.items():
            epoch = entry['epoch_time']
            epoch_times.append(epoch) # Add each of the epoch times 
        first_time = min(epoch_times) # Get the epoch time for the beginning of the run
        idx_first_time = epoch_times.index(first_time) # Get the index of the first time 
        key_first_time = md_keys[idx_first_time] # This gives us the timecode to look for
        fn_first_time = metadata_data[key_first_time]['filename'] # Give the exact filename 
        if idx_first_time != 0:
            if debug:
                print(f'Starting index is not zero! idx: {idx_first_time}')
                print(f'Starting timecode: {key_first_time}\nFilename: {fn_first_time}')
        return (first_time, idx_first_time, key_first_time, fn_first_time)
            
    #}}}
    # check_order_against_time: {{{
    def check_order_against_time(self,tmp_rng:list = None,data_dict_keys:list = None,  metadata_data:dict = None, mode:int= 0,
            debug:bool = False):
        '''
        This function is designed to reorder the files you are analyzing 
        if you discover that the order is wrong after analysis.

        This will return the re-ordered range (if necessary). 

        Mode:
            0: This is normal mode, returns a range of indices from the original dataset you pull from (for refinements)
            1: This is the alt mode, returns a range of indices from the refined dataset (after refinement, for analysis)
        '''
        # First, figure out what the actual t0 time is: {{{
        md_keys = list(metadata_data.keys()) # These are the timecodes pulled from the filenames
        start_time, idx_first_time, md_key_for_zero, md_filename = self._get_first_time(metadata_data, debug)
        #}}}
        # Now, we need to check if the order is correct regarding the metadata: {{{   
        fixed_range = []
        negative_times = [] # indices of the patterns we need to reorient. 
        for idx, number in enumerate(tmp_rng): 
            file_time = data_dict_keys[int(number)-1]  
            md_entry = metadata_data[file_time] # Get the metadata for the current time
            #start_time = metadata_data[md_keys[0]]['epoch_time'] # This gives us the starting time
            current_epoch_time = md_entry['epoch_time'] # This gives the current epoch time
            time = (current_epoch_time - start_time)/60 # This is in minutes 
            if time <0:
                negative_times.append(idx)

        if negative_times:  
            for idx in negative_times: 
                if mode == 0:
                    fixed_range.append(tmp_rng[idx])
                else:
                    fixed_range.append(idx)
            for idx,  number in enumerate(tmp_rng):
                if idx not in negative_times:
                    if mode == 0:
                        fixed_range.append(number) 
                    else:
                        fixed_range.append(idx)
        else: 
            #fixed_range = np.linspace(0, len(tmp_rng)-1, len(tmp_rng), dtype=int)
            if mode == 0:
                fixed_range = tmp_rng
            elif mode == 1:
                fixed_range = np.linspace(0, len(tmp_rng)-1, len(tmp_rng), dtype=int) # I think this has to start at 1 because we subtract 1 elsewhere.
        
        #}}} 
        if debug:
            print(f'Final fixed range: {fixed_range}')
        return fixed_range
    
    #}}} 
    # get_raw_patterns: {{{
    def get_raw_patterns(self,
            start_idx:int = 0,
            end_idx:int = None,
            num_patterns:int = 2,
        ):
        '''
        The purpose of this function is to quickly get pattern data from 
        raw data that have been located and allow you to plot the data as a waterfall. 

        This is a good tool for when you want to see a broad overview of what happened during an experiment
        without having to refine all the data first. 

        The resulting dataset will have evenly spaced data given your input parameters
        '''
        os.chdir(self.data_dir)
        files = self.metadata_data # It is better to use this because these keys are sorted in time order
        total_files = len(files)
        
        if end_idx == None:
            end_idx = total_files - 1

        pattern_rng = np.linspace(start_idx, end_idx, num_patterns, dtype= int)

        self.raw_data = {}
        pattern = 0

        for i, (key, md) in enumerate(files.items()):
            ''' 
            If the index (i) is equal to a value in the 
            pattern_range, we load and record it. 
            If not, we discard.
            '''
            try:
                f = self.file_dict[key] 
                if i in pattern_rng:
                    tth, yobs = self._load_raw_xy(f, self.data_dir) 
                    temp = md['temperature'] # This is the temp in deg C
                    corrected_time = md['corrected_time']
                    time = np.around(corrected_time/60, 2) # This is the time in minutes

                    hovertemplate = f'2{self._theta}{self._degree_symbol}: '+'%{x}<br>Intensity: '+'%{y}<br>'+f'Pattern {i}: {time} min<br>{temp} {self._degree_celsius}'
                    self.raw_data[pattern] = {
                            'tth': tth,
                            'yobs': yobs,
                            'md': md,
                            'temp': temp,
                            'time': time,
                            'corrected_time': corrected_time,
                            'hovertemplate': hovertemplate,
                    }
                    pattern += 1
            except:
                time_min = np.around(md['corrected_time']/60, 2)
                index = md['pattern_index']
                print(f'Key: {key} not found in file dict: \n\tTime: {time_min} min\n\tPattern index: {index}\n\tpossible missing data')
                pass
        os.chdir(self.current_dir)

    #}}}
#}}}
# is_number: {{{
def is_number(v):
    '''
    Simply test if something is a number.
    '''
    try:
        float(v)
        return True
    except:
        return False
#}}}

