import json
import boto3
import os
import uuid
import datetime
import time
import secrets
import base64
import re
import mimetypes
from enum import Enum
from boto3.dynamodb.conditions import Key
from botocore.config import Config
from common_headers import *
from my_common import *
import model.file as my_file

s3_resource = boto3.resource('s3')
s3_client = boto3.client('s3', config=Config(signature_version='s3v4'))
FILE_BUCKET_NAME = 'md-memo-storage' + os.environ['FileStorageBucketSuffix']
storageBucket = s3_resource.Bucket(FILE_BUCKET_NAME)
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
        res = storageBucket.put_object(
            Body = imageBody,
            Key = key
        )
        if not res:
            raise 'failed to upload'
        if not my_file.add_file(new_file_name, user_uuid, len(imageBody), ext):
            raise 'failed to add record'
        return new_file_name
    except Exception as e:
        print(e)
        return None
    return None

'''
base64で送られてきた画像を保存する

@return {str, str} 作成したファイル名(key), url
'''
def create_put_url_and_record(user_uuid, file_name, file_size):
    ext = ''
    if file_name:
        ext = os.path.splitext(file_name)[1]

    # ファイルの置き場所のキーを作成
    new_file_name = secrets.token_urlsafe(64)
    new_file_name = re.sub("[^\w\-*().]", '_', new_file_name)
    key = user_uuid + '/' + FILES_KEY + '/' + new_file_name + ext

    # mime_typeを取得
    mime_type = 'text/plain'
    if ext:
        mime_type = mimetypes.guess_type(new_file_name + ext)[0]

    try:
        signed_url = s3_client.generate_presigned_url(
            ClientMethod = 'put_object',
            Params = {
                'Bucket': FILE_BUCKET_NAME,
                'Key': key,
                'ContentType': mime_type
            },
            ExpiresIn = 10,
            HttpMethod = 'PUT',
        )
        if not my_file.add_file(new_file_name, user_uuid, file_size, ext):
            raise 'failed to add record'
        return new_file_name, signed_url
    except Exception as e:
        print(e)
        return False

'''
ファイルを読み込んでバイナリとmime_typeを返す
'''
def get_file(file_info):
    if not file_info:
        return False, None

    ext = file_info['ext']
    key = file_info['user_uuid'] + '/' + FILES_KEY + '/' + file_info['file_key'] + ext
    try:
        obj = s3_client.get_object(Bucket=FILE_BUCKET_NAME, Key=key)
        body = obj['Body'].read()
        mime_type = 'text/plain'
        if ext:
            mime_type = mimetypes.guess_type(file_info['file_key'] + ext)[0]
        return body, mime_type
    except Exception as e:
        print(e)
        return False, None
    return False, None