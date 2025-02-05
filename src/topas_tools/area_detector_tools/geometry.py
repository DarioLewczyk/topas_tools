# Authorship: {{{ 
'''
Written by: Dario C. Lewczyk
Date: 12-13-2024
Purpose: Simulate different detector positions and orientations in a lab frame of reference to determine 
experimental resolution and angular range for a given set of experimental conditions. 
'''
#}}}
# Imports: {{{
from topas_tools.utils.topas_utils import UsefulUnicode
import numpy as np
import pandas as pd
#}}}
# DiffracGeometryInterface: {{{
class DiffracGeometryInterface:
    def define_detector(self, **kwargs):
        pass
    def convert_tth_to_d(self,tth, precision, print_result = False):
        pass
    def _update_geometry_properties(self, **kwargs):
        pass
    

#}}}
# DiffracCalc: {{{ 
class DiffracGeometry(DiffracGeometryInterface):
    # __init__: {{{
    def __init__(
            self,
            pixel_size:float = 200e-3,
            detector_x_pixels:int = 2048,
            detector_y_pixels:int = 2048,
            distance:float = 650,
            tilt_angle:float = 0,
            sample_x:float = 0,
            sample_y:float = 0,
            detector_x:float = 0,
            detector_y:float = 0,
            lam:float = None,
            energy:float = None,
            ):
        '''
        pixel_size: size of a square pixel (in mm)
        detector_x_pixels: number of pixels in the x axis (horizontal)
        detector_y_pixels: number of pixels in the y axis (vertical)
        distance: sample-to-detector distance (in mm)
        tilt_angle: angle to tilt detector about the sample (in degrees)
        sample_x: x position of your sample (in mm from the center of the detector)
        sample_y: y position of your sample (in mm from the center of the detector)
        detector_x: x position of your detector
        detector_y: y position of your detector
        lam: wavelength of experiment (in Å)
        energy: energy of the experiment (in eV) *optional*
        ''' 
        self.uni = UsefulUnicode()
        self.pixel_size = pixel_size
        self.detector_x_pixels = detector_x_pixels
        self.detector_y_pixels = detector_y_pixels
        self.distance = distance
        self.tilt_angle = tilt_angle
        self.sample_x = sample_x
        self.sample_y = sample_y
        self.detector_x = detector_x
        self.detector_y = detector_y
        if lam != None: 
            self.lam = lam
            self.energy = energy
        if energy != None: 
            self.energy = energy
            self.lam = lam

        self.avg_tths = None
        self.avg_ds = None
        self.delta_d_over_ds = None

        # calculate the detector and its properties relative to your sample: {{{
        self.define_detector()
        #}}} 
    #}}} 
    # Property Definitions: {{{
    # Detector Properties: {{{
    # pixel_size: {{{
    @property
    def pixel_size(self):
        return self._pixel_size
    @pixel_size.setter
    def pixel_size(self, pixel_size):
        if isinstance(pixel_size, (int,float)):
            self._pixel_size = pixel_size
        else:
            raise ValueError(f'Pixel size must be numerical! You gave: {pixel_size}')
    #}}}
    # detector_x_pixels: {{{
    @property
    def detector_x_pixels(self):
        return self._detector_x_pixels
    @detector_x_pixels.setter
    def detector_x_pixels(self, value):
        if isinstance(value, int):
            self._detector_x_pixels = value
        else:
            raise ValueError(f'Detector X Pixels Must be an Integer, cannot have part of a pixel!')
    #}}}
    # detector_y_pixels: {{{
    @property
    def detector_y_pixels(self):
        return self._detector_y_pixels
    @detector_y_pixels.setter
    def detector_y_pixels(self,value):
        if isinstance(value, int):
            self._detector_y_pixels = value
        else:
            raise ValueError(f'Detector Y Pixels Must be an Integer, cannot have part of a pixel!')
    #}}}
    # distance: {{{
    @property
    def distance(self):
        return self._distance
    @distance.setter
    def distance(self, distance):
        if isinstance(distance, (int,float)):
            self._distance = distance
        else:
            raise ValueError('You must give a numerical distance!')
    #}}}
    # tilt_angle: {{{
    @property
    def tilt_angle(self):
        return self._tilt_angle
    @tilt_angle.setter
    def tilt_angle(self,tilt_angle):
        if isinstance(tilt_angle, (int,float)):
            self._tilt_angle = tilt_angle
        else:
            raise ValueError('You must give a numerical tilt angle for the detector!')
    #}}}
    # detector_width: {{{
    @property 
    def detector_width(self):
        self._detector_width = self._calculate_detector_dimension(self.detector_x_pixels)
        return self._detector_width
    #}}}
    # detector_height: {{{
    @property 
    def detector_height(self):
        self._detector_height = self._calculate_detector_dimension(self.detector_y_pixels)
        return self._detector_height
    #}}}
    # detector_x: {{{
    @property
    def detector_x(self):
        return self._detector_x
    @detector_x.setter
    def detector_x(self,detector_x):
        if isinstance(detector_x, (int,float)):
            self._detector_x = detector_x
        else:
            raise ValueError('Detector X position must be numeric!')
    #}}}
    # detector_y: {{{
    @property
    def detector_y(self):
        return self._detector_y
    @detector_y.setter
    def detector_y(self,detector_y):
        if isinstance(detector_y, (int,float)):
            self._detector_y = detector_y
        else:
            raise ValueError('Detector Y position must be numeric!')
    #}}}
    #}}}
    # Sample Properties: {{{
    # sample_x: {{{
    @property
    def sample_x(self):
        return self._sample_x
    @sample_x.setter
    def sample_x(self, sample_x):
        if isinstance(sample_x, (int,float)):
            self._sample_x = sample_x
        else:
            raise ValueError('Sample_X must be numeric!')
    #}}}
    #sample_y: {{{
    @property
    def sample_y(self):
        return self._sample_y
    @sample_y.setter
    def sample_y(self, sample_y):
        if isinstance(sample_y, (int,float)):
            self._sample_y = sample_y
        else:
            raise ValueError('Sample_Y must be numeric!')
    #}}}
    #}}} 
    # Beamline Properties: {{{
    # lam: {{{
    @property
    def lam(self):
        return self._lam
    @lam.setter
    def lam(self,lam):
        if isinstance(lam, (float)):
            self._lam = lam
        else:
            if self.energy:
                self.lam = self.convert_keV_to_lam(self.energy)
            else:
                raise ValueError('You must provide either a wavelength in Å or an energy in keV!')
    #}}}
    # energy: {{{
    @property
    def energy(self):
        return self._energy
    @energy.setter
    def energy(self, energy):
        if isinstance(energy, (float,int)):
            self._energy = energy
        else: 
            if self.lam:
                self._energy = self.convert_lam_to_keV(self.lam) # calculate the energy
            else:
                raise ValueError('You must provide at least a wavelength in Å or an energy in keV!')
    #}}}
    #}}}
    #}}} 
    # _update_geometry_properties: {{{
    def _update_geometry_properties(self,**kwargs):
        '''
        Gives a quick function to update the properties of this class easily.

        kwargs:
            pixel_size
            detector_x_pixels
            detector_y_pixels
            distance
            tilt_angle
            sample_x
            sample_y
            detector_x
            detector_y
            lam
            energy
        '''
        self.pixel_size = kwargs.get('pixel_size', self.pixel_size)
        self.detector_x_pixels = kwargs.get('detector_x_pixels', self.detector_x_pixels)
        self.detector_y_pixels = kwargs.get('detector_y_pixels', self.detector_y_pixels)
        self.distance = kwargs.get('distance', self.distance)
        self.tilt_angle = kwargs.get('tilt_angle', self.tilt_angle)
        self.sample_x = kwargs.get('sample_x', self.sample_x)
        self.sample_y = kwargs.get('sample_y', self.sample_y)
        self.detector_x = kwargs.get('detector_x', self.detector_x)
        self.detector_y = kwargs.get('detector_y', self.detector_y)
        self.lam = kwargs.get('lam', self.lam)
        self.energy = kwargs.get('energy', self.energy)
    #}}}
    # convert_keV_to_lam: {{{
    def convert_keV_to_lam(self,energy:float = None):
        '''
        This converts a given energy in keV to wavelength in angstroms
        '''
        h = 4.135667696*10**(-18) #keV·s
        c = 2.9979*10**(18) # Å/s
        lam = h*c/energy
        return lam
    #}}}
    # convert_lam_to_keV: {{{
    def convert_lam_to_keV(self,lam:float = None):
        '''
        Converts a given wavelength in Å to energy in keV
        '''
        h = 4.135667696*10**(-18) #keV·s
        c = 2.9979*10**(18) # Å/s
        energy = h*c/lam
        return energy
    #}}}
    # convert_tth_to_d: {{{
    def convert_tth_to_d(self, tth:float, precision:int = 6, print_result = False):
        '''
        This uses the wavelength and a 2theta value 
        to give the d spacing in Å

        precision only affects the print
        '''
        d = self.lam/(2*np.sin(np.radians(tth)/2))
        if print_result:
            print(f'2{self.uni._theta}: {tth}{self.uni._degree_symbol} has a d-spacing of: {np.around(d,precision)} Å at {self.uni._lambda} = {self.lam} Å')
        return d
    #}}}
    # calculate_d_spacings_for_pixel_corners: {{{
    def calculate_d_spacings_for_pixel_corners(self, tths):
        '''
        Calculates the d-spacings at a specified precision 

        Order is:
        1) LB, 2) RB, 3) LT, 4) RT
        '''
        d_spacings = []
        for tth in tths:
            d = self.convert_tth_to_d(tth)
            d_spacings.append(d)
        d_spacings = np.array(d_spacings)
        return d_spacings
    #}}}
    # calculate_delta_d: {{{
    def calculate_delta_d_over_d(self, ):
        '''
        This needs to calculate the ∆d/d values
        
        To get the ∆d values, it is relatively simple. We just need to take self.pixel_scan
        and average the d spacings for all the pixels. Then we just take that list and take the absolute np.diff(avg_ds)
        '''
        avg_ds = []
        avg_tths = []
        px_names = []
        delta_d_over_ds = []
        for px, entry in self.pixel_scan.items():
            tth = entry['tth'] # Gets the tth for the sample frame of reference
            avg_tth = np.average(tth) 
            ds = self.calculate_d_spacings_for_pixel_corners(tth)  # Get the d spacings for each of the pixel corners.
            avg_d = np.average(ds)
            avg_ds.append(avg_d)
            px_names.append(px)
            avg_tths.append(avg_tth)
        delta_d = np.abs(np.diff(avg_ds)) # Get the delta d (1 shorter than the original pixel list)
        # record the ∆d values in the dictionary: {{{
        for i, key in enumerate(px_names):
            avg_d = avg_ds[i]
            avg_tth = avg_tths[i]
            if i == 0:
                delta_d_over_ds.append(0)
                self.pixel_scan[key].update({
                    'avg_d': avg_d,
                    'avg_tth':avg_tth,
                    'delta_d': 0,
                    'delta_d_over_d': 0/avg_d
                })
            else:
                delta_d_over_ds.append(delta_d[i-1])
                self.pixel_scan[key].update({
                    'avg_d': avg_d,
                    'avg_tth':avg_tth, 
                    'delta_d':delta_d[i-1],
                    'delta_d_over_d':delta_d[i-1]/avg_d,
                })
        #}}} 
        self.avg_tths = avg_tths
        self.avg_ds = avg_ds
        self.delta_d_over_ds = delta_d_over_ds
    #}}}
    # _calculate_detector_dimension: {{{
    def _calculate_detector_dimension(self, detector_pixels):
        return self.pixel_size * detector_pixels
    #}}}
    # angle_between_points: {{{
    def angle_between_points(self, a:list = None,b:list = None,c:list = None):
        '''
        This function simply calculates the angle between 3 2-dimensional points. 

        The function returns the angle in degrees for simplicity
        '''
        angle = np.degrees(
            np.arctan2(c[1]-b[1], c[0] - b[0]) - np.arctan2(a[1]-b[1], a[0]-b[0])
        )
        return angle
    #}}}
    # angle_between_vectors: {{{
    def angle_between_vectors(self, v1, v2):
        '''
        Calculate the angle in degrees between two vectors
        
        '''
        v1 = np.array(v1)
        v2 = np.array(v2)

        # Calculate the dot product of the two vectors
        dot_product = np.dot(v1,v2)

        # Calculate the magnitude of each vector 
        mag_v1 = np.linalg.norm(v1)
        mag_v2 = np.linalg.norm(v2)

        # Calculate the cosine of the angle between the vectors
        cos_angle = dot_product/(mag_v1*mag_v2)

        # Calculate the angle in radians: 
        angle_rad = np.arccos(cos_angle)

        # Convert to deg
        angle_deg = np.degrees(angle_rad)

        return angle_deg
    #}}}
    # distance_offset: {{{
    def distance_offset(self, v1, angle_deg):
        # This will calculate the distance offset between two vectors when we have a given angle between them
        v1 = np.array(v1)
        # Calculate the magnitude of the vectors
        mag_v1 = np.linalg.norm(v1)
        
        # Convert the angle from deg to rad
        angle_rad = np.radians(angle_deg)

        # Calculate the distance offset using the vectors
        distance_offset = mag_v1 * np.sin(angle_rad)
        return distance_offset
    #}}}
    # move_detector_by_angle: {{{
    def move_detector_by_angle(self, v1=None, angle, axis = 'x',update_prms:bool = False):
        '''
        This uses a vector (the unmodified detector position) and an angle to 
        determine the new vector that defines the top of the detector after some rotation
        
        As a part of this, the detector distance will change but the magnitude of the sample to the detector will not.
        '''
        if v1 == None:
            v1 = np.array([0,0,self.distance]) # If you don't specify the vector, use the vector of the sample to the detector
        angle_rad = np.radians(angle)
        # Create a rotation matrix to rotate about either x or z axis (y)
        axis = axis.lower()
        # Define rotation matrices: {{{
        if axis == 'x':
            rotation_matrix = np.array([
                [1,0,0],
                [0, np.cos(angle_rad), -np.sin(angle_rad)],
                [0, np.sin(angle_rad), np.cos(angle_rad)]
            ])
        elif axis == 'y':
            rotation_matrix = np.array([
                [np.cos(angle_rad), 0, np.sin(angle)],
                [0,1,0],
                [-np.sin(angle_rad), 0, np.cos(angle)]
            ])
        elif axis == 'z':
            rotation_matrix = np.array([
                [np.cos(angle_rad), -np.sin(angle_rad), 0],
                [np.sin(angle_rad), np.cos(angle_rad), 0],
                [0, 0, 1]
            ])
        else:
            raise ValueError('Axis must be either x, y, or z')
        #}}}
        # Rotate the vector
        v2 = np.dot(rotation_matrix, v1)
        if update_prms:
            if axis == 'x':
                self._update_geometry_properties(
                    detector_y = self.detector_y+v2[1],
                    distance = v2[2]
                )
            elif axis == 'y':
                raise ValueError ('If you want to rotate about y, use z because the y and z axes are swapped')
            elif axis == 'z':
                self._update_geometry_properties(
                    detector_x = self.detector_x + v2[0],
                    distance = v2[2]
                )
        else:
            return v2


    #}}}
    # calc_detector_size: {{{
    def calc_detector_size(self, x_grid, y_grid, z_grid, print_corners:bool = False):
        '''
        When we plot a rotated detector, we do so by making a grid of points that lie on the detector
        plane. 

        To calculate the width and height, we need its corners (x,y,z)

        After this, we calculate the magnitude of the vector between those points. 
        This ensures that 
        '''
        LBX = x_grid[0][0]
        RBX = x_grid[0][-1]
        LTX = x_grid[-1][0]
        RTX = x_grid[-1][-1]
     
        LBY = y_grid[0][0]
        RBY = y_grid[0][-1]
        LTY = y_grid[-1][0]
        RTY = y_grid[-1][-1]
     
        LBZ = z_grid[0][0]
        RBZ = z_grid[0][-1]
        LTZ = z_grid[-1][0]
        RTZ = z_grid[-1][-1]
     
        LB = np.array([LBX, LBY, LBZ])
        LT = np.array([LTX, LTY, LTZ])
        RB = np.array([RBX, RBY, RBZ])
        RT = np.array([RTX, RTY, RTZ])
        if print_corners:
            print(f'Detector Corners:\n\tLB: ({LB})\n\tLT: ({LT})\n\tRB: ({RB})\n\tRT: ({RT})')
        det_width = np.linalg.norm([RB-LB])
        det_height = np.linalg.norm([LT-LB])
        print(f'Detector Width (calculated): {det_width} mm\nDetector Height (calculated): {det_height} mm')
    #}}}
    # calculate_pixel_edges: {{{
    def calculate_pixel_edges(
            self, 
            pixel_x:int = None, 
            pixel_y:int = None,  
        ):
        ''' 
        pixel x: Pixel Column number
        pixel y: pixel row number
        -------------
        Returns: 
            A dictionary with a 3 tuple for each of the keys: 

            The first key is: detector – This stands for the pixels location relative to the detector frame of reference for plotting
            The second key is: sample – This stands for the pixels location relative to the sample frame of reference for calculations.
        '''
        # Check if pixel is in detector: {{{
        if pixel_x < 0 or pixel_x >= self.detector_x_pixels or pixel_y < 0 or pixel_y >= self.detector_y_pixels:
            raise ValueError(f'Pixel coordinates ({pixel_x}, {pixel_y}) are outside of the bounds of the detector ({self.detector_x_pixels}, {self.detector_y_pixels})')
        #}}}
        # Calculate the coordinates of the pixel corners {{{
        half_width = self.detector_width / 2
        half_height = self.detector_height / 2
    
        x0 = pixel_x * self.pixel_size - half_width + self.detector_x  # Bottom left offset by detector_x
        x1 = (pixel_x + 1) * self.pixel_size - half_width + self.detector_x  # Bottom Right offset by detector_x
        y0 = pixel_y * self.pixel_size - half_height + self.detector_y  # Top Left # offset by detector_y
        y1 = (pixel_y + 1) * self.pixel_size - half_height + self.detector_y  # Top Right offset by detector_y
    
        corners = [(x0, y0), (x1, y0), (x0, y1), (x1, y1)]
        #}}}
        # Apply tilt to the detector surface about the center point {{{
        theta_tilt = np.radians(self.tilt_angle)
     
        rs_det = []
        thetas_det = []
        phis_det = []

        rs_sample = []
        thetas_sample = []
        phis_sample = []
     
        for i, (x, y) in enumerate(corners):
            # Calculate coordinates in detector frame of reference: {{{
            r_det, theta_det, phi_det = self.calculate_spherical_coordinates_from_origin(
                    origin_x= 0,
                    origin_y = 0,
                    point_x= x,
                    point_y = y,
                    point_z= self.distance,
            )
            #}}}
            # Calculate coordinates in sample frame of reference: {{{
            r_sample, theta_sample, phi_sample = self.calculate_spherical_coordinates_from_origin(
                    origin_x= self.sample_x,
                    origin_y = self.sample_y,
                    point_x= x,
                    point_y = y,
                    point_z= self.distance,
            )
            #}}}

            rs_det.append(r_det)
            thetas_det.append(theta_det)
            phis_det.append(phi_det)

            rs_sample.append(r_sample)
            thetas_sample.append(theta_sample)
            phis_sample.append(phi_sample) 
        #}}}
        # make the output dictionary: {{{
        output = {
                'detector': (np.array(rs_det), np.array(thetas_det), np.array(phis_det)),
                'sample': (np.array(rs_sample), np.array(thetas_sample), np.array(phis_sample))
        }
        #}}} 
        return output
    #}}}
    # calculate_spherical_coordinates_from_origin: {{{
    def calculate_spherical_coordinates_from_origin(self,origin_x, origin_y, point_x, point_y, point_z):
        '''
        origin_x: x coordinate of the origin
        origin_y: y coordinate of the origin
        point_x: x coordinate of the point
        point_y: y coordinate of the point
        point_z: z coordinate of the point
        '''
        theta_tilt = np.radians(self.tilt_angle)
        # Calculate the differences in coordinates
        dx = point_x - origin_x
        dy = point_y - origin_y
        dz = point_z 
     
        # Apply a rotation matrix to tilt about the x axis
        dz_tilt = dz * np.cos(theta_tilt) - dy * np.sin(theta_tilt)
        dy_tilt = dz * np.sin(theta_tilt) + dy * np.cos(theta_tilt)
    
        # Calculate spherical coordinates
        r = np.sqrt(dx**2 + dy_tilt**2 + dz_tilt**2)
        theta = np.arccos(dz_tilt / r)
        phi = np.arctan2(dy_tilt, dx)
    
        # Convert theta and phi to degrees
        theta_degrees = np.degrees(theta)
        phi_degrees = np.degrees(phi)
    
        return r, theta_degrees, phi_degrees
     
    #}}} 
    # _calc_pixel_scan_dict: {{{
    def _calc_pixel_scan_dict(
            self, 
            pixel_x,
            pixel_y,  
        ):
        '''
        This function helps out the function: "calculate_pixel_scan"

        Basically, it just creates a dictionary entry which is properly formatted
        '''
        pixel_dict = self.calculate_pixel_edges(pixel_x=pixel_x, pixel_y=pixel_y)
        rd, tthd, phid = pixel_dict['detector'] # These are in detector frame of reference
        r, tth, phi = pixel_dict['sample'] # These are in sample frame of reference
        xd = rd * np.sin(np.radians(tthd)) * np.cos(np.radians(phid))
        yd = rd * np.sin(np.radians(tthd)) * np.sin(np.radians(phid))
        zd = rd * np.cos(np.radians(tthd))
    
        x = r * np.sin(np.radians(tth)) * np.cos(np.radians(phi))
        y = r * np.sin(np.radians(tth)) * np.sin(np.radians(phi))
        z = r * np.cos(np.radians(tth))
        return {
            'x': x,
            'y': y,
            'z': z,
            'r': r,
            'tth': tth,
            'phi': phi,
    
            'x_d': xd,
            'y_d': yd,
            'z_d': zd,
            'r_d': rd,
            'tth_d': tthd,
            'phi_d': phid
        }
        
    #}}}
    # calculate_pixel_scan: {{{
    def calculate_pixel_scan( 
        self,
        scan_type:str = 'x',
        scan_rng:range = None,
        pixel_x:int = None,
        pixel_y:int = None, 
        ):
        ''' 
        scan_type: either "x" or "y", if x, choose a pixel y, if y choose a pixel x
        scan_rng: How many pixels you want to scan across, starting index to ending index
        pixel_x: column index (staring from the left of the detector)
        pixel_y: row index (starting from the bottom of the detector) 
        ---------
        Outputs: a dictionary with keys in the form: pixel_(x,y)
            entries are x, y, z, r, tth, phi, x_d, y_d, z_d, tth_d, phi_d, d, delta_d, delta_d_over_d

        The _d entries are with respect to the detector.
        These should only be used for plotting! The non-subscript ones are with respect to the sample position and accurately reflect the positioning relative to it. 
        '''
        # Get important prms: {{{
        scan_type = scan_type.lower() 
        #}}}
        self.pixel_scan = {}
        # pixel y scan: {{{
        if scan_type == 'y':
            # Get scan range: {{{
            if type(scan_rng) == type(None):
                scan_rng = range(0, int(self.detector_y_pixels)) # Scan the whole y axis
            #}}}
            # Loop through pixel coords: {{{
            for pixel_y in scan_rng:
                self.pixel_scan[f'pixel_({pixel_x},{pixel_y})'] = self._calc_pixel_scan_dict(pixel_x, pixel_y)
            #}}}
        #}}}
        # pixel x scan: {{{
        elif scan_type == 'x':
            # Get scan range: {{{
            if type(scan_rng) == type(None):
                scan_rng = range(0, int(self.detector_x_pixels)) # Scan the whole x axis
            #}}}
            # Loop through pixel coords: {{{
            for pixel_x in scan_rng:
                self.pixel_scan[f'pixel_({pixel_x},{pixel_y})'] = self._calc_pixel_scan_dict(pixel_x, pixel_y) 
            #}}}
        #}}} 
        #Calculate the resolution: {{{
        self.calculate_delta_d_over_d() # This automatically updates the dictionary with the delta d over d
        #}}}
        return self.pixel_scan
    #}}}    
    # define_detector: {{{ 
    def define_detector(self, **kwargs):
        ''' 
        that will define a detector in 3D space 
        This detector will be defined rotated about the x-axis of a sample

        The self.detector_x and self.detector_y parameters will be used to move the detector relative to the sample

        self._x_grid, self._y_grid, self._z_grid: These are the x, y, z meshgrid values for your detector before any tilt is applied
        self.x_grid, self.y_grid, self.z_grid: These are the x, y, z meshgrid values for the actual detector (with tilt applied)
        
        self.s2d_distances: The sample to detector distances for each point on the detector.
        self.s2d_distances_rotated: The sample to detector distances for each point on the detector rotated so that the hover templates on the figure work out.
        --------
        kwargs: 
            grid_step: Allows you to make a larger or smaller grid. Use a large number to increase speed by reducing the points in the grid
        '''
        # kwargs: {{{
        grid_step = kwargs.get('grid_step', 10)
        #}}}
        # Make the detector without a tilt first: {{{ 
        num_points = int((self.detector_width + grid_step * self.pixel_size) / (grid_step * self.pixel_size)) + 1

        

        x_vals = np.linspace(-self.detector_width/2+self.detector_x, self.detector_width/2+self.detector_x, num = int(self.detector_width/grid_step))
        y_vals = np.linspace(-self.detector_height/2+self.detector_y, self.detector_height/2+self.detector_y, num = int(self.detector_height/grid_step))

        self._x_grid, self._y_grid = np.meshgrid(x_vals, y_vals) # Construct the grid
        self._z_grid = np.full_like(self._x_grid, self.distance) # Untransformed detector grid
        #}}}
        # Apply 3D transformation matrix to tilt the detector: {{{
        theta_tilt = np.radians(self.tilt_angle)
     
        z_grid = self.distance * np.cos(theta_tilt) - self._y_grid * np.sin(theta_tilt)
        y_grid_tilted = self.distance * np.sin(theta_tilt) + self._y_grid * np.cos(theta_tilt)
     
        self.y_grid , self.z_grid = z_grid, y_grid_tilted
        self.x_grid = self._x_grid 
        #}}}
        # Calculate the sample to detector distances: {{{
        self.s2d_distances = np.sqrt((self.x_grid-self.sample_x)**2 + (self.y_grid)**2 + (self.z_grid-self.sample_y)**2) # S2D Distances
        self.s2d_distances_rotated = np.rot90(self.s2d_distances)
        #}}}
    #}}}
#}}}
