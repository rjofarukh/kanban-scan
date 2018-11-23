import numpy as np
import cv2
import imutils
from imutils import perspective
import random
import utils

# THRESHOLDS FOR BORDER - WORKS
THREHSOLD_MIN = (0,0,0)
THRESHOLD_MAX = (180, 255, 55)

# EXPERIMENTAL
TMIN = (0,20,120)
TMAX = (180, 255, 255)

# takes in transformed image from find_and_transform_board (going to be in RGB)
# returns changed objects, which will have only the coordinates for now
# if the objects are too small - not a ticket
# else  they are actual changes - meaning it's a ticket or an empty space
#   
def find_tickets(prev_image, curr_image):

    # diff = cv2.absdiff(normalize(prev_image), normalize(curr_image))
    # mask = cv2.cvtColor(diff, cv2.COLOR_BGR2GRAY)

    # th = 1
    # imask =  mask>th
    # canvas = np.zeros_like(curr_image, np.uint8)
    # canvas[imask] = curr_image[imask] 

    # utils.show_images(canvas, prev_image, curr_image)
    image1 = normalize(curr_image)
    image2 = normalize(prev_image)
    result = cv2.bitwise_xor(image1, image2)
    utils.show_images(result, image1, image2)

def normalize(image):
    blurred = cv2.GaussianBlur(image, (5, 5), 0)

    min_t, max_t = utils.get_thresh_tuples("NORMAL")
    thresholded = utils.threshold(blurred, min_t, max_t)
    utils.erode(thresholded, iter_num=5)
    return thresholded

def find_sections(image, border):
    thresholded = utils.threshold(image, "BLACK")
    dilated = utils.dilate(thresholded, iter_num=7)
    eroded = utils.erode(dilated)
    black_sections = cv2.bitwise_or(eroded, border)
    
    #could be used to AND with ticket finder
    white_sections = cv2.bitwise_not(black_sections)

    im, contours, hierarchy = cv2.findContours(white_sections.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    contours = sorted(contours, key = cv2.contourArea, reverse = True)

    out = np.zeros_like(white_sections)
    lst_intensities = []

    # For each list of contour points...
    for i in range(len(contours)):

        # Create a mask image that contains the contour filled in
        cimg = np.zeros_like(out)
        cv2.drawContours(cimg, contours, i, color=255, thickness=-1)

        # Access the image pixels and create a 1D numpy array then add to list
        pts = np.where(cimg == 255)
        lst_intensities.append(out[pts[0], pts[1]])

        print("length %d - " % i, contours[i].shape[0])

        cv2.imwrite("../img_out/section%d.jpg" % i, cimg)

        #utils.show_images(cimg)

  