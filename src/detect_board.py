import numpy as np
import cv2
import imutils
from imutils import perspective

MAGENTA_MIN = (135,50,50)
MAGENTA_MAX = (165,255,255)

RED1_MIN = (0, 20, 50)
RED1_MAX = (15, 255, 255)
RED2_MIN = (165, 20, 50)
RED2_MAX = (180, 255, 255)

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
    contours = threshold(image, RED1_MIN, RED1_MAX, RED2_MIN, RED2_MAX)
    
    # dilate to connect pixels which might be apart for the border
    dilated = dilate(image)

    # once connected, make them thinner
    eroded = erode(dilated)

    points = find_points(eroded)

    warped = transform_corners(image, points)

    # returns just the board insided the contour
    return warped

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
    
def threshold(image, min1, max1, min2 = None, max2 = None):
    hsv_image = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    mask1 = cv2.inRange(hsv_image, min1, max1)

    if min2 is None or max2 is None:
        return mask1

    mask2 = cv2.inRange(hsv_image, min1, max1)

    result = cv2.bitwise_or(mask1, mask2)

    return result

def dilate(image, kern_size = 5, iter_num = 1):
    kernel = np.ones((kern_size, kern_size), np.uint8)
    dilated = cv2.dilate(image, kernel, iterations=iter_num)

    return dilated

def erode(image, kern_size = 5, iter_num = 1):
    kernel = np.ones((kern_size, kern_size), np.uint8)
    eroded = cv2.dilate(image, kernel, iterations=iter_num)

    return eroded

def distance_between_points(point1, point2):
    return np.sqrt(((point1[0] - point2[0]) ** 2) + ((point1[1] - point2[1]) ** 2))

def transform_corners(image, pts):
    ordered_pts = perspective.order_points(pts)
    print(ordered_pts)
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


