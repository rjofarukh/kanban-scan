from detect_board import find_board, find_and_transform_board, transform_corners
from detect_tickets import find_assignees, find_limits, find_tickets
from db_controller import Database
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

def load_logging(logging_level):
    time = datetime.datetime.now().strftime("%H:%M:%S")

    logging.basicConfig(
        format='%(asctime)s - [%(levelname).4s] - %(message)s',
        datefmt="%m/%d/%Y %I:%M:%S",
        level=logging_level,
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

def load_settings(settings_file, settings_id):
    logging.info(f"Loading settings #{settings_id} from \"{settings_file}\"")
    with open(settings_file) as infile:
        settings = json.load(infile)
    return settings[settings_id]

def load_thresholds(settings_file):
    logging.info(f"""Loading thresholds from \"{settings_file["General"]["thresholds_file"]}\"""")
    utils.setup_thresholds(settings_file["General"]["thresholds_file"])

def save_pickle_files(object_file_names, *objects):
    if len(objects) != len(object_file_names):
        logging.error("Number of names supplied for pickling is different "\
                      "from the number of labels for them!")
    else:
        logging.info("Saving pickle files..")
        for i in range(len(objects)):
            logging.info(f"  ../pkl/{object_file_names[i]}.pkl")
            with open("../pkl/%s.pkl" % object_file_names[i], "wb") as outFile:
                pickle.dump(objects[i], outFile)
        logging.info("Saved pickle files!")
    
def load_from_pickle_files(object_file_names):
    objects = []
    if len(object_file_names) <= len(os.listdir("../pkl")):
        logging.info("Loading pickle files..")
        for i in range(len(object_file_names)):
            logging.info(f"  ../pkl/{object_file_names[i]}.pkl")
            with open(f"../pkl/{object_file_names[i]}.pkl", "rb") as inFile:
                objects.append(pickle.load(inFile))
        logging.info("Loaded pickle files!")
    else:
        logging.error("Number of objects in directory is different from "\
                      "the number of objects supplied!")
    return objects
    
def demo(logging_level, photo_folder="", demo_id="", load_pkls=False):
    load_logging(logging_level)
    object_file_names = ["settings", "sections", "board"]

    stage = None
    settings = []
    sections = {}
    database = None
    board = None

    if load_pkls:
        stage = Stage.MAIN
        settings, sections, board = load_from_pickle_files(object_file_names)
        database = Database(settings["General"]["token"])
    else:
        stage = Stage.INIT
        settings = load_settings("../json/settings.json", demo_id)
        board = Board(photo_folder)
        board.classifier = load_classifiers(settings["Tickets"]["Digits"]["recognition_alg"])

        database = Database(settings["General"]["token"])
        database.reset()
        database.init_ticket_collection(settings["General"]["ticket_file"], demo_id)
        database.init_section_collection(settings["General"]["section_file"], demo_id)
        board.data = database.data

    
    load_thresholds(settings)
    photo = board.next_photo()

    while photo is not None:
        if stage == Stage.INIT and find_board(photo, settings["Board"]):
            background_image, sections, points = find_and_transform_board(photo, sections, settings["Board"])

            board.set_background_image(background_image)
            board.set_points(points)

            board.unmapped_sections = board.draw_section_rectangles(sections)
            sections = Section.map_section_names(sections, board.data["Sections"])
            board.board_sections = board.draw_section_rectangles(sections)

            stage = Stage.MAIN

        elif stage == Stage.MAIN and find_board(photo, settings["Board"]):
            board.set_curr_image(transform_corners(photo, board.points))
            added_tickets, removed_tickets = find_tickets(board, settings["Tickets"], board.data["Tickets"])
            
            assignees = find_assignees(board)
            
            find_limits(board, sections, settings["Tickets"], board.data["Sections"])

            board.map_tickets_to_sections(added_tickets, removed_tickets, assignees, sections, database)

            save_view(sections, board)
            interface(object_file_names, settings, sections, board, demo_id)
            

        photo = board.next_photo()
    
    sys.exit()
        
def save_view(sections, board):
    from terminaltables import AsciiTable

    cv2.imwrite("../live_view/changes_grid.jpg", board.colored_grid)
    cv2.imwrite("../live_view/thresholds_grid.jpg", board.threshold_grid)
    cv2.imwrite("../live_view/mapped_sections.jpg", board.board_sections)
    cv2.imwrite("../live_view/unmapped_sections.jpg", board.unmapped_sections)


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
        b.write(f"\n\nDemo folder: {board.dir_name}\n")
        b.write("Saved files:\n")
        b.write("  ../live_view/changes_grid.jpg\n")
        b.write("  ../live_view/thresholds_grid.jpg\n")
        b.write("  ../live_view/mapped_sections.jpg\n")
        b.write("  ../live_view/unmapped_sections.jpg\n")
        

def interface(object_file_names, settings, sections, board, demo_id):

    while True:
        cmd = input("\n[t][s][q][enter]=> ")

        if cmd == "t":
            tickets = Section.tickets_keys_on_board(sections)
            print(f"Tickets: {tickets}")
            if len(tickets) > 0:
                cmd = input("Choose a ticket=> ")
                while cmd not in tickets:
                    cmd = input("Not a valid number. Choose again=> ")
                print(Section.get_ticket(cmd, sections))
        elif cmd == "s":
            print(f"Sections: {sections.keys()}")
            if len(sections.keys()) > 0:
                cmd = input("Choose a section=> ")
                while cmd not in sections.keys():
                    cmd = input("Not a valid number. Choose again=> ")
                print(sections[cmd])
        elif cmd == "q":
            board.ticket_collection = None
            board.section_collection = None
            save_pickle_files(object_file_names, settings, sections, board)
            logging.warning("Exiting program!")
            sys.exit()
        else:
            return
        
        cmd = ""

def main():
    args = load_parsers()

    if args.test is not None:
        demo(logging.DEBUG, photo_folder=args.folder, demo_id=args.test[0])
    elif args.demo is not None:
        demo(logging.INFO, photo_folder=args.folder, demo_id=args.demo[0])
    elif args.reload:
        demo(logging.INFO, load_pkls=True)


if __name__ == "__main__": main()

