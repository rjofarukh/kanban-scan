import detect_board
import detect_tickets
import argparse
import cv2
import utils
import sys 
import os
import json
import logging
import time
import datetime
import pickle

from enum import Enum
from Enums import Stage, Mode
from Board import Board

from sklearn.externals import joblib
from keras.models import load_model

def load_parsers():
    parser = argparse.ArgumentParser()

    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--demo", nargs=1, help="Demo number - important for settings.json (logger.INFO)", action='store')
    mode.add_argument("--test", nargs=1, help="Run specific test file (logger.DEBUG)", action="store")
    mode.add_argument("--reload", help="Reload from the last session (if it exists and hasn't ended) (logger.INFO)", action='store_true')

    files = parser.add_mutually_exclusive_group()
    files.add_argument("--dir", nargs=1, help="Directory to be used for simulation", action="store")
    files.add_argument("--vid", nargs=1, help="Video to be used for a simulation", action="store")
    files.add_argument("--tst", nargs="*", help="Files to be used for testing, or txt containing files", action="store")
    args = parser.parse_args()

def load_logging(loggingLevel):
    time = datetime.datetime.now().strftime("%H:%M:%S")

    logging.basicConfig(
        format='%(asctime)s - [%(levelname)s] - %(message)s',
        datefmt="%m/%d/%Y %I:%M:%S",
        level=loggingLevel,
        handlers=[
            logging.FileHandler("../logs/%s.log" % time),
            logging.StreamHandler(sys.stdout)
        ])

def load_classifiers(recognitionAlg):
    cnn_file = "../classifiers/mnist_keras_cnn_model.h5"
    svm_file = "../classifiers/mnist_keras_svm_model.pkl"
    cnn = load_model(cnn_file)
    svm = joblib.load(svm_file)

    if recognitionAlg == "cnn":
        return cnn
    else:
        return svm

def load_settings(settingsFile, settingsID):
    with open(settingsFile) as infile:
        settings = json.load(infile)
    utils.setup_thresholds(settings[settingsID]["General"]["thresholds_file"])
    return settings[settingsID]

def save_pickle_files(objFileNames, *objects):
    if len(objects) != len(objFileNames):
        logging.error("Number of names supplied for pickling is different "\
                      "the number of labels for them!")
    else:
        for i in range(len(objects)):
            with open("../pkl/%s.pkl" % objFileNames[i], "wb") as outFile:
                pickle.dump(objects[i], outFile)
    
def load_from_pickle_files(objFileNames, *objects):
    if len(objects) == len(objFileNames) and len(objects) == len(os.listdir("../pkl")):
        for i in range(len(objects)):
            with open("../pkl/%s.pkl" % objFileNames[i], "wb") as outFile:
                objects[i] = pickle.load(outFile)
    else:
        logging.error("Number of objects in directory is different from "\
                      "the number of objects supplied!")


def load_from_logs(*objects):
    return None
    
def test()
    objectFileNames = ["stage", "settings", "classifier", "sections", "background",
                    "curr_image", "prev_image", "board_points"]

    STAGE = None
    SETTINGS = []
    CLASSIFIER = None
    SECTIONS = {}
    BACKGROUND = []
    CURR_IMAGE = []
    PREV_IMAGE = []
    BOARD_POINTS = []


    load_logging(logging.DEBUG)
    SETTINGS = load_settings("../json/settings.json", "1")
    CLASSIFIER = load_classifiers(SETTINGS["Digits"]["recognition_alg"])


    image = cv2.imread("../data/standard_noTags/_DSC7343.JPG")
    CURR_IMAGE, SECTIONS, BOARD_POINTS = detect_board.find_and_transform_board(image, SECTIONS, SETTINGS["Board"])

    nextImage = cv2.imread("../data/standard_noTags/_DSC7344.JPG")
    a,b,c = detect_board.find_and_transform_board(nextImage, SETTINGS["Board"])

    if a is None:
        print("thefuck")
    else:
        PREV_IMAGE = CURR_IMAGE
        CURR_IMAGE = detect_board.transform_corners(nextImage, BOARD_POINTS)
        SECTIONS = detect_tickets.find_tickets(PREV_IMAGE, CURR_IMAGE, SECTIONS, SETTINGS["Tickets"])

    save_pickle_files(objectFileNames, STAGE, SETTINGS, CLASSIFIER, SECTIONS,
                      BACKGROUND,CURR_IMAGE, PREV_IMAGE, BOARD_POINTS)


###############################################


# Load classifiers
# Load pickle files
# Load thresholds json
# Load the board name I will be working with
# Transform image to suitable resolution

# Main Loop
#
# SAVE PICKLE FILES AFTER EVERY PHOTO
# ABILITY TO RELOAD 

# Load pickles if from last session if last keyboard
# interrupt happens
# Capture keyboard interrupt and save pickles just in case
# 
# IN CASE OF FURTHER ERROR - MINE LOGS TO GET LAST STATE

def main():
    objectFileNames = ["curr_stage", "settings", "classifier", "sections", "state"]

    Curr_Stage = None
    Settings = []
    Classifier = None
    Sections = {}
    State = None



    load_parsers()
    load_logging(logging.DEBUG)
    Settings = load_settings("../json/settings.json", "1")
    Classifier = load_classifiers(Settings["Digits"]["recognition_alg"])
    State = Board(Settings["General"]["photo_folder"])

    
    # load Reload/Demo/Test from arguments to determine what to do
    # TO COMPLETE

    while (photo = State.next_photo()) != None:

        if Curr_Stage == Stage.INIT:
            current, Sections, points = detect_board.find_and_transform_board(photo, Sections, Settings["Board"])
            
            if current == Sections == points == None:
                logging.warning("Board is currently blocked. Waiting for the next image!")
            
            State.set_current_image(current)
            State.set_background_image(current)
            State.set_points(points)
            Curr_Stage = Stage.MAIN

            # WAIT FOR Settings[General][image_interval] number of seconds,
            # Or for keyboard input if that's preferable

            save_pickle_files(objectFileNames, Curr_Stage, Settings, Classifier, Sections, State)
        
        elif Curr_Stage == Stage.MAIN: 
            if detect_board.find_board(photo,Settings["Board"])
                current = detect_board.transform_corners(photo, State.points)
                State.set_current_image(current)

                # Detect tickets/assignments

                # WAIT FOR Settings[General][image_interval] number of seconds,
                # Or for keyboard input if that's preferable
            save_pickle_files(objectFileNames, Curr_Stage, Settings, Classifier, Sections, State)
        
        elif Curr_Stage == Stage.QUIT:
            save_pickle_files(objectFileNames, Curr_Stage, Settings, Classifier, Sections, State)



#if __name__ == "__main__": main()

