import numpy as np
import cv2
import imutils
from imutils import perspective
import utils
import logging

from Section import Section
from Enums import Function

def find_board(image, board_settings):
    if(board_settings["border_color"] == "RED"):
        mask1 = utils.threshold(image, "RED1")
        mask2 = utils.threshold(image, "RED2")
        contours = cv2.bitwise_or(mask1, mask2)
    else:
        contours = utils.threshold(image, board_settings["border_color"])
    
    dilated = utils.dilate(contours)
    eroded = utils.erode(dilated)
    points = find_points(eroded)

    return points is not None


def find_and_transform_board(image, sections, board_settings):

    if(board_settings["border_color"] == "RED"):
        mask1 = utils.threshold(image, "RED1")
        mask2 = utils.threshold(image, "RED2")
        contours = cv2.bitwise_or(mask1, mask2)
    else:
        contours = utils.threshold(image, board_settings["border_color"])
    
    dilated = utils.dilate(contours)
    eroded = utils.erode(dilated)
    points = find_points(eroded)

    if points is None:
        return None, None, None

    flood_mask = np.zeros((eroded.shape[0]+2, eroded.shape[1]+2), np.uint8)
    cv2.floodFill(eroded, flood_mask, (0,0), 255)

    warped_image = transform_corners(image, points)
    warped_border = transform_corners(eroded, points)

    flood_mask = np.zeros((warped_border.shape[0]+2, warped_border.shape[1]+2), np.uint8)
    cv2.floodFill(warped_border, flood_mask, (0,0), 255)

    sections = find_sections(warped_image, warped_border, sections, board_settings)
    
    return warped_image, sections, points

def find_points(image):
    contours = cv2.findContours(image, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
    contours = contours[0] if imutils.is_cv2() else contours[1]
    largest = sorted(contours, key = cv2.contourArea, reverse = True)[0]

    p = cv2.arcLength(largest, True)
    points = cv2.approxPolyDP(largest, 0.02 * p, True)

    if len(points) == 4:
        return points.reshape(4, 2)
    else:
        logging.warning("The board is obstructed!")

    return None 

def find_sections(image, border, sections, board_settings):
    thresholded = utils.threshold(image, board_settings["grid_color"])
    dilated = utils.dilate(thresholded, iter_num=int(board_settings["dilation"]))
    eroded = utils.erode(dilated,  iter_num=int(board_settings["erosion"]))
    black_sections = cv2.bitwise_or(eroded, border)
    
    white_sections = cv2.bitwise_not(black_sections)

    im, contours, hierarchy = cv2.findContours(white_sections.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    contours = sorted(contours, key = cv2.contourArea, reverse = True)

    for i in range(len(contours)):
        if cv2.contourArea(contours[i]) * int(board_settings["min_section_scale"]) > image.shape[0] * image.shape[1]:

            section_num = i + 1
            cimg = np.zeros_like(white_sections)
            cv2.drawContours(cimg, contours, i, color=255, thickness=-1)

            sections[str(section_num)] = Section(cimg, section_num, function=Function.TICKET)
        else:
            break
    
    return sections

def distance_between_points(point1, point2):
    return np.sqrt(((point1[0] - point2[0]) ** 2) + ((point1[1] - point2[1]) ** 2))

def transform_corners(image, pts):
    ordered_pts = perspective.order_points(pts)
    (top_left, top_right, bottom_right, bottom_left) = ordered_pts

    width1 = distance_between_points(top_left, top_right)
    width2 = distance_between_points(bottom_left, bottom_right)
    height1 = distance_between_points(top_left, bottom_left)
    height2 = distance_between_points(top_right, bottom_right)

    warped_width = max(int(width1), int(width2))
    warped_height = max(int(height1), int(height2))

    warped_dimentions = np.array([[0,0],
                                     [warped_width - 1, 0],
                                     [warped_width - 1, warped_height - 1],
                                     [0, warped_height - 1]], dtype = "float32")

    perspectiveTransform = cv2.getPerspectiveTransform(ordered_pts, warped_dimentions)
    
    warped = cv2.warpPerspective(image, perspectiveTransform, (warped_width, warped_height))
    return warped
