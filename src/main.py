import detect_board
import detect_tickets
import cv2


image1 = cv2.imread("../img_test/image2.jpg")


#detect_tickets.find_tickets(image1, image1)

detect_tickets.find_areas(image1)

###############################################
# Main Loop
#
# if it is the first iteration
#   initialize board (transform)
#   this will be the board returned to the UI for gridding
# else
#   ticket objects[] = detect changes(prev_image, curr_image)
#   (each ticket has coordinates, which detect changes returns)
#   (detect changes will only return the blobs with numbers on them)
#   
#
#
#
#
#
###############################################
# RED1_MIN = (0, 20, 50)
# RED1_MAX = (15, 255, 255)
# RED2_MIN = (165, 20, 50)
# RED2_MAX = (180, 255, 255)



# image2 = detect_board.threshold(image1, RED1_MIN, RED1_MAX, RED2_MIN, RED2_MAX)

# image3 = detect_board.dilate(image2)
# image4 = detect_board.erode(image3)

# # gray = cv2.cvtColor(image1, cv2.COLOR_BGR2GRAY)
# # edged = cv2.Canny(gray, 75, 200)
# points = detect_board.find_points(image4)

# warped = detect_board.transform_corners(image1, points)

# cv2.imwrite("IMAAAGE.jpg", warped)
