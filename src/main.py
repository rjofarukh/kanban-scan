import detect_board
import detect_tickets
import argparse
import cv2
import utils
import os

###############################################
parser = argparse.ArgumentParser()

mode = parser.add_mutually_exclusive_group()
mode.add_argument("--find", help="Mode for finding changes on the board (tickets)", action='store_true')
mode.add_argument("--init", help="Mode for initiating board - find borders and sections", action='store_true')

files = parser.add_mutually_exclusive_group()
files.add_argument("--img", nargs=1, help="Name of the file to be used", action="store")
files.add_argument("--dir", nargs=1, help="Directory to be used for simulation", action="store")
files.add_argument("--vid", nargs=1, help="Video to be used for a simulation", action="store")
files.add_argument("--tst", nargs="*", help="Files to be used for testing, or txt containing files", action="store")
args = parser.parse_args()
###############################################

###############################################

# image = cv2.imread("../img_test/2.jpg")
# image2 = cv2.imread("../img_test/3.jpg")
# detect_tickets.find_tickets(image, image2)
###############################################

#utils.plot_hsv(cv2.imread("../img_test/image6.jpg"), root_scale=100)
# knn = utils.knn_classifier("../img_training")
# utils.prediction(knn, cv2.imread("../img_test/1.jpg"), "../img_out/1.jpg")
# utils.prediction(knn, cv2.imread("../img_test/2.jpg"), "../img_out/2.jpg")
# utils.prediction(knn, cv2.imread("../img_test/3.jpg"), "../img_out/3.jpg")
# utils.prediction(knn, cv2.imread("../img_test/4.jpg"), "../img_out/4.jpg")
# utils.prediction(knn, cv2.imread("../img_test/5.jpg"), "../img_out/5.jpg")
# utils.prediction(knn, cv2.imread("../img_test/6.jpg"), "../img_out/6.jpg")
# utils.prediction(knn, cv2.imread("../img_test/7.jpg"), "../img_out/7.jpg")


###############################################
img, border = detect_board.find_and_transform_board(cv2.imread("../img_training/BOARD2.jpg"))

detect_tickets.find_sections(img, border)
#utils.plot_hsv(cv2.imread("../img_training/TICKET1.jpg"))

###############################################
# Load classifiers
# Load pickle files
# Load thresholds json

# Main Loop
# 
# if I am in app mode - one used by default
    # if it is the first iteration
    # initialize board (transform)
    # this will be the board returned to the UI for gridding
    # else
    # ticket objects[] = detect changes(prev_image, curr_image)
    # (each ticket has coordinates, which detect changes returns)
    # (detect changes will only return the blobs with numbers on them)
#   
# if in simulation mode:..
#
#
#
#
#

