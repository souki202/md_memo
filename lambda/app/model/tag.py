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

TAG_TABLE_NAME = 'md_memo_tags' + os.environ['DbSuffix']
TAG_RELATION_TABLE_NAME = 'md_memo_tag_and_memo_relation' + os.environ['DbSuffix']
tags_table = db_resource.Table(TAG_TABLE_NAME)
tag_relation_table = db_resource.Table(TAG_RELATION_TABLE_NAME)

GET_SEARCH_MEMO_PER_PAGE = 20

'''
タグを作成

@return str 成功すればタグのuuid, 失敗すればfalse
'''
def create_tag(name: str, user_uuid: str) -> str:
    tag_uuid = str(uuid.uuid4())

    try:
        res = tags_table.put_item(
            Item = {
                'uuid': tag_uuid,
                'name': name,
                'user_uuid': user_uuid,
                'created_at': get_now_string()
            }
        )
        if not res:
            return False
        return tag_uuid
    except Exception as e:
        print(e)
        return False
    return False

def update_tag_name(name: str, tag_uuid: str):
    try:
        res = tags_table.update_item(
            Key = {
                'uuid': tag_uuid
            },
            UpdateExpression = 'set name=:tag_name',
            ExpressionAttributeValues = {
                ':tag_name': name
            },
            ReturnValues="UPDATED_NEW"
        )
        return not not res
    except Exception as e:
        print(e)
        return False
    return False

def get_all_tags(user_uuid):
    try:
        exclusive_start_key = None
        items = []
        while True:
            if exclusive_start_key is None:
                res = tags_table.query(
                        IndexName='user_uuid-name-index',
                        KeyConditionExpression=Key('user_uuid').eq(user_uuid)
                    )
            else:
                res = tags_table.query(
                        IndexName='user_uuid-name-index',
                        KeyConditionExpression=Key('user_uuid').eq(user_uuid),
                        ExclusiveStartKey=exclusive_start_key
                    )
            items.extend(res['Items'])
            if ("LastEvaluatedKey" in res) == True:
                ExclusiveStartKey = res["LastEvaluatedKey"]
            else:
                break
        if len(items) == 0:
            return []
        return items
    except Exception as e:
        print(e)
        return False
    return False

def get_tag(tag_uuid: str):
    try:
        res = tags_table.query(
            KeyConditionExpression=Key('uuid').eq(tag_uuid)
        )['Items']
        if not res:
            return False
        return res[0]
    except Exception as e:
        print(e)
        return False
    return False

def get_tags_count(user_uuid: str):
    try:
        res = tags_table.query(
            IndexName='user_uuid-name-index',
            KeyConditionExpression=Key('user_uuid').eq(user_uuid),
            Select='COUNT'
        )
        if not res:
            return None
        return res['Count']
    except Exception as e:
        print(e)
        return None
    return None

def get_tag_id(user_uuid: str, name: str):
    try:
        res = tags_table.query(
            IndexName = 'user_uuid-name-index',
            KeyConditionExpression=Key('user_uuid').eq(user_uuid) & Key('name').eq(name)
        )['Items']
        if not res:
            return None
        return res[0]['uuid']
    except Exception as e:
        print(e)
        return False
    return False

def get_tag_relations(memo_uuid: str) -> list:
    try:
        res = tag_relation_table.query(
            IndexName='memo_uuid-index',
            KeyConditionExpression=Key('memo_uuid').eq(memo_uuid)
        )['Items']
        if not res:
            return []
        return res
    except Exception as e:
        print(e)
        return False
    return False

def set_tag_relation(tag_uuid: str, memo_uuid: str, memo_created_at: str) -> bool:
    try:
        res = tag_relation_table.put_item(
            Item = {
                'tag_uuid': tag_uuid,
                'memo_uuid': memo_uuid,
                'memo_created_at': memo_created_at
            }
        )
        return not not res
    except Exception as e:
        print(e)
        return False
    return False

def delete_tag_relation(tag_uuid: str, memo_uuid: str) -> bool:
    try:
        res = tag_relation_table.delete_item(
            Key = {
                'tag_uuid': tag_uuid,
                'memo_uuid': memo_uuid
            }
        )
        return not not res
    except Exception as e:
        print(e)
        return False
    return False

def delete_tag_relation_multi(tag_uuids: list, memo_id: str) -> bool:
    try:
        with tag_relation_table.batch_writer() as batch:
            for tag_uuid in tag_uuids:
                batch.delete_item(
                    Key = {
                        'tag_uuid': tag_uuid,
                        'memo_uuid': memo_id
                    }
                )
        return True
    except Exception as e:
        print(e)
        return False
    return False

def delete_tag_relations_by_memo_id(memo_id: str) -> bool:
    if not memo_id:
        return False
    
    # メモとのrelationを全て取得
    relations = get_tag_relations(memo_id)
    if relations == False:
        return False
    # 単に関連付けがない場合
    if not relations:
        return True

    try:
        uuids = [r['tag_uuid'] for r in relations]
        return delete_tag_relation_multi(uuids, memo_id)
    except Exception as e:
        print(e)
        return False
    return False

def check_is_owner_of_the_tag(tag_uuid: str, user_uuid: str) -> bool:
    tag_data = get_tag(tag_uuid)
    if not tag_data:
        return False
    
    return tag_data['user_uuid'] == user_uuid

'''
検索結果を取得
'''
def get_memo_uuids_by_tag(tag_uuid: str, exclusive_start_key: dict) -> list:
    try:
        res = None
        if exclusive_start_key is None:
            res = tag_relation_table.query(
                IndexName='tag_uuid-memo_created_at-index',
                KeyConditionExpression=Key('tag_uuid').eq(tag_uuid),
                Limit=GET_SEARCH_MEMO_PER_PAGE
            )
        else:
            res = tag_relation_table.query(
                IndexName='tag_uuid-memo_created_at-index',
                KeyConditionExpression=Key('tag_uuid').eq(tag_uuid),
                ExclusiveStartKey=exclusive_start_key,
                Limit=GET_SEARCH_MEMO_PER_PAGE
            )
        items = res['Items']
        exclusive_start_key = res.get('LastEvaluatedKey')

        if len(items) == 0:
            return [], None
        items = [i['memo_uuid'] for i in items]
        return items, exclusive_start_key
    except Exception as e:
        print(e)
        return False
    return False