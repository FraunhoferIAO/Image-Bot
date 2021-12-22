"""Pipeline definition for greenscreen processing/removal.

Todo:
    - Add license boilerplate.
    - Cleanup
    - File necessary?
"""

from os.path import isfile, join
from os import listdir
from types import MethodWrapperType
from typing import List
from multiprocessing import Lock

import cv2
from cv2 import imread
import numpy as np

from ImageBot.Config import *

from ImageBot.infrastructure.ImageMessage import ImageMessage
from ImageBot.infrastructure.Pipeline import Pipeline

from ImageBot.image_processing.greenscreen import *
from ImageBot.image_processing.masks import clean_mask_surrounding

# Main Filter for PostProcessor

GreenscreenPipeline : Pipeline = None

def _init_GreenscreenPipeline():
    global GreenscreenPipeline
    GreenscreenPipeline = Pipeline(with_multiprocessing=True)

    # Generate the greenscreen mask
    GreenscreenPipeline.add(w_color_based_filer)
    # Remove everything outside the center mask
    GreenscreenPipeline.add(w_clean_mask_surrouding)
    # Tigthen the mask a little bit
    GreenscreenPipeline.add(w_tigthen_mask)

def remove_greenscreen(message : ImageMessage) -> List[ImageMessage]:
    """Removes the greenscreen from the image inside the given message.

    Args:
        message (ImageMessage): Message containing the image to remove the greenscreen from

    Returns:
        List[ImageMessage]: ImageMessage containing removed greenscreen and mask

    TODO: Move mask to metadata
    """
    current_image = message.image

    def pick_green(event, x, y, flags, param):
        if event == cv2.EVENT_LBUTTONUP:
            message.green = pick_color(current_image, (x, y), 5)
            #print("Green value set to " + str(message.green))

            # Now show the mask
            diff_image = color_based_filter(current_image, message.green, GREEN_MIN_THRESHOLD, GREEN_MAX_THRESHOLD)
            diff_image = clean_mask_surrounding(diff_image, MASK_CONTOUR_SMOOTHING, MASK_CONTOUR_MIN_SIZE)
            cv2.imshow('mask', np.uint8(diff_image*255))
            # Show the mask for 3 seconds
            cv2.waitKey(1000)
            cv2.destroyWindow('mask')

    # If the green value has not been set yet, set it
    #print("Please select the green value by clicking on the image.")
    #print("If you selected an appropriate green value or want to select a green value later on, click any key to continue.")

    cv2.imshow('image', message.image)
    cv2.namedWindow('image')
    cv2.setMouseCallback('image', pick_green)
    pressed_key = cv2.waitKey(0)
    cv2.destroyAllWindows()

    # If the x key is pressed we skip this image, this might be used if the mask is not good enough
    if pressed_key != ord('x'):
        result = GreenscreenPipeline(message)
    else:
        result = []

    return result

def save_with_mask(message, dest_folder, mask_suffix='mask', extension='png'):
    """Save given image into specified folder.

    Args:
        message (ImageMessage): ImageMessage containing the image to save
        dest_folder (path|str): Path to the desired location
        extension (str, optional): File extension to use for file. Defaults to 'jpg'.

    Returns:
        ImageMessage: Returns the given message
    """
    filename = ""
    filename_mask = ""

    try:
        filename = message.metadata["filename"]
        filename_mask = message.metadata['filename_mask']
        if not filename.endwith(extension):
            filename = str(message.id) + '.' + extension
            filename_mask = str(message.id) + '_' + mask_suffix + '.' + extension
    except KeyError as k:
        filename = str(message.id) + "." + extension
        filename_mask = str(message.id) + '_' + mask_suffix + '.' + extension

    print(filename)
    cv2.imwrite(os.path.join(dest_folder, filename), np.uint8(message.image*255))
    cv2.imwrite(os.path.join(dest_folder, filename_mask), np.uint8(message.mask*255))

    return message

