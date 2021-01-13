# -*- coding: utf-8 -*-

import json
import boto3
import os
import uuid
import datetime
import time
import secrets
import base64
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
import model.file as my_file

MAX_UPLOAD_SIZE = 1024 * 1024 * 8 + 10000

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

def create_upload_url_event(event, context):
    if os.environ['EnvName'] != 'Prod':
        print(json.dumps(event))

    user_uuid: str = get_user_uuid_by_event(event)
    if not user_uuid:
        return create_common_return_array(401, {'message': 'session timeout'})
    
    params = json.loads(event['body'] or '{ }')
    if not params:
        return create_common_return_array(406, {'message': 'Insufficient input'})
    
    file_name: str = params['params'].get('fileName', '')
    file_size: int = int(params['params'].get('fileSize', 0))

    if not file_name or not file_size or file_size <= 0:
        return create_common_return_array(406, {'message': 'Insufficient input'})

    if file_size >= MAX_UPLOAD_SIZE:
        return create_common_return_array(403, {'message': 'The upper limit is 8MB'})

    key, url = my_s3.create_put_url_and_record(user_uuid, file_name, file_size)
    if not key or not url:
        return create_common_return_array(500, {'message': 'Failed to create upload url.'})
    
    return create_common_return_array(200, {'url': url, 'key': key})

def get_file_event(event, context):
    if os.environ['EnvName'] != 'Prod':
        print(json.dumps(event))

    file_key = event.get('queryStringParameters', {}).get('file_key', '')

    if not file_key:
        return create_common_return_array(406, {'message': "Insufficient input"})

    # ファイルの情報を取得
    file_info = my_file.get_file(file_key)
    if file_info is None:
        return create_common_return_array(404, {'message': "Not Found"})
    if file_info == False:
        return create_common_return_array(500, {'message': "Failed to get file info"})
    
    user_uuid: str = get_user_uuid_by_event(event)
    user_id = ''
    if user_uuid:
        user_data = get_user_data_by_uuid(user_uuid)
        if user_data:
            user_id = user_data['user_id']

    if not my_file.get_file_shareing_auth(file_info['file_key'], file_info['user_uuid'], user_uuid, user_id):
        print('no authentication: ' + str(file_key) + ' user_uuid:' + user_uuid)
        return create_common_return_array(404, {'message': "Not Found"})

    # 権限があったのでファイルを取得
    obj, mime_type = my_s3.get_file(file_info)
    if obj is None:
        return create_common_return_array(404, {'message': "Not Found"})
    if obj == False:
        return create_common_return_array(500, {'message': "Failed to get file"})

    if my_file.check_is_binary(mime_type):
        return {
            "statusCode": 200,
            "headers": create_header_with_mime_type(mime_type),
            "body": base64.b64encode(obj),
            'isBase64Encoded': True
        }
    else:
        return {
            "statusCode": 200,
            "headers": create_header_with_mime_type(mime_type),
            "body": obj,
            'isBase64Encoded': False,
        }
