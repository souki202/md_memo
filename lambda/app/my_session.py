
import boto3
import os
import time
import datetime
import secrets
from argon2 import PasswordHasher
from http.cookies import SimpleCookie
from boto3.dynamodb.conditions import Key

db_client = boto3.resource("dynamodb")
users_table = db_client.Table('md_memo_users' + os.environ['DbSuffix'])
sessions_table = db_client.Table('md_memo_sessions' + os.environ['DbSuffix'])

EXPIRATION_TIME_PERIOD = 3600 * 24 * 30

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

def check_and_update_session(event):
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

def check_session(event):
    cookie = create_simple_cookie(event)
    if not cookie.get('session_token', None):
        return False
    token = cookie.get('session_token').value
    is_correct_session = get_is_correct_session(token)
    if not is_correct_session:
        print('不正なトークン: ' + token)
        False
    return True

def get_is_correct_session(session_token):
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

def create_session(user_uuid):
    if not user_uuid:
        return None, None
    token = secrets.token_urlsafe(64)
    now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    try:
        res = sessions_table.put_item(
            Item = {
                'session_token': token,
                'user_uuid': user_uuid,
                'created_at': now,
                'expiration_time': int(time.time()) + EXPIRATION_TIME_PERIOD
            }
        )
        return res, token
    except Exception as e:
        print(e)
        return False, None
    return None, None

def delete_session(token):
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
        if not res:
            return False
        return True
    except Exception as e:
        print(e)
        return False

def get_user_uuid_by_token(session_token) -> str:
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

def update_session(token):
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
        return res
    except Exception as e:
        print(e)
        return False
    return False

'''
入力されたパスワードが, ユーザのものと一致するか確認

@return {bool} 一致すればtrue
'''
def check_password(input_password, hashed_password):
    # パスワードチェック
    ph = PasswordHasher()
    try:
        ph.verify(hashed_password, input_password)
    except Exception as e:
        return False
    return True