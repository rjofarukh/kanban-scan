import numpy as np
from Enums import Function
import cv2
import logging

class Section(object):
    def __init__(self, mask, num, function=Function.NONE):
        self.mask = mask
        self.num = num
        self.name = num
        self.size = np.sum(np.array(self.mask))
        self.tickets = {}
        self.function = function
        self.parent_section = None

    def has_ticket(self, ticket):
        return ticket.num in self.tickets.keys()
    
    def tickets_in_section(self):
        return [x.num for x in self.tickets]

    def add_ticket(self, ticket):
        if self.has_ticket(ticket):
            return False
        else:
            self.tickets[ticket.num] = ticket
            return True

    def remove_ticket(self, ticket):
        del self.tickets[ticket.num]

    def set_name(self, name):
        self.name = name

    def set_function(self, function):
        self.function = function

    def set_parent_sec(self, section_num):
        self.parent_section = section_num

    def __str__(self):
        ticket_nums = self.tickets_in_section()
        
        return f"""\
Section Number {self.num}
  Name : {self.name}
  Function : {self.function.name}
  Parent Section : {self.parent_section}
  Tickets : {ticket_nums}
"""



