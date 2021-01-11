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
from model.share import *
import model.memo as my_memo

db_resource = boto3.resource("dynamodb")
db_client = boto3.client("dynamodb", region_name='ap-northeast-1')
FILES_TABLE_NAME = 'md_memo_files' + os.environ['DbSuffix']
RELATION_TABLE_NAME = 'md_memo_file_and_memo_relation' + os.environ['DbSuffix']

files_table = db_resource.Table(FILES_TABLE_NAME)
relation_table = db_resource.Table(RELATION_TABLE_NAME)

def add_file(file_key, user_uuid, file_size, ext):
    try:
        res = files_table.put_item(
            Item = {
                'file_key': file_key,
                'user_uuid': user_uuid,
                'memos': [],
                'ext': ext,
                'created_at': get_now_string(),
                'file_size': file_size,
            }
        )
        return not not res
    except Exception as e:
        print(e)
        return False
    return True

def get_file(file_key):
    try:
        res = files_table.query(
            KeyConditionExpression=Key('file_key').eq(file_key)
        )['Items']
        if len(res) == 0:
            return None
        return res[0]
    except Exception as e:
        print(e)
        return False
    return False

def get_file_list_by_memo_id(memo_id):
    if not memo_id:
        return False
    try:
        result = relation_table.query(
            IndexName='memo_id-index',
            KeyConditionExpression=Key('memo_id').eq(memo_id)
        )['Items']
        if len(result) == 0:
            return []
        return result
    except Exception as e:
        print(e)
        return False
    return False

def get_memo_list_by_file_key(file_key):
    if not file_key:
        return False
    try:
        result = relation_table.query(
            KeyConditionExpression=Key('file_key').eq(file_key)
        )['Items']
        if len(result) == 0:
            return []
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
    if now_files == False:
        print('failed to get memo id: ' + memo_id)
        return False
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

def delete_file_and_memo_relation_by_memos(memo_ids):
    for memo_id in memo_ids:
        # 削除対象のファイルをまとめる
        now_files = get_file_list_by_memo_id(memo_id)
        if now_files == False:
            print('delete_file_and_memo_relation_by_memos failed to get file and memo relation: ' + memo_id)
            continue
        now_files = [f['file_key'] for f in now_files]

        # 削除実行
        try:
            result = delete_file_and_memo_relation_multi(memo_id, now_files)
            if not result:
                raise 'Failed to delete relation'
        except Exception as e:
            print(e)
            return False
        return False
    return True

def get_file_shareing_auth(file_key, file_user_uuid, user_uuid):
    # 所持者自身
    if file_user_uuid == user_uuid:
        return True

    if not file_key:
        return ShareType.NO_SHARE.value
        
    memos = get_memo_list_by_file_key(file_key)
    if not memos:
        return ShareType.NO_SHARE.value

    for memo in memos:
        memo_id = memo['memo_id']
        share_setting = my_memo.get_share_setting_by_memo_id(memo_id)
        if not share_setting:
            continue

        # シェアしない設定になっていれば次
        if share_setting['share_scope'] == ShareType.NO_SHARE.value:
            continue

        scope = share_setting['share_scope']
        # publicなら誰でも見られるのでその時点で終了
        if scope == ShareScope.PUBLIC.value:
            return True
        if scope == ShareScope.SPECIFIC_USERS.value:
            if check_is_in_share_target(user_uuid, share_setting['share_users']):
                return True
    return False

def check_is_binary(mime_type):
    binary_types = [
        'image/', 'video/', 'audio/', 'font/', 'model/', 'multipart/form-data',
        'application/octet-stream', 'application/zip', 'application/pdf', 'application/ms',
        'application/java', 'application/vnd*', 'application/rtf', 'application/x-7z-compressed'
    ]
    for binary_type in binary_types:
        if binary_type in mime_type:
            return True
    return False