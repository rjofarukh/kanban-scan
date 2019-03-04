from enum import Enum, unique, auto

@unique
class Mode(Enum):
    DEMO = auto()
    TEST = auto()
    RELOAD = auto()

@unique
class Stage(Enum):
    INIT = auto()
    MAIN = auto()
    QUIT = auto()

@unique
class Function(Enum):
    TICKET = auto()
    LIMIT = auto()
    FINAL = auto()
    NONE = auto()

@unique
class Priority(Enum):
    LOW = auto()
    MEDUIM = auto()
    HIGH = auto()

class Msg_Level(Enum):
    TICKET_NUMBER_INVALID = 3
    TICKET_REGEX = 2
    ASSIGNEE_MULTIPLE = 1
    INFO = 0
