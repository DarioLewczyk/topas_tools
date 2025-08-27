# Authorship: {{{
'''
Written by: Dario C. Lewczyk
Date: 12-18-24
'''
#}}}
# Imports: {{{
from topas_tools.plotting.experiment_geometry_plotting import GeometryPlotterInterface, GeometryPlotter
from topas_tools.area_detector_tools.geometry import DiffracGeometryInterface,DiffracGeometry
from topas_tools.utils.topas_utils import Utils, UsefulUnicode
import numpy as np
# }}}
# ExperimentPlanAnalyzer: {{{
class ExperimentPlanAnalyzer(Utils, UsefulUnicode):
    # __init__: {{{
    def __init__(self,    
         diffrac_geometry:DiffracGeometryInterface, 
         diffrac_geometry_plotter:GeometryPlotterInterface,
        **kwargs
        ):
        '''
        Create instances of DiffracGeometry and GeometryPlotter before initializing this class
        This allows you to make use of all the attributes of both classes. 

        kwargs:
           pixel_size: size in mm of square pixel
           detector_x_pixels: pixels in each row of the detector
           detector_y_pixels: pixels in each column of the detector
           distance: sample to detector distance
           tilt_angle: tilt angle about the x axis of the sample for the detector to tilt
           sample_x: x position from the center of the detector (in mm)
           sample_y: y position from the center of the detector (in mm)
        '''
        UsefulUnicode.__init__(self)
        self.diffrac_geometry = diffrac_geometry
        self.diffrac_geometry_plotter = diffrac_geometry_plotter
        # handle kwargs updates: {{{
        self.diffrac_geometry.pixel_size = kwargs.get('pixel_size', self.diffrac_geometry.pixel_size)
        self.diffrac_geometry.detector_x_pixels = kwargs.get('detector_x_pixels',self.diffrac_geometry.detector_x_pixels)
        self.diffrac_geometry.detector_y_pixels = kwargs.get('detector_y_pixels',self.diffrac_geometry.detector_y_pixels)
        self.diffrac_geometry.distance = kwargs.get('distance', self.diffrac_geometry.distance)
        self.diffrac_geometry.tilt_angle= kwargs.get('tilt_angle', self.diffrac_geometry.tilt_angle)
        self.diffrac_geometry.sample_x = kwargs.get('sample_x', self.diffrac_geometry.sample_x)
        self.diffrac_geometry.sample_y = kwargs.get('sample_y', self.diffrac_geometry.sample_y)
        #}}} 

    #}}}
    # get_detector_precision: {{{ 
    def get_detector_precision(self,
            pixel_x:int = 0,
            pixel_y:int = 0,
            scan_type:str = None,
            scan_rng:range = None,
            precision:int = 5,
            print_config:bool = True,
            plot_detector:bool = True,
            show_sample_frame_pixels:bool = False, 
            **kwargs
            ):
        '''
        This function is designed to calculate the precision of your specified detector and 
        print out the detector configuration alongside plotting the detector and 
        any pixels you are looking at in the lab frame in an interactive window. 

        
        '''
        self.diffrac_geometry._update_geometry_properties(**kwargs) # Update the geometry properties first
        if print_config:
            self.print_experimental_configuration(pixel_x, pixel_y, scan_type, scan_rng, precision)
            self.diffrac_geometry.calc_detector_size(
                    self.diffrac_geometry.x_grid,
                    self.diffrac_geometry.z_grid,
                    self.diffrac_geometry.y_grid
            )
        if plot_detector:
            self.diffrac_geometry_plotter.plot_detector_in_lab( 
                    pixel_x=pixel_x,
                    pixel_y=pixel_y,
                    scan_type=scan_type,
                    scan_rng=scan_rng,
                    show_sample_frame_pixels=show_sample_frame_pixels,
                    **kwargs
            )
    #}}}
    # print_experimental_configuration: {{{
    def print_experimental_configuration(self, 
            pixel_x=0, 
            pixel_y=0, 
            scan_type=None,
            scan_rng=None,
            precision:int = 5,
            ):
        '''
        Quick printout to get all the necessary information 
        about your experiment in an easy to read view
        '''
        # Configuration Printouts: {{{ 
        print('Experimental Parameters:')
        # keys: {{{
        keys = [
            f'{self._lambda}',#1
            'Energy',#2
            'Distance',#3
            'Tilt Angle',#4
            'Detector Width',#5
            'Detector Height',#6
            'Pixel Size',#7
            'Detector Size',#8
            'Selected Pixel',#9
            'Scan Type',#10
            'Scan Range',#11
            'Sample Position',#12
            'Detector Position', # 13
        ]
        #}}}
        # prms: {{{
        prms = [
            f'{np.around(self.diffrac_geometry.lam, precision)} Å',#1
            f'{np.around(self.diffrac_geometry.energy, precision)} keV',#2
            f'{self.diffrac_geometry.distance} mm',#3
            f'{self.diffrac_geometry.tilt_angle} {self._degree_symbol}',#4
            f'{self.diffrac_geometry.detector_width} mm',#5
            f'{self.diffrac_geometry.detector_height} mm',#6
            f'{self.diffrac_geometry.pixel_size*10**3} µm',#7
            f'{self.diffrac_geometry.detector_x_pixels} px x {self.diffrac_geometry.detector_y_pixels} px',#8
            f'{pixel_x},{pixel_y}',#9
            f'{scan_type}',#10
            f'{scan_rng}',#11
            f'({self.diffrac_geometry.sample_x}, {self.diffrac_geometry.sample_y}) mm',#12
            f'({self.diffrac_geometry.detector_x}, {self.diffrac_geometry.detector_y}) mm', # 13
        ]
        #}}}
        # Generate the summary table: {{{
        self.generate_table(
            iterable = prms,
            header = ['Key', 'Value'],
            index_list = keys,
        )
        #}}}
        #}}}
    #}}}
#}}}
