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
from my_common import *
from model.auth import *
from my_mail import *
from dynamo_utility import *
from model.user import *
from model.memo import *

def get_user_data_event(event, context):
    if os.environ['EnvName'] != 'Prod':
        print(json.dumps(event))
    user_uuid: str = get_user_uuid_by_event(event)
    if not user_uuid:
        return create_common_return_array(401, {'message': 'session timeout'})

    user_data: dict = get_user_data_for_view(user_uuid)
    if not user_data:
        return create_common_return_array(500, {'message': 'Failed to get user data.'})
    
    return create_common_return_array(200, {"user": user_data,})

def update_user_data_event(event, context):
    if os.environ['EnvName'] != 'Prod':
        print(json.dumps(event))
    user_uuid: str = get_user_uuid_by_event(event)
    if not user_uuid:
        return create_common_return_array(401, {'message': 'session timeout',})
    
    # 各種入力を取ってくる
    params = json.loads(event['body'] or '{ }')
    if not params:
        return create_common_return_array(406, {'message': 'Insufficient input'})
    
    new_user_id: str          = params['params'].get('email', '')
    password: str             = params['params'].get('password', '')
    new_password: str         = params['params'].get('newPassword', '')
    confirm_new_password: str = params['params'].get('confirmNewPassword', '')

    # 入力不足
    if new_user_id == '':
        return create_common_return_array(406, {'message': 'Insufficient input'})
    
    # パスワード更新時の, 確認用パスワードが間違っている
    if new_password != confirm_new_password:
        return create_common_return_array(406, {'message': 'The password entries do not match.'})

    # 現在の設定を取る
    user_data: dict = get_user_data_by_uuid(user_uuid)

    if not user_data:
        return create_common_return_array(500, {'message': 'Failed to get user data.'})

    # ユーザ認証 (パスワードがない, SNS認証の場合はチェックしない)
    now_password = user_data.get('password')
    if password and not check_password(password, now_password):
        print('Wrong password: ' + user_data['uuid'])
        return create_common_return_array(401, {'message': 'Wrong Email or Password'})
    
    # ユーザIDの更新
    if new_user_id != user_data['user_id']:
        # 登録できるユーザIDかチェック
        if not get_can_be_registered_user(new_user_id):
            return create_common_return_array(403, {'message': 'Cannot be registered user id'})

        if not update_user_id(user_data, new_user_id):
            return create_common_return_array(500, {'message': 'Failed to update user_id'})
    
    # パスワードの更新
    if new_password != '':
        if not update_password(user_data['user_id'], new_password):
            return create_common_return_array(500, {'message': 'Failed to update password'})
    
    return create_common_return_array(200, {'message': 'success'})

def withdrawal_event(event, context):
    if os.environ['EnvName'] != 'Prod':
        print(json.dumps(event))
    user_uuid: str = get_user_uuid_by_event(event)
    if not user_uuid:
        return create_common_return_array(401, {'message': 'session timeout'})
    
    user_data: dict = get_user_data_by_uuid(user_uuid)

    if not user_data:
        print('failed to get user data')
        return create_common_return_array(500, {'message': 'Failed to withdrawal.'})
    
    if not change_delete_all_shares(user_uuid):
        print('failed to change share settings')
        return create_common_return_array(500, {'message': 'Failed to withdrawal.'})
    
    if not delete_session(get_session_token(event)):
        print('failed to logout')
        return create_common_return_array(500, {'message': 'Failed to withdrawal.'})
    
    if not withdrawal(user_data):
        print('failed to delete user data')
        return create_common_return_array(500, {'message': 'Failed to withdrawal.'})
    
    return create_common_return_array(200, {'message': 'success'})



