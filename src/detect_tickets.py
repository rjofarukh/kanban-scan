import numpy as np
import cv2
import imutils
from imutils import perspective
import random
import detect_board
import utils

# THRESHOLDS FOR BORDER
THREHSOLD_MIN = (0,0,0)
THRESHOLD_MAX = (180, 255, 55)

# takes in transformed image from find_and_transform_board (going to be in RGB)
# returns changed objects, which will have only the coordinates for now
# if the objects are too small - not a ticket
# else  they are actual changes - meaning it's a ticket or an empty space
#   
def find_tickets(prev_image, curr_image):
    blurred = cv2.GaussianBlur(prev_image, (5, 5), 0)

    thresholded = detect_board.threshold(blurred, THREHSOLD_MIN, THRESHOLD_MAX)
    dilated = detect_board.dilate(thresholded, iter_num=7)
    eroded = detect_board.erode(dilated)
    
    edges = cv2.Canny(eroded,10,50)

    utils.show_images(edges,thresholded, blurred)
    #cv2.imwrite("image%f.jpg" % random.random(), thresh)

def find_areas(image):
    thresholded = detect_board.threshold(image, THREHSOLD_MIN, THRESHOLD_MAX)
    dilated = detect_board.dilate(thresholded, iter_num=7)
    eroded = detect_board.erode(dilated)

    eroded = cv2.bitwise_not(eroded)
    utils.show_images(thresholded, dilated, eroded, image)
