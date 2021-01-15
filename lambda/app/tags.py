import json
import boto3
import os
import uuid
import datetime
import time
import secrets
from enum import Enum
from common_headers import *
from model.auth import *
from my_common import *
from model.user import *
from model.memo import *
from model.plan import *
import model.file as my_file
from model.share import *
import model.tag as my_tag

MAX_TAG_COUNT = 500
MAX_TAG_NAME_LEN = 50

def tag_event(event, context):
    if os.environ['EnvName'] != 'Prod':
        print(json.dumps(event))
    
    httpMethod = str.upper(event['httpMethod'])
    resource = str.lower(event['resource'])
    
    if httpMethod == 'POST':
        if resource == '/update_tag':
            return update_tag_event(event, context)
        elif resource == '/get_tag_id':
            return get_tag_id_event(event, context)
        elif resource == '/set_tag_relation':
            return set_tag_relation_event(event, context)
        elif resource == '/delete_tag_relation':
            return delete_tag_relation_event(event, context)
    elif httpMethod == 'GET':
        if resource == '/get_tags':
            return get_tags_event(event, context)
        elif resource == '/get_relation_tags':
            return get_relation_tags_event(event, context)
    
    return create_common_return_array(404, {'message': 'Not Found',})


def update_tag_event(event, context):
    user_uuid: str = get_user_uuid_by_event(event)
    # 更新はログイン必須
    if not user_uuid:
        return create_common_return_array(401, {'message': 'session timeout.',})
    
    # 各種値を変数に
    params = json.loads(event['body'] or '{ }')
    if 'params' not in params:
        return create_common_return_array(406, {'message': 'Insufficient input'})

    name: str       = params['params'].get('name', '')
    tag_uuid: str   = params['params'].get('id', '')

    if not name:
        return create_common_return_array(406, {'message': 'Insufficient input'})

    if len(name) > MAX_TAG_NAME_LEN:
        return create_common_return_array(403, {'message': 'The name can be up to 50 characters.'})


    if not tag_uuid:
        # uuidが無ければ新規作成
        # まずは件数を取得して作成できるか調べる
        num_of_tags = my_tag.get_tags_count(user_uuid)
        
        if num_of_tags is None:
            return create_common_return_array(500, {'message': 'Failed to create tag'})
        
        if num_of_tags >= MAX_TAG_COUNT:
            return create_common_return_array(500, {'message': 'Failed to create tag', 'is_limit': True})
            
        # タグの新規作成
        tag_uuid = my_tag.create_tag(name, user_uuid)
        if not tag_uuid:
            return create_common_return_array(500, {'message': 'Failed to create tag'})
    else:
        # uuidがあれば更新
        tag_info = my_tag.get_tag(tag_uuid)
        if not tag_info:
            return create_common_return_array(500, {'message': 'Failed to create tag'})
        if tag_info['user_uuid'] != user_uuid:
            return create_common_return_array(401, {'message': 'Unauthorized'})
        
        # 書き換え
        if not my_tag(name, tag_info['uuid']):
            return create_common_return_array(500, {'message': 'Failed to update tag'})

    return create_common_return_array(200, {'id': tag_uuid})

def get_tags_event(event, context):
    user_uuid: str = get_user_uuid_by_event(event)
    # 更新はログイン必須
    if not user_uuid:
        return create_common_return_array(401, {'message': 'session timeout.',})
        
    tags = my_tag.get_all_tags(user_uuid)

    if tags == False or tags is None:
        return create_common_return_array(500, {'message': 'Failed to get tags.',})

    return create_common_return_array(200, {'tags': tags})


def get_tag_id_event(event, context):
    user_uuid: str = get_user_uuid_by_event(event)
    # 更新はログイン必須
    if not user_uuid:
        return create_common_return_array(401, {'message': 'session timeout.',})

    params = json.loads(event['body'] or '{ }')
    if 'params' not in params:
        return create_common_return_array(406, {'message': 'Insufficient input'})

    name: str = params['params'].get('name', '')
    if not name:
        return create_common_return_array(406, {'message': 'Insufficient input'})

    tag_uuid = my_tag.get_tag_id(user_uuid, name)

    if tag_uuid == False:
        return create_common_return_array(500, {'message': 'Failed to get tag id'})

    if tag_uuid is None:
        tag_uuid = ''

    return create_common_return_array(200, {'id': tag_uuid})

'''
そのメモに関連付けられているタグを取得する
'''
def get_relation_tags_event(event, context):
    user_uuid: str = get_user_uuid_by_event(event)
    # 更新はログイン必須
    if not user_uuid:
        return create_common_return_array(401, {'message': 'session timeout.',})

    memo_id = event.get('queryStringParameters', {}).get('memo_id', '')

    if not memo_id:
        return create_common_return_array(406, {'message': 'Insufficient input'})

    # 取得時はメモの持ち主が一致しているか確認
    if not check_is_owner_of_the_memo(memo_id, user_uuid):
        return create_common_return_array(401, {'message': 'Unauthorized',})
    
    # 取得
    tags = my_tag.get_tag_relations(memo_id)
    if tags == False:
        return create_common_return_array(500, {'message': 'Failed to set tag relation'})
    
    return create_common_return_array(200, {'tags': tags,})

'''
メモとタグを関連付ける
'''
def set_tag_relation_event(event, context):
    user_uuid: str = get_user_uuid_by_event(event)
    # 更新はログイン必須
    if not user_uuid:
        return create_common_return_array(401, {'message': 'session timeout.',})

    params = json.loads(event['body'] or '{ }')
    if 'params' not in params:
        return create_common_return_array(406, {'message': 'Insufficient input'})
    
    tag_uuid: str = params['params'].get('tag_uuid', '')
    memo_uuid: str = params['params'].get('memo_uuid', '')

    if not tag_uuid or not memo_uuid:
        return create_common_return_array(406, {'message': 'Insufficient input'})

    # メモとタグの所持者がどちらもログインユーザか調べる
    tag_info = my_tag.get_tag(tag_uuid)
    memo_overview = get_memo_overview(memo_uuid)

    if tag_info['user_uuid'] != user_uuid or memo_overview['user_uuid'] != user_uuid:
        return create_common_return_array(401, {'message': 'Unauthorized'})

    # relationをつける
    if not my_tag.set_tag_relation(tag_uuid, memo_uuid, memo_overview['created_at']):
        return create_common_return_array(500, {'message': 'Failed to set tag relation'})
    return create_common_return_array(200, {'message': 'Success'})

'''
メモとタグの関連付けを削除する
'''
def delete_tag_relation_event(event, context):
    user_uuid: str = get_user_uuid_by_event(event)
    # 更新はログイン必須
    if not user_uuid:
        return create_common_return_array(401, {'message': 'session timeout.',})

    params = json.loads(event['body'] or '{ }')
    if 'params' not in params:
        return create_common_return_array(406, {'message': 'Insufficient input'})
    
    tag_uuid: str = params['params'].get('tag_uuid', '')
    memo_uuid: str = params['params'].get('memo_uuid', '')

    if not tag_uuid or not memo_uuid:
        return create_common_return_array(406, {'message': 'Insufficient input'})

    # メモとタグの所持者がどちらもログインユーザか調べる
    tag_info = my_tag.get_tag(tag_uuid)
    memo_overview = get_memo_overview(memo_uuid)

    if tag_info['user_uuid'] != user_uuid or memo_overview['user_uuid'] != user_uuid:
        return create_common_return_array(401, {'message': 'Unauthorized'})

    # relationを削除
    if not my_tag.delete_tag_relation(tag_uuid, memo_uuid):
        return create_common_return_array(500, {'message': 'Failed to set tag relation'})

    return create_common_return_array(200, {'message': 'Success'})
