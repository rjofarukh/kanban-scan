import numpy as np
import cv2
import imutils
import random
import utils
import difflib
from Section import Section
from Ticket import Ticket, Assignee
from imutils import perspective
from Enums import Function

import pyzbar.pyzbar as pyzbar
import logging

from imutils import perspective
from sklearn.externals import joblib
from skimage import feature
from keras.models import load_model



def difference_mask(image1, image2, ticket_settings):
    h1,s1,v1 = cv2.split(normalize(image1.copy()))
    h2,s2,v2 = cv2.split(normalize(image2.copy()))

    hsv_diff = cv2.absdiff(s1,s2)
    _, dst = cv2.threshold(hsv_diff, int(ticket_settings["difference_threshold"]), 255, cv2.THRESH_BINARY)
    
    return dst

def find_limits(state, sections, ticket_settings, classifier, section_data):
    c_i = state.curr_image.copy()
    b_i = state.background_image.copy()

    diff_mask = difference_mask(c_i, b_i, ticket_settings)

    limit = ""
    for section_num, section in sections.items():
        if section.function == Function.LIMIT:
            mask = cv2.bitwise_and(section.mask, diff_mask)
            _, contours, _ = cv2.findContours(mask.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
            contour = sorted(contours, key = cv2.contourArea, reverse = True)

            if len(contour) > 0:
                contour = contour[0]
            else:
                continue
            x,y,w,h = cv2.boundingRect(contour)

            if h > 40 and w > 40:
                thresh_limit, colored_limit = cluster(c_i[y:y+h, x:x+w])
                limit = find_numbers_in_mask(thresh_limit, colored_limit, classifier, ticket_settings["Digits"])

                if limit != "" and limit != 0:
                    prev_limit = section_data[section.name]
                    section_data[section.name] = int(limit)
                    Section.map_section_names(sections, section_data)
                    if int(prev_limit) != int(limit):
                        logging.info(f"SECTION - The \"{section.name}\" has changed from {prev_limit} to {limit} (ID:#{section_num})")
                        state.board_sections = state.draw_section_rectangles(sections)

    return sections, section_data

def find_tickets(state, classifier, ticket_settings, ticket_data):
    prev_image = state.prev_image
    curr_image = state.curr_image
    background_image = state.background_image

    curr_prev_diff = difference_mask(curr_image, prev_image, ticket_settings)
    curr_back_diff = difference_mask(curr_image, background_image, ticket_settings)
    prev_back_diff = difference_mask(prev_image, background_image, ticket_settings)

    added_ticket_mask = cv2.bitwise_and(curr_prev_diff, curr_back_diff)
    removed_ticket_mask = cv2.bitwise_and(curr_prev_diff, prev_back_diff)

    colored_grid = utils.image_grid(curr_image, prev_image, background_image, np.zeros_like(prev_image))
    threshold_grid = utils.image_grid(curr_back_diff, prev_back_diff, added_ticket_mask, removed_ticket_mask)
    state.set_grids(colored_grid, threshold_grid)

    added_tickets = changed_tickets(curr_image, added_ticket_mask, classifier, ticket_settings, ticket_data)

    removed_tickets = changed_tickets(prev_image, removed_ticket_mask, classifier, ticket_settings, ticket_data)

    return added_tickets, removed_tickets

def changed_tickets(bgr_image, ticket_mask, classifier, ticket_settings, ticket_data):
    hsv_image = cv2.cvtColor(bgr_image, cv2.COLOR_BGR2HSV)

    _, contours, _ = cv2.findContours(ticket_mask.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    contours = sorted(contours, key = cv2.contourArea, reverse = True)

    tickets = {}

    for i in range(len(contours)):
        _,_,width,height = cv2.boundingRect(contours[i])
        if (cv2.contourArea(contours[i]) * int(ticket_settings["min_ticket_scale"]) > hsv_image.shape[0] * hsv_image.shape[1]) and width < hsv_image.shape[1] / 3 and height < hsv_image.shape[0] / 3:

            ticket_mask = np.zeros_like(ticket_mask)

            hulls = []
            hulls.append(cv2.convexHull(contours[i], False))

            cv2.drawContours(ticket_mask, hulls, 0, color=255, thickness=-1)

            area = cv2.contourArea(contours[i])

            rect = cv2.boundingRect(contours[i])
            x,y,width, height = rect

            ticket_area = bgr_image[y:y+height, x:x+width]

            thresholded_ticket, colored_ticket = cluster(ticket_area)
            thresholded_digits, colored_digits = digit_area(thresholded_ticket, colored_ticket, ticket_settings)

            ticket_number = find_numbers_in_mask(thresholded_digits, colored_digits, classifier, ticket_settings["Digits"])

            if len(difflib.get_close_matches(ticket_number, ticket_data.keys())) > 0:
                ticket_number = difflib.get_close_matches(ticket_number, ticket_data.keys())[0]
                tickets[ticket_number] = Ticket(ticket_mask, ticket_number, [area, width, height, rect],desc=ticket_data[ticket_number]["description"])
            else: 
                tickets[ticket_number] = Ticket(ticket_mask, ticket_number, [area, width, height, rect])

        else:
            break

    return tickets

def digit_area(thresholded_ticket, colored_ticket, ticket_settings):
    height, width = thresholded_ticket.shape[:2]
    im1 = thresholded_ticket[0:0+int(height * float(ticket_settings["top_digit_area"])),0:0+width]
    im2 = colored_ticket[0:0+int(height * float(ticket_settings["top_digit_area"])),0:0+width]

    return im1, im2

def cluster(image):

    Z = image.reshape((-1,3))
    Z = np.float32(Z)

    criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 10, 1.0)
    K = 3
    ret,label,center=cv2.kmeans(Z,K,None,criteria,10,cv2.KMEANS_RANDOM_CENTERS)

    center = np.uint8(center)
    res = center[label.flatten()]
    res2 = res.reshape((image.shape))

    center = center[np.argmin(np.sum(center, axis=1))]

    mask = cv2.inRange(res2, np.subtract(center,1), np.add(center, 1))
 
    return mask, res2

def normalize(image):

    #return image
    blurred = cv2.GaussianBlur(image, (5, 5), 0)
    blurred = cv2.cvtColor(blurred, cv2.COLOR_BGR2HSV)

    return blurred

def deskew(image, SZ=20):
    m = cv2.moments(image)
    if abs(m['mu02']) < 1e-2:
        return image.copy()
    skew = m['mu11']/m['mu02']
    M = np.float32([[1, skew, -0.5*SZ*skew], [0, 1, 0]])
    image = cv2.warpAffine(image, M, (SZ, SZ))
    return image

def find_assignees_in_image(state):
    assignees = []

    image = state.curr_image
    decodedObjects = pyzbar.decode(image)
 
    for decodedObject in decodedObjects:
        blank = np.zeros_like(cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)) 
        
        points = decodedObject.polygon
 
        if len(points) > 4 : 
            hull = cv2.convexHull(np.array([point for point in points], dtype=np.float32))
            hull = list(map(tuple, np.squeeze(hull)))
        else : 
            hull = points;
        
        (top_left, top_right, bottom_right, bottom_left) = perspective.order_points(np.asarray(points)[:4])

        cv2.rectangle(blank, (top_left[0], top_left[1]), (bottom_right[0], bottom_right[1]), (255,255,255), -1)

        _, assignee_mask = cv2.threshold(blank, 200, 255, cv2.THRESH_BINARY)
        assignees.append(Assignee(str(decodedObject.data, 'utf-8', 'ignore'), assignee_mask, [top_left, bottom_right]))

    return assignees
 
def find_numbers_in_mask(image, colored, classifier, digit_settings):

    ctrs = cv2.findContours(image.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    ctrs = ctrs[0] if imutils.is_cv2() else ctrs[1]

    numbers = {}
    for ctr in ctrs:
        area = cv2.contourArea(ctr)
        x,y,w,h = cv2.boundingRect(ctr)
        
        if area > int(digit_settings["min_area"]) and h > int(digit_settings["min_height"]):
            digit_mask = np.zeros_like(image)
            digit_mask[y:y+h, x:x+w] = image[y:y+h, x:x+w]

            bounding_square_len = int(h * 1.6)
            pt1 = int(y + h // 2 - bounding_square_len // 2)
            pt2 = int(x + w // 2 - bounding_square_len // 2)

            roi = digit_mask[pt1:pt1+bounding_square_len, pt2:pt2+bounding_square_len]

            if np.size(roi) == 0:
                continue
            roi = cv2.resize(roi, (28,28))

            roi_arr = np.array(roi, 'float32') / 255
            roi_arr = roi_arr.reshape(1,28,28,1)

            nbr = classifier.predict(roi_arr).argmax(axis=1)
            numbers[x + w // 2] =  nbr[0]

            cv2.rectangle(colored, (x, y), (x + w, y + h), (0, 255, 0), 3)
            cv2.putText(colored, str(int(nbr[0])), (x, y),cv2.FONT_HERSHEY_DUPLEX, 2, (0, 255, 255), 3)

    result = ""

    for key in sorted(numbers):
        result += str(numbers[key])
        
    return result
