from enum import Enum


class RefreshPolicy(Enum):
    ADD = "add"
    DELETE = "delete"
    UPDATE = "update"
    UPSERT = "upsert"
    REPLACE = "replace"
