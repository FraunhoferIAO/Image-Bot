"""Supporting file containing functions used by filter definitions.

Todo:
    - Add license boilerplate.
"""

import numpy as np
import cv2
from collections.abc import Iterable
from ImageBot.image_processing.masks import mask_bounding_box
    
def crop_to_mask(image, mask):
    """Crop image to mask.

    Takes image and mask and crops both to down, so that the mask fills up the image.

    Args:
        image (np.ndarray): Image to process.
        mask (np.ndarray): Corresponding mask.

    Returns:
        np.ndarray: Cropped image.
    """
    bb = mask_bounding_box(mask)
    image = image[bb[0][1]:bb[1][1], bb[0][0]:bb[1][0]]
    return image

def create_color_matt(size, color):
    """Create image of one color.

    Args:
        size ([type]): Image Size.
        color ([type]): Image color.

    Returns:
        np.ndarray: Image of single color.
    """
    # Norm the color to float
    color = [x/255.0 for x in color]
    
    # Create a blank black image
    image = np.zeros((size[0], size[1], 3), np.float64)
    # Set the color
    image[:] = color
    return image

def expand_canvas(image, directions, color=None):
    """Expand canvas in given directions and fill with given color.

    Expands the image in the given directions.
    If a single value is given, the canvas expands in all four directions. The source image is placed in the center.
    If a tuple of tuples of values is given, it expands the image in the directions given by the tupels. The image is placed at coordinates (x_left, y_up).

    The expanded canvas is filled with the given color (RGB or single) or black (None).

    Args:
        image (np.ndarray): Image to expand.
        directions ([int|Tuple[Tuple[int]]]): Directions to expand. Can either be a single value or tuple of tuples of values like ((x_left, x_right), (y_up, y_down)).
        color (Tuple[int]|float, optional): Color to set created pixels to. Can either be an RGB tuple, single value or None. Defaults to None.

    Returns:
        np.ndarray: Image with expanded canvas.
    """
    # First get the color dimension of the image
    color_dim = -1
    if len(image.shape) > 2:
        color_dim = image.shape[2]
        
    # Now set the color to black if it was not set previously
    if color is None:
        if color_dim <= 0:
            color = 0
        else:
            color = [0 for _ in range(color_dim)]
    
    # Now check the set or generated color dimension
    if color_dim > 0:
        assert isinstance(color, Iterable) and (len(color) == color_dim)
        color = np.array([c/255.0 for c in color])
    else:
        assert not isinstance(color, Iterable)
        color = color/255.0
        
    # If directions is a single number, we expand in all four directions, if it
    # is an array, it is given for each side
    if not isinstance(directions, Iterable):
        directions = ((directions, directions), (directions, directions))
    assert isinstance(directions, Iterable) and (len(directions) == 2)
    for d in directions:
        assert isinstance(directions, Iterable) and (len(directions) == 2)
        for i in d:
            assert isinstance(i, int)
    
    # Create a new image with the new dimensions
    if color_dim > 0:
        new_shape = [image.shape[0] + directions[0][0] + directions[0][1], image.shape[1] + directions[1][0] + directions[1][1], color_dim]
    else:
        new_shape = [image.shape[0] + directions[0][0] + directions[0][1], image.shape[1] + directions[1][0] + directions[1][1]]
    result = np.full(new_shape, color)
    # Insert the old image at the correct position
    result[directions[0][0]: image.shape[0]+directions[0][0],  directions[1][0]:image.shape[1]+directions[1][0]] = image
    
    return result


        
        
        
        
        
        
        
        
        