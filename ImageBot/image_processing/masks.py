'''
Created on 19.02.2021

@author: lblock
'''
import cv2
import numpy as np
from scipy.interpolate import splprep, splev
from scipy.ndimage.filters import maximum_filter

def mask_to_alpha(image, mask):
    assert image.shape[0] == mask.shape[0]
    assert image.shape[1] == mask.shape[1]
    
    # Now merge
    b, g, r = cv2.split(image)
    return cv2.merge((b, g, r, mask))

def combine_images(background, foreground, mask):
    assert background.shape[0] == foreground.shape[0] == mask.shape[0]
    assert background.shape[1] == foreground.shape[1] == mask.shape[1]
    assert background.shape[2] == foreground.shape[2] == 3
    
    # We must make the mask times three to work with the 3 channels of the original images
    mask = cv2.merge((mask, mask, mask))
    
    # Multiply the images to get the overlay
    foreground = cv2.multiply(mask, foreground)
    background = cv2.multiply(1.0-mask, background)
    
    # Add the overlays to each other
    return cv2.add(foreground, background)


def detect_edges(mask, distance_smoothing):
    tmpMask = cv2.merge((mask, mask, mask))
    tmpMask = np.uint8(tmpMask*255)
    tmpMask = cv2.cvtColor(tmpMask, cv2.COLOR_BGR2GRAY)
    
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (distance_smoothing, distance_smoothing))
    dilated = cv2.dilate(tmpMask, kernel)
    return cv2.findContours(dilated.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

def clean_mask_surrounding(mask, distance_smoothing, min_percentage):
    # Idea: Detect the object and delete everything outside of it
    cnts, hierarchy = detect_edges(mask, distance_smoothing)
    
    # Calculate the image center
    image_center = np.array((mask.shape[0]/2, mask.shape[1]/2))
    
    # Calculate the minimum size a contour must have to be detected
    min_cnt_size = mask.shape[0]*mask.shape[1]*min_percentage
    
    # Select the contour closest to the center of the image
    selected_cnt = None
    selected_center_distance = 1000000
    for cnt in cnts:
        # Calculate the moments
        cnt_moment = cv2.moments(cnt)
        
        # First check if the size of the contour
        if cnt_moment["m00"] > min_cnt_size:
            cX = int(cnt_moment["m10"] / cnt_moment["m00"])
            cY = int(cnt_moment["m01"] / cnt_moment["m00"])
            cnt_center = np.array((cY, cX))
            distance = np.linalg.norm(cnt_center-image_center)
            if distance < selected_center_distance:
                selected_cnt = cnt
                selected_center_distance = distance
                
    # TODO: Take into account hierarchy?
    
    # Make everything outside the mask black
    stencil = np.zeros(mask.shape).astype(mask.dtype)
    color = [1.0, 1.0, 1.0]
    cv2.fillPoly(stencil, [selected_cnt], color)
    return cv2.multiply(mask, stencil)

def tigthen_mask(mask, pixels, distance_smoothing):
    # Detect the mask edges and paint a black border around them
    cnts, _ = detect_edges(mask, distance_smoothing)
    
    # making the mask tighter is no problem (just draw a line around the contour)
    # except for the image border, where this reduces the mask from the image
    # border inwards
    # Thus we search for all contour points on the border and move the outwards
    # so that they are just not visible anymore
    new_cnts = []
    for c in cnts:
        new_c = []
        for p in c:
            # The contours are not always exactly on the border, but derivate
            # of up to 1 pixel due to the detect_edges algorithm
            if (p[0][1] <= 1):
                p[0][1] = p[0][1]-(pixels+1)
            if (p[0][1] >= mask.shape[0]-1):
                p[0][1] = p[0][1]+(pixels+1)
            if (p[0][0] <= 1):
                p[0][0] = p[0][0]-(pixels+1)
            if (p[0][0] >= mask.shape[1]-1):
                p[0][0] = p[0][0]+(pixels+1)
            new_c.append(p)
        new_c = np.array(new_c)
        new_cnts.append(new_c)
    
    # Draw the mask in black, which in fact removes the outer x pixels
    # TODO: Use antialiasing in here
    result = mask.copy()
    cv2.drawContours(result, new_cnts, -1, (0,), pixels*2)

    return result

def enlarge_mask(mask, distance):
    return maximum_filter(mask, footprint=np.ones((distance,distance)), mode='constant')

def smoothen_contours(mask, distance_smoothing):
    '''
    Code from here: https://agniva.me/scipy/2016/10/25/contour-smoothing.html
    and altered a little bit, does not currently not work so well
    '''
    # TODO: Make better
    
    contours, _ = detect_edges(mask, distance_smoothing)
    
    smoothened = []
    for contour in contours:
        x,y = contour.T
        # Convert from numpy arrays to normal arrays
        x = x.tolist()[0]
        y = y.tolist()[0]
        # https://docs.scipy.org/doc/scipy-0.14.0/reference/generated/scipy.interpolate.splprep.html
        tck, u = splprep([x,y], u=None, s=1.0, per=1)
        # https://docs.scipy.org/doc/numpy-1.10.1/reference/generated/numpy.linspace.html
        u_new = np.linspace(u.min(), u.max(), 250)
        # https://docs.scipy.org/doc/scipy-0.14.0/reference/generated/scipy.interpolate.splev.html
        x_new, y_new = splev(u_new, tck, der=0)
        # Convert it back to numpy format for opencv to be able to display it
        res_array = [[[int(i[0]), int(i[1])]] for i in zip(x_new,y_new)]
        smoothened.append(np.asarray(res_array, dtype=np.int32))
        
    result = mask.copy()
    cv2.drawContours(result, smoothened, -1, (0,), 10)
    
    return result

def mask_bounding_box(mask, epsilon=0.01):
    non_zeros = np.argwhere(mask.flatten() > epsilon)[:,0]
    if len(non_zeros) == 0:
        # Somehow there is no mask there
        print("Nothing to mask")
        return [[0, 0], [0, 0]]
    else:
        min_height = int(min(non_zeros)/mask.shape[1])
        max_height = int(max(non_zeros)/mask.shape[1])
        min_width = min(non_zeros%mask.shape[1])
        max_width = max(non_zeros%mask.shape[1])

    res = [[min_width, min_height], [max_width, max_height]]
    return res
    
    
    