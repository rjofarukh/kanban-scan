import re
import cv2
import os
import logging
import utils
from Ticket import Assignee
from Enums import Function, Msg_Level
from PIL import ImageFont, ImageDraw, Image  

class Board(object):
    def __init__(self, dir_name):
        self.photos = sorted(os.listdir(dir_name))
        self.dir_name = dir_name

        self.curr_index = 0

        self.classifier = None
        self.api = None
        self.data = None

        self.ticket_collection = None
        self.section_collection = None


        self.curr_image = None
        self.prev_image = None
        self.background_image = None
        self.points = None

        self.colored_grid = 0
        self.threshold_grid = 0
        self.board_sections = 0
        self.board_extracted = 0

        self.unmapped_sections = 0


        logging.info(f"Running the board at directory \"{self.dir_name}\"")

    def next_photo(self):
        if self.curr_index < len(self.photos):
            logging.info("##### Loading photo \"{}\" ({}/{}) #####".format(self.photos[self.curr_index],self.curr_index+1, len(self.photos)))
            curr_photo = cv2.imread(f"{self.dir_name}/{self.photos[self.curr_index]}")
            self.curr_index += 1
            return curr_photo
        else:
            logging.info("##### Reached the end of the current sequence! #####")
            return None

    def set_background_image(self, image):
        logging.info(f"\"{self.photos[self.curr_index-1]}\" has become the background image")
        self.background_image = image
        self.set_curr_image(image)
    
    def set_curr_image(self, image):
        logging.info(f"\"{self.photos[self.curr_index-1]}\" has become the current photo")
        self.prev_image = self.curr_image
        self.curr_image = image

    def set_points(self, points):
        logging.info(f"Setting the points of the board")
        self.points = points

    def set_grids(self, colored, threshold):
        self.colored_grid = colored
        self.threshold_grid = threshold

    def draw_section_rectangles(self, sections):
        image = self.background_image.copy()

        COLOR = (30, 75, 60)
        for section_num, section in sections.items():
            x,y,w,h = section.bounding_rect
            cv2.rectangle(image, (x, y), (x + w, y + h), COLOR, 4)

            if section.function == Function.LIMIT:
                cv2.putText(image, f"{section.limit}", (x, y+70),cv2.FONT_HERSHEY_DUPLEX, 3, (0, 150, 90), 2)
            elif section.function != Function.NONE:
                cv2.putText(image, f"ID:{section.num}", (x, y+25),cv2.FONT_HERSHEY_DUPLEX, 1, COLOR, 1)
                cv2.putText(image, f"Name:{section.name}", (x, y+55),cv2.FONT_HERSHEY_DUPLEX, 1, COLOR, 1)
                cv2.putText(image, f"Func:{section.function.name}", (x, y+85),cv2.FONT_HERSHEY_DUPLEX, 1, COLOR, 1)
                cv2.putText(image, f"Limit:{section.limit}", (x, y+115),cv2.FONT_HERSHEY_DUPLEX, 1, COLOR, 1)

        return image

    def map_tickets_to_sections(self, added_tickets, removed_tickets, assignees, sections, ticket_data, section_data):
        ASSIGNEE_MULTIPLE_COLOR = (0, 160, 225) 
        ASSIGNEE_DUPLICATE_LINE_COLOR = (0, 175, 255)
        ASSIGNEE_NOT_ON_TICKET = (0, 0, 255)
        ASSIGNEE_COLOR = (230, 90, 10)

        TICKET_MOVED_LINE_COLOR = (50, 255, 50)
        TICKET_MOVED_COLOR = (30, 255, 30)
        TICKET_MOVED_ILLEGALLY_COLOR = (0, 0, 255)
        TICKET_REMOVED_COLOR = (0, 200, 225)
        TICKET_REMOVED_FROM_FINAL_COLOR = (70, 90, 70) 
        TICKET_DUPLICATE_COLOR = (0, 175, 255)
        TICKET_DUPLICATE_LINE_COLOR = (0, 175, 255)
        TICKET_NUMBER_INVALID_COLOR = (200, 0, 200)

        SECTION_LIMIT_REACHED_COLOR = (45, 195, 255)
        SECTION_LIMIT_SURPASSED_COLOR = (100, 100, 255)


        image = self.curr_image.copy()
        workflow = re.compile(section_data["regex"])
        moved_ticket_numbers = set(added_tickets.keys()) & set(removed_tickets.keys())

        for ticket_num, ticket in removed_tickets.items():
            x,y,w,h = ticket.bounding_rect
            
            previous_section, certainty = ticket.belongs_to(sections)
            sections[previous_section].remove_ticket(ticket)

            if sections[previous_section].function == Function.LIMIT or sections[previous_section].function == Function.NONE:
                continue

            if sections[previous_section].function == Function.FINAL and ticket_num not in added_tickets:
                if ticket_num in ticket_data.keys():
                    ticket_data[ticket_num]["history"] = ""
                cv2.rectangle(image, (x, y), (x + w, y + h), TICKET_REMOVED_FROM_FINAL_COLOR, 3)
                logging.info(f"TICKET - Ticket #{ticket.num} has been SUCCESSFULLY REMOVED from section \"{sections[previous_section].name}\" (ID:#{previous_section}, {certainty}%)")
            else:
                cv2.rectangle(image, (x, y), (x + w, y + h), TICKET_REMOVED_COLOR, 3)
                if ticket_num not in added_tickets:
                    logging.warning(f"TICKET - Ticket #{ticket_num} REMOVED from section \"{sections[previous_section].name}\" (ID:#{previous_section}, {certainty}%)")

            ticket.prev_section = sections[previous_section].name

        for ticket_num, ticket in added_tickets.items():
            x,y,w,h = ticket.bounding_rect

            section_num, certainty = ticket.belongs_to(sections)
            if sections[section_num].function == Function.LIMIT or sections[section_num].function == Function.NONE:
                continue

            duplicates = ticket.num_belongs_to(sections)

            for num in duplicates:
                x2,y2,w2,h2 = sections[num].tickets[ticket_num].bounding_rect
                cv2.rectangle(image, (x2, y2), (x2 + w2, y2 + h2), TICKET_DUPLICATE_COLOR, 3)
                cv2.line(image, (int(x + w/2), int(y + h/2)), (int(x2 + w2/2),int(y2 + h2/2)), TICKET_DUPLICATE_LINE_COLOR, 3)

                ticket.add_msg(f"WARNING: TICKET - Ticket #{ticket_num} already exists in section \"{sections[num].name}\" (ID:#{num})")
                ticket.add_msg(f"INFO: TICKET - Ticket #{ticket_num} NEW reference REMOVED from section \"{sections[section_num].name}\" (ID:#{section_num})")
                sections[section_num].remove_ticket(ticket)

            section_num, certainty = ticket.belongs_to(sections)
            if ticket_num in ticket_data.keys():
                if not (ticket_num in removed_tickets and removed_tickets[ticket_num].prev_section == section_num):
                    ticket_history = ticket_data[ticket_num]["history"] + str(sections[section_num].name) + "-"
                    ticket.desc = ticket_data[ticket_num]["description"]
            else: 
                ticket.add_error(Msg_Level.TICKET_NUMBER_INVALID, f"ERROR: TICKET - Ticket #{ticket_num} does not exist in the database!")
                
                ticket_history = ""
                # ticket_history = sections[section_num].name + "-"
                # ticket_data.update({ticket_num : {"description" : "", "history" : ""}})


            if workflow.fullmatch(ticket_history) is not None:
                ticket_data[ticket_num]["history"] = ticket_history
                ticket.section_history = ticket_history
                if ticket_num in removed_tickets:
                    x2,y2,w2,h2 = removed_tickets[ticket_num].bounding_rect
                    cv2.line(image, (int(x + w/2), int(y + h/2)), (int(x2 + w2/2),int(y2 + h2/2)), TICKET_MOVED_LINE_COLOR, 3)

                    previous_section = removed_tickets[ticket_num].prev_section

                    if previous_section != sections[section_num].name:
                        ticket.add_msg(f"INFO: TICKET - Ticket #{ticket_num} successfully MOVED from section \"{previous_section}\" to section \"{sections[section_num].name}\" (ID:#{section_num}, {certainty}%)")
                else:
                    ticket.add_msg(f"INFO: TICKET - Ticket #{ticket.num} has been ADDED to section \"{sections[section_num].name}\" (ID:#{section_num}, {certainty}%)")
            else:
                if ticket_num in removed_tickets:
                    x2,y2,w2,h2 = removed_tickets[ticket_num].bounding_rect
                    cv2.line(image, (int(x + w/2), int(y + h/2)), (int(x2 + w2/2),int(y2 + h2/2)), TICKET_MOVED_ILLEGALLY_COLOR, 3)
    
                    previous_section = removed_tickets[ticket_num].prev_section

                    ticket.add_error(Msg_Level.TICKET_REGEX, f"WARNING: TICKET - Ticket #{ticket_num} illegally MOVED from section \"{previous_section}\" to section \"{sections[section_num].name}\"  (ID:#{section_num}, {certainty}%)")
                else:
                    ticket.add_error(Msg_Level.TICKET_REGEX, f"WARNING: TICKET - Ticket #{ticket_num} illegally ADDED to section \"{sections[section_num].name}\" (ID:#{section_num}, {certainty}%)")


            if len(ticket.errors) == 0:
                cv2.rectangle(image, (x, y), (x + w, y + h), TICKET_MOVED_COLOR, 3)

            sections[section_num].add_ticket(ticket)


        for assignee in assignees:
            assignee.assign_to_ticket(sections)


        for section_num, section in sections.items():
            for ticket_num, ticket in section.tickets.items():
                ticket_assignees = Assignee.belonging_to_ticket_and_section(assignees, ticket_num, section_num)

                ticket.set_assignee(ticket_assignees)

                ticket.print_msgs()

                x,y,w,h = ticket.bounding_rect
                offset = 0

                for error in ticket.errors:
                    if error == Msg_Level.ASSIGNEE_MULTIPLE:
                        cv2.rectangle(image, (x - offset, y - offset), (x + w + offset, y + h + offset), ASSIGNEE_MULTIPLE_COLOR, 3)
                    elif error == Msg_Level.TICKET_REGEX:
                        cv2.rectangle(image, (x - offset, y - offset), (x + w + offset, y + h + offset), TICKET_MOVED_ILLEGALLY_COLOR, 3)
                    elif error == Msg_Level.TICKET_NUMBER_INVALID:
                        cv2.rectangle(image, (x - offset, y - offset), (x + w + offset, y + h + offset), TICKET_NUMBER_INVALID_COLOR, 3)
                    offset += 15


            if section.over_section_limit():
                x,y,w,h = section.bounding_rect
                cv2.rectangle(image, (x, y), (x + w, y + h), SECTION_LIMIT_SURPASSED_COLOR, 4)
                logging.warning(f"SECTION - The ticket limit of {section.limit} has been surpassed for section \"{section.name}\" (ID:#{section_num})")
            elif len(section.tickets) == section.limit:
                x,y,w,h = section.bounding_rect
                cv2.rectangle(image, (x, y), (x + w, y + h), SECTION_LIMIT_REACHED_COLOR, 4)
                logging.info(f"SECTION - The ticket limit of {section.limit} has been reached for section \"{section.name}\" (ID:#{section_num})")

        
        while len(assignees) > 0:
            a1 = assignees.pop(0)

            tl1, br1 = a1.bounding_rect

            if a1.ticket_num == None: 
                cv2.rectangle(image, (tl1[0], tl1[1]), (br1[0], br1[1]), ASSIGNEE_NOT_ON_TICKET, 3)
            else: 
                cv2.putText(image, f"{a1.name}", (int(tl1[0]), int(tl1[1]-10)),cv2.FONT_HERSHEY_DUPLEX, 1, ASSIGNEE_COLOR, 1)

                cv2.rectangle(image, (tl1[0], tl1[1]), (br1[0], br1[1]), ASSIGNEE_COLOR, 3)
                for a2 in assignees:
                    if a1.name == a2.name:
                        tl2, br2 = a2.bounding_rect

                        cv2.putText(image, f"{a2.name}", (int(tl2[0]), int(tl2[1]-10)),cv2.FONT_HERSHEY_DUPLEX, 1, ASSIGNEE_COLOR, 1)

                        cv2.rectangle(image, (tl2[0], tl2[1]), (br2[0], br2[1]), ASSIGNEE_COLOR, 3)

                        x1 = int((tl1[0] + br1[0]) // 2 )
                        x2 = int((tl2[0] + br2[0]) // 2 )

                        y1 = int((tl1[1] + br1[1]) // 2 )
                        y2 = int((tl2[1] + br2[1]) // 2 )

                        cv2.line(image, (x1, y1), (x2,y2), ASSIGNEE_DUPLICATE_LINE_COLOR, 3)
                        assignees.remove(a2)
        
        self.board_extracted = image
        self.colored_grid = utils.image_grid(self.curr_image, self.prev_image, self.board_extracted, self.board_sections)
