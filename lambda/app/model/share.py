from enum import Enum

class ShareType(Enum):
    NO_SHARE = 1
    READONLY = 2
    EDITABLE = 4
    
class ShareScope(Enum):
    PUBLIC = 1
    SPECIFIC_USERS = 2