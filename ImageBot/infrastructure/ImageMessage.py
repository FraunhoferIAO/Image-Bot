"""ImageMessage container type definition.

ImageMessage container stores and provides access to an image
and its corresponding mask and picked "green" RGB tupel.

The message object, containing the image to be passed around in the pipeline.

Authors:
    - Lukas Block
    - Adrian Raiser

Todo:
    - Add license boilerplate
"""

import os
import cv2
import numpy as np

class ImageMessage(object):
    """Container to hold the images and metadata.

    Each ImageMessage holds a Numpy reference to the image to be transported.
    Optionally, it can store a mask, a green value tupel and other metadata inside a dict.
    """


    def __init__(self, messageId, image=None, mask=None, green=None, metadata=None):
        """Construct image message container.

        Args:
            messageId (uuid|int): Message identifier
            image (np.ndarray, optional): Image to carry. Defaults to None.
            mask ([type], optional): Mask to be applied on image. Defaults to None.
            green ([type], optional): RGB-values picked by user. Defaults to None.
            metadata ([type], optional): Metadata to identify/classify carried image or supply additional information. Defaults to None.

        TODO: move mask and green to metadata
        """
        self.image = image
        self.mask = mask
        self.green = green
        self.id = messageId
        self.metadata = metadata or {}
        # if not provided, add a default name to metadata dict
        self.metadata['name'] = 'Image' if not 'name' in self.metadata.keys() else self.metadata['name']
