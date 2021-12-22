"""Supporting file containing the filter definitions.

Todo:
    - Add license boilerplate.
"""

from ImageBot.infrastructure.ImageMessage import ImageMessage
from collections.abc import Iterable
import uuid
from pathlib import Path
import random

from typing import List

import numpy as np
import cv2

from .poisson_merge.poisson_image_editing import poisson_edit

from ..infrastructure.Pipeline import Pipeline
from ..image_processing.general import expand_canvas
from ..image_processing.masks import combine_images, mask_bounding_box
from ..infrastructure.ImageMessage import ImageMessage
from ..Config import *

import imgaug.augmenters as iaa
import imgaug.parameters as iap
from imgaug.augmentables.heatmaps import HeatmapsOnImage

def image_resize(image : np.ndarray, height=None, width=None) -> np.ndarray:
    """Resize image while keeping aspect ratio.

    Args:
        image (np.ndarray): Image to resize
        height (int|None, optional): Desired height or None if it should be calculated. Defaults to None.
        width (int|None, optional): Desired width or None if it should be calculated. Defaults to None.

    Returns:
        np.ndarray: Resized image
    """
    assert (width != None) ^ (height != None) 
    
    # Provided parameter is reference
    source_height = image.shape[0]
    source_width = image.shape[1]
    ratio = source_width / source_height

    target_value = width or height

    target_height = height or target_value/ratio 
    target_width = width or target_value*ratio

    target_size = (int(target_width), int(target_height))

    return cv2.resize(image, target_size)

def merge_with_bg_at_random_pos(message : ImageMessage, bg_img_pool : List[Path]) -> List[ImageMessage]:
    """Insert the given image into random selected backgrounds using poisson_merge.

    Args:
        message (ImageMessage): Image to be merged
        bg_img_pool (List[Path]): Pool of paths to background images to merge into

    Returns:
        List[ImageMessage]: List of all merged images
    """
    #assert isinstance(bg_img_pool, Iterable)
    
    result = []
    
    for _ in range(MODEL_MULTIPLY_MESSAGE_BACKGROUND_ASSIGNMENT):
        
        new_message = ImageMessage(uuid.uuid4())
        
        # Randomly select an image from the image bg pool
        bg_index = np.random.randint(0, len(bg_img_pool))
        # Load the backkground image
        bg = cv2.imread(bg_img_pool[bg_index].as_posix(), cv2.IMREAD_GRAYSCALE) / 255.0
        if(bg.shape[0] > bg.shape[1]):
            bg = image_resize(bg, height=416)
        else:
            bg = image_resize(bg, width=416)

    
        
        # Draw a random scale factor for insertion
        scale = np.random.rand()*(MODEL_MAX_RELATIVE_SIZE-MODEL_MIN_RELATIVE_SIZE) + MODEL_MIN_RELATIVE_SIZE
        
        dsize = None
        factor1 = message.image.shape[0]/bg.shape[0]
        factor2 = message.image.shape[1]/bg.shape[1]
        if factor1 > factor2:
            dsize = (int(message.image.shape[1]/factor1*scale), int(message.image.shape[0]/factor1*scale))
        else:
            dsize = (int(message.image.shape[1]/factor2*scale), int(message.image.shape[0]/factor2*scale))
        
        new_message.image = cv2.resize(message.image, dsize=dsize, interpolation=cv2.INTER_AREA)
        new_message.mask = cv2.resize(message.mask, dsize=dsize, interpolation=cv2.INTER_AREA)

        # Now add the image at a random position
        pos = (np.random.randint(0, max(1, bg.shape[0]-dsize[1])), np.random.randint(0, max(1, bg.shape[1]-dsize[0])))
        canvas_expand = [ (pos[0], bg.shape[0]-dsize[1]-pos[0]), (pos[1], bg.shape[1]-dsize[0]-pos[1]) ]
        # Expand the canvas of the orignal image
        new_message.image = expand_canvas(new_message.image, canvas_expand)
        new_message.mask = expand_canvas(new_message.mask, canvas_expand)

        new_message.image = poisson_edit(np.uint8(new_message.image*255), np.uint8(bg*255), np.uint8(new_message.mask*255), (0, 0)) / 255.0

        # Append it to the results
        result.append(new_message)
    
    return result

def augment_training_images(messages : ImageMessage) -> List[ImageMessage]:
    """Apply augmentations to the given image.

    Args:
        messages (ImageMessage): Image to augment

    Returns:
        List[ImageMessage]: List of augmented images
    """
    grayscale = False

    # Convert the images to the proper size and generate the heatmaps
    heatmaps = [HeatmapsOnImage(np.float32(m.mask), shape=m.image.shape, min_value=0.0, max_value=1.0) for m in messages]
    for m in messages:
        m.image = np.uint8(m.image*255.0)
        if m.image.shape[2] == 1:
            m.metadata['grayscale']  = True
            m.image = cv2.merge((m.image, m.image, m.image))
        
    # Generate some identity images which we still keep
    identity_messages = [m for m in messages]
    
    # Multiply the images for augmentation
    new_messages = []
    new_heatmaps = []
    for _ in range(TRAINING_AUGEMENTATION_MULTIPLY-1):
        # Substract minus one, because we have images with no alternation
        new_messages.extend(messages)
        new_heatmaps.extend(heatmaps)
        
    # Now define the image pipeline
    sometimes = lambda aug: iaa.Sometimes(0.5, aug)
    
    seq = iaa.Sequential(
        [
            # Radomly flip the images in one or the other direction
            iaa.Fliplr(0.5),
            iaa.Flipud(0.25),
            # Crop the images by -5% to 10% of their height/width
            sometimes(iaa.CropAndPad(
                percent=(-0.05, 0.1),
                pad_mode=["constant", "edge"],
                pad_cval=(0, 255)
            )),
            sometimes(iaa.Affine(
                scale={"x": (0.8, 1.2), "y": (0.8, 1.2)}, # scale images to 80-120% of their size, individually per axis
                translate_percent={"x": (-0.2, 0.2), "y": (-0.2, 0.2)}, # translate by -20 to +20 percent (per axis)
                rotate=(-45, 45), # rotate by -45 to +45 degrees
                shear=(-16, 16), # shear by -16 to +16 degrees
                mode=["constant", "edge"] # use any of scikit-image's warping modes (see 2nd image from the top for examples)
            )),
            # execute 0 to 5 of the following (less important) augmenters per image
            # don't execute all of them, as that would often be way too strong
            iaa.SomeOf((0, 5),
                [
                    # Convert image to superpixels which is kind of partial blur
                    sometimes(iaa.Superpixels(p_replace=(0, 0.5), n_segments=(100, 200))),
                    # Blur via one of the following functions
                    iaa.OneOf([
                        iaa.GaussianBlur((0, 3.0)), # blur images with a sigma between 0 and 3.0
                        iaa.AverageBlur(k=(2, 7)), # blur image using local means with kernel sizes between 2 and 7
                        iaa.MedianBlur(k=(3, 11)), # blur image using local medians with kernel sizes between 2 and 7
                    ]),
                    # TODO: Possibly leave it out
                    # Sharpen the image
                    iaa.Sharpen(alpha=(0, 1.0), lightness=(0.75, 1.5)),
                    # Add some black fogs in the foreground, with a little threshold
                    #iaa.BlendAlphaSimplexNoise(iaa.EdgeDetect(1.0), sigmoid_thresh=iap.Normal(10.0, 5.0)),
                    # Add some Gaussian noise
                    #iaa.AdditiveGaussianNoise(loc=0, scale=(0.0, 0.05*255), per_channel=0.5),
                    # Change brightness of images per channel
                    iaa.Add((-5, 5), per_channel=0.5), 
                    # Change hue and saturation
                    #iaa.AddToHueAndSaturation((-20, 20)),
                    # Change the brightness of the image by multiplying it
                    iaa.Multiply((1.0, 1.5), per_channel=0.5),
                    # Improve or worsen the contrast
                    iaa.LinearContrast((0.5, 1.5), per_channel=0.5),
                    # Make the image black and white
                    iaa.Grayscale(alpha=(0.0, 1.0)),
                    # Add some "wiggle" to the image
                    sometimes(iaa.PiecewiseAffine(scale=(0.01, 0.075))),
                    # Simulate dust in production environments
                    iaa.Fog()
                ],
                random_order=True
            )
        ],
        random_order=True
    )
    
    # Run the image pipeline
    images, heatmaps = seq(images=[m.image for m in new_messages], heatmaps=new_heatmaps)
    
    # Now convert the heatmaps back to the right profile
    result = [ImageMessage(uuid.uuid4(), image=image/255.0, mask=np.float64(heatmaps[i].get_arr())) for i, image in enumerate(images)]
    # Add the identity images
    for m in identity_messages:
        m.image = m.image/255.0
        result.append(m)

    return result