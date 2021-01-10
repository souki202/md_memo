import json
import boto3
import os
import uuid
import datetime
import time
import secrets
from http.cookies import SimpleCookie
from boto3.dynamodb.conditions import Key
from my_common import *
from dynamo_utility import *

db_resource = boto3.resource("dynamodb")
db_client = boto3.client("dynamodb", region_name='ap-northeast-1')
FILES_TABLE_NAME = 'md_memo_files' + os.environ['DbSuffix']
RELATION_TABLE_NAME = 'md_memo_file_and_memo_relation' + os.environ['DbSuffix']

files_table = db_resource.Table(FILES_TABLE_NAME)
relation_table = db_resource.Table(RELATION_TABLE_NAME)

def add_file(file_key, user_uuid, file_size):
    try:
        res = files_table.put_item(
            Item = {
                'file_key': file_key,
                'user_uuid': user_uuid,
                'memos': [],
                'created_at': get_now_string(),
                'file_size': file_size,
            }
        )
        return not not res
    except Exception as e:
        print(e)
        return False
    return True


def get_file_list_by_memo_id(memo_id):
    try:
        result = relation_table.query(
            IndexName='memo_id-index',
            KeyConditionExpression=Key('memo_id').eq(memo_id)
        )['Items']
        return result
    except Exception as e:
        print(e)
        return False
    return False

def delete_file_and_memo_relation(memo_id, file_key):
    try:
        result = relation_table.delete_item(
            Key = {
                'file_key': file_key,
                'memo_id': memo_id
            }
        )
        return not not result
    except Exception as e:
        print(e)
        return False
    return False

def delete_file_and_memo_relation_multi(memo_id, file_keys):
    try:
        with relation_table.batch_writer() as batch:
            for file_key in file_keys:
                print(file_key)
                print(memo_id)
                batch.delete_item(
                    Key = {
                        'file_key': file_key,
                        'memo_id': memo_id
                    }
                )
        return True
    except Exception as e:
        print(e)
        return False
    return False

def add_file_and_memo_relation_multi(memo_id, file_keys):
    try:
        with relation_table.batch_writer() as batch:
            for file_key in file_keys:
                batch.put_item(
                    Item = {
                        'file_key': file_key,
                        'memo_id': memo_id
                    }
                )
        return True
    except Exception as e:
        print(e)
        return False
    return False

def update_file_and_memo_relation(memo_id, files) -> bool:
    now_files = get_file_list_by_memo_id(memo_id)
    now_files = [f['file_key'] for f in now_files]
    # メモから取り除かれたファイルを検索
    removed_files = [f for f in now_files if f not in files]
    print(removed_files)
    # メモに追加されたファイルを検索
    new_files = [f for f in files if f not in now_files]
    # DB操作
    try:
        result = delete_file_and_memo_relation_multi(memo_id, removed_files)
        if not result:
            raise 'Failed to delete relation'
        result = add_file_and_memo_relation_multi(memo_id, new_files)
        if not result:
            raise 'Failed to add relation'
        return True
    except Exception as e:
        print(e)
        return False
    return False