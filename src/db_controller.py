from pymongo import MongoClient
from Enums import Msg_Level
from api_controller import *
import json
import logging
from copy import deepcopy

class Database(object):
    def __init__(self, token):
        self.api = load_api_controller(token)
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
            try:
                section.delete()
                commands += 1
                if commands == 40:
                    self.api.commit()
                    commands = 0
            except:
                logging.warning("Sync error with the Todoist API")

        try: 
            logging.info("API - Removing tickets and sections from Todoist")
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

    def update_ticket(self, ticket, ticket_data, section_name):
        self.api.sync()
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

            for section_num, section_name in self.data["Sections"]["map_string"].items():
                self.section_collection.insert_one({
                    "_id" : section_num,
                    "rest_id" : rest_mapping[section_num],
                    "name" : section_name
                })


    def update_section(self, section):
        if section.function in (Function.TICKET, Function.FINAL):
            section_rest_id = self.section_collection.find_one({"name" : section.name})["rest_id"]
            update_project(self.api, section, section_rest_id)
            self.api.commit()


