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
from model.auth import *
from my_mail import *
from model.user import *
from model.auth import *
from user import *
import firebase_admin
from firebase_admin import credentials, auth

def create_firebase_credentials():
    filepath = ''
    if os.environ['EnvName'] == 'Prod':
        filepath = ''
    elif os.environ['EnvName'] == 'Stg':
        filepath =  'credentials/md-memo-dev-firebase-adminsdk-qwftc-e039f06975.json'
    elif os.environ['EnvName'] == 'Dev':
        filepath =  'credentials/md-memo-dev-firebase-adminsdk-qwftc-e039f06975.json'
    elif os.environ['EnvName'] == 'Local':
        filepath =  'credentials/md-memo-dev-firebase-adminsdk-qwftc-e039f06975.json'
    return credentials.Certificate(filepath)

db_client = boto3.resource("dynamodb")
users_table = db_client.Table('md_memo_users' + os.environ['DbSuffix'])
sessions_table = db_client.Table('md_memo_sessions' + os.environ['DbSuffix'])
reset_password_table = db_client.Table('md_memo_reset_password' + os.environ['DbSuffix'])
EXPIRATION_RESET_PASS = 60 * 5 # 5分


def login(event, context):
    if os.environ['EnvName'] != 'Prod':
        print(json.dumps(event))

    params = json.loads(event['body'] or '')
    email = params['params']['email'] or ''
    password = params['params']['password'] or ''
    if not email or not password:
        return create_common_return_array(401, {'message': 'Missing Email or Password.',})

    # ログイン履歴の確認と追加
    ip_address = event['requestContext']['identity']['sourceIp']
    if not check_login_history(email, ip_address):
        return create_common_return_array(401, {'message': 'Reached the maximum number of logins.', 'limit_try_login': True})
    
    if not add_login_history(email, ip_address):
        return create_common_return_array(500, {'message': 'Failure add login history.',})


    # 既存のユーザがいるか調べる
    existing_user = get_user(email)

    # ユーザの取得でエラーが発生した
    if existing_user == False:
        return create_common_return_array(401, {'message': 'Failure search existing user.',})
    
    # ユーザがいなかった
    if existing_user is None:
        print('Missing user: ' + email)
        return create_common_return_array(401, {'message': 'Wrong email or password.',})
    
    # 仮登録状態なら終了
    if existing_user.get('is_temporary', False):
        print("Temporary user. login failed")
        return create_common_return_array(401, {'message': 'Temporary user.',})

    # パスワードチェック
    if not check_password(password, existing_user.get('password')):
        print('Wrong password: ' + email)
        return create_common_return_array(401, {'message': 'Wrong email or password.',})
    
    # セッション作成
    user_uuid = existing_user['uuid']
    create_result, session_token = create_session(user_uuid)
    if create_result == False:
        return create_common_return_array(500, {'message': 'Failure create session.',})
    
    return create_common_return_array(200, {"token": session_token})

def signup(event, context):
    if os.environ['EnvName'] != 'Prod':
        print(json.dumps(event))
    params = json.loads(event['body'])
    email = params['params']['email'] or ''
    password = params['params']['password'] or ''
    if not email or not password:
        return create_common_return_array(403, {'message': 'Missing Email or Password.',})

    # 登録できるユーザIDかチェック
    if not get_can_be_registered_user(email):
        return create_common_return_array(403, {'message': 'Cannot be registered user id.',})

    # ユーザがいないので新規登録
    ph = PasswordHasher()
    pass_hash = ph.hash(password)

    # ユーザ作成
    create_result, user_uuid, temp_token = add_user(email, pass_hash)
    print(user_uuid)
    if create_result == False:
        return create_common_return_array(500, {'message': 'Failure add user.',})

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

    return create_common_return_array(200, {})

def sns_login(event, context):
    if os.environ['EnvName'] != 'Prod':
        print(json.dumps(event))
    
    params = json.loads(event['body'] or '{ }')
    if not params:
        return create_common_return_array(406, {'message': 'Insufficient input'})
    
    id_token: str = params['params'].get('id_token', '')

    # 初期化済みかを判定する
    if not firebase_admin._apps:
        # 初期済みでない場合は初期化処理を行う
        cred = create_firebase_credentials()
        firebase_admin.initialize_app(cred)
    
    sns_user_id = ''
    sns_email   = ''
    try:
        id_info     = auth.verify_id_token(id_token)
        sns_user_id = id_info['sub']
        sns_email   = id_info['email']
    except Exception as e:
        print('invalid token')
        print(e)
        return create_common_return_array(401, {'message': "Invalid token."})

    # SNS登録済なら値が取得できる
    user_id   = get_user_id_by_firebase_user_id(sns_user_id)
    user_uuid = ''
    if user_id == False: # Noneは単にユーザがいない場合, Falseはエラー
        print('Error on get_user_id_by_firebase_user_id')
        return create_common_return_array(500, {'message': "Server error"})
    
    if user_id is None:
        # 新規登録
        # 登録できるemailかチェック
        if not get_can_be_registered_user(sns_email):
            print('Alreadly registerd: ' + sns_email)
            return create_common_return_array(403, {'message': "Already registered", 'registerd': True})
        # ユーザ作成
        create_result, user_uuid, temp_token = add_firebase_user(sns_email, sns_user_id)
        if not create_result:
            return create_common_return_array(500, {'message': "Failure add user."})
    else:
        user_data = get_user(user_id)
        if not user_data:
            return create_common_return_array(500, {'message': "Failure get user data."})
        user_uuid = user_data['uuid']

    # ログインする
    create_result, session_token = create_session(user_uuid)
    if create_result == False:
        return create_common_return_array(500, {'message': 'Failure create session.',})

    return create_common_return_array(200, {"token": session_token})

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