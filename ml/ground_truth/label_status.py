
from enum import Enum
from typing import Optional


class LabelStatus(str, Enum):
    TP = "tp"
    FR = "fr"
    CWE_MISMATCH = "cwe_mismatch"
    NOT_A_TEST = "not_a_test"


