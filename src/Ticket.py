import numpy as np
import cv2
import logging
from Enums import Priority, Msg_Level


class Ticket(object):
    def __init__(self, mask, num, properties, desc=""):
        self.num = num
        self.desc = ""
        self.mask = mask

        self.area = properties[0]
        self.width = properties[1]
        self.height = properties[2]
        self.bounding_rect = properties[3]

        self.section_history = ""
        self.prev_section = ""
        self.assignee_names = []

        self.errors = []
        self.msg_str = []


    def add_error(self, error, msg):
        if error not in self.errors:
            self.errors.append(error)
        self.add_msg(msg)

    def add_msg(self, msg):
        self.msg_str.append(msg)

    def print_msgs(self):
        for msg in self.msg_str:
            if msg.startswith("INFO: "):
                logging.info(msg[len("INFO: "):])
            elif msg.startswith("ERROR: "):
                logging.error(msg[len("ERROR: "):])
            elif msg.startswith("WARNING: "):
                logging.warning(msg[len("WARNING: "):])


        self.msg_str = []
                

    def set_assignee(self, scanned_assignees):
        for assignee in self.assignee_names:
            if assignee not in scanned_assignees:
                self.assignee_names.remove(assignee)
                self.add_msg(f"INFO: ASSIGNEE - Ticket #{self.num} is NO LONGER assigned to \"{assignee}")

        for scanned_assignee in scanned_assignees:
            if scanned_assignee not in self.assignee_names:
                self.assignee_names.append(scanned_assignee)
                self.add_msg(f"INFO: ASSIGNEE - Ticket #{self.num} is now assigned to \"{scanned_assignee}\"")

        
        if len(self.assignee_names) > 1:
            self.add_error(Msg_Level.ASSIGNEE_MULTIPLE, f"WARNING: ASSIGNEE - Ticket #{self.num} has multiple assignees: {self.assignee_names}!")
        elif Msg_Level.ASSIGNEE_MULTIPLE in self.errors:
            self.errors.remove(Msg_Level.ASSIGNEE_MULTIPLE)


    def vertical(self):
        return self.height > self.width

    def horizontal(self):
        return not self.vertical()

    def belongs_to(self, sections):
        max_section_num = None
        max_intersection = 0 

        mask_sum = np.sum(np.array(self.mask))
        
        for num,section in sections.items(): 
            curr_intersection = cv2.bitwise_and(self.mask, section.mask)
            curr_intersection = np.sum(np.array(curr_intersection))

            if curr_intersection > max_intersection:
                certainty = curr_intersection / mask_sum
                max_intersection = curr_intersection
                max_section_num = num

        return max_section_num, int(float(certainty) * 100)
    
    def num_belongs_to(self, sections):
        belonging_sections = []
        for num, section in sections.items():
            if section.has_ticket(self):
                belonging_sections.append(section.num)
        return belonging_sections


    def __str__(self):
        error_names = [err.name for err in self.errors]
        return f"""
Ticket Number {self.num}
  Description : {self.desc}
  Assignees : {self.assignee_names}
  Errors : {error_names}
  Horizontal : {self.horizontal()}"""

    
class Assignee(object):
    def __init__(self, name, mask, bounding_rect):
        self.name = name
        self.mask = mask
        self.bounding_rect = bounding_rect
        self.ticket_num = None
        self.section_num = None
        self.certainty = None


    def assign_to_ticket(self, sections):
        max_ticket_num = None
        max_section_num = None
        max_intersection = 0 
        mask_sum = np.sum(np.array(self.mask))
        
        for section_num,section in sections.items(): 
            for ticket_num,ticket in section.tickets.items():
                curr_intersection = cv2.bitwise_and(self.mask, ticket.mask)
                curr_intersection = np.sum(np.array(curr_intersection))

                if curr_intersection > max_intersection:
                    max_intersection = curr_intersection
                    self.certainty = curr_intersection / mask_sum
                    self.ticket_num = ticket_num
                    self.section_num = section_num
        
        if self.ticket_num is None:        
            for section_num,section in sections.items(): 
                curr_intersection = cv2.bitwise_and(self.mask, section.mask)
                curr_intersection = np.sum(np.array(curr_intersection))

                if curr_intersection > max_intersection:
                    certainty = curr_intersection / mask_sum
                    max_intersection = curr_intersection
                    self.section_num = section_num

    def belonging_to_ticket_and_section(assignees, ticket_num, section_num):
        belonging = []

        for assignee in assignees:
            if assignee.ticket_num == ticket_num and assignee.section_num == section_num:
                belonging.append(assignee.name)

        return belonging