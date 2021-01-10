import json
import boto3
import os
import uuid
import datetime
import time
import secrets
from enum import Enum
from decimal import Decimal
from http.cookies import SimpleCookie
from boto3.dynamodb.conditions import Key
from common_headers import *
from model.auth import *
from my_common import *
from model.user import *
from model.memo import *
from model.plan import *
import service.s3 as my_s3

def upload_file_event(event, context):
    # 流石に長過ぎるのでコメントアウト
    # if os.environ['EnvName'] != 'Prod':
    #     print(json.dumps(event))
    user_uuid: str = get_user_uuid_by_event(event)
    if not user_uuid:
        return create_common_return_array(401, {'message': 'session timeout'})

    file_name = event.get('queryStringParameters', {}).get('fileName', '')
    file_key = my_s3.put_image(user_uuid, file_name, event['body'])

    if not file_key:
        create_common_return_array(401, {'message': "failed to upload"})
    
    return create_common_return_array(200, {'key': file_key})
