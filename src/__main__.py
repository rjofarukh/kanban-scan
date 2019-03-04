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
from Section import Section

from sklearn.externals import joblib
from keras.models import load_model

def load_parsers():
    parser = argparse.ArgumentParser()

    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--demo", help="Demo number - important for settings.json (logger.INFO)", action='store')
    mode.add_argument("--test", nargs=1, help="Run specific test file (logger.DEBUG)", action="store")
    mode.add_argument("--reload", help="Reload from the last session (if it exists and hasn't ended)", action='store_true')

    args = parser.parse_args()
    return args

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

def load_classifiers(recognition_alg):
    if recognition_alg == "cnn":
        cnn_file = "../classifiers/mnist_keras_cnn_model.h5"
        cnn = load_model(cnn_file)
        return cnn
    else:
        svm_file = "../classifiers/mnist_keras_svm_model.pkl"
        svm = joblib.load(svm_file)
        return svm

def load_settings(settingsFile, settingsID):
    logging.info(f"Loading settings #{settingsID} from \"{settingsFile}\"")
    with open(settingsFile) as infile:
        settings = json.load(infile)
    # utils.setup_thresholds(settings[settingsID]["General"]["thresholds_file"])
    return settings[settingsID]

def load_thresholds(settingsFile):
    logging.info(f"""Loading thresholds from \"{settingsFile["General"]["thresholds_file"]}\"""")
    utils.setup_thresholds(settingsFile["General"]["thresholds_file"])

def save_pickle_files(objFileNames, *objects):
    if len(objects) != len(objFileNames):
        logging.error("Number of names supplied for pickling is different "\
                      "from the number of labels for them!")
    else:
        logging.info("Saving pickle files..")
        for i in range(len(objects)):
            logging.info(f"  ../pkl/{objFileNames[i]}.pkl")
            with open("../pkl/%s.pkl" % objFileNames[i], "wb") as outFile:
                pickle.dump(objects[i], outFile)
        logging.info("Saved pickle files!")
    
def load_from_pickle_files(objFileNames):
    objects = []
    if len(objFileNames) == len(os.listdir("../pkl")):
        logging.info("Loading pickle files..")
        for i in range(len(objFileNames)):
            logging.info(f"  ../pkl/{objFileNames[i]}.pkl")
            with open("../pkl/%s.pkl" % objFileNames[i], "rb") as inFile:
                objects.append(pickle.load(inFile))
        logging.info("Loaded pickle files!")
    else:
        logging.error("Number of objects in directory is different from "\
                      "the number of objects supplied!")
    return objects

def load_tic_sec_info(settingsID):
    data = {}
    logging.info(f"Loading ticket and section JSON files (DEMO #{settingsID})")
    with open("../json/Tickets.json") as tickets:
        tickets = json.load(tickets)
    with open("../json/Sections.json") as sections:
        sections = json.load(sections)

    data["Tickets"] = tickets[settingsID]
    data["Sections"] = sections[settingsID]
    return data

    
def demo(logging_level, demo_id, load_pkls=False):
    load_logging(logging_level)
    object_file_names = ["stage", "settings", "classifier", "sections", "state", "data"]

    Curr_Stage = Stage.INIT
    Settings = []
    Classifier = None
    Sections = {}
    State = None
    Data = []

    if load_pkls:
        Curr_Stage, Settings, Classifier, Sections, State, Data = load_from_pickle_files(object_file_names)
    else:
        Settings = load_settings("../json/settings.json", demo_id)
        Classifier = load_classifiers(Settings["Tickets"]["Digits"]["recognition_alg"])
        State = Board(Settings["General"]["photo_folder"])
        Data = load_tic_sec_info(demo_id)
    
    load_thresholds(Settings)
    photo = State.next_photo()

    while photo is not None:
        if Curr_Stage == Stage.INIT and detect_board.find_board(photo, Settings["Board"]):
            background_image, Sections, points = detect_board.find_and_transform_board(photo, Sections, Settings["Board"])
            Sections = Section.map_section_names(Sections, Data["Sections"])

            State.set_background_image(background_image)
            State.set_points(points)
            State.draw_section_rectangles(Sections)

            save_pickle_files(object_file_names, Curr_Stage, Settings, Classifier, Sections, State, Data)

            Curr_Stage = Stage.MAIN

        elif Curr_Stage == Stage.MAIN and detect_board.find_board(photo, Settings["Board"]):
            State.set_curr_image(detect_board.transform_corners(photo, State.points))
            added_tickets, removed_tickets = detect_tickets.find_tickets(State, Classifier, Settings["Tickets"], Data["Tickets"])
            
            assignees = detect_tickets.find_assignees_in_image(State)
            
            State.map_tickets_to_sections(added_tickets, removed_tickets, assignees, Sections, Data["Tickets"], Data["Sections"])
            interface(object_file_names, Curr_Stage, Settings, Classifier, Sections, State, Data)

        photo = State.next_photo()
    
    sys.exit()
        
def interface(object_file_names, Curr_Stage, Settings, Classifier, Sections, State, Data):
    print("")
    print("  View:")
    print("    [t]ickets")
    print("    [s]ections")
    print("    [co]lored grid")
    print("    [th]reshold grid")
    print("    [cu]rrent image")
    print("    [pr]evious image")
    print("    [bo]rder")
    print("  [r]eload ticket data")
    print("  [q]uit and save pickles")
    print("  (ENTER) continue")

    while True:
        cmd = input("=> ")

        if cmd == "t":
            tickets = Section.tickets_keys_on_board(Sections)
            print(f"Tickets: {tickets}")
            cmd = input("Choose a ticket: ")
            while cmd not in tickets:
                cmd = input("Not a valid number. Choose again: ")
            print(Section.get_ticket(cmd, Sections))
        elif cmd == "s":
            print(f"Sections: {Sections.keys()}")
            cmd = input("Choose a section: ")
            while cmd not in Sections.keys():
                cmd = input("Not a valid number. Choose again: ")
            print(Sections[cmd])
        elif cmd == "co":
            color = utils.image_grid(State.curr_image, State.prev_image, State.board_sections, State.board_extracted)
            utils.show_images(color, name="Colored Grid", scale=5)
        elif cmd == "th":
            utils.show_images(State.threshold_grid, name="Threshold Grid", scale=5)
        elif cmd == "cu":
            utils.show_images(State.curr_image, name="Current Image", scale=3)
        elif cmd == "pr":
            utils.show_images(State.prev_image, name="Previous Image", scale=3)
        elif cmd == "bo":
            utils.show_images(State.board_sections, name="Border Image", scale=3)
        elif cmd == "r":
            return
        elif cmd == "q":
            save_pickle_files(object_file_names, Curr_Stage, Settings, Classifier, Sections, State, Data)
            logging.warning("Exiting program!")
            sys.exit()
        else:
            return
        
        cmd = ""


###############################################



def main():
    args = load_parsers()

    if args.test is not None:
        demo(logging.DEBUG, args.test[0])
    elif args.demo is not None:
        demo(logging.INFO, args.demo[0])
    elif args.reload:
        demo(logging.INFO, "", load_pkls=True)


if __name__ == "__main__": main()

