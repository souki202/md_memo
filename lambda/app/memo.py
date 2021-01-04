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
from my_session import *
from my_common import *
from model.user import *
from model.memo import *

def decimal_default_proc(obj):
    if isinstance(obj, Decimal):
        return float(obj)
    raise TypeError

class ShareScope(Enum):
    PUBLIC = 1
    SPECIFIC_USERS = 2

class ShareType(Enum):
    NO_SHARE = 1
    READONLY = 2
    EDITABLE = 4

MULTIPLE_SELECT_MEMO_LIMIT = 25

db_client = boto3.resource("dynamodb")
users_table = db_client.Table('md_memo_users' + os.environ['DbSuffix'])
sessions_table = db_client.Table('md_memo_sessions' + os.environ['DbSuffix'])
memo_overviews_table = db_client.Table('md_memo_overviews' + os.environ['DbSuffix'])
memo_bodies_table = db_client.Table('md_memo_bodies' + os.environ['DbSuffix'])
memo_shares_table = db_client.Table('md_memo_shares' + os.environ['DbSuffix'])


def get_memo_list_event(event, context):
    if os.environ['EnvName'] != 'Prod':
        print(json.dumps(event))
    user_uuid: str = get_user_uuid_by_event(event)
    if not user_uuid:
        return {
            "statusCode": 401,
            "headers": create_common_header(),
            "body": json.dumps({'message': "session timeout",}),
        }
    memos = get_available_memo_list(user_uuid)
    if memos is None:
        print('Failed get memo list.')
        print('user_uuid: ' + user_uuid)
        return {
            "statusCode": 500,
            "headers": create_common_header(),
            "body": json.dumps({'message': 'Failed to get the memo list.',}),
        }
    for memo in memos:
        del memo['user_uuid']
    return {
        "statusCode": 200,
        "headers": create_common_header(),
        "body": json.dumps({'items': memos,}, default=decimal_default_proc),
    }

def get_memo_data_event(event, content):
    if os.environ['EnvName'] != 'Prod':
        print(json.dumps(event))
    user_uuid: str = get_user_uuid_by_event(event)
    if not user_uuid:
        return {
            "statusCode": 401,
            "headers": create_common_header(),
            "body": json.dumps({'message': "session timeout",}),
        }
    
    memo_id = ''
    if 'queryStringParameters' in event:
        memo_id = event['queryStringParameters'].get('memo_id', '')
    # 取得時はメモの持ち主が一致しているか確認
    if not check_is_owner_of_the_memo(memo_id, user_uuid):
        print('Unauthorized get memo data.')
        print({'user': user_uuid, 'memo_id': memo_id})
        return {
            'statusCode': 404,
            'headers': create_common_header(),
            'body': json.dumps({'message': 'Not Found',}),
        }
    # メモ情報の取得
    memo_data = get_memo_data(memo_id)
    if not memo_data:
        return {
            'statusCode': 404,
            'headers': create_common_header(),
            'body': json.dumps({'message': 'Not Found',}),
        }
    del memo_data['user_uuid']
    return {
        "statusCode": 200,
        "headers": create_common_header(),
        "body": json.dumps({'memo': memo_data,}, default=decimal_default_proc),
    }

def save_memo_event(event, context):
    if os.environ['EnvName'] != 'Prod':
        print(json.dumps(event))
    user_uuid: str = get_user_uuid_by_event(event)
    # 更新はログイン必須
    if not user_uuid:
        return {
            "statusCode": 401,
            "headers": create_common_header(),
            "body": json.dumps({'message': "session timeout",}),
        }
    # 各種値を変数に
    params           = json.loads(event['body'] or '{ }')
    title: str       = params['params'].get('title', '')
    memo_id: str     = params['params'].get('id', '')
    description: str = params['params'].get('description', '')
    memo_type: int   = int(params['params'].get('type', 1))
    body: str        = params['params'].get('body', '')

    # 更新時はメモの編集権限があるかチェック
    if memo_id:
        share_settings: dict = get_share_setting_by_memo_id(memo_id)
        share_users: str = ''
        edit_auth: bool = False
        user_data: dict = get_user_data_by_uuid(user_uuid)
        memo_data: dict = get_memo_overview(memo_id)

        if share_settings and share_settings['share_type'] == ShareType.EDITABLE.value:
            # シェア時に, 更新権限があるか調べる
            if share_settings['share_scope'] == ShareScope.SPECIFIC_USERS.value:
                share_users = share_settings['share_users'] 
                edit_auth = check_has_auth_memo(user_data, memo_data['user_uuid'], share_users)
            if share_settings['share_scope'] == ShareScope.PUBLIC.value:
                edit_auth = True
        else: # シェア設定がない場合
            edit_auth = check_has_auth_memo(user_data, memo_data['user_uuid'], share_users)
        if not memo_data or not edit_auth:
            print('Unauthorized memo save.')
            print({'user': user_uuid, 'memo_id': memo_id})
            return {
                'statusCode': 401,
                'headers': create_common_header(),
                'body': json.dumps({'message': 'Unauthorized',}),
            }
    
    # メモを更新または作成
    saved_uuid: str = save_memo(memo_id, title, description, body, memo_type, user_uuid)
    if saved_uuid is None:
        print('Failed to save.')
        print(params)
        return {
            "statusCode": 500,
            "headers": create_common_header(),
            "body": json.dumps({'message': 'Failed to save.',}),
        }
    return {
        "statusCode": 200,
        "headers": create_common_header(),
        "body": json.dumps({'id': saved_uuid,}),
    }

'''
シェア設定を更新する
'''
def update_share_settings_event(event, context):
    if os.environ['EnvName'] != 'Prod':
        print(json.dumps(event))
    user_uuid: str = get_user_uuid_by_event(event)
    if not user_uuid:
        return {
            "statusCode": 401,
            "headers": create_common_header(),
            "body": json.dumps({'message': "session timeout",}),
        }

    params           = json.loads(event['body'] or '{ }')
    memo_id: str     = params['params']['id'] or ''
    share_type: int  = int(params['params']['share']['type']) or 1
    share_scope: int = int(params['params']['share']['scope']) or 1
    share_users: str = params['params']['share']['users'] or ''

    # シェア設定は持ち主しか変更できない
    if not check_is_owner_of_the_memo(memo_id, user_uuid):
        print('Unauthorized memo save.')
        print({'user': user_uuid, 'memo_id': memo_id})
        return {
            'statusCode': 401,
            'headers': create_common_header(),
            'body': json.dumps({'message': 'Unauthorized',}),
        }

    # メモ設定を更新
    share_id: str = update_share_settings(memo_id, share_type, share_scope, share_users)
    if not share_id:
        print('Failed update share setting')
        print({'user': user_uuid, 'memo_id': memo_id, 'type': share_type, 'scope': share_scope, 'users': share_users})
        return {
            'statusCode': 500,
            'headers': create_common_header(),
            'body': json.dumps({'message': 'Unauthorized',}),
        }

    return {
        "statusCode": 200,
        "headers": create_common_header(),
        "body": json.dumps({'share_id': share_id,}),
    }

def get_memo_data_by_share_id(event, context):
    if os.environ['EnvName'] != 'Prod':
        print(json.dumps(event))
    
    share_id: str = None
    if 'queryStringParameters' in event:
        share_id: str = event['queryStringParameters'].get('share_id')
    
    # メモのシェア設定を取得
    share_settings: dict = get_share_setting_by_share_id(share_id)
    share_scope: int = int(share_settings['share_scope'])

    # メモのデータを取得
    memo_data: dict = get_memo_data(share_settings['memo_id'])
    is_no_auth: bool = False
    if share_scope == ShareScope.PUBLIC.value:
        is_no_auth = False
    elif share_scope == ShareScope.SPECIFIC_USERS.value:
        # ログイン中のユーザ情報を取得
        user_uuid: str = get_user_uuid_by_event(event)
        user_data: dict = get_user_data_by_uuid(user_uuid)
        if not user_data or not user_uuid:
            is_no_auth = True
        # 取得権限があるか調べる
        is_no_auth = not check_has_auth_memo(user_data, memo_data['user_uuid'], share_settings['share_users'])
    
    if is_no_auth:
        return {
            'statusCode': 401,
            'headers': create_common_header(),
            'body': json.dumps({'message': 'Unauthorized',}),
        }
    
    # 権限があるので取得
    return {
        "statusCode": 200,
        "headers": create_common_header(),
        "body": json.dumps({'memo': memo_data,}, default=decimal_default_proc),
    }

def delete_memo(event, context):
    if os.environ['EnvName'] != 'Prod':
        print(json.dumps(event))
    user_uuid: str = get_user_uuid_by_event(event)
    if not user_uuid:
        return create_common_return_array(401, {'message': "Failed to delete memo.",})

    params = json.loads(event['body'] or '{ }')
    if not params or not params.get('params'):
        return create_common_return_array(406, {'message': "Failed to delete memo.",})

    memo_id_list = params['params'].get('memo_id_list')
    if not memo_id_list:
        return create_common_return_array(406, {'message': "Failed to delete memo.",})
    
    if len(memo_id_list) > MULTIPLE_SELECT_MEMO_LIMIT:
        return create_common_return_array(406, {'message': "The maximum number of selections is 25.",})

    # 重複消去
    memo_id_list = list(set(memo_id_list))

    # メモの持ち主と一致してるか調べる
    if not check_is_owner_of_the_memo_multi(memo_id_list, user_uuid):
        print('Unauthorized delete operation.')
        return create_common_return_array(401, {'message': "Failed to delete memo.",})
    
    # 削除
    if not delete_memo_multi(memo_id_list):
        return create_common_return_array(500, {'message': "Failed to delete memo.",})
    
    return create_common_return_array(200, {'memo': 'success',})

