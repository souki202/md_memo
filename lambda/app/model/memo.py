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



