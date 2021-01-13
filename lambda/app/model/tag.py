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
tags_table = db_resource.Table(TAG_TABLE_NAME)

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
                        IndexName='user_uuid-index',
                        KeyConditionExpression=Key('user_uuid').eq(user_uuid)
                    )
            else:
                res = tags_table.query(
                        IndexName='user_uuid-index',
                        KeyConditionExpression=Key('user_uuid').eq(user_uuid),
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
            IndexName='user_uuid-index',
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