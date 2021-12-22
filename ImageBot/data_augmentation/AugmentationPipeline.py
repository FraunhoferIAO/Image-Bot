"""Pipeline for image augmentation.

This module contains the image augmentation pipeline.

Todo:
    - Add license boilerplate.
    - Cleanup
"""

from multiprocessing import Pipe
from ImageBot.Config import *
from collections.abc import Iterable
import uuid
from functools import partial
from queue import Queue
from multiprocessing import Manager
from ImageBot.image_processing.greenscreen import w_enlarge_mask

import numpy as np
import cv2

#from numba import jit

from ImageBot.infrastructure.ImageMessage import ImageMessage
from ImageBot.infrastructure.Pipeline import Pipeline
from ImageBot.infrastructure.filter import *
from ImageBot.data_augmentation.poisson_merge.poisson_image_editing import poisson_edit

from ImageBot.data_augmentation.augmentations import *

from ImageBot.image_processing.general import expand_canvas

Loader : 'Queue[Path]' = Queue()
Backgrounds : List[Path] = []
manager : Manager = None

def load_images(source_folder : Path, bgs_folder : Path, mask_suffix='_mask', extension='png'):
    """Load images paths into loader queue.

    Args:
        source_folder (Path): Path to image source directory.
        bgs_folder (Path): Path to backgrounds folder.
        mask_suffix (str, optional): Suffix for mask image files. Defaults to '_mask'.
        extension (str, optional): File extension and therefore codec to load. Defaults to 'png'.
    """
    for file in source_folder.iterdir():
        if not (mask_suffix) in file.stem:
            Loader.put(file)

    for file in bgs_folder.iterdir():
        Backgrounds.append(file)

# TODO: Fix threadpool issue
AugmentationPipeline : Pipeline = None

def init(dest_folder : Path = None):
    """Initialize image augmentation pipeline.

    Initialize the image augmentation pipeline by creating an pipeline object and adding the necessary filters to it.

    Args:
        dest_folder (Path, optional): Path to folder to store images in. If the folder doesn´t exist, it will be created. 
            If not provided (None), no images will be saved. Defaults to None.
    """
    global AugmentationPipeline, manager, Backgrounds
    AugmentationPipeline = Pipeline(with_multiprocessing=True)
    manager = Manager()
    bgs = manager.list(Backgrounds)
    

    # Load image
    #AugmentationPipeline.add(partial(load_image, source=Loader, load_mask=True))
    #AugmentationPipeline.add(show)

    # Convert to grayscale
    AugmentationPipeline.add(to_grayscale_image)
    #AugmentationPipeline.add(show)

    # Only enlarge the mask if the variable to prevent blurring is set
    if PREVENT_BLURRED_OBJECTS:
        AugmentationPipeline.add(w_enlarge_mask)

    # Apply merging filter (poisson_merge)
    AugmentationPipeline.add(partial(merge_with_bg_at_random_pos, bg_img_pool=bgs))
    #AugmentationPipeline.add(show)

    # Last augmentation step
    AugmentationPipeline.add(augment_training_images, True)

    # Convert to grayscale again
    AugmentationPipeline.add(to_grayscale_image)

    # If given, save image to folder
    if dest_folder is not None:
        dest_folder.mkdir(parents=True, exist_ok=True)
        AugmentationPipeline.add(partial(save_message, dest_folder=dest_folder, save_mask=True))