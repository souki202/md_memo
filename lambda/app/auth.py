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
from common_headers import *
from my_session import *
from my_mail import *
from user import *

db_client = boto3.resource("dynamodb")
users_table = db_client.Table('md_memo_users' + os.environ['DbSuffix'])
sessions_table = db_client.Table('md_memo_sessions' + os.environ['DbSuffix'])
reset_password_table = db_client.Table('md_memo_reset_password' + os.environ['DbSuffix'])
EXPIRATION_RESET_PASS = 60 * 5 # 5分

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

'''
パスワードリセット用の登録とメール送信まで
'''
def reset_password_event(event, context):
    if os.environ['EnvName'] != 'Prod':
        print(json.dumps(event))

    params = json.loads(event['body'] or '')
    if not params:
        return {
            "statusCode": 406,
            "headers": create_common_header(),
            "body": json.dumps({'message': 'Insufficient input'}),
        }
    email = params['params']['email'] or ''
    if not email:
        return {
            "statusCode": 406,
            "headers": create_common_header(),
            "body": json.dumps({'message': 'Insufficient input'}),
        }

    # ユーザがいるか調べる
    if not get_user(email):
        print('User not found. : ' + email)
        return {
            "statusCode": 200,
            "headers": create_common_header(),
            "body": json.dumps({'message': 'User Not Found.'}),
        }
    
    # 新規パス発行
    new_password = secrets.token_urlsafe(12)
    result, reset_token = add_reset_password(new_password, email)
    if not result or not reset_token:
        return {
            "statusCode": 500,
            "headers": create_common_header(),
            "body": json.dumps({'message': 'Failed to reset password.'}),
        }
    
    # メール送信
    send_reset_password_mail(email, new_password, reset_token)

    return {
            "statusCode": 200,
            "headers": create_common_header(),
            "body": json.dumps({'message': 'User Not Found.'}),
        }

def execute_reset_password_event(event, context):
    if os.environ['EnvName'] != 'Prod':
        print(json.dumps(event))

    params = json.loads(event['body'] or '')
    if not params:
        return {
            "statusCode": 406,
            "headers": create_common_header(),
            "body": json.dumps({'message': 'Insufficient input'}),
        }
    reset_token = params['params']['token'] or ''
    if not reset_token:
        return {
            "statusCode": 406,
            "headers": create_common_header(),
            "body": json.dumps({'message': 'Insufficient input'}),
        }

    reset_info = get_reset_password(reset_token)

    if not reset_info or not reset_info.get('user_id') or not reset_info.get('password'):
        return {
            "statusCode": 404,
            "headers": create_common_header(),
            "body": json.dumps({'message': 'Not Found'}),
        }
    
    if not reset_password(reset_info['user_id'], reset_info['password'], reset_token):
        return {
            "statusCode": 500,
            "headers": create_common_header(),
            "body": json.dumps({'message': 'Failed to reset password'}),
        }

    return {
            "statusCode": 200,
            "headers": create_common_header(),
            "body": json.dumps({'message': 'success'}),
        }