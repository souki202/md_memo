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
from my_mail import *
from user import *

db_client = boto3.resource("dynamodb")
users_table = db_client.Table('md_memo_users' + os.environ['DbSuffix'])
sessions_table = db_client.Table('md_memo_sessions' + os.environ['DbSuffix'])

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
            "body": json.dumps({'message': "Missing Email or Password.",}),
        }

    # 既存のユーザがいるか調べる
    existing_user = get_user(email)

    # ユーザの取得でエラーが発生した
    if existing_user == False:
        return {
            "statusCode": 500,
            "headers": create_common_header(),
            "body": json.dumps({'message': "Failure search existing user",}),
        }
    # ユーザがいなかった
    if existing_user is None:
        print('Missing user: ' + email)
        return {
            "statusCode": 401,
            "headers": create_common_header(),
            "body": json.dumps({'message': "Wrong email or password.",}),
        }
    
    # 仮登録状態なら終了
    if existing_user.get('is_temporary', False):
        print("Temporary user. login failed")
        return {
            "statusCode": 401,
            "headers": create_common_header(),
            "body": json.dumps({'message': "Temporary user.",}),
        }

    # パスワードチェック
    if not check_password(password, existing_user['password']):
        print('Wrong password: ' + email)
        return {
            "statusCode": 401,
            "headers": create_common_header(),
            "body": json.dumps({'message': "Wrong email or password.",}),
        }
    
    # セッション作成
    user_uuid = existing_user['uuid']
    create_result, session_token = create_session(user_uuid)
    if create_result == False:
        return {
            "statusCode": 500,
            "headers": create_common_header(),
            "body": json.dumps({'message': "Failure create session.",}),
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
            "body": json.dumps({'message': "Missing Email or Password.",}),
        }

    # 登録できるユーザIDかチェック
    if not get_can_be_registered_user(email):
        return {
            "statusCode": 403,
            "headers": create_common_header(),
            "body": json.dumps({'message': "Cannot be registered user id",}),
        }

    # ユーザがいないので新規登録
    ph = PasswordHasher()
    pass_hash = ph.hash(password)

    # ユーザ作成
    create_result, user_uuid, temp_token = add_user(email, pass_hash)
    print(user_uuid)
    if create_result == False:
        return {
            "statusCode": 500,
            "headers": create_common_header(),
            "body": json.dumps({'message': "Failure add user.",}),
        }

    # セッション作成
    # create_result, session_token = create_session(user_uuid)
    # if create_result == False:
    #     return {
    #         "statusCode": 500,
    #         "headers": create_common_header(),
    #         "body": json.dumps({'message': "Failure create session.",}),
    #     }

    # 仮登録メール送信
    send_temporary_regist_mail(email, temp_token)

    return {
        "statusCode": 200,
        "headers": create_common_header(),
        "body": json.dumps({}),
    }

def check_token(event, context):
    if os.environ['EnvName'] != 'Prod':
        print(json.dumps(event))
    result = check_and_update_session(event)
    
    if not result:
        return {
            "statusCode": 401,
            "headers": create_common_header(),
            "body": json.dumps({'message': "session timeout",}),
        }

    return {
            "statusCode": 200,
            "headers": create_common_header(),
            "body": json.dumps({'message': "ok",}),
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

def regist_complete(event, context):
    if os.environ['EnvName'] != 'Prod':
        print(json.dumps(event))

    params = json.loads(event['body'])
    temp_token = params.get('token', '')

    if not temp_token:
        return {
            "statusCode": 406,
            "headers": create_common_header(),
            "body": json.dumps({'message': 'Failed to regist.',}),
        }

    # tokenに対応するユーザを取得
    user: dict = get_user_by_temporary_token(temp_token)

    # 仮登録tokenからユーザを見つけられなかった
    if not user:
        print("Not Found temporary user: " + temp_token)
        print(user)
        return {
            "statusCode": 406,
            "headers": create_common_header(),
            "body": json.dumps({'message': 'Failed to regist.',}),
        }

    # 仮登録ユーザでない
    if not user.get('is_temporary', False):
        print("The User is Not temporary user: " + temp_token)
        print(user)
        return {
            "statusCode": 406,
            "headers": create_common_header(),
            "body": json.dumps({'message': 'Failed to regist.',}),
        }

    # 本登録する
    if not release_temporary(user['user_id']):
        print("Failed to release temporary: " + temp_token)
        print(user)
        return {
            "statusCode": 500,
            "headers": create_common_header(),
            "body": json.dumps({'message': 'Failed to regist.',}),
        }
    
    # ログインする
    # セッション作成
    user_uuid = user['uuid']
    create_result, session_token = create_session(user_uuid)
    if create_result == False:
        print("Failed to create session.: " + temp_token)
        return {
            "statusCode": 500,
            "headers": create_common_header(),
            "body": json.dumps({'message': "Failure create session.",}),
        }

    print("registrated")
    print(user)
    return {
        "statusCode": 200,
        "headers": create_common_header(),
        "body": json.dumps({"token": session_token,}),
    }