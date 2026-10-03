from dataclasses import dataclass
from enum import Enum


class EditOperationType(str, Enum):
    INSERT_BEFORE = "insert_before"
    INSERT_AFTER = "insert_after"
    REPLACE = "replace"
    DELETE = "delete"


@dataclass
class EditOperation:
    path: str
    target_id: str
    operation: EditOperationType
    text: str = ""