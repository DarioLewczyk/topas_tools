### Importing modules
import numpy as np
from math import pi
from imageio.v2 import imread
import fabio as fb

import pyFAI.azimuthalIntegrator
import pyFAI.distortion
import pyFAI.detectors
import pyFAI.ext
import pyFAI.io
import pyFAI.test.utilstest
import pyFAI.gui

def image_geometry_data(tiff, poni, mask=None, unit='2th_deg'):
    '''
    Function to extract geometry information of individual pixels via pyFAI.
    Values correspond to each other in the outputted order.

    Required Args:
        - tiff (image file): .tif/.tiff image of XRD pattern
        - poni (text file): .poni/.dat/.txt/equivalent file containing PONI geometry information
    
    Optional Arg:
        - mask (mask file): image file/2D array of masked pixels
            Default = None
        - unit (str): unit of 2θ (options include: ["q_nm^-1", "2th_deg", "r_mm"])
            Default = '2th_deg'
    
    Returns:
        - pixel_index_x (1d array): x-pixel positions
        - pixel_index_y (1d array): y-pixel positions
        - intensities_1d (1d array): 1d array of image intensities at each pixel
        - intensities_2d (2d array): 2d array of image intensities
        - tth (1d array): twotheta position at each pixel
        - chi (1d array): azimuthal angle position at each pixel
    '''

    ### Set-Up

    # Loading PONI geometry file to create azimuthal integrator object
    ai = pyFAI.load(poni)

    # Obtaining geometry information from azimuthal integrator
    pixel1 = ai.pixel1
    pixel2 = ai.pixel2

    image_dimensions = ai.get_shape()
    pixel_x = ai.get_shape()[0]
    pixel_y = ai.get_shape()[1]

    # Creating detector object via pyFAI
    detector = pyFAI.detectors.Detector(pixel1=pixel1,
                                        pixel2=pixel2,
                                        max_shape=image_dimensions)

    # Applying mask if inputted
    if mask is not None:
        ai.set_maskfile(mask)
    
    # Adding detector to azimuthal integrator
    ai.detector = detector

    ### Obtaining x_pixel, y_pixel, intensities
    
    # Pixel array instantiation
    pixel_count = pixel_x * pixel_y
    pixel_indices_full = np.arange(pixel_count, dtype=int)

    pixel_index_x = np.arange(pixel_x, dtype=int)
    pixel_index_y = np.arange(pixel_y, dtype=int)

    pixel_index_x = np.tile(pixel_index_x, pixel_x)
    pixel_index_y = np.repeat(pixel_index_y, pixel_y)
    
    # Reading tiff file
    im = imread(tiff)
    
    # Iterating through pixels in image and saving intensities
    intensities_1d = np.empty(pixel_count)
    
    for index in pixel_indices_full:
        intensities_1d[index] = im[pixel_index_y[index], pixel_index_x[index]]
    
    # Turning intensities into 2D array
    intensities_2d = intensities_1d.reshape(-1, pixel_x)
    
    # Masking values if inputted
    if mask is not None:
        mask_array = fb.open(mask).data
        mask_array = 1 - mask_array
        intensities_2d = np.where(mask_array == 0, 0, intensities_2d)
    
        # Converting back to 1d array
        intensities_1d = intensities_2d.reshape(-1, 1, order='c')
        intensities_1d = intensities_1d.flatten()
    
    ### Obtaining tth and chi of each pixel
    
    # tth Calculation
    tth = ai.array_from_unit(unit=unit,scale=True,typ='center') # tth at center of pixels
    tth = tth.reshape(-1, 1, order='c')
    tth = tth.flatten()
    
    # chi Calculation
    chi = ai.chiArray() # chi array
    chi = chi * (180/pi) # Convert to degrees
    chi = chi.reshape(-1, 1, order='c')
    chi = chi.flatten()
    chi = (chi + 360) % 360 # converting to azimuthal range of 0 to 360 instead of -180 to 180
    
    ### Returning outputs
    
    return pixel_index_x, pixel_index_y, intensities_1d, intensities_2d, tth, chi
