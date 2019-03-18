from pymongo import MongoClient
from Enums import Msg_Level
from api_controller import *
import json
import logging
from copy import deepcopy

class Database(object):
    def __init__(self):
        self.api = load_api_controller()
        self.api.sync()

        self.client = MongoClient("mongodb://localhost:27017/")
        self.db = self.client["kanban-scan"]
        self.ticket_collection = self.db["tickets"]
        self.section_collection = self.db["sections"]

        self.data = {}

    def reset(self):
        self.api.sync()

        commands = 0
        for ticket in self.api.state["items"]:
            #if "is_deleted" not in ticket.keys() or not ticket["is_deleted"]:
                try:
                    ticket.delete()
                    commands += 1
                    if commands == 40:
                        self.api.commit()
                        commands = 0
                except:
                    logging.warning("Sync error with the Todoist API")

        commands = 0
        for section in self.api.state["projects"]:
            #if "is_deleted" not in section.keys() or not section["is_deleted"]:
                try:
                    section.delete()
                    commands += 1
                    if commands == 40:
                        self.api.commit()
                        commands = 0
                except:
                    logging.warning("Sync error with the Todoist API")

        try: 
            self.api.commit()
        except:
            logging.warning("Sync error with the Todoist API")

        self.ticket_collection.drop()
        self.section_collection.drop()

    def init_ticket_collection(self, ticket_file, settings_id):
        project_id = create_project(self.api, "database", -2)
        self.section_collection.insert_one({"name" : "database", "rest_id" : project_id})

        with open(ticket_file) as tickets:
            ticket_data = json.load(tickets)[settings_id]
            self.data["Tickets"] = deepcopy(ticket_data)

            rest_mapping = create_items(self.api, ticket_data, project_id)
            for ticket_num, ticket in self.data["Tickets"].items():
                
                self.data["Tickets"][ticket_num]["history"] = ""
                self.ticket_collection.insert_one({
                    "_id" : ticket_num,
                    "rest_id" : rest_mapping[ticket_num]["rest_id"],
                    "description" : ticket["description"],
                    "assignee" : "",
                    "current_section_name" : "database",
                    "history" : "",
                    "errors" : []
                })

    # The update will happend at the end of the removed ticket sequence in Board.py
    # or after the the tickets have been assigned  (near the ned)
    def update_ticket(self, ticket, ticket_data, section_name):

        section_rest_id = self.section_collection.find_one({"name" : section_name})["rest_id"]
    
        if ticket.num in ticket_data.keys():
            ticket_rest_id = self.ticket_collection.find_one({"_id" : ticket.num})["rest_id"]
            update_item(self.api, ticket, ticket_rest_id, section_rest_id)

            query = {"_id" : ticket.num}
            update = {
                "$set" : {
                    "description" : ticket.desc,
                    "assignee" : ticket.assignee_names,
                    "current_section_name" : section_name,
                    "history" : ticket_data[ticket.num]["history"],
                    "errors" : [err.name for err in ticket.errors]
                }
            }

            self.ticket_collection.update_one(query, update)

        self.api.commit()


    def init_section_collection(self, section_file, settings_id):
        project_id = create_project(self.api, "kanban-scan", -1)
        self.section_collection.insert_one({"name" : "kanban-scan", "rest_id" : project_id})

        with open(section_file) as section_data:
            section_data = json.load(section_data)[settings_id]
            self.data["Sections"] = deepcopy(section_data)

            rest_mapping = create_projects(self.api, section_data["map_string"])
            logging.debug(rest_mapping)
            for section_num, section_name in self.data["Sections"]["map_string"].items():
                self.section_collection.insert_one({
                    "_id" : section_num,
                    "rest_id" : rest_mapping[section_num],
                    "name" : section_name
                })
        
    # will only change the API
    # Will change the color based on the ticket limit
    def update_section(self, section):
        if section.function in (Function.TICKET, Function.FINAL):
            section_rest_id = self.section_collection.find_one({"name" : section.name})["rest_id"]
            update_project(self.api, section, section_rest_id)
            self.api.commit()



if __name__ == "__main__":
    database = Database()
    database.init_ticket_collection("../json/Tickets.json", "1")
    database.init_section_collection("../json/Sections.json", "1")

