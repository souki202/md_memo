import json
import boto3
import os
import uuid
import datetime
import time
import secrets
import base64
import re
from enum import Enum
from decimal import Decimal
from http.cookies import SimpleCookie
from boto3.dynamodb.conditions import Key
from common_headers import *
import model.file as my_file

s3 = boto3.resource('s3')
strageBucket = s3.Bucket('md-memo-strage' + os.environ['FileStrageBucketSuffix'])
FILES_KEY = 'files'
MEMOS_KEY = 'memos'

'''
base64で送られてきた画像を保存する

@return {str} 作成したファイル名
'''
def put_image(user_uuid, file_name, base64body) -> str:
    ext = ''
    if file_name:
        ext = os.path.splitext(file_name)[1]

    new_file_name = secrets.token_urlsafe(64)

    imageBody = base64.b64decode(base64body)
    new_file_name = re.sub("[^\w\-*().]", '_', new_file_name)
    key = user_uuid + '/' + FILES_KEY + '/' + new_file_name + ext
    
    try:
        res = strageBucket.put_object(
            Body = imageBody,
            Key = key
        )
        if not res:
            raise 'failed to upload'
        if not my_file.add_file(new_file_name, user_uuid, len(imageBody)):
            raise 'failed to add record'
        return new_file_name
    except Exception as e:
        print(e)
        return None
    return None
