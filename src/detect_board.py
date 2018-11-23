import numpy as np
import cv2
import imutils
from imutils import perspective
import utils


# Will get the roll of tape and plaster it 
# all over a sheet of paper and use it to determine
# the COLOR_MIN and COLOR_MAX for thresholding 
# Test under various lighting conditions
#def color_threshold(images):

#def scan_photo(image):
    #Before everything, I will need to read the color from some
    #Scanned photos to be sure I have the right HSV MIN and MAX
    #Second, we threshold to the color of the tape
    #Then we dilate the image to close the gaps (or erode, will test)
    #Then I find the board - getting the contour I can Use that 

def find_and_transform_board(image):

    # placeholder color
    mask1 = utils.threshold(image, "RED1")
    mask2 = utils.threshold(image, "RED2")

    contours = cv2.bitwise_or(mask1, mask2)
    dilated = utils.dilate(contours)
    eroded = utils.erode(dilated)
    points = find_points(eroded)

    flood_mask = np.zeros((eroded.shape[0]+2, eroded.shape[1]+2), np.uint8)
    cv2.floodFill(eroded, flood_mask, (0,0), 255)

    warped_image = transform_corners(image, points)
    warped_border = transform_corners(eroded, points)

    flood_mask = np.zeros((warped_border.shape[0]+2, warped_border.shape[1]+2), np.uint8)
    cv2.floodFill(warped_border, flood_mask, (0,0), 255)

    return warped_image, warped_border

def find_points(image):
    contours = cv2.findContours(image, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
    contours = contours[0] if imutils.is_cv2() else contours[1]
    largest = sorted(contours, key = cv2.contourArea, reverse = True)[0]

    p = cv2.arcLength(largest, True)
    points = cv2.approxPolyDP(largest, 0.02 * p, True)

    if len(points) == 4:
        return points.reshape(4, 2)
    else:
        raise Exception("Could not find the board!")

    return None 

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
