import json
import boto3
import os
import uuid
import datetime
import time
import secrets
from enum import Enum
from boto3.dynamodb.conditions import Key
from common_headers import *
from my_common import *
from dynamo_utility import *
from model.share import *
from service.user import *

db_resource = boto3.resource("dynamodb")
db_client = boto3.client("dynamodb", region_name='ap-northeast-1')

MEMO_PAGE_LIMIT = 20

class MemoStates(Enum):
    AVAILABLE = 1
    TRASH = 2
    DELETED = 3

class PinnedType(Enum):
    NO_PINNED = 1
    PINNED = 2

MEMO_OVERVIEWS_TABLE_NAME = 'md_memo_overviews' + os.environ['DbSuffix']
MEMO_TRASH_TABLE_NAME = 'md_memo_trash_memos' + os.environ['DbSuffix']
MEMO_BODIES_TABLE_NAME = 'md_memo_bodies' + os.environ['DbSuffix']
MEMO_SHARES_TABLE_NAME = 'md_memo_shares' + os.environ['DbSuffix']

memo_overviews_table = db_resource.Table(MEMO_OVERVIEWS_TABLE_NAME)
memo_trash_table = db_resource.Table(MEMO_TRASH_TABLE_NAME)
memo_bodies_table = db_resource.Table(MEMO_BODIES_TABLE_NAME)
memo_shares_table = db_resource.Table(MEMO_SHARES_TABLE_NAME)

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
def check_is_owner_of_the_memo(memo_id: str, user_uuid: str) -> bool:
    if not memo_id or not user_uuid:
        return False
    try:
        result = get_memo_overview(memo_id)
        if not result:
            return False
        return result['user_uuid'] == user_uuid
    except Exception as e:
        print(e)
        return False

def check_id_owner_of_the_memo_by_data(memo_data: dict, user_uuid: str) -> bool:
    return memo_data['user_uuid'] == user_uuid

'''
すべてのメモが持ち主と一致しているか確認する
'''
def check_is_owner_of_the_memo_multi(memo_id_list: list, user_uuid: str) -> bool:
    for memo_id in memo_id_list:
        if not check_is_owner_of_the_memo(memo_id, user_uuid):
            return False
    return True

def get_memo_list_include_trash(user_uuid):
    try:
        exclusive_start_key = None
        items = []
        while True:
            if exclusive_start_key is None:
                response = memo_overviews_table.query(
                    IndexName='user_uuid-created_at-index',
                    KeyConditionExpression=Key('user_uuid').eq(user_uuid),
                    ScanIndexForward = False,
                    )
            else:
                response = memo_overviews_table.query(
                    IndexName='user_uuid-created_at-index',
                    KeyConditionExpression=Key('user_uuid').eq(user_uuid),
                    ScanIndexForward = False,
                    ExclusiveStartKey=exclusive_start_key
                )
            items.extend([i['uuid'] for i in response['Items']])
            if ("LastEvaluatedKey" in response) == True:
                ExclusiveStartKey = response["LastEvaluatedKey"]
            else:
                break
        if len(items) == 0:
            return []
        return items
    except Exception as e:
        print(e)
        return None
    return None

def get_all_memo_ids(user_uuid: str) -> list:
    try:
        exclusive_start_key = None
        items = []
        while True:
            if exclusive_start_key is None:
                response = memo_overviews_table.query(
                    IndexName='user_uuid-created_at-index',
                    ProjectionExpression='#my_uuid',
                    ExpressionAttributeNames= {
                        '#my_uuid' : 'uuid'
                    },
                    ReturnConsumedCapacity="TOTAL",
                    KeyConditionExpression=Key('user_uuid').eq(user_uuid),
                    ScanIndexForward = False,
                    )
            else:
                response = memo_overviews_table.query(
                    IndexName='user_uuid-created_at-index',
                    ProjectionExpression='uuid',
                    KeyConditionExpression=Key('user_uuid').eq(user_uuid),
                    ScanIndexForward = False,
                    ExclusiveStartKey=exclusive_start_key
                )
            items.extend([i['uuid'] for i in response['Items']])
            if ("LastEvaluatedKey" in response) == True:
                ExclusiveStartKey = response["LastEvaluatedKey"]
            else:
                break
        if len(items) == 0:
            return []
        return items
    except Exception as e:
        print(e)
        return None
    return None

def get_available_memo_list_page(user_uuid: str, exclusive_start_key:dict):
    return get_memo_list_page(user_uuid, exclusive_start_key)

def get_memo_list_in_trash_page(user_uuid: str, exclusive_start_key:dict):
    return get_memo_list_page(user_uuid, exclusive_start_key)

'''
メモ一覧を取得する

@return {list, str} メモ一覧, 次の取得に使用するキー
'''
def get_memo_list_page(user_uuid, exclusive_start_key):
    try:
        items = []
        if exclusive_start_key is None:
            response = memo_overviews_table.query(
                IndexName='user_uuid-created_at-index',
                KeyConditionExpression=Key('user_uuid').eq(user_uuid),
                ScanIndexForward = False,
                Limit=MEMO_PAGE_LIMIT
            )
        else:
            response = memo_overviews_table.query(
                IndexName='user_uuid-created_at-index',
                KeyConditionExpression=Key('user_uuid').eq(user_uuid),
                ExclusiveStartKey=exclusive_start_key,
                ScanIndexForward = False,
                Limit=MEMO_PAGE_LIMIT
            )
        items = response['Items']
        exclusive_start_key = response.get('LastEvaluatedKey')

        if len(items) == 0:
            return [], None
        return items, exclusive_start_key
    except Exception as e:
        print(e)
        return None, None
    return None, None

def get_memo_list_in_trash_page(user_uuid, exclusive_start_key):
    try:
        items = []
        if exclusive_start_key is None:
            response = memo_trash_table.query(
                IndexName='user_uuid-created_at-index',
                KeyConditionExpression=Key('user_uuid').eq(user_uuid),
                ScanIndexForward = False,
                Limit=MEMO_PAGE_LIMIT
            )
        else:
            response = memo_trash_table.query(
                IndexName='user_uuid-created_at-index',
                KeyConditionExpression=Key('user_uuid').eq(user_uuid),
                ExclusiveStartKey=exclusive_start_key,
                ScanIndexForward = False,
                Limit=MEMO_PAGE_LIMIT
            )
        items = response['Items']
        exclusive_start_key = response.get('LastEvaluatedKey')

        if len(items) == 0:
            return [], None
        return items, exclusive_start_key
    except Exception as e:
        print(e)
        return None, None
    return None, None

def get_pinned_memo_list(user_uuid):
    state = MemoStates.AVAILABLE.value
    try:
        exclusive_start_key = None
        items = []
        while True:
            if exclusive_start_key is None:
                response = memo_overviews_table.query(
                    IndexName='user_uuid-pinned_type-index',
                    KeyConditionExpression=Key('user_uuid').eq(user_uuid) & Key('pinned_type').eq(PinnedType.PINNED.value),
                    ScanIndexForward = False
                )
            else:
                response = memo_overviews_table.query(
                    IndexName='user_uuid-pinned_type-index',
                    KeyConditionExpression=Key('user_uuid').eq(user_uuid) & Key('pinned_type').eq(PinnedType.PINNED.value),
                    ScanIndexForward = False,
                    ExclusiveStartKey=exclusive_start_key
                )
            items.extend(response['Items'])
            if ("LastEvaluatedKey" in response) == True:
                ExclusiveStartKey = response["LastEvaluatedKey"]
            else:
                break
        if len(items) == 0:
            return []
        return items
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
            KeyConditionExpression=Key('uuid').eq(memo_id),
        )['Items']
        # 無ければゴミ箱から検索
        if len(result) == 0:
            return get_memo_overview_in_trash(memo_id)
        return result[0]
    except Exception as e:
        print(e)
        return None
    return None

def get_memo_overview_in_trash(memo_id: str) -> dict:
    if not memo_id:
        return None
    try:
        # overviewの取得
        result = memo_trash_table.query(
            KeyConditionExpression=Key('uuid').eq(memo_id),
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
            KeyConditionExpression=Key('uuid').eq(memo_id),
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
        return False
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
        return False
    return False

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

'''
そのメモそのものの情報をハードデリートする
リレーション周りは削除しない
'''
def delete_memo(memo_id: str) -> bool:
    try:
        transacts = [
            {
                # overviewの消去
                'Delete': {
                    'TableName': MEMO_TRASH_TABLE_NAME,
                    'Key': {
                        'uuid': to_dynamo_format(memo_id)
                    },
                },
                # bodyの消去
                'Delete': {
                    'TableName': MEMO_BODIES_TABLE_NAME,
                    'Key': {
                        'uuid': to_dynamo_format(memo_id)
                    },
                }
            }
        ]
        # シェア設定があればそれも削除
        share_settings = get_share_setting_by_memo_id(memo_id)
        if share_settings:
            transacts.append({
                'Delete': {
                    'TableName': MEMO_SHARES_TABLE_NAME,
                    'Key': {
                        'share_id': to_dynamo_format(share_settings['share_id'])
                    }
                }
            })
        # 削除処理
        res = db_client.transact_write_items(
            TransactItems = transacts
        )
        return not not res
    except Exception as e:
        print(e)
        return False
    return False

'''
メモをゴミ箱に移動する
シェアは物理削除
'''
def move_trash_memo(memo_id):
    share_settings = get_share_setting_by_memo_id(memo_id)
    if share_settings == False:
        return False
    # メモ設定を取得
    memo_info = get_memo_overview(memo_id)
    if not memo_info:
        return False
    
    if 'pinned_type' in memo_info:
        del memo_info['pinned_type']
    memo_info['deleted_at'] = get_now_string()
    try:
        res = memo_trash_table.put_item(
            Item=memo_info
        )
        if not res:
            return False
        transacts = [
            {
                'Delete': {
                    'TableName': MEMO_OVERVIEWS_TABLE_NAME,
                    'Key': {
                        'uuid': to_dynamo_format(memo_id)
                    },
                }
            }
        ]
        if share_settings:
            transacts.append({
                'Delete': {
                    'TableName': MEMO_SHARES_TABLE_NAME,
                    'Key': {
                        'share_id': to_dynamo_format(share_settings['share_id'])
                    }
                }
            })
        result = db_client.transact_write_items(
            TransactItems = transacts
        )
        return not not result
    except Exception as e:
        print(e)
        # 消したデータを戻す
        memo_trash_table.delete_item(
            Key={
                'uuid': memo_info['uuid']
            }
        )
        return False

def delete_share_setting(share_id):
    try:
        res = memo_shares_table.delete_item(
            Key={
                'share_id': share_id
            }
        )
        return not not res
    except Exception as e:
        print(e)
        return False

def change_delete_all_shares(user_uuid: str) -> bool:
    memo_list = get_all_memo_ids(user_uuid)
    for memo_id in memo_list:
        share_settings = get_share_setting_by_memo_id(memo_id)
        # シェア設定があれば削除
        if share_settings:
            result = delete_share_setting(share_settings['share_id'])
            if not result:
                print('Failed to share settings: ' + memo_id)
                return False
    return True

def update_pinned_memo(memo_id: str, state: int) -> bool:
    if not memo_id or not state:
        return False

    try:
        result = memo_overviews_table.update_item(
            Key = {
                'uuid': memo_id
            },
            UpdateExpression = 'set pinned_type=:pinned_type',
            ExpressionAttributeValues = {
                ':pinned_type': state,
            },
            ReturnValues="UPDATED_NEW"
        )
        return not not result
    except Exception as e:
        print(e)
        return False
    return False


