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
from dynamo_utility import *

db_resource = boto3.resource("dynamodb")
db_client = boto3.client("dynamodb", region_name='ap-northeast-1')
USERS_TABLE_NAME = 'md_memo_users' + os.environ['DbSuffix']
RESET_PASS_TABLE_NAME = 'md_memo_reset_password' + os.environ['DbSuffix']
users_table = db_resource.Table(USERS_TABLE_NAME)
sessions_table = db_resource.Table('md_memo_sessions' + os.environ['DbSuffix'])
reset_password_table = db_resource.Table(RESET_PASS_TABLE_NAME)

'''
user_idからユーザ情報を取得

@return {dict|False} 取得にエラーが発生すればFalse, 成功すればそのdictかNone
'''
def get_user(id: str):
    try:
        result = users_table.query(
            KeyConditionExpression=Key('user_id').eq(id)
        )['Items']
        if len(result) == 0:
            print('Not found user id: ' + id)
            return None
        return result[0]
    except Exception as e:
        print(e)
        return False
    return False

def get_can_be_registered_user(user_id: str) -> bool:
    # 更新後のIDですでに登録されていないかチェック
    existing_user = get_user(user_id)

    # ユーザの取得でエラーが発生した
    if existing_user == False:
        print('Failure search existing user')
        return False
    # ユーザが既に存在した
    if existing_user is not None:
        print('The user is already registered.')
        return False
    return True

def get_user_data_by_uuid(user_uuid: str) -> dict:
    if not user_uuid:
        return None
    try:
        result = users_table.query(
            IndexName = 'uuid-index',
            KeyConditionExpression=Key('uuid').eq(user_uuid)
        )['Items']
        if len(result) == 0:
            print('Not found user uuid: ' + user_uuid)
            return None
        return result[0]
    except Exception as e:
        print(e)
        return False
    return False

def get_user_data_for_view(user_uuid: str) -> dict:
    user_data = get_user_data_by_uuid(user_uuid)
    if not user_data:
        return None
    del user_data['uuid']
    del user_data['password']
    if 'temporary_token' in user_data:
        del user_data['temporary_token']
    return user_data

def update_user_id(user_data: dict, new_user_id: str):
    old_user_id = user_data['user_id']
    now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    user_data['user_id'] = new_user_id
    user_data['update_at'] = now
    try:
        result = db_client.transact_write_items(
            TransactItems = [
                {
                    'Delete': {
                        'TableName': USERS_TABLE_NAME,
                        'Key': {
                            'user_id': to_dynamo_format(old_user_id),
                        }
                    }
                },
                {
                    'Put': {
                        'TableName': USERS_TABLE_NAME,
                        'Item': dict2dynamoformat(user_data),
                    }
                }
            ]
        )
        print(result)
        return not not result
    except Exception as e:
        print(e)
        return False
    return False

def reset_password(user_id: str, pass_hash: str, reset_token: str):
    try:
        result = db_client.transact_write_items(
            TransactItems = [
                {
                    'Delete': {
                        'TableName': RESET_PASS_TABLE_NAME,
                        'Key': {
                            'reset_token': to_dynamo_format(reset_token),
                        },
                    }
                },
                {
                    'Update': {
                        'TableName': USERS_TABLE_NAME,
                        'Key': {
                            'user_id': to_dynamo_format(user_id)
                        },
                        'UpdateExpression': 'SET password=:password',
                        'ExpressionAttributeValues': {
                            ':password': to_dynamo_format(pass_hash)
                        }
                    }
                }
            ]
        )
        return not not result
    except Exception as e:
        print(e)
        return False
    return False

def update_password(user_id: str, new_password: str):
    ph = PasswordHasher()
    pass_hash = ph.hash(new_password)
    return update_password_hash(user_id, pass_hash)

def update_password_hash(user_id: str, pass_hash: str):
    try:
        now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        result = users_table.update_item(
            Key = {
                'user_id': user_id,
            },
            UpdateExpression = 'set password=:password, updated_at=:updated_at',
            ExpressionAttributeValues = {
                ':password': pass_hash,
                ':updated_at': now,
            },
            ReturnValues="UPDATED_NEW"   
        )
        return not not result
    except Exception as e:
        print(e)
        return False
    return False

def get_user_by_temporary_token(token: str) -> dict:
    try:
        result = users_table.query(
            IndexName = 'temporary_token-index',
            KeyConditionExpression = Key('temporary_token').eq(token)
        )['Items']
        if len(result) == 0:
            return None
        return result[0]
    except Exception as e:
        print(e)
        return None
    return None

def release_temporary(user_id) -> bool:
    try:
        now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        result = users_table.update_item(
            Key = {
                'user_id': user_id,
            },
            UpdateExpression = 'set is_temporary=:is_temporary, updated_at=:updated_at',
            ExpressionAttributeValues = {
                ':is_temporary': False,
                ':updated_at': now,
            },
            ReturnValues="UPDATED_NEW"   
        )
        return not not result
    except Exception as e:
        print(e)
        return False
    return False

def add_user(id, passHash):
    now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    user_uuid = str(uuid.uuid4())
    temp_token = secrets.token_urlsafe(64)
    try:
        res = users_table.put_item(
           Item = {
               'user_id': id,
               'uuid': user_uuid,
               'password': passHash,
               'created_at': now,
               'updated_at': now,
               'is_temporary': True,
               'temporary_token': temp_token,
           }
        )
        return res, user_uuid, temp_token
    except Exception as e:
        print(e)
        return False, None, None
    return False, None, None

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