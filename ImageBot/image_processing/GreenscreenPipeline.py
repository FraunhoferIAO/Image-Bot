from ..infrastructure.Pipeline import Pipeline
from ..infrastructure.ImageMessage import ImageMessage

from ImageBot.image_processing.greenscreen import color_based_filter,\
    remove_green_spill, green_spill_mask
from ..Config import *
from ImageBot.image_processing.masks import clean_mask_surrounding,\
    tigthen_mask
from ImageBot.infrastructure.filter import *

import cv2
import numpy as np



'''
def w_remove_green_spill(message):
    # First get the green spill mask
    gs_mask = green_spill_mask(message.image, GREEN_SPILL_COLOR, GREEN_SPILL_MIN_THRESHOLD, GREEN_SPILL_MAX_THRESHOLD)
    gs_mask = smooth(gs_mask, GREEN_SPILl_SMOOTH_DISTANCE)
    message.image = remove_green_spill(message.image, gs_mask, GREEN_SPILL_REDUCTION)
    return message
'''




class _GreenscreenPipeline(Pipeline):
    def __init__(self, with_multiprocessing, max_no_processes):
        super().__init__(with_multiprocessing=with_multiprocessing, max_no_processes=max_no_processes)

        self._pipeline()

    def _pipeline(self):
        # Generate the greenscreen mask
        self.add(w_color_based_filer)
        # Remove everything outside the center mask
        self.add(w_clean_mask_surrouding)
        # Tigthen the mask a little bit
        self.add(w_tigthen_mask)
        # Smooth the mask
        #self.add(smooth_mask)
        # Apply mask
        #self.add(apply_mask)

GreenscreenPipeline = _GreenscreenPipeline(False, 1)

