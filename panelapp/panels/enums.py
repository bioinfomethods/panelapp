from enum import Enum


class GeneDataType(Enum):
    CLASS = 0
    LONG = 1
    SHORT = 2
    COLOR = 3


class GeneStatus(Enum):
    NOLIST = 0
    RED = 1
    AMBER = 2
    GREEN = 3
