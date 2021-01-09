import json
import boto3
import os
import uuid
import datetime
import time
from enum import Enum

class Plans(Enum):
    FREE = 1
    PAYMENT = 1000
    TEAM = 10000

def get_memo_body_max_len(plan: int):
    if plan == Plans.FREE.value:
        return 10000
    elif plan >= Plans.PAYMENT.value:
        return 100000
    elif plan >= Plans.TEAM.value:
        return 100000
    else:
        return 10000











