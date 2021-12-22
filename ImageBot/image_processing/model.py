'''
Created on 22.02.2021

@author: Lukas Block
'''
from ImageBot.image_processing.general import expand_canvas
from math import sqrt
import numpy as np
import imgaug.augmenters as iaa
from ..Config import MODEL_MAX_SCALE, MODEL_MIN_SCALE, MODEL_MIN_ROT,\
    MODEL_MAX_ROT, MODEL_PERCENTAGE_FLIP, MODEL_PERSPECTIVE_MIN_TRANSFORMATION, \
    MODEL_PERSPECTIVE_MAX_TRANSFORMATION, MODEL_MASK_CUTOUT_ITERATIONS,\
    MODEL_MASK_CUTOUT_SIZE, MODEL_MASK_CUTOUT_PROB,\
    MODEL_MULTIPLY_MESSAGE_IMAGE_AUGMENTATION,\
    MODEL_MULTIPLY_MESSAGE_MASK_AUGMENTATION
from imgaug.augmentables.heatmaps import HeatmapsOnImage
from ImageBot.infrastructure.ImageMessage import ImageMessage
import uuid
from ImageBot.image_processing.masks import mask_bounding_box

def w_crop_to_mask(message):
    # We do not use crop to mask here, because it is slower calling it two times
    # because the bounding box must be calculated accordingly
    bb = mask_bounding_box(message.mask)
    margin = 20
    if bb is not None:
        # Add 5 Pixel on each side to bb
        bb[0][0] = max(0, bb[0][0] - margin)
        bb[0][1] = max(0, bb[0][1] - margin)
        bb[1][0] = min(message.image.shape[1] - 1, bb[1][0] + margin)
        bb[1][1] = min(message.image.shape[0] - 1, bb[1][1] + margin)
        message.image = message.image[bb[0][1]:bb[1][1], bb[0][0]:bb[1][0]]
        message.mask =  message.mask[bb[0][1]:bb[1][1], bb[0][0]:bb[1][0]]
    return message

def w_expand_for_max_affine(message):
    max_addition = int((sqrt(2)-1) * max(message.image.shape[0], message.image.shape[1]) * MODEL_MAX_SCALE) + 1
    message.image = expand_canvas(message.image, max_addition)
    message.mask = expand_canvas(message.mask, max_addition)
    return message
    
def w_model_augement(messages):
    # Convert the image to uint8
    for message in messages:
        message.image = np.uint8(message.image*255.0)
    
    # Leave at least each of one image as it is
    identity_messages = list(messages)
    
    # Imgaug lib only supports masks of boolean value, thus we use heatmaps
    # Multiply some messages
    new_heatmaps = []
    new_images = []
    origins = []
    greens = []
    for message in messages:
        new_heatmaps.extend([HeatmapsOnImage(np.float32(message.mask), shape=message.image.shape, min_value=0.0, max_value=1.0) for _ in range(MODEL_MULTIPLY_MESSAGE_IMAGE_AUGMENTATION-1)])
        new_images.extend([message.image for _ in range(MODEL_MULTIPLY_MESSAGE_IMAGE_AUGMENTATION-1)])
        #origins.extend([message.origin for _ in range(MODEL_MULTIPLY_MESSAGE_IMAGE_AUGMENTATION-1)])
        greens.extend([message.green for _ in range(MODEL_MULTIPLY_MESSAGE_IMAGE_AUGMENTATION-1)])
    
    seq = iaa.Sequential([
        # Make a random persective transformation
        iaa.PerspectiveTransform(scale=(MODEL_PERSPECTIVE_MIN_TRANSFORMATION, MODEL_PERSPECTIVE_MAX_TRANSFORMATION)),
        # Flip 50% of the images horizontally
        iaa.Fliplr(MODEL_PERCENTAGE_FLIP),
        # Apply an affine transformation to the images
        iaa.Affine(scale={"x": (MODEL_MIN_SCALE, MODEL_MAX_SCALE), "y": (MODEL_MIN_SCALE, MODEL_MAX_SCALE)}, rotate=(MODEL_MIN_ROT, MODEL_MAX_ROT))
        ])
    
    # Do the processing
    images, heatmaps = seq(images=new_images, heatmaps=new_heatmaps)
    
    # Convert it back to the original file format that we use
    result = [ImageMessage(uuid.uuid4(), image/255.0, np.float64(heatmaps[i].get_arr()), greens[i].copy()) for i, image in enumerate(images)]
    for im in identity_messages:
        im.image = im.image/255.0
    result.extend(identity_messages)
    
    return result

def w_augment_mask(messages):
    # TODO: Keep one untouched
    # Convert the image to uint8
    for message in messages:
        message.mask = np.uint8(message.mask*255.0)
    
    # Leave at least each of one image as it is
    identity_messages = list(messages)
    
    # Multiply some messages
    new_masks = []
    origins = []
    greens = []
    images = []
    for message in messages:
        new_masks.extend([message.mask for _ in range(MODEL_MULTIPLY_MESSAGE_MASK_AUGMENTATION-1)])
        #origins.extend([message.origin for _ in range(MODEL_MULTIPLY_MESSAGE_MASK_AUGMENTATION-1)])
        images.extend([message.image for _ in range(MODEL_MULTIPLY_MESSAGE_MASK_AUGMENTATION-1)])
        greens.extend([message.green for _ in range(MODEL_MULTIPLY_MESSAGE_MASK_AUGMENTATION-1)])
    
    
    # Setup manipulation to cover random types 
    seq_mask = iaa.Sequential([
        iaa.Sometimes(MODEL_MASK_CUTOUT_PROB, iaa.Cutout(nb_iterations=MODEL_MASK_CUTOUT_ITERATIONS, size=MODEL_MASK_CUTOUT_SIZE, fill_mode="constant", cval=0))
        ])
    
    # Convert to the right value and apply
    masks = seq_mask(images=new_masks)
    
    # Convert it back and merge it with the identity messages
    result = [ImageMessage(uuid.uuid4(), images[i].copy(), mask/255.0, greens[i].copy()) for i, mask in enumerate(masks)]
    for im in identity_messages:
        # Convert back to correct dimensions 
        im.mask = np.float64(im.mask)/255.0
        # Add it to the result
        result.append(im)
    
    return result
    