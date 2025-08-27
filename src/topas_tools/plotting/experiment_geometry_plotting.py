# Authorship:  {{{
'''
Written by: Dario C. Lewczyk
Date: 12-18-24
'''
#}}}
# Imports: {{{
from topas_tools.plotting.plotting_utils import GenericPlotter
from topas_tools.area_detector_tools.geometry import DiffracGeometryInterface
import plotly.graph_objects as go
import numpy as np
#}}}
# GeometryPlotterInterface: {{{
class GeometryPlotterInterface:
    def plot_detector_in_lab(self,pixel_x, pixel_y, scan_type, scan_rng,show_sample_frame_pixels, **kwargs):
        super().plot_detector_in_lab(pixel_x,pixel_y, scan_type, scan_rng,show_sample_frame_pixels, **kwargs)
#}}}
# GeometryPlotter: {{{
class GeometryPlotter(GenericPlotter,GeometryPlotterInterface):
    #__init__: {{{
    def __init__(self, diffrac_geometry:DiffracGeometryInterface):
        GenericPlotter.__init__(self)
        self.diffrac_geometry = diffrac_geometry # Give us all the attributes of the DiffracGeometry to work with.
    #}}} 
    # plot_detector_in_lab: {{{
    def plot_detector_in_lab( 
        self,
        pixel_x=0, 
        pixel_y=0,
        scan_type:str = None,
        scan_rng:range = None,
        show_sample_frame_pixels:bool = True,
        **kwargs
        ):
        ''' 
        distance: S2D distance in mm
        tilt_angle: tilt angle for the detector in degrees. 
        sample_x: x position of the sample (in mm, offset from center of detector)
        sample_y: y position of the sample (in mm, offset from the center of detector)
        scan_type: either "x" or "y", if x, choose a pixel y, if y choose a pixel x
        scan_rng: How many pixels you want to scan cross, starting index to ending index
        pixel_x: column index (starting from the left of the detector)
        pixel_y: row index (starting from the bottom of the detector)
        ---------------
        kwargs: 
            grid_step: # allows you to adjust the value of the grid to reduce the number of points plotted. 
            height: height of figure
            width: width of figure

            pixel_size: pixel size (in mm)
            detector_x_pixels: pixels in x direction
            detector_y_pixels: pixels in y direction
            distance: S2D distance
            tilt_angle: tilt angle of detector (in deg.)
            sample_x: sample x position (relative to the detector center point (mm))
            sample_y: sample y position (relative to the detector center point (mm))

            debug: True or False
        '''
        # Get Kwargs: {{{
        grid_step = kwargs.get('grid_step',10)  # Adjust this value to control the grid precision
        height = kwargs.get('height', 800)
        width = kwargs.get('width', 800)
        
        # If changing the geometry: {{{
        self.diffrac_geometry._update_geometry_properties(**kwargs)
        #}}}
        debug = kwargs.get('debug', False)
        #}}} 
        theta_tilt = np.radians(self.diffrac_geometry.tilt_angle)
        # Calculate the Detector and the S2D distances:  {{{
        self.diffrac_geometry.define_detector(**kwargs) # This gives us x_grid, y_grid, z_grid, and the distances
        #}}}
        fig = go.Figure() 
        # Plot the detector surface with color scale based on distances: {{{
        fig.add_surface(
            x= self.diffrac_geometry.x_grid,
            y = self.diffrac_geometry.y_grid,
            z = self.diffrac_geometry.z_grid,
            hovertemplate='x: %{x} mm<br>y: %{z} mm<br>z: %{y} mm<br>Sample to Detector Distance: %{customdata:.2f} mm', 
            customdata= self.diffrac_geometry.s2d_distances_rotated,
            surfacecolor = self.diffrac_geometry.s2d_distances,
            colorscale='Viridis',
            opacity=0.8,
            showscale=True,
            colorbar=dict(title='Distance', len = 0.5)
        )
        #}}}
        # Calculate the point on the detector hit by projecting the sample point onto the detector: {{{
        hit_x = self.diffrac_geometry.sample_x
        hit_y = self.diffrac_geometry.distance * np.sin(theta_tilt) + self.diffrac_geometry.sample_y * np.cos(theta_tilt)
        hit_z = self.diffrac_geometry.distance * np.cos(theta_tilt) - self.diffrac_geometry.sample_y * np.sin(theta_tilt)
        #}}}
        # Plot the line connecting the sample to the hit point on the detector: {{{
        s2d_distance = np.sqrt((hit_x-self.diffrac_geometry.sample_x)**2 + (hit_y-self.diffrac_geometry.sample_y)**2 + (hit_z-0)**2)
        fig.add_scatter3d(
            x=[self.diffrac_geometry.sample_x, hit_x],
            y=[0, hit_z],
            z=[self.diffrac_geometry.sample_y, hit_y],
            mode='lines',
            line=dict(color='blue', width=2),
            hovertemplate=f'Distance: {s2d_distance:.2f} mm',
        )
        #}}}
        # Calculate the point on the detector where it would hit if not tilted.: {{{
        normal_hit_x = self.diffrac_geometry.sample_x
        normal_hit_y = self.diffrac_geometry.sample_y
        normal_hit_z = self.diffrac_geometry.distance 
        #}}}
        # Plot a line to the point the sample would hit on the detector if not tilted. : {{{
        fig.add_scatter3d(
            x = [self.diffrac_geometry.sample_x, normal_hit_x],
            y = [0, normal_hit_z],
            z = [self.diffrac_geometry.sample_y, normal_hit_y],
            mode = 'lines',
            line = dict(color = 'black', width = 2, dash = 'dash'),
            name = 'Normal hit point',
        )
        #}}}
        # Now add the angle between the normal hit point and the actual hit point to the sample hovertemplate: {{{
        vec1 = [hit_x - self.diffrac_geometry.sample_x, hit_z - 0, hit_y - self.diffrac_geometry.sample_y]
        vec2 = [normal_hit_x - self.diffrac_geometry.sample_x, normal_hit_z - 0, normal_hit_y - self.diffrac_geometry.sample_y]
        cos_theta = np.dot(vec1, vec2)/(np.linalg.norm(vec1)*np.linalg.norm(vec2))
        angle_deg = np.degrees(np.arccos(cos_theta)) # Get the angle between the two vectors. 
        # Plot the sample position
        fig.add_scatter3d(
            x=[self.diffrac_geometry.sample_x],
            y=[0],  # Sample z is always 0
            z=[self.diffrac_geometry.sample_y],
            hovertemplate = 'x: %{x}<br>y: %{z}<br>z: %{y}<br>'+f'Tilt angle (calculated): {angle_deg:.2f} degrees',
            mode='markers',
            marker=dict(size=5, color='blue'),
            name='Sample'
        )
        #}}} 
        # Plot the pixel corners as red markers: {{{
        # If only plotting one pixel: {{{
        if scan_type == None:
            pixel_dict = self.diffrac_geometry.calculate_pixel_edges(
                pixel_x, pixel_y
            )
            rs,thetas,phis = pixel_dict['sample'] # Sample frame values
            rd,thetad,phid = pixel_dict['detector'] # Detector frame values

            mean_tth = np.around(np.average(thetas),2) # Get the average 2theta from the sample frame (correct)
            mean_d = np.around(self.diffrac_geometry.convert_tth_to_d(mean_tth),2) # Gives the average d spacing for the pixel
            # Plot the x,y,z in the detector frame of reference{{{
            x_coords = rd * np.sin(np.radians(thetad)) * np.cos(np.radians(phid))
            y_coords = rd * np.cos(np.radians(thetad))
            z_coords = rd * np.sin(np.radians(thetad)) * np.sin(np.radians(phid))
            
            fig.add_scatter3d(
                x=x_coords,
                y=y_coords,
                z=z_coords,
                mode='markers',
                marker=dict(size=2, color='red'),
                hovertemplate = 'x: %{x}<br>y: %{y}<br>z: %{z}<br>'+f'2{self._theta}: {mean_tth}{self._degree_symbol}<br>d-spacing: {mean_d} Å',
                name = 'Pixel Corners (Detector Frame)',
            )
            #}}}
            # Plot the x,y,z in the sample frame of reference{{{
            if show_sample_frame_pixels:
                x_coords = rs * np.sin(np.radians(thetas)) * np.cos(np.radians(phis))
                y_coords = rs * np.cos(np.radians(thetas))
                z_coords = rs * np.sin(np.radians(thetas)) * np.sin(np.radians(phis))
            
                fig.add_scatter3d(
                    x=x_coords,
                    y=y_coords,
                    z=z_coords,
                    mode='markers',
                    marker=dict(size=2, color='blue'),
                    hovertemplate = 'x: %{x}<br>y: %{y}<br>z: %{z}<br>'+f'2{self._theta}: {mean_tth}{self._degree_symbol}<br>d-spacing: {mean_d} Å',
                    name = 'Pixel Corners (Sample Frame)',
                ) 
        #}}}
        #}}}
        # If plotting a scan across pixels: {{{
        else:
            scan_dict = self.diffrac_geometry.calculate_pixel_scan(
                scan_type = scan_type,
                scan_rng = scan_rng,
                pixel_x = pixel_x,
                pixel_y = pixel_y,
            )
            # Loop through the scan dictionary: {{{ 
            for pixel_label, entry in scan_dict.items():
                mean_tth = np.around(np.average(entry['tth']),2) # 2theta for sample to pixel
                mean_d = np.around(self.diffrac_geometry.convert_tth_to_d(mean_tth), 2) # Mean d spacing for the pixel
                # Plot the pixels in detector FOR: {{{
                xd = entry['x_d']
                yd = entry['y_d']
                zd = entry['z_d']
                
                fig.add_scatter3d(
                    x=xd,
                    y=zd,
                    z=yd,
                    mode='markers',
                    marker=dict(size=2, color='red'),
                    showlegend=False,
                    hovertemplate = f'{pixel_label}<br>'+'x: %{x}<br>y: %{z}<br>z: %{y}<br>'+f'2{self._theta}: {mean_tth} {self._degree_symbol}<br>d-spacing: {mean_d} Å',
                )
                #}}}
                # Plot the pixels in Sample Frame of Reference: {{{
                if show_sample_frame_pixels:
                    xs = entry['x'] # sample frame of ref
                    ys = entry['y'] # sample frame of ref
                    zs = entry['z'] # sample frame of ref
             
                    fig.add_trace(go.Scatter3d(
                        x = xs,
                        y = zs,
                        z = ys,
                        mode='markers',
                        marker=dict(size=2, color='blue'),
                        showlegend=False,
                        hovertemplate = f'{pixel_label} (Sample Frame)<br>'+'x: %{x}<br>y: %{z}<br>z: %{y}<br>'+f'2{self._theta}: {mean_tth} {self._degree_symbol}<br>d-spacing: {mean_d} Å',
                        
                    ))
                #}}}
            #}}} 
        #}}}
        #}}} 
        # Update the layout: {{{
        fig.update_layout(
            scene=dict(
                xaxis_title='X',
                yaxis_title='Z',
                zaxis_title='Y',
                aspectmode = 'manual',
                aspectratio = dict(x=1, y=2, z=1),
            ), 
            template="simple_white", 
            width=width, 
            height=height,

        )
        #}}}  
        fig.show() 
    #}}}
    # plot_{{{<++>#}}}
#}}}
