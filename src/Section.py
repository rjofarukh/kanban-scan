import numpy as np
from Enums import Function
import cv2
import logging

class Section(object):
    def __init__(self, mask, num, bounding_rect):

        self.num = num
        self.name = num
        self.function = Function.TICKET

        self.mask = mask
        self.size = np.sum(np.array(self.mask))
        self.bounding_rect = bounding_rect

        self.tickets = {}
        self.limit = -1

    def merge_section(self, section):
        self.mask = cv2.bitwise_or(self.mask, section.mask)
        self.size = np.sum(np.array(self.mask))
        
        for ticket_num, ticket in section.tickets:
            self.add_ticket(ticket)

    def has_ticket(self, ticket):
        return ticket.num in self.tickets.keys()
    
    def get_tickets_in_section(self):
        return [x.num for x in self.tickets]

    def add_ticket(self, ticket):
        if self.has_ticket(ticket):
            return False
        else:
            self.tickets[ticket.num] = ticket
            return True

    def remove_ticket(self, ticket):
        if self.has_ticket(ticket):
            del self.tickets[ticket.num]

    def set_name(self, name):
        self.name = name

    def set_function(self, function):
        if function == Function.NONE:
            self.mask = np.zeros_like(self.mask)

        self.function = function

    def set_limit(self, limit):
        if int(limit) <= 0:
            self.limit = 100
        else:
            self.limit = int(limit)

    def over_section_limit(self):
        if self.limit > 0 and self.function == Function.TICKET:
            return len(self.tickets) > self.limit
        else:
            return False

    def __str__(self):
        return f"""
Section Number {self.num}
  Name : {self.name}
  Function : {self.function.name}
  Limit : {self.limit}
  Tickets : {self.tickets.keys()}"""

    def map_section_names(sections, section_data):
        map_str = section_data["map_string"]
        sec_data_limit_keys = [ x.replace("_limit","") for x in section_data.keys() if "_limit" in x ]

        for section_num, section in sections.items():
            sec_name = map_str[section_num]

            limits_for_section = [key+"_limit" for key in sec_data_limit_keys if key in sec_name]

            if sec_name == "none":
                sections[section_num].set_function(Function.NONE)
                sections[section_num].set_name("")
            elif sec_name == "final":
                sections[section_num].set_name("final")
                sections[section_num].set_function(Function.FINAL)
                sections[section_num].set_limit(-1)
            elif "limit" in sec_name:
                limit_str = section_data[sec_name]

                sections[section_num].set_function(Function.LIMIT)
                # sections[section_num].set_name(limit_str)

                sections[section_num].set_name(sec_name)
                sections[section_num].set_limit(limit_str)

            elif len(limits_for_section) > 0:
                possible_limits = [int(section_data[x]) for x in limits_for_section]
                limit = max(possible_limits)

                sections[section_num].set_name(sec_name)
                sections[section_num].set_function(Function.TICKET)
                sections[section_num].set_limit(limit)
            else:
                sections[section_num].set_name(sec_name)
                sections[section_num].set_function(Function.TICKET)
                sections[section_num].set_limit(-1)

        return sections

    def tickets_on_board(sections):
        tickets = []
        for section in sections.values():
            tickets += section.tickets.values()

        return tickets
    
    def tickets_keys_on_board(sections):
        tickets = []
        for section in sections.values():
            tickets += section.tickets.keys()

        return tickets
    def get_ticket(num, sections):
        for section in sections.values():
            if num in section.tickets.keys():
                return section.tickets[num]


