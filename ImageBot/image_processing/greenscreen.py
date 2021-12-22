"""Supporting file coontaining functions used by filter definitions.

Todo:
    - Add license boilerplate.
    - Confirm and expand docstrings
"""

from ImageBot.infrastructure.Pipeline import Pipeline
from ImageBot.infrastructure.ImageMessage import ImageMessage

from ImageBot.Config import *
from ImageBot.image_processing.masks import clean_mask_surrounding, enlarge_mask,\
    tigthen_mask
from ImageBot.infrastructure.filter import *

import cv2
import numpy as np

from collections.abc import Iterable

def color_based_filter(image, green, min_threshold, max_threshold):
    """Apply color-based filter.

    Args:
        image (np.ndarray): Image to apply filter on.
        green (Tuple[int]): RGB value to filter for.
        min_threshold (float): Lower threshold.
        max_threshold (float): Upper threshold.

    Returns:
        np.ndarray: Filtered image.
    """
    # Check the image param
    assert isinstance(image, np.ndarray)
    assert image.shape[2] == 3

    #print("Image min:", np.min(image))
    #print ("Image max:",np.max(image))
    
    # Check the green param and convert it to an array
    assert isinstance(green, Iterable)
    assert len(green) == 3
    # Norm the green color
    green = np.array(green)
    #print("Green Value:", green)
    
    # Numpy channels are sorted in BGR,substract the green channel
    diff_image = image - green

    #print("Diff_Image min:", np.min(diff_image))
    #print ("Diff_Image max:",np.max(diff_image))
    
    # Get the absolute difference
    diff_image = np.linalg.norm(diff_image, axis=2)
    
    diff_image = (diff_image - min_threshold) / (max_threshold - min_threshold)
    diff_image = np.clip(0.0, diff_image, 1.0)
    
    return diff_image

def green_spill_mask(image, green, min_angle_threshold, max_angle_threshold, min_reduction_threshold=0.0, max_reduction_threshold=1.0):
    """Generate mask to reduce green spill effect.

    Args:
        image (np.ndarray): Image  to create mask for.
        green (Tuple[int]): Picked RGB value of greenscreen.
        min_angle_threshold (float): Lower threshold.
        max_angle_threshold (float): Upper threshold.
        min_reduction_threshold (float, optional): Lower reduction threshold. Defaults to 0.0.
        max_reduction_threshold (float, optional): Upper reducton threshold. Defaults to 1.0.

    Returns:
        np.ndarray: Mask for the given image.
    """
    # check the green color
    assert isinstance(green, Iterable)
    assert len(green) == 3
    
    green = np.array(green)/255.0
    
    # Calculate the cosine angle between each image pixel and the green value
    angle_image = np.dot(image, green)/np.linalg.norm(image, axis=2)/np.linalg.norm(green)
    angle_image = np.abs(angle_image)
    # Black pixels might create a NaN value, because the have zero norm length
    angle_image = np.nan_to_num(angle_image, nan=0.0)
    
    # Apply threshold
    angle_image = (angle_image - min_angle_threshold) / (max_angle_threshold - min_angle_threshold)
    angle_image = np.clip(0.0, angle_image, 1.0)
    
    # Calculate the maximum reduction of green per pixel
    max_reduction = (image/green).min(axis=2)
    
    # Apply threshold
    max_reduction = (max_reduction - min_reduction_threshold) / (max_reduction_threshold - min_reduction_threshold)
    max_reduction = np.clip(0.0, angle_image, 1.0)
    
    # Calculate the 
    reduce = cv2.multiply(max_reduction, angle_image)
    
    # return the mask
    return reduce
    
def remove_green_spill(image, mask, reduction=0.75):
    """Remove green spill on object from image.

    Args:
        image (np.ndarray): Image to remove green spill from.
        mask (np.ndarray): Mask of object to remove green spill from.
        reduction (float, optional): Reduction factor. Defaults to 0.75.

    Returns:
        np.ndarray: Image with removed green spill.
    """
    # We are working with inverse color, thus we only apply half of the color, to
    # return from green to a neutral grey
    mask = mask*0.5*reduction
    
    # Now invert the colors of the image
    bw_image = cv2.cvtColor(np.uint8(image*255), cv2.COLOR_BGR2HSV)
    bw_image[:,:,0] = (bw_image[:,:,0] + 90) % 180
    bw_image = cv2.cvtColor(bw_image, cv2.COLOR_HSV2BGR)
    
    mask = cv2.merge((mask, mask, mask))
    bw_image = ((1.0-mask)*np.uint8(image*255) + mask*bw_image)/255
    
    return bw_image

def pick_color(img, pos, average_radius=1):
    """Extract color from position in image.

    Args:
        img (np.ndarray): Image to pick color from.
        pos (Tuple[int]): Position to pick from.
        average_radius (int, optional): Smoothing radius. Defaults to 1.

    Returns:
        Tuple[int]: Picked color.
    """
    assert average_radius%2 == 1
    assert len(img.shape) == 3
    
    # Calculate the radius
    r = int(average_radius/2.0)
    # Get the position, slice the image and calculate the average
    x, y = pos
    color = np.average(img[y-r:y+r+1, x-r:x+r+1], axis=(0,1))
    return color
    
def w_color_based_filer(message : ImageMessage) -> ImageMessage:
    """Filter definition of color_based_filter.

    Args:
        message (ImageMessage): Image to apply filter on.

    Returns:
        ImageMessage: Filtered image.
    """
    message.mask = color_based_filter(message.image, message.green, GREEN_MIN_THRESHOLD, GREEN_MAX_THRESHOLD)
    return message

def w_clean_mask_surrouding(message : ImageMessage) -> ImageMessage:
    """Filter definition for cleaning mask.

    Args:
        message (ImageMessage): Image to apply filter on.

    Returns:
        ImageMessage: Filtered image.
    """
    message.mask = clean_mask_surrounding(message.mask, MASK_CONTOUR_SMOOTHING, MASK_CONTOUR_MIN_SIZE)
    return message

def w_tigthen_mask(message : ImageMessage) -> ImageMessage:
    """Filter definition for tightening mask to object.

    Args:
        message (ImageMessage): Image to apply filter on.

    Returns:
        ImageMessage: Filtered image
    """
    message.mask = tigthen_mask(message.mask, MASK_TIGTHEN_DISTANCE, MASK_CONTOUR_SMOOTHING)
    return message

def w_enlarge_mask(message : ImageMessage) -> ImageMessage:
    """Filter definition for enlarging a mask.

    Args:
        message (ImageMessage): Image to apply filter on.

    Returns:
        ImageMessage: Filtered image
    """
    message.mask = enlarge_mask(message.mask, MASK_ENLARGE_DISTANCE)
    return message


# Currently unused but maybe interessting for the future

def histo_green(img, colorrange , low_saturation, valuerange):
    """Histogram filter for background removal.

    Args:
        img ([type]): [description]
        colorrange ([type]): [description]
        low_saturation ([type]): [description]
        valuerange ([type]): [description]

    Returns:
        [type]: [description]
    """
    assert len(img.shape) == 3
    assert isinstance(colorrange,float)
    assert isinstance(low_saturation,float)
    assert isinstance(valuerange,float)

    histhue = cv2.calcHist([img], [0], None, [256], [0, 256])
    histsat = cv2.calcHist([img], [1], None, [256], [0, 256])
    histval = cv2.calcHist([img], [2], None, [256], [0, 256])

    cv2.imwrite("imghue.jpg",img[:,:,0])
    cv2.imwrite("imgsat.jpg",img[:,:,1])
    cv2.imwrite("imgval.jpg",img[:,:,2])
    
    limithue = np.argmax(histhue) 
    limitsat = np.argmax(histsat)
    limitval = np.argmax(histval) 

    masklow = img[:,:,0] >= limithue*(1-colorrange)
    maskhigh = img[:,:,0] < limithue*(1+colorrange)
    masksat = img[:,:,1] >= limitsat*(1-low_saturation)
    maskvallow = img[:,:,2] >= limitval*(1-valuerange)
    maskvalhigh = img[:,:,2] < limitval*(1+valuerange)

    bitmap = (~((masklow & maskhigh) & (maskvallow) & (masksat)))
    
    return np.array(bitmap*255, dtype = np.uint8)




    

