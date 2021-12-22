"""Pipeline definition for post processing.

Todo:
    - Add license boilerplate.
    - Cleanup
"""

from os.path import isfile, join
from os import PathLike, listdir
from functools import partial
from typing import List
from pathlib import Path
from queue import Queue

from numpy import source

from ImageBot.infrastructure.Pipeline import Pipeline
from ImageBot.infrastructure.Pipeline import Pipeline
from ImageBot.infrastructure.ImageMessage import ImageMessage
from ImageBot.infrastructure.filter import *
from ImageBot.image_processing.masks import *
from ImageBot.image_processing.general import *
from ImageBot.image_processing.greenscreen import *
from ImageBot.image_processing.model import *

from ImageBot.image_processing.Filter import remove_greenscreen, save_with_mask, _init_GreenscreenPipeline

# TODO: Fix threadpool issue 
Loader : 'Queue[Path]' = Queue()
PostProcessor: Pipeline = None

def load_images(source_folder : Path, mask_suffix='_mask', extension='png'):
    """Load image paths into Loader queue.

    Args:
        source_folder (Path): Path to folder containing input images.
        mask_suffix (str, optional): Suffix of image files to mark mask images. Defaults to '_mask'.
        extension (str, optional): File extension to load. Defaults to 'png'.
    """
    for file in source_folder.iterdir():
        if not (mask_suffix in file.stem):
            Loader.put(file)

def init(dest_folder: Path = None) -> None:
    """Initialize the post processing pipeline.

    Args:
        dest_folder (Path, optional): Path to folder to save the resulting images in. Defaults to None.

    Todo:
        Rewrite Loader to be on demand or more flexible?
    """
    global PostProcessor
    PostProcessor = Pipeline()

    _init_GreenscreenPipeline()

    # Load image from loader
    #PostProcessor.add(partial(load_image, source=Loader))
    #PostProcessor.add(show)

    # First, find the mask by removing the greenscreen
    PostProcessor.add(remove_greenscreen)

    # Then, apply the first augmentation steps
    # Crop the image
    PostProcessor.add(w_crop_to_mask)
    #PostProcessor.add(show)

    # Apply random augmentation of model parts (generates multiple 
    PostProcessor.add(w_augment_mask, True)
    #PostProcessor.add(show)

    # Expand the canvas to fit all possible rotations
    PostProcessor.add(w_expand_for_max_affine)
    #PostProcessor.add(show)

    # Apply the augmentation / transformation
    PostProcessor.add(w_model_augement, True)

    # Crop it back again
    PostProcessor.add(w_crop_to_mask)

    # If provided, save image in given folder
    if dest_folder is not None:
        dest_folder.mkdir(parents=True, exist_ok=True)
        PostProcessor.add(partial(save_message, dest_folder=dest_folder, save_mask=True))

    #return PostProcessor

