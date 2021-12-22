"""Basic filters for pipelines with ImageMessage processing.

Definition of commonly used filter (eg. loading and saving images).

Authors: Lukas Block, Adrian Raiser

Todo:
    - Add license boilerplate
"""

from .ImageMessage import ImageMessage

import os
from collections.abc import Iterable
from pathlib import Path
from typing import List
import uuid
from queue import Queue

import numpy as np
import cv2


def load_image(message : ImageMessage, source : 'Queue[Path]', load_mask=False, extension='png', mask_suffix='_mask') -> ImageMessage:
    """Load image from file and optionally its mask.

    Args:
        message (ImageMessage): List of incoming messages. Will be ignored (only for compatability)
        source (queue[Path]): Queue containing Path-objects.
        load_mask (bool, optional): If set, a mask with the same name and the given suffix is loaded additionally. Defaults to False
        extension (str, optional): Specific extension to look for. Defaults to 'png'.
        mask_suffix (str, optional): Mask suffix of the image file. Defaults to '_mask'

    Returns:
        ImageMessage: Loaded images in ImageMessage
    """
    image_file : Path = source.get()
    mask_file : Path

    # Load image and, if set, its mask
    message.image = cv2.imread(image_file.as_posix(), cv2.IMREAD_COLOR) / 255.0
    if load_mask:
        mask_file = image_file.parent / (image_file.stem + mask_suffix + '.' + extension)
        message.mask = cv2.imread(mask_file.as_posix(), cv2.IMREAD_GRAYSCALE) / 255.0
    
    # If source_file is a Path, set metadata
    if isinstance(image_file, Path):
        message.metadata['image_path'] = image_file

    return message

def save_message(message : ImageMessage, dest_folder : Path, save_mask=False, mask_suffix='_mask', extension='png') -> ImageMessage:
    """Save given image and, if set, its mask into specified folder.

    Args:
        message (ImageMessage): ImageMessage containing the image to save
        dest_folder (Path): Path to the desired location
        save_mask (bool, optional): If set, the mask is saved additionally. Defaults to False
        mask_suffix (str, optional): Suffix to use when mask is saved. Default to '_mask'
        extension (str, optional): File extension to use for file. Defaults to 'png'.

    Returns:
        ImageMessage: Returns the given message
    """
    image_file : Path
    mask_file : Path

    try:
        image_file = dest_folder / message.metadata['image_path'].name

    except KeyError as k:
        image_file = dest_folder / (str(message.id) + "." + extension)

    mask_file = dest_folder / ('%s%s.%s' % (image_file.stem, mask_suffix, extension))

    cv2.imwrite(image_file.as_posix(), np.uint8(message.image*255))
    if save_mask:
        cv2.imwrite(mask_file.as_posix(), np.uint8(message.mask*255))

    return message

def show(message : ImageMessage) -> ImageMessage:
    """Create a window and display the image given in message.

    Args:
        message (ImageMessage): Message containing the image to display

    Returns:
        ImageMessage: Provided message
    """
    cv2.imshow("Message Image", np.uint8(message.image*255))
    if message.mask is not None:
        cv2.imshow("Message Mask", np.uint8(message.mask*255))
    cv2.waitKey(0)
    cv2.destroyAllWindows()
    return message


def to_float64_image(message : ImageMessage) -> ImageMessage:
    """Convert image to float64.

    Args:
        message (ImageMessage): Image to be converted

    Returns:
        ImageMessage: Resulting image
    """
    message.image = np.float64(message.image)/255.0
    if message.mask is not None:
        message.mask = np.float64(message.mask) / 255.0
    return message

def smooth_mask(message : ImageMessage, radius) -> ImageMessage:
    """Apply gaussian blur on image.

    Args:
        message (ImageMessage): Image to be operated on
        radius ([type]): Param

    Returns:
        ImageMessage: Resulting image
    """
    message.mask = cv2.GaussianBlur(message.image, (radius, radius), 0)
    return message

def to_uint8_image(message : ImageMessage) -> ImageMessage:
    """Convert image type to uint8.

    Args:
        message (ImageMessage): Image to be converted

    Returns:
        ImageMessage: Resulting iamge
    """
    message.image = np.uint8(message.image*255)
    if message.mask is not None:
        message.mask = np.uint8(message.mask*255)
    return message

def to_grayscale_image(message : ImageMessage) -> ImageMessage:
    """Convert image to grayscale.

    Args:
        message (ImageMessage): Image to be converted

    Returns:
        ImageMessage: Resulting image
    """
    assert (len(message.image.shape) == 3) and (message.image.shape[2] == 3)
    message.image = cv2.cvtColor(np.uint8(message.image*255), cv2.COLOR_BGR2GRAY)/255.0
    return message