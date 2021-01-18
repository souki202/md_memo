import json
import boto3
import os
import uuid
import datetime
import time
import secrets
from argon2 import PasswordHasher
from http.cookies import SimpleCookie
from boto3.dynamodb.conditions import Key
from my_common import *
from common_headers import *

db_client = boto3.resource("dynamodb")
users_table = db_client.Table('md_memo_users' + os.environ['DbSuffix'])
sessions_table = db_client.Table('md_memo_sessions' + os.environ['DbSuffix'])
reset_password_table = db_client.Table('md_memo_reset_password' + os.environ['DbSuffix'])
login_histories_table = db_client.Table('md_memo_login_histories' + os.environ['DbSuffix'])

EXPIRATION_RESET_PASS = 60 * 5 # 5分
EXPIRATION_TIME_PERIOD = 3600 * 24 * 30 # 30日
EXPIRATION_LOGIN_HISTORY = 3600 * 24 * 90 # 90日
LOGIN_TIME_RANGE = 60 * 5

MAX_LOGIN_TRY_COUNT = 7

def check_and_update_session(event) -> bool:
    cookie = create_simple_cookie(event)
    if not cookie.get('session_token', None):
        return False
    token = cookie.get('session_token').value
    is_correct_session = get_is_correct_session(token)

    if not is_correct_session:
        return False
    
    # 今は更新成功のチェックはしない
    update_result = update_session(token)
    return True

def check_session(event) -> bool:
    cookie = create_simple_cookie(event)
    if not cookie.get('session_token', None):
        return False
    token = cookie.get('session_token').value
    is_correct_session = get_is_correct_session(token)
    if not is_correct_session:
        print('不正なトークン: ' + token)
        False
    return True

def create_simple_cookie(event) -> SimpleCookie:
    cookie = SimpleCookie()

    if 'multiValueHeaders' not in event:
        return cookie
    if 'cookie' not in event['multiValueHeaders']:
        return cookie

    try:
        raw_cookie = event['multiValueHeaders']['cookie'][0]
        cookie.load(raw_cookie)
        return cookie
    except Exception as e:
        print(e)
        return cookie
    return cookie

def get_session_token(event) -> str:
    cookie = create_simple_cookie(event)
    if not cookie.get('session_token', None):
        return False
    return cookie.get('session_token').value


def get_is_correct_session(session_token: str) -> bool:
    if not session_token:
        return False
    try:
        result = sessions_table.query(
            KeyConditionExpression=Key('session_token').eq(session_token)
        )['Items']
        if len(result) == 0:
            return False
        
        if 'user_uuid' not in result[0] or not result[0]['user_uuid']:
            print('deleted session: ' + session_token)
            return False
        return True
    except Exception as e:
        print(e)
        return False
    return False

def create_session(user_uuid: str) -> (bool, str):
    if not user_uuid:
        return None, None
    token = secrets.token_urlsafe(64)
    try:
        res = sessions_table.put_item(
            Item = {
                'session_token': token,
                'user_uuid': user_uuid,
                'created_at': get_now_string(),
                'expiration_time': int(time.time()) + EXPIRATION_TIME_PERIOD
            }
        )
        return not not res, token
    except Exception as e:
        print(e)
        return False, None
    return None, None

def delete_session(token: str) -> bool:
    if not token:
        return False
    try:
        # まずTTLを0に
        res = sessions_table.update_item(
            Key = {
                'session_token': token,
            },
            UpdateExpression = 'set expiration_time=:e',
            ExpressionAttributeValues = {
                ':e': 0
            },
            ReturnValues="UPDATED_NEW"
        )
        if not res:
            return False
        # 項目削除
        res = sessions_table.delete_item(
            Key = {
                'session_token': token,
            },
        )
        return not not res
    except Exception as e:
        print(e)
        return False

def add_login_history(user_id: str, ip_address: str) -> bool:
    if not user_id or not ip_address:
        return False
    
    try:
        res = login_histories_table.put_item(
            Item = {
                'user_id': user_id,
                'ip_address': ip_address,
                'created_at': get_now_string(),
                'expiration_time': int(time.time()) + EXPIRATION_TIME_PERIOD
            }
        )
        return not not res
    except Exception as e:
        print(e)
        return False
    return False

def check_login_history(user_id: str, ip_address: str) -> bool:
    now = get_now_string()
    from_time = get_calced_from_now_string(LOGIN_TIME_RANGE)

    try:
        result = login_histories_table.query(
            IndexName='ip_address-index',
            KeyConditionExpression=Key('ip_address').eq(ip_address),
            FilterExpression='created_at > :created_at',
            ExpressionAttributeValues={
                ':created_at': from_time
            }
        )
        # レコード数が多ければログイン試行が多いので拒否
        if len(result['Items']) > MAX_LOGIN_TRY_COUNT:
            return False
        print(len(result['Items']))
        return True
    except Exception as e:
        print(e)
        return False
    return False

def get_user_uuid_by_token(session_token: str) -> str:
    if not session_token:
        return None
    try:
        result = sessions_table.query(
            KeyConditionExpression=Key('session_token').eq(session_token)
        )['Items']
        if len(result) == 0:
            return None
        return result[0]['user_uuid']
    except Exception as e:
        print(e)
        return None
    return None

'''
lambdaのイベントからcookieを取り出し, そのトークンを利用してuser_uuidを取得する
トークンが不正な場合はNone

@return {str} user_uuid
'''
def get_user_uuid_by_event(event) -> str:
    cookie = create_simple_cookie(event)
    if not cookie.get('session_token', None):
        return False

    token = cookie.get('session_token').value
    if not token:
        return None
    return get_user_uuid_by_token(token)

def update_session(token: str) -> bool:
    try:
        res = sessions_table.update_item(
            Key = {
                'session_token': token,
            },
            UpdateExpression = 'set expiration_time=:e',
            ExpressionAttributeValues = {
                ':e': int(time.time()) + EXPIRATION_TIME_PERIOD
            },
            ReturnValues="UPDATED_NEW"
        )
        return not not res
    except Exception as e:
        print(e)
        return False
    return False

'''
パスワードリセット用のデータを登録する

@return {dict, str} 成功時はその結果とreset_token
'''
def add_reset_password(new_password: str, user_id: str):
    try:
        ttl = int(time.time()) + EXPIRATION_RESET_PASS
        reset_token = secrets.token_urlsafe(64)
        ph = PasswordHasher()
        pass_hash = ph.hash(new_password)
        result = reset_password_table.put_item(
            Item = {
                'reset_token': reset_token,
                'user_id': user_id,
                'password': pass_hash,
                'expiration_time': ttl,
            }
        )
        return result, reset_token
    except Exception as e:
        print(e)
        return False, None
    return False, None

def get_reset_password(token: str) -> dict:
    try:
        result = reset_password_table.query(
            KeyConditionExpression=Key('reset_token').eq(token)
        )['Items']
        if len(result) == 0:
            return None
        return result[0]
    except Exception as e:
        print(e)
        return False
    return False

'''
入力されたパスワードが, ユーザのものと一致するか確認

@return {bool} 一致すればtrue
'''
def check_password(input_password, hashed_password):
    # SNS認証の場合はパスワードが設定されていない場合がある
    if not hashed_password or not input_password:
        return False
         
    # パスワードチェック
    ph = PasswordHasher()
    try:
        ph.verify(hashed_password, input_password)
    except Exception as e:
        return False
    return True