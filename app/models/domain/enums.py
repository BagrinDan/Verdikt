from enum import Enum


class Step(str, Enum):
    CODEQL = "codeql"
    SALIERI = "salieri"
    AMADEUS = "amadeus"


class EventStatus(str, Enum):        
    ACTIVE = "active"
    COMPLETED = "completed"
    ERROR = "error"


class StageStatus(str, Enum):      
    OK = "ok"
    ERROR = "error"
    SKIPPED = "skipped"
