# Authorship: {{{
'''
Written by: Dario Lewczyk
Date: 06-28-24
Purpose:
    Give the user tools needed to get information about 2D area detector images
    - Used to get conclusive definitions of what the integrated intensity in a 1D 
    pattern means when using pyFAI
    - Used to determine the angular range of individual pixels on a detector
    - Leverages plotting tools to generate images of the diffraction data, cake plots, etc.
'''
#}}}
# Imports: {{{
import os, re
from tqdm import tqdm
import numpy as np
from glob import glob
import pyFAI
import fabio

from topas_tools.plotting.image_plotting import ImagePlotter
#}}}
# ADTools: {{{
class ADTools(ImagePlotter):
    # __init__: {{{
    def __init__(self,
            data_dir:str = None,
            fileextension:str = 'tiff',
            mode:int = 0,
            metadata:dict = None,
            poni_dir:str = None,
            mask_dir:str = None,
            poni_extension:str = 'poni',
            mask_extension:str = 'npy',
            **kwargs
            ):
        '''
        The inputs for this function automatically get passed to ImagePlotter

        kwargs: 
            position_of_time = 1 # This refers to when you run regular expressions on the filename, where does the timestamp show up?
            len_of_time = 6 # Refers to how long your timecode in the filename is. If it is present.
            time_units = min # Refers to the time unit you would like displayed (if available)
            file_time_units = sec # Refers to the time units recorded in the filename
            skiprows = 1 # Refers to the number of rows numpy should skip when reading data from .xy files
        '''
        ImagePlotter.__init__(self,data_dir=data_dir, fileextension=fileextension, mode = mode, metadata= metadata, **kwargs)
        # Get the masks and PONI files: {{{
        self.poni_file, self.poni_dir = self.find_a_file(poni_dir, poni_extension)
        self.mask_file, self.mask_dir = self.find_a_file(mask_dir, mask_extension)
        self._load_poni(self.poni_file, self.poni_dir)
        self._load_mask(self.mask_file, self.mask_dir)
        #}}}
       
    #}}}
    # _load_poni: {{{
    def _load_poni(self, poni_file, poni_dir, **kwargs):
        os.chdir(poni_dir)
        self.ai = pyFAI.load(poni_file)
        os.chdir(self.data_dir)
    #}}}
    # _load_mask: {{{
    def _load_mask(self, mask_file, mask_dir):
        os.chdir(mask_dir)
        self.mask = fabio.open(mask_file).data # load mask file
        self._make_nan_mask() # Convert zeros to NAN for plotting
        self.mask_x, self.mask_y, self.mask_z, self.max_mask_z = self._parse_imarr(self.mask) # Get individual components
        self.nan_mask_x, self.nan_mask_y, self.nan_mask_z, self.nan_max_mask_z = self._parse_imarr(self.nan_mask) # Get individual components of NAN
        os.chdir(self.data_dir)
    #}}}
    # _import_poni_and_mask: {{{
    def _import_poni_and_mask(self,fileindex=None, **kwargs):
        # kwargs: {{{
        self.poni_file = kwargs.get('poni_file', self.poni_file)
        self.poni_dir = kwargs.get('poni_dir', self.poni_dir)
        self.mask_file = kwargs.get('mask_file', self.mask_file)
        self.mask_dir = kwargs.get('mask_dir', self.mask_dir)
        #}}} 
        # Load image file
        if fileindex != None:
            os.chdir(self.data_dir)
            self.get_imarr(fileindex) # Loads the image array as self.im_arr
        # load the PONI and mask files: {{{
        self._load_poni(self.poni_file, self.poni_dir)
        self._load_mask(self.mask_file, self.mask_dir)
        # get relevant stuff from Azimuthal Integrator: {{{
        self.poni_y = self.ai.poni1
        self.poni_x = self.ai.poni2 

        self.pixel_x = self.ai.pixel2 # pixel2 should be the x direction
        self.pixel_y = self.ai.pixel1 # pixel1 should be the y direction
        #}}}
        #}}}
        # convert pixels to distances: {{{
        self._transform_pixels_to_distances()
        #}}}
    #}}}
    # make_nan_mask: {{{
    def _make_nan_mask(self,):
        '''
        This function will operate on your mask array.
        It will replace every zero value with nan so when it is plotted
        you just have blank space and can see the diffraction pattern below.
        '''
        self.nan_mask = np.where(self.mask == 0, np.nan, self.mask)
    #}}}
    # integrate_2d: {{{
    def integrate_2d(
            self,
            fileindex:int = None,
            npt_rad = 1200,
            npt_azim = 360,
            unit:str = '2th_deg',
            method:tuple = ('full split', 'csl', 'cython'),
            plot:bool = True,
            return_cake:bool = False,
            **kwargs
        ):
        '''
        This function leverages pyFAI for integration of an area detector image to a cake plot

        **kwargs:
            poni_dir: default is self.poni_dir
            poni_file: default is self.poni
            mask_dir: default is self.mask_dir
            mask_file: default is self.mask

            imarr: self.im_arr by default
            mask: self.mask by default

            Also includes kwargs from the image plotter tool. 
        '''
        if fileindex != None:
            self._import_poni_and_mask(fileindex=fileindex, **kwargs)
        
        imarr = kwargs.get('imarr', self.im_arr)
        mask = kwargs.get('mask', self.mask)
       
        # Get the caked data: {{{ 
        cake, radial, chi = self.ai.integrate2d(imarr, npt_rad, npt_azim, mask = mask, method = method, unit = unit)
        #}}}
        if plot:
            self.plot_cake(radial=self.radial, chi = self.chi, cake = self.cake, unit = unit, **kwargs)
        # If you want to return the integration result or not: {{{
        if return_cake:
            return cake, radial, chi
        else:
            self.cake = cake
            self.radial = radial
            self.chi = chi
        #}}}
    #}}}
    # integrate_1d: {{{
    def integrate_1d(self,
            fileindex:int = None,
            npt:int = 6000,
            unit:str = '2th_deg',
            correctSolidAngle:bool = False,
            method:tuple = (1, 'full split', 'csr', 'opencl', 'gpu'),
            plot:bool = True,
            return_pattern:bool = False,
            **kwargs,
        ):
        '''
        This function leverages pyFAI for integration of an area detector image to a 1D 
        diffraction pattern. 

        **kwargs:
            poni_dir: default is self.poni_dir
            poni_file: default is self.poni
            mask_dir: default is self.mask_dir
            mask_file: default is self.mask

            imarr: self.im_arr by default
            mask: self.mask by default
        '''
        if fileindex != None:
            self._import_poni_and_mask(fileindex=fileindex, **kwargs)
       
      
        imarr = kwargs.get('imarr', self.im_arr)
        mask = kwargs.get('mask', self.mask)
        # Integrate the data: {{{ 
        x_1d, y_1d = self.ai.integrate1d(
            imarr,
            npt = npt,
            mask = mask,
            unit = unit,
            correctSolidAngle=correctSolidAngle,
            method=method,
        )
        #}}}
        # plot: {{{
        if plot:
            self.plot_1d_integrated_pattern(x =x_1d, y =y_1d, unit = unit,**kwargs)
        #}}}
        # Check if you want to return arrays or not: {{{
        if not return_pattern:
            self.x_1d =  x_1d
            self.y_1d = y_1d
        else:
            return x_1d, y_1d
        #}}}
    #}}}
    # check_avg_intensity_at_point: {{{
    def check_avg_intensity_at_radial_point(self,radial_point:float = None, return_intensities:bool = False):
        '''
        This function is designed to find the average 
        intensity across all patterns of a cake plot
        at a given point.

        if you choose to return_intensities, it will output a list of intensities.
        '''
        intensities = []
        #loop through the cake: {{{
        for pattern in self.cake:
            idx = self.find_closest(self.radial, radial_point, mode = 1) # Mode 1 returns an index
            intensity = pattern[idx] # Get the intensity at the current point.
            if intensity >0:
                intensities.append(intensity) # Ignore masked regions
        #}}}
        intensities = np.array(intensities)
        if return_intensities:
            return intensities
        else:
            return np.average(intensities)
    #}}}
    # transform_pixels_to_distances: {{{
    def _transform_pixels_to_distances(self):
        '''
        This function is automatically called when a PONI and image file
        are loaded, so it will remain hidden from the end user.
        '''
        # Convert x, y: {{{
        self.im_x_dist = self.im_x *  self.pixel_x
        self.im_y_dist = self.im_y *  self.pixel_y
        #}}}
        # Convert mask_x, mask_y:{{{ 
        self.mask_x_dist = self.mask_x * self.pixel_x
        self.mask_y_dist = self.mask_y * self.pixel_y

        self.nan_mask_x_dist = self.nan_mask_x * self.pixel_x
        self.nan_mask_y_dist = self.nan_mask_y * self.pixel_y
        #}}}

    #}}}
    # plot_2d_diffraction_image: {{{
    def plot_2d_diffraction_image(
            self,
            fileindex:int = 0, 
            title_text:str = '2D Diffraction Image',
            show_mask:bool = False,
            plot_distances:bool = False,
            show_figure:bool = True,
            **kwargs,
            ):
        '''
        This function calls "_plot_2d_diffraction_image" from the ImagePlotter
        The reason why it needs to be defined here is because we need to have access
        to the distance functionality
        '''
        self._import_poni_and_mask(fileindex = fileindex, **kwargs)
        self._plot_2d_diffraction_image(
                fileindex=fileindex,
                title_text=title_text,
                show_mask=show_mask,
                plot_distances=plot_distances,
                show_figure=show_figure,
                **kwargs,
                )

    #}}}
    # extract_detector_slices: {{{
    def extract_detector_slices(self,
            fileindex:int = None,
            width:int = 0,
            return_maps:bool = False,
            **kwargs
        ):
        '''
        This function is for getting slices of a 2D diffraction image
        NOTE: You can just run the function having only specified the width if you choose. 
                If you do this, it will just default to using the data this class already has loaded.

        x: Pixel X direction distances
        y: Pixel Y direction distances
        center_x: a value for the PONI x (m) unless you are using a different coordinate system for x,y
        center_y: a value for the PONI y (m)
        heat_map: this is your z values for the diffraction image
        mask: This is your mask
        width: This is the number of pixels to the left or right
        '''
        # If given a fileindex:{{{
        if fileindex != None:
            self._import_poni_and_mask(fileindex = fileindex, **kwargs)
        #}}}
        # Defaults from kwargs: {{{
        x = kwargs.get('x',self.im_x_dist)
        y = kwargs.get('y',self.im_y_dist)
        center_x = kwargs.get('center_x',self.poni_x)
        center_y = kwargs.get('center_y',self.poni_y)
        heat_map = kwargs.get('heat_map',self.im_z)
        mask = kwargs.get('mask',self.mask) 
        #}}}
        x, y = np.meshgrid(x, y)
        # Get the IDX values for the center point: {{{  
        x_center = self.find_closest(x[0,:],center_x, mode = 1)
        y_center = self.find_closest(y[:,0],center_y, mode = 1) 
        #}}}
        # Initialize Heatmaps for Vertical and Horizontal Scans: {{{
        self.vertical_scan  = np.full_like(heat_map, np.nan)
        self.horizontal_scan  = np.full_like(heat_map, np.nan)
        #}}}
        # Extract vertical scans: {{{
        for i in range(max(0, x_center - width), min(x.shape[0], x_center + width + 1)):
            for j in range(x.shape[1]):
                if mask[i, j] == 0:  # If the data should not be ignored
                    self.vertical_scan[i, j] = heat_map[i, j]
        #}}}
        # Extract horizontal scans: {{{ 
        for j in range(max(0, y_center - width), min(y.shape[1], y_center + width + 1)):
            for i in range(y.shape[0]):
                if mask[i, j] == 0:  # If the data should not be ignored
                    self.horizontal_scan[i, j] = heat_map[i, j]
        #}}}
        if return_maps:
            return self.vertical_scan, self.horizontal_scan
    #}}}
    # integrate_slice: {{{
    def integrate_slice(self,
            fileindex:int = None,
            width:int = 0, 
            npt:int = 6000,
            unit:str = '2th_deg',
            correctSolidAngle:bool = False,
            method:tuple = (1, 'full split', 'csr', 'opencl', 'gpu'), 
            plot_patterns:bool = True,
            **kwargs
        ):
        '''
        This function uses the slicing algorithm,  extract_detector_slices()
        and automatically integrates it using the 1d integration. 

        This function has the same kwargs as those functions. 
        '''
        self.extract_detector_slices(fileindex, width, **kwargs)
        # integrate the vertical scan: {{{
        self.tth_vert_slice, self.i_vert_slice = self.integrate_1d(
            npt=npt,
            unit=unit,
            correctSolidAngle=correctSolidAngle,
            method = method,
            plot = plot_patterns, 
            return_pattern = True,
            imarr = self.vertical_scan,
            title_text = f'Vertical scan ({width+1} pixels)',
            color = 'green',
            **kwargs
        )
        #}}} 
        # integrate the horizontal scan: {{{
        self.tth_horiz_slice, self.i_horiz_slice = self.integrate_1d(
            npt=npt,
            unit=unit,
            correctSolidAngle=correctSolidAngle,
            method = method,
            plot = plot_patterns, 
            return_pattern=True,
            imarr = self.horizontal_scan,
            title_text = f'Horizontal scan ({width+1} pixels)',
            color = 'blue',
            **kwargs
        )
        #}}}

    #}}}
#}}}
