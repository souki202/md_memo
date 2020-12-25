import json
import boto3
import os
import uuid
import datetime
import time
import secrets
from http.cookies import SimpleCookie
from boto3.dynamodb.conditions import Key
from argon2 import PasswordHasher
from common_headers import create_common_header
from my_session import *

db_client = boto3.resource("dynamodb")
users_table = db_client.Table('md_memo_users' + os.environ['DbSuffix'])
sessions_table = db_client.Table('md_memo_sessions' + os.environ['DbSuffix'])

def get_user(id):
    try:
        result = users_table.query(
            KeyConditionExpression=Key('user_id').eq(id)
        )['Items']
        if len(result) == 0:
            return None
        return result[0]
    except Exception as e:
        print(e)
        return False
    return None

def add_user(id, passHash):
    now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    user_uuid = str(uuid.uuid4())
    try:
        res = users_table.put_item(
           Item = {
               'user_id': id,
               'uuid': user_uuid,
               'password': passHash,
               'created_at': now,
               'updated_at': now,
           }
        )
        return res, user_uuid
    except Exception as e:
        print(e)
        return False, None
    return False, None

def login(event, context):
    if os.environ['EnvName'] != 'Prod':
        print(json.dumps(event))

    params = json.loads(event['body'] or '')
    email = params['params']['email'] or ''
    password = params['params']['password'] or ''
    if (not email or not password):
        return {
            "statusCode": 401,
            "headers": create_common_header(),
            "body": json.dumps({"message": "Missing Email or Password.",}),
        }

    # 既存のユーザがいるか調べる
    existing_user = get_user(email)

    # ユーザの取得でエラーが発生した
    if existing_user == False:
        return {
            "statusCode": 500,
            "headers": create_common_header(),
            "body": json.dumps({"message": "Failure search existing user",}),
        }
    # ユーザがいなかった
    if existing_user is None:
        print('Missing user: ' + email)
        return {
            "statusCode": 401,
            "headers": create_common_header(),
            "body": json.dumps({"message": "Wrong email or password.",}),
        }

    # パスワードチェック
    ph = PasswordHasher()
    try:
        ph.verify(existing_user['password'], password)
    except Exception as e:
        print('Wrong password: ' + email)
        return {
            "statusCode": 401,
            "headers": create_common_header(),
            "body": json.dumps({"message": "Wrong email or password.",}),
        }  
    
    # セッション作成
    user_uuid = existing_user['uuid']
    create_result, session_token = create_session(user_uuid)
    if create_result == False:
        return {
            "statusCode": 500,
            "headers": create_common_header(),
            "body": json.dumps({"message": "Failure create session.",}),
        }
    return {
        "statusCode": 200,
        "headers": create_common_header(),
        "body": json.dumps({"token": session_token,}),
    }

def signup(event, context):
    if os.environ['EnvName'] != 'Prod':
        print(json.dumps(event))
    params = json.loads(event['body'])
    email = params['params']['email'] or ''
    password = params['params']['password'] or ''
    if (not email or not password):
        return {
            "statusCode": 403,
            "headers": create_common_header(),
            "body": json.dumps({"message": "Missing Email or Password.",}),
        }

    # 既存のユーザがいるか調べる
    existing_user = get_user(email)

    # ユーザの取得でエラーが発生した
    if existing_user == False:
        return {
            "statusCode": 500,
            "headers": create_common_header(),
            "body": json.dumps({"message": "Failure search existing user",}),
        }
    # ユーザが既に存在した
    if existing_user is not None:
        return {
            "statusCode": 403,
            "headers": create_common_header(),
            "body": json.dumps({"message": "The user is already registered.",}),
        }

    # ユーザがいないので新規登録
    ph = PasswordHasher()
    pass_hash = ph.hash(password)

    # ユーザ作成
    create_result, user_uuid = add_user(email, pass_hash)
    print(user_uuid)
    if create_result == False:
        return {
            "statusCode": 500,
            "headers": create_common_header(),
            "body": json.dumps({"message": "Failure add user.",}),
        }

    # セッション作成
    create_result, session_token = create_session(user_uuid)
    if create_result == False:
        return {
            "statusCode": 500,
            "headers": create_common_header(),
            "body": json.dumps({"message": "Failure create session.",}),
        }

    return {
        "statusCode": 200,
        "headers": create_common_header(),
        "body": json.dumps({"token": session_token,}),
    }

def check_token(event, context):
    if os.environ['EnvName'] != 'Prod':
        print(json.dumps(event))
    result = check_and_update_session(event)
    
    if not result:
        return {
            "statusCode": 401,
            "headers": create_common_header(),
            "body": json.dumps({"message": "session timeout",}),
        }

    return {
            "statusCode": 200,
            "headers": create_common_header(),
            "body": json.dumps({"message": "ok",}),
        }

def logout(event, context):
    if os.environ['EnvName'] != 'Prod':
        print(json.dumps(event))
    
    if not check_session(event):
        return {
            "statusCode": 401,
            "headers": create_common_header(),
            "body": json.dumps({'message': 'Failed to logout.',}),
        }

    raw_cookie = event['multiValueHeaders']['cookie'][0] or ''

    if not raw_cookie:
        return False
    
    cookie = SimpleCookie()
    cookie.load(raw_cookie)
    token = cookie['session_token'].value

    if not delete_session(token):
        return {
            "statusCode": 401,
            "headers": create_common_header(),
            "body": json.dumps({'message': 'Failed to logout.',}),
        }
    return {
            "statusCode": 200,
            "headers": create_common_header(),
            "body": json.dumps({'message': 'Complete logout.',}),
        }