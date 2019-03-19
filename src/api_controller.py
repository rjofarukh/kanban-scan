from todoist.api import TodoistAPI
from Enums import Function, Msg_Level
import logging
import time


def create_projects(api, section_data):
    logging.info("API - Loading projects into Todoist")
    api.sync()
    for section_num, section_name in section_data.items():
        if not "limit" in section_name and not "none" in section_name:
            project = api.projects.add(f"{section_name}")
            project.update(item_order=int(section_num), indent=2, color=4)
        else:
            section_data[section_num] = ""
    api.commit()

    for section in api.state["projects"]:
        if section["name"] != "Inbox":
            section_num = str(section["item_order"])
            section_data[section_num] = section["id"]

    return section_data

def create_project(api, name, order):
    project = api.projects.add(name)
    project.update(item_order=order, indent=1, color=10)

    response = api.commit()
    return response["projects"][0]["id"]

def update_project(api, section, section_rest_id):
    api_section = api.projects.get_by_id(section_rest_id)
    color = api_section["color"]
    if len(section.tickets) > section.limit and color != 8:
        api_section.update(color=8)
    elif len(section.tickets) == section.limit and color != 3:
        api_section.update(color=3)
    elif color != 4:
        api_section.update(color=4)
    else:
        return

    api.commit()

def create_items(api, ticket_data, project_id):
    logging.info("API - Loading tickets into Todoist")
    for ticket_num, ticket in ticket_data.items():
        api.items.add(f"""{ticket_num} - {ticket["description"]}""", project_id)

    response = api.commit()

    api.sync()
    for ticket in api.state["items"]:
        ticket_num = ticket["content"].split("-")[0].strip()
        ticket_data[ticket_num]["rest_id"] = ticket["id"]
    
    return ticket_data

def update_item(api, ticket, ticket_rest_id, section_rest_id):
    api.sync()

    priority = 1
    if Msg_Level.TICKET_REGEX in ticket.errors:
        priority = 4
    elif Msg_Level.ASSIGNEE_MULTIPLE in ticket.errors:
        priority = 3
    
    api_ticket = api.items.get_by_id(ticket_rest_id)
    api_ticket.update(content=f"""{ticket.num} - {ticket.desc} {ticket.assignee_names}""", priority=priority)
    api_ticket.move(section_rest_id)

def load_api_controller(token):
    logging.info("API - Loading Todoist API")
    api = TodoistAPI(token)
    api.sync()

    return api
