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
from Enums import Stage, Mode, Function
from Board import Board
from Section import Section

from sklearn.externals import joblib
from keras.models import load_model

def load_parsers():
    parser = argparse.ArgumentParser()

    parser.add_argument("--folder", help="Folder containing the photos for scanning (mandatory)", action="store")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--demo", help="Demo number - important for settings.json (logger.INFO)", action='store')
    mode.add_argument("--test", nargs=1, help="Run specific test file (logger.DEBUG)", action="store")
    mode.add_argument("--reload", help="Reload from the last session (if it exists and hasn't ended)", action='store_true')

    args = parser.parse_args()
    return args

def load_logging(loggingLevel):
    time = datetime.datetime.now().strftime("%H:%M:%S")

    logging.basicConfig(
        format='%(asctime)s - [%(levelname).4s] - %(message)s',
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

    
def demo(logging_level, photo_folder="", demo_id="", load_pkls=False):
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
        State = Board(photo_folder)
        Data = load_tic_sec_info(demo_id)
    
    load_thresholds(Settings)
    photo = State.next_photo()

    while photo is not None:
        if Curr_Stage == Stage.INIT and detect_board.find_board(photo, Settings["Board"]):
            background_image, Sections, points = detect_board.find_and_transform_board(photo, Sections, Settings["Board"])

            State.set_background_image(background_image)
            State.set_points(points)

            State.unmapped_sections = State.draw_section_rectangles(Sections)
            Sections = Section.map_section_names(Sections, Data["Sections"])
            State.board_sections = State.draw_section_rectangles(Sections)

            Curr_Stage = Stage.MAIN

        elif Curr_Stage == Stage.MAIN and detect_board.find_board(photo, Settings["Board"]):
            State.set_curr_image(detect_board.transform_corners(photo, State.points))
            added_tickets, removed_tickets = detect_tickets.find_tickets(State, Classifier, Settings["Tickets"], Data["Tickets"])
            
            assignees = detect_tickets.find_assignees_in_image(State)
            
            detect_tickets.find_limits(State, Sections, Settings["Tickets"], Classifier, Data["Sections"])

            State.map_tickets_to_sections(added_tickets, removed_tickets, assignees, Sections, Data["Tickets"], Data["Sections"])

            save_view(Sections, State)
            interface(object_file_names, Curr_Stage, Settings, Classifier, Sections, State, Data, demo_id)
            

        photo = State.next_photo()
    
    sys.exit()
        
def save_view(sections, State):
    from terminaltables import AsciiTable

    cv2.imwrite("../live_view/changes_grid.jpg", State.colored_grid)
    cv2.imwrite("../live_view/thresholds_grid.jpg", State.threshold_grid)
    cv2.imwrite("../live_view/mapped_sections.jpg", State.board_sections)
    cv2.imwrite("../live_view/unmapped_sections.jpg", State.unmapped_sections)


    table_data = [["ID", "Function", "Name", "Limit", "Tickets"]]
    for section_num, section in sections.items():
        if section.function != Function.NONE:
            curr = []
            curr.append(section_num)
            curr.append(section.function.name)

            curr.append(section.name)
            
            if section.function == Function.TICKET or section.function == Function.FINAL:
                curr.append(section.limit)
            else:
                curr.append("-")
            
            ticket_str = ""
            for ticket_num, ticket in section.tickets.items():
                ticket_str += f"{ticket_num} : {ticket.desc[:30]} ({ticket.assignee_names})\n"
            curr.append(ticket_str)

            table_data.append(curr)
    
    table = AsciiTable(table_data)
    table.inner_row_border = True

    with open("../live_view/board.txt", "w+") as b:
        b.write(table.table)
        b.write(f"\n\nDemo folder: {State.dir_name}\n")
        b.write("Saved files:\n")
        b.write("  ../live_view/changes_grid.jpg\n")
        b.write("  ../live_view/thresholds_grid.jpg\n")
        b.write("  ../live_view/mapped_sections.jpg\n")
        b.write("  ../live_view/unmapped_sections.jpg\n")
        

def interface(object_file_names, Curr_Stage, Settings, Classifier, Sections, State, Data, demo_id):
    # print("")
    # print("  View:")
    # print("    [t]ickets")
    # print("    [s]ections")
    # print("  [q]uit and save pickles")
    # print("  (ENTER) continue")

    while True:
        cmd = input("\n[t][s][q][enter]=> ")

        if cmd == "t":
            tickets = Section.tickets_keys_on_board(Sections)
            print(f"Tickets: {tickets}")
            if len(tickets) > 0:
                cmd = input("Choose a ticket=> ")
                while cmd not in tickets:
                    cmd = input("Not a valid number. Choose again=> ")
                print(Section.get_ticket(cmd, Sections))
        elif cmd == "s":
            print(f"Sections: {Sections.keys()}")
            if len(Sessions.keys()) > 0:
                cmd = input("Choose a section=> ")
                while cmd not in Sections.keys():
                    cmd = input("Not a valid number. Choose again=> ")
                print(Sections[cmd])
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
        demo(logging.DEBUG, photo_folder=args.folder, demo_id=args.test[0])
    elif args.demo is not None:
        demo(logging.INFO, photo_folder=args.folder, demo_id=args.demo[0])
    elif args.reload:
        demo(logging.INFO, load_pkls=True)


if __name__ == "__main__": main()

