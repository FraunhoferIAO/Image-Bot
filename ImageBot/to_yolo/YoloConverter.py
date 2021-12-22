import numpy as np
import cv2
import uuid
import os
import random
import imgaug.augmenters as iaa
import imgaug.parameters as iap
from pathlib import Path

from queue import Queue

import os

from ..Config import CLASS_ID
from ..infrastructure.ImageMessage import ImageMessage
from ..infrastructure.filter import load_image
from ..image_processing.masks import mask_bounding_box


def to_yolo_dataset(source_folder, target_folder, test_training_split=0.3):

    # Get all filenames
    filenames = [f.replace('_mask.png', "") for f in os.listdir(source_folder) if f.endswith('_mask.png')]

    # First shuffle the list
    random.shuffle(filenames)
    # Now select the test_aquisition split
    max_index = int(test_training_split*len(filenames))
    test_messages = filenames[:max_index]
    training_messages = filenames[max_index:]
    
    # Now save them and their labels in different folders
    train_folder = os.path.join(target_folder, 'train')
    test_folder = os.path.join(target_folder, 'test')
    
    # Make the folders if the do not already exist
    # TODO: Remove hard coded paths
    Path(target_folder).mkdir(parents=True, exist_ok=True)
    Path(train_folder).mkdir(parents=True, exist_ok=True)
    Path(test_folder).mkdir(parents=True, exist_ok=True)
    Path(os.path.join(train_folder, "images")).mkdir(parents=True, exist_ok=True)
    Path(os.path.join(test_folder, "images")).mkdir(parents=True, exist_ok=True)
    Path(os.path.join(train_folder, "labels")).mkdir(parents=True, exist_ok=True)
    Path(os.path.join(test_folder, "labels")).mkdir(parents=True, exist_ok=True)
    
    # Helper function to save the file
    def save_message(filename, parent_path):
        image = cv2.imread(os.path.join(source_folder, filename + ".png"), cv2.IMREAD_GRAYSCALE)
        mask = cv2.imread(os.path.join(source_folder, filename + "_mask.png"), cv2.IMREAD_GRAYSCALE)

        # Save the image
        cv2.imwrite(os.path.join(parent_path, "images", filename + ".png"), image)
        # Save the label
        bb = bounding_box_darknet_format(mask)
        bb_str = ""
        if bb is not None:
            bb_str = str(CLASS_ID) + " " + str(bb[0][0]) + " " + str(bb[0][1]) + " " + str(bb[1][0]) + " " + str(bb[1][1])
        with open(os.path.join(os.path.join(parent_path, "labels"), filename + ".txt"), "w") as label_file:
            label_file.write(bb_str)
    
    # Now save them
    for m in test_messages:
        save_message(m, test_folder)
    for m in training_messages:
        save_message(m, train_folder)

def bounding_box_darknet_format(mask):
    bb = mask_bounding_box(mask)
    if bb is None:
        return None
    s = mask.shape
    center = ((bb[0][0]+bb[1][0])/2.0/s[1], (bb[0][1]+bb[1][1])/2.0/s[0])
    size = ((bb[1][0]-bb[0][0])/s[1], (bb[1][1]-bb[0][1])/s[0])
    return (center, size)