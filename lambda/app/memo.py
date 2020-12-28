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
from common_headers import create_common_header
from my_session import *

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

users_table = db_client.Table('md_memo_users' + os.environ['DbSuffix'])
sessions_table = db_client.Table('md_memo_sessions' + os.environ['DbSuffix'])
memo_overviews_table = db_client.Table('md_memo_overviews' + os.environ['DbSuffix'])
memo_bodies_table = db_client.Table('md_memo_bodies' + os.environ['DbSuffix'])
memo_shares_table = db_client.Table('md_memo_shares' + os.environ['DbSuffix'])

def save_memo(memo_id: str, title: str, description: str, body: str, memo_type: int, user_uuid: str) -> str:
    # 新規作成時はuuidを新しく付与
    is_new: bool = not memo_id
    if not memo_id:
        memo_id = str(uuid.uuid4())
    now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    try:
        if is_new:
            memo_overviews_table.put_item(
                Item = {
                    'uuid': memo_id,
                    'title': title,
                    'description': description,
                    'memo_type': memo_type,
                    'user_uuid': user_uuid,
                    'created_at': now,
                    'updated_at': now,
                }
            )
        else:
            memo_overviews_table.update_item(
                Key = {
                    'uuid': memo_id,
                },
                UpdateExpression = 'set title=:title, description=:description, memo_type=:memo_type, updated_at=:updated_at',
                ExpressionAttributeValues = {
                    ':title': title,
                    ':description': description,
                    ':memo_type': memo_type,
                    ':updated_at': now,
                },
                ReturnValues="UPDATED_NEW"
            )
        with memo_bodies_table.batch_writer(overwrite_by_pkeys=['uuid']) as batch:
            batch.put_item(
                Item = {
                    'uuid': memo_id,
                    'body': body,
                }
            )
    except Exception as e:
        print(e)
        return None
    return memo_id

'''
メモの持ち主とログインユーザが一致しているか確認する
'''
def check_is_correct_user_memo(memo_id: str, user_uuid: str) -> bool:
    if not memo_id or not user_uuid:
        return False
    try:
        result = memo_overviews_table.query(
            KeyConditionExpression=Key('uuid').eq(memo_id)
        )['Items']
        if len(result) == 0:
            return False
        return result[0]['user_uuid'] == user_uuid
    except Exception as e:
        print(e)
        return False

def get_memo_list(user_uuid):
    try:
        result = memo_overviews_table.query(
            IndexName = 'user_uuid-index',
            KeyConditionExpression = Key('user_uuid').eq(user_uuid)
        )['Items']
        if len(result) == 0:
            return []
        return result
    except Exception as e:
        print(e)
        return None
    return None

def get_memo_overview(memo_id: str) -> dict:
    if not memo_id:
        return None
    try:
        # overviewの取得
        result = memo_overviews_table.query(
            KeyConditionExpression=Key('uuid').eq(memo_id)
        )['Items']
        if len(result) == 0:
            return None
        return result[0]
    except Exception as e:
        print(e)
        return None
    return None

'''
該当メモのoverview, body, shareを全て取得する
'''
def get_memo_data(memo_id: str):
    if not memo_id:
        return None
    memo_data = {}
    try:
        # overviewの取得
        result = memo_overviews_table.query(
            KeyConditionExpression=Key('uuid').eq(memo_id)
        )['Items']
        if len(result) == 0:
            return None
        memo_data = result[0]

        # bodyの取得
        result = memo_bodies_table.query(
            KeyConditionExpression=Key('uuid').eq(memo_id)
        )['Items']
        if len(result) == 0:
            print('Overview found, but body not found')
            return None
        memo_data['body'] = result[0]['body']

        # share情報の取得
        share_setting = get_share_setting_by_memo_id(memo_id)
        if share_setting:
            memo_data['share'] = share_setting
        return memo_data
    except Exception as e:
        print(e)
        return None
    
def update_share_settings(memo_id: str, share_type: int, share_scope: int, share_users: str) -> str:
    if not memo_id:
        return None
    try:
        # すでにそのメモのシェア設定があるか調べる
        existing_setting = get_share_setting_by_memo_id(memo_id)

        share_id = secrets.token_urlsafe(32)
        # すでに設定が存在すればshare_idはそれを使用する
        if existing_setting is not None:
            share_id = existing_setting['share_id']

        # 設定を更新
        with memo_shares_table.batch_writer(overwrite_by_pkeys=['share_id']) as batch:
            batch.put_item(
                Item = {
                    'share_id': share_id,
                    'memo_id': memo_id,
                    'share_type': share_type,
                    'share_scope': share_scope,
                    'share_users': share_users,
                }
            )
        return share_id
    except Exception as e:
        print(e)
        return None
    return None

def get_share_setting_by_memo_id(memo_id: str) -> dict:
    if not memo_id:
        return None
    try:
        result = memo_shares_table.query(
            IndexName = 'memo_id-index',
            KeyConditionExpression = Key('memo_id').eq(memo_id)
        )['Items']
        if not len(result):
            return None
        return result[0]
    except Exception as e:
        print(e)
        return None
    return None

def get_share_setting_by_share_id(share_id: str) -> dict:
    if not share_id:
        return None
    try:
        result = memo_shares_table.query(
            KeyConditionExpression = Key('share_id').eq(share_id)
        )['Items']
        if not len(result):
            return None
        return result[0]
    except Exception as e:
        print(e)
        return None
    return None

def check_is_in_share_target(user_id: str, share_targets: str) -> bool:
    if not share_targets or not user_id:
        return False
    target_users = share_targets.replace(' ', '').split(',')
    return user_id in target_users

'''
@param list user_data get_user_data_by_uuid等から取得したもの. 主にログイン中のユーザ
@param str  memo_user_uuid メモの作成者
@param share_targets シェア対象の一覧. ユーザが入力した文字列そのまま

@return bool readable権限があればtrue
'''
def check_has_auth_memo(user_data: dict, memo_user_uuid: str, share_targets: str) -> bool:
    if not user_data or not memo_user_uuid:
        return False
    
    # メモの作成者と一致していれば権限あり
    if memo_user_uuid == user_data['uuid']:
        return True
    
    # メモが共有対象かどうか
    return check_is_in_share_target(user_data['user_id'], share_targets)
    

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
    memos = get_memo_list(user_uuid)
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
    if not check_is_correct_user_memo(memo_id, user_uuid):
        print('Unauthorized get memo data.')
        print({'user': user_uuid, 'memo_id': memo_id})
        return {
            'statusCode': 404,
            'headers': create_common_header(),
            'body': json.dumps({'message': 'Not Found',}),
        }
    # メモ情報の取得
    memo_data = get_memo_data(memo_id)
    del memo_data['user_uuid']
    if not memo_data:
        return {
            'statusCode': 404,
            'headers': create_common_header(),
            'body': json.dumps({'message': 'Not Found',}),
        }
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
    if not check_is_correct_user_memo(memo_id, user_uuid):
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