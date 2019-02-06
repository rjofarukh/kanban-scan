import numpy as np
import cv2
import imutils
import random
import utils
from Ticket import Ticket

import pyzbar.pyzbar as pyzbar
import logging

from imutils import perspective
from sklearn.externals import joblib
from skimage import feature
from keras.models import load_model


# takes in transformed image from find_and_transform_board (going to be in RGB)
# returns changed objects, which will have only the coordinates for now
# if the objects are too small - not a ticket
# else  they are actual changes - meaning it's a ticket or an empty space
#   
def find_tickets(prev_image, curr_image, sections, ticket_settings):

    prev_image = normalize(prev_image)
    curr_image = normalize(curr_image)

    h1,s1,v1 = cv2.split(prev_image)
    h2,s2,v2 = cv2.split(curr_image)

    diff = cv2.absdiff(h1,h2)
    diff2 = cv2.absdiff(v1,v2)

    th, dst = cv2.threshold(diff, int(ticket_settings["difference_threshold"]), 255, cv2.THRESH_BINARY)

    #utils.show_images(diff, diff2, h1, h2, dst, scale=1)

    im, contours, hierarchy = cv2.findContours(dst.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    contours = sorted(contours, key = cv2.contourArea, reverse = True)

    bgr_curr_image = cv2.cvtColor(curr_image, cv2.COLOR_HSV2BGR)

    for i in range(len(contours)):
        if cv2.contourArea(contours[i]) * int(ticket_settings["min_ticket_scale"]) > prev_image.shape[0] * prev_image.shape[1]:
            ticket_num = i + 1
            ticket_mask = np.zeros_like(dst)
            cv2.drawContours(ticket_mask, contours, i, color=255, thickness=-1)

            area = cv2.contourArea(contours[i])
            *_,width, height = cv2.boundingRect(contours[i])

            logging.debug("AREA %f" % cv2.contourArea(contours[i]))
            logging.debug(f"HEIGHT {height}")
            logging.debug(f"WIDTH {width}")
            logging.debug("----------")


            output = cv2.bitwise_and(bgr_curr_image, bgr_curr_image, mask=ticket_mask)
            utils.show_images(output, scale=1)

            find_numbers_in_mask(diff2.copy(), bgr_curr_image.copy())
            
            ticket = Ticket(ticket_mask, ticket_num, [area, width, height])
            parent_section = ticket.ticket_belongs_to(sections)
            sections[parent_section].add_ticket(ticket)

        else:
            break

    return sections


def normalize(image):
    blurred = cv2.GaussianBlur(image, (5, 5), 0)
    blurred = cv2.cvtColor(blurred, cv2.COLOR_BGR2HSV)

    return blurred

def deskew(image):
    m = cv2.moments(image)
    if abs(m['mu02']) < 1e-2:
        return image.copy()
    skew = m['mu11']/m['mu02']
    M = np.float32([[1, skew, -0.5*SZ*skew], [0, 1, 0]])
    image = cv2.warpAffine(image, M, (SZ, SZ), flags=affine_flags)
    return image

def find_tag_in_mask(image):
    decodedObjects = pyzbar.decode(image)
 
    # Print results
    for obj in decodedObjects:
        print('Type : ', obj.type)
        print('Data : ', obj.data,'\n')

      # Loop over all decoded objects
    for decodedObject in decodedObjects: 
        points = decodedObject.polygon
 
        # If the points do not form a quad, find convex hull
        if len(points) > 4 : 
            hull = cv2.convexHull(np.array([point for point in points], dtype=np.float32))
            hull = list(map(tuple, np.squeeze(hull)))
        else : 
            hull = points;
        
        # Number of points in the convex hull
        n = len(hull)
    
        # Draw the convext hull
        for j in range(0,n):
            cv2.line(image, hull[j], hull[ (j+1) % n], (255,0,0), 3)
 
    utils.show_images(image, scale=2)

def find_numbers_in_mask(im, curr_image):
    cnn = load_model("../classifiers/mnist_keras_cnn_model.h5")

    #im_gray = cv2.cvtColor(im, cv2.COLOR_BGR2GRAY)
    #im_gray = cv2.GaussianBlur(im_gray, (5, 5), 0)

    im_th = cv2.Canny(im,100,200)
    im = curr_image
    #im_th = cv2.adaptiveThreshold(im_gray, 255, cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY, 5, 10)
    #im_th = cv2.bitwise_not(im_th)

    # !! IDEA - overly dialate just to get the areas of interest, then use proper edge detection
    # on those regions along with deskewing!!!

    ctrs = cv2.findContours(im_th.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    ctrs = ctrs[0] if imutils.is_cv2() else ctrs[1]
    rects = [cv2.boundingRect(ctr) for ctr in ctrs]

    for rect in rects:
        x,y,w,h = rect
        
        if w > 5 and h > 5:
            bounding_square_len = int(h * 1.6)
            pt1 = int(y + h // 2 - bounding_square_len // 2)
            pt2 = int(x + w // 2 - bounding_square_len // 2)

            roi = im_th[pt1:pt1+bounding_square_len, pt2:pt2+bounding_square_len]
            roi = cv2.resize(roi, (28,28))
            roi_arr = np.array(roi, 'float32') / 255
            roi_arr = roi_arr.reshape(1,28,28,1)

            nbr = cnn.predict(roi_arr).argmax(axis=1)

            cv2.rectangle(im, (x, y), (x + w, y + h), (0, 255, 0), 3)
            cv2.putText(im, str(int(nbr[0])), (rect[0], rect[1]),cv2.FONT_HERSHEY_DUPLEX, 2, (0, 255, 255), 3)

    utils.show_images(im, scale = 2)