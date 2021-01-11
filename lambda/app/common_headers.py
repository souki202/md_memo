import json
import os
from decimal import Decimal

def decimal_default_proc(obj):
    if isinstance(obj, Decimal):
        return float(obj)
    raise TypeError

def get_allow_origin():
    return os.environ['AllowOrigin'][1:-1]

def create_common_header():
    return create_header_with_mime_type('application/json')

def create_header_with_mime_type(mime_type):
    return {
                'Access-Control-Allow-Credentials': 'true',
                'Access-Control-Allow-Origin': get_allow_origin(),
                'Access-Control-Allow-Headers': 'Origin, Authorization, Accept, Content-Type',
                'Content-Type': mime_type
            }

def create_common_return(code: int, body: str):
    return {
        "statusCode": code,
        "headers": create_common_header(),
        "body": body,
    }

def create_common_return_array(code: int, body):
    return {
        "statusCode": code,
        "headers": create_common_header(),
        "body": json.dumps(body, default=decimal_default_proc),
    }