import re
import cv2
import os
import logging

    # STAGE = None
    # SETTINGS = []
    # CLASSIFIER = None
    # SECTIONS = {}
    # BACKGROUND = []
    # CURR_IMAGE = []
    # PREV_IMAGE = []
    # BOARD_POINTS = []
class Board(object):
    def __init__(self, dir_name):
        self.photos = os.listdir(dir_name)
        self.curr_index = 0

        self.current_image = None
        self.previous_image = None
        self.background_image = None
        self.points = None

    def next_photo(self):
        if curr_index < len(photos):
            logging.info("LOADING PHOTO \"{}\" ({}/{})".format(self.photos[curr_index],curr_index+1, len(photos)))
            self.curr_photo = cv2.imread(self.photos[curr_index])
            self.curr_index += 1
            return curr_photo
        else:
            logging.info("REACHED THE END OF THE CURRENT DEMO")
            return None

    def set_background_image(self, image):
        self.background_image = image
    
    def set_current_image(self, image):
        self.previous_image = current_image
        self.current_image = image

    def set_points(self, points):
        self.points = points


class SmartphonePhoto(object):
    def __init__(self, photoFile):
        self.photo = photoFile

        with open(photoFile) as inFile:
            self.filename = inFile.readline()
            inFile.close()
        groups = re.match(r'(.*)IMG-(?P<year>....)-(?P<month>.*)-(?P<day>.*) (?P<hours>.*)h(?P<minutes>.*)m(?P<seconds>.*)s_(?P<battery>.*)%.jpg', self.filename)
        
        try:
            self.year = int(groups.group("year"))
            self.month = int(groups.group("month"))
            self.day = int(groups.group("day"))

            self.hours = int(groups.group("hours"))
            self.minutes = int(groups.group("minutes"))
            self.seconds = int(groups.group("seconds"))

            self.battery = int(groups.group("battery"))
        
        except (AttributeError, ValueError):
            logger.critical("The format of the screenshot name file is incorrect. Please reconfigure.")

    def __str__(self):
        return  f"Year:    {self.year}\n" \
                f"Month:   {self.month}\n" \
                f"Day:     {self.day}\n" \
                f"Hours:   {self.hours}\n" \
                f"Minutes: {self.minutes}\n" \
                f"Seconds: {self.seconds}\n" \
                f"Battery: {self.battery}"


        