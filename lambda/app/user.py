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
from dynamo_utility import *
from model.user import *
from model.memo import *
# from oauth2client import client, crypt
from firebase_admin import credentials

def get_google_client():
    return {
        'client_id': '376887486571-aeu7qvvt6013p0agsralcs6kekvon295.apps.googleusercontent.com',
        'secret': 'oEEPOw21nQn2XBU0-mfjpz5_'
    }

def firebase_key():
    if os.environ['EnvName'] == 'Prod':
        return ''
    elif os.environ['EnvName'] == 'Stg':
        return ''
    elif os.environ['EnvName'] == 'Dev':
        return 'AAAA71eSPY8:APA91bHlJi2hzI6zeCOPld6fIgO-E-tWVa9b0UqadBoS6Foo1qyE-WLZ-3IYHsOzIkMLkjpfnyDjehJrWQvkHQQoCkzrp7ISyEPy_VJxjYERyfFLiqGqRAtW-dkiXD05HfF4-FdZpBE_'
    elif os.environ['EnvName'] == 'Local':
        return 'AAAA71eSPY8:APA91bHlJi2hzI6zeCOPld6fIgO-E-tWVa9b0UqadBoS6Foo1qyE-WLZ-3IYHsOzIkMLkjpfnyDjehJrWQvkHQQoCkzrp7ISyEPy_VJxjYERyfFLiqGqRAtW-dkiXD05HfF4-FdZpBE_'

def create_firebase_credentials():
    filepath = ''
    if os.environ['EnvName'] == 'Prod':
        filepath = ''
    elif os.environ['EnvName'] == 'Stg':
        filepath = ''
    elif os.environ['EnvName'] == 'Dev':
        filepath =  'credentials/md-memo-dev-firebase-adminsdk-qwftc-e039f06975.json'
    elif os.environ['EnvName'] == 'Local':
        filepath =  'credentials/md-memo-dev-firebase-adminsdk-qwftc-e039f06975.json'
    return credentials.Certificate(filepath)

def get_user_data_event(event, context):
    if os.environ['EnvName'] != 'Prod':
        print(json.dumps(event))
    user_uuid: str = get_user_uuid_by_event(event)
    if not user_uuid:
        return {
            "statusCode": 401,
            "headers": create_common_header(),
            "body": json.dumps({'message': "session timeout",}),
        }
    user_data: dict = get_user_data_for_view(user_uuid)
    if not user_data:
        return {
            "statusCode": 500,
            "headers": create_common_header(),
            "body": json.dumps({'message': "Failed to get user data.",}),
        }
    return {
        "statusCode": 200,
        "headers": create_common_header(),
        "body": json.dumps({"user": user_data,}),
    }

def update_user_data_event(event, context):
    if os.environ['EnvName'] != 'Prod':
        print(json.dumps(event))
    user_uuid: str = get_user_uuid_by_event(event)
    if not user_uuid:
        return {
            "statusCode": 401,
            "headers": create_common_header(),
            "body": json.dumps({'message': "session timeout",}),
        }
    
    # 各種入力を取ってくる
    params = json.loads(event['body'] or '{ }')
    if not params:
        return {
            "statusCode": 406,
            "headers": create_common_header(),
            "body": json.dumps({'message': 'Insufficient input'}),
        }
    
    new_user_id: str          = params['params'].get('email', '')
    password: str             = params['params'].get('password', '')
    new_password: str         = params['params'].get('newPassword', '')
    confirm_new_password: str = params['params'].get('confirmNewPassword', '')

    # 入力不足
    if new_user_id == '' or password == '':
        return {
            "statusCode": 406,
            "headers": create_common_header(),
            "body": json.dumps({'message': 'Insufficient input'}),
        }
    
    # パスワード更新時の, 確認用パスワードが間違っている
    if new_password != confirm_new_password:
        return {
            "statusCode": 406,
            "headers": create_common_header(),
            "body": json.dumps({'message': 'The password entries do not match.'}),
        }

    # 現在の設定を取る
    user_data: dict = get_user_data_by_uuid(user_uuid)

    if not user_data:
        return {
            "statusCode": 500,
            "headers": create_common_header(),
            "body": json.dumps({'message': "Failed to get user data.",}),
        }

    # ユーザ認証
    if not check_password(password, user_data['password']):
        print('Wrong password: ' + user_data['uuid'])
        return {
            "statusCode": 401,
            "headers": create_common_header(),
            "body": json.dumps({'message': "Wrong password.",}),
        }
    
    # ユーザIDの更新
    if new_user_id != user_data['user_id']:
        # 登録できるユーザIDかチェック
        if not get_can_be_registered_user(new_user_id):
            return {
                "statusCode": 403,
                "headers": create_common_header(),
                "body": json.dumps({'message': "Cannot be registered user id",}),
            }
        if not update_user_id(user_data, new_user_id):
            return {
                "statusCode": 500,
                "headers": create_common_header(),
                "body": json.dumps({'message': "Failed to update user_id.",}),
            }
    
    # パスワードの更新
    if new_password != '':
        if not update_password(user_data['user_id'], new_password):
            return {
                "statusCode": 500,
                "headers": create_common_header(),
                "body": json.dumps({'message': "Failed to update password.",}),
            }

    return {
        "statusCode": 200,
        "headers": create_common_header(),
        "body": json.dumps({'message': 'success',}),
    }

# def google_login(event, context):
#     if os.environ['EnvName'] != 'Prod':
#         print(json.dumps(event))
    
#     params = json.loads(event['body'] or '{ }')
#     if not params:
#         return {
#             "statusCode": 406,
#             "headers": create_common_header(),
#             "body": json.dumps({'message': 'Insufficient input'}),
#         }
    
#     id_token: str = params['params'].get('id_token', '')

#     cred = create_firebase_credentials()
#     firebase_admin.initialize_app(cred)

#     try:
#         idinfo = client.verify_id_token(id_token, get_google_client()['secret'])
#         print(idinfo)
#         if idinfo['iss'] not in ['accounts.google.com', 'https://accounts.google.com']:
#             raise crypt.AppIdentityError("Wrong issuer.")
#         if idinfo['hd'] != get_domain():
#             raise crypt.AppIdentityError("Wrong hosted domain.")
#     except crypt.AppIdentityError as e:
#         print('invalid google token')
#         print(e)
#         return create_common_return_array(401, {'message': "Invalid token."})

#     userid = idinfo['sub']
#     return create_common_return_array(200, {'message': "loggined."})



def withdrawal_event(event, context):
    if os.environ['EnvName'] != 'Prod':
        print(json.dumps(event))
    user_uuid: str = get_user_uuid_by_event(event)
    if not user_uuid:
        return {
            "statusCode": 401,
            "headers": create_common_header(),
            "body": json.dumps({'message': "session timeout",}),
        }
    
    user_data: dict = get_user_data_by_uuid(user_uuid)

    if not user_data:
        print('failed to get user data')
        return {
            "statusCode": 500,
            "headers": create_common_header(),
            "body": json.dumps({'message': "Failed to leave service.",}),
        }
    
    if not change_all_memos_to_private(user_uuid):
        print('failed to change share settings')
        return {
            "statusCode": 500,
            "headers": create_common_header(),
            "body": json.dumps({'message': "Failed to leave service.",}),
        }
    
    if not delete_session(get_session_token(event)):
        print('failed to logout')
        return {
            "statusCode": 500,
            "headers": create_common_header(),
            "body": json.dumps({'message': "Failed to leave service.",}),
        }
    
    if not withdrawal(user_data):
        print('failed to delete user data')
        return {
            "statusCode": 500,
            "headers": create_common_header(),
            "body": json.dumps({'message': "Failed to leave service.",}),
        }

    return {
        "statusCode": 200,
        "headers": create_common_header(),
        "body": json.dumps({'message': 'success',}),
    }




