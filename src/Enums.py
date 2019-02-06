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
    NUMBER = auto()
    FINAL = auto()
    NONE = auto()

@unique
class Priority(Enum):
    LOW = auto()
    MEDUIM = auto()
    HIGH = auto()
