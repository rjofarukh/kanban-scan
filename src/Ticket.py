import numpy as np
import cv2
import logging
from Enums import Priority


class Ticket(object):
    def __init__(self, mask, num, properties, priority=Priority.LOW):

        self.num = num
        self.desc = ""
        self.mask = mask

        self.area = properties[0]
        self.width = properties[1]
        self.height = properties[2]

        self.section = None
        self.asignee = None
        self.color = None
        self.priority = priority
    
    def set_section(self, section):
        self.section = section_num

    def set_asignee(self, asignee):
        self.asignee = asignee

    def set_priority(self, priority):
        self.priority = priority
    
    def set_color(self, color):
        self.color = color

    def set_number(self, number):
        self.num = number

    def ticket_belongs_to(self, sections):
        max_section_num = None
        max_intersection = 0 

        for num,section in sections.items(): 

            curr_intersection = cv2.bitwise_and(self.mask, section.mask)
            curr_intersection = np.sum(np.array(curr_intersection))

            if curr_intersection > max_intersection:
                max_section_num = num

        return max_section_num
    
    def num_belongs_to(self, sections):
        if self.section_num is None: 
            for num, section in sections:
                if section.has_ticket(self):
                    self.section_num = section.num
                    return section.num

            return None
        else: 
            return section_num

    def __str__(self):
        return f"""\
Ticket Number {self.num}
  Description : {self.desc}
  Asignee : {self.asignee}
  Priority : {self.priority}
  Section : {self.section}
  Color : {self.color}
"""
