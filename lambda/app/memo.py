import json
import boto3
import os
import uuid
import datetime
import time
import secrets
from enum import Enum
from decimal import Decimal
from common_headers import *
from model.auth import *
from my_common import *
from model.user import *
from model.memo import *
from model.plan import *
import model.file as my_file
from model.share import *
import model.tag as my_tag

def decimal_default_proc(obj):
    if isinstance(obj, Decimal):
        return float(obj)
    raise TypeError

MULTIPLE_SELECT_MEMO_LIMIT = 10
MAX_TITLE_LEN = 200

def get_memo_list_event(event, context):
    if os.environ['EnvName'] != 'Prod':
        print(json.dumps(event))
    
    httpMethod = str.upper(event['httpMethod'])
    resource = str.lower(event['resource'])
    
    if httpMethod == 'GET':
        if resource == '/get_memo_list':
            return get_available_memo_list_event(event, context)
        elif resource == '/get_trash_memo_list':
            return get_trash_memo_list_event(event, context)
        elif resource == '/search_memo_by_tag':
            return search_memo_by_tag_event(event, context)

    return create_common_return_array(404, {'message': 'Not Found',})

def get_available_memo_list_event(event, context):
    user_uuid: str = get_user_uuid_by_event(event)
    if not user_uuid:
        return create_common_return_array(401, {'message': "session timeout.",})
    
    exclusive_start_key = None
    if 'queryStringParameters' in event and event['queryStringParameters']:
        next_memo_uuid = event['queryStringParameters'].get('next_page_memo_id', '')
        exclusive_start_key = {'user_uuid': user_uuid, 'uuid': next_memo_uuid}

    memos, exclusive_start_key = get_available_memo_list_page(user_uuid, exclusive_start_key)
    next_page_memo_id = ''
    if exclusive_start_key is not None:
        next_page_memo_id = exclusive_start_key['uuid']
    
    if memos is None:
        print('Failed get memo list.')
        print('user_uuid: ' + user_uuid)
        return create_common_return_array(500, {'message': "Failed to get the memo list.",})

    for memo in memos:
        del memo['user_uuid']
    
    return create_common_return_array(200, {'items': memos, 'next_page_memo_id': next_page_memo_id})

def get_trash_memo_list_event(event, context):
    user_uuid: str = get_user_uuid_by_event(event)
    if not user_uuid:
        return create_common_return_array(401, {'message': "session timeout.",})
    
    exclusive_start_key = None
    if 'queryStringParameters' in event and event['queryStringParameters']:
        next_memo_uuid = event['queryStringParameters'].get('next_page_memo_id', '')
        exclusive_start_key = {'user_uuid': user_uuid, 'uuid': next_memo_uuid}

    memos, exclusive_start_key = get_memo_list_in_trash_page(user_uuid, exclusive_start_key)
    next_page_memo_id = ''
    if exclusive_start_key is not None:
        next_page_memo_id = exclusive_start_key['uuid']
    
    if memos is None:
        print('Failed get memo list.')
        print('user_uuid: ' + user_uuid)
        return create_common_return_array(500, {'message': "Failed to get the memo list.",})

    for memo in memos:
        del memo['user_uuid']
    
    return create_common_return_array(200, {'items': memos, 'next_page_memo_id': next_page_memo_id})

def search_memo_by_tag_event(event, context):
    user_uuid: str = get_user_uuid_by_event(event)
    if not user_uuid:
        return create_common_return_array(401, {'message': "session timeout.",})
    
    tag_uuid: str = event.get('queryStringParameters', {}).get('uuid', '')
    exclusive_start_key: str = event.get('queryStringParameters', {}).get('next_page_memo_id', '')
    if not tag_uuid:
        return create_common_return_array(406, {'message': 'Insufficient input'})

    # そのタグがログインユーザのものかチェック
    if not my_tag.check_is_owner_of_the_tag(tag_uuid, user_uuid):
        return create_common_return_array(401, {'message': 'Unauthorized'})
    
    # メモuuid一覧を取得
    memo_uuids, exclusive_start_key = my_tag.get_memo_uuids_by_tag(user_uuid, exclusive_start_key)
    if memo_uuids == False:
        print('Failed to get memo ids. tag_uuid: ' + tag_uuid)
        return create_common_return_array(500, {'message': 'Failed to get memo ids.'})

    # uuid一覧からoverview一覧を取得
    memos = get_memo_overviews_by_uuids(memo_uuids)
    return create_common_return_array(200, {'items': memos, 'next_page_memo_id': exclusive_start_key})

def get_pinned_memo_list_event(event, context):
    if os.environ['EnvName'] != 'Prod':
        print(json.dumps(event))
    user_uuid: str = get_user_uuid_by_event(event)
    if not user_uuid:
        return create_common_return_array(401, {'message': "session timeout.",})

    memos = get_pinned_memo_list(user_uuid)
    if memos is None:
        print('Failed get memo list.')
        print('user_uuid: ' + user_uuid)
        return create_common_return_array(500, {'message': "Failed to get the memo list.",})

    for memo in memos:
        del memo['user_uuid']
    return create_common_return_array(200, {'items': memos})

def get_memo_data_event(event, content):
    if os.environ['EnvName'] != 'Prod':
        print(json.dumps(event))
    
    memo_id = ''
    if 'queryStringParameters' in event:
        memo_id = event['queryStringParameters'].get('memo_id', '')

    user_uuid: str = get_user_uuid_by_event(event)
    if not user_uuid:
        return create_common_return_array(401, {'message': 'session timeout',})


    # 取得時はメモの持ち主が一致しているか確認
    if not check_is_owner_of_the_memo(memo_id, user_uuid):
        print('Unauthorized get memo data.')
        print({'user': user_uuid, 'memo_id': memo_id})
        return create_common_return_array(401, {'message': 'Unauthorized',})

    # メモ情報の取得
    memo_data = get_memo_data(memo_id)
    if not memo_data:
        return create_common_return_array(404, {'message': 'Not Found',})

    del memo_data['user_uuid']

    return create_common_return_array(200, {'memo': memo_data,})


def save_memo_event(event, context):
    if os.environ['EnvName'] != 'Prod':
        print(json.dumps(event))

    # 各種値を変数に
    params = json.loads(event['body'] or '{ }')
    if 'params' not in params:
        return create_common_return_array(406, {'message': 'Insufficient input'})

    title: str       = params['params'].get('memo', {}).get('title', '')
    memo_id: str     = params['params'].get('memo', {}).get('id', '')
    description: str = params['params'].get('memo', {}).get('description', '')
    memo_type: int   = int(params['params'].get('memo', {}).get('type', 1))
    body: str        = params['params'].get('memo', {}).get('body', '')
    is_trash: list      = params['params'].get('memo', {}).get('isTrash', [])
    files: list      = params['params'].get('files', [])

    if not title or not memo_type:
        return create_common_return_array(406, {'message': 'Insufficient input'})

    if len(title) > MAX_TITLE_LEN:
        return create_common_return_array(403, {'message': 'The title can be up to ' + str(MAX_TITLE_LEN) + ' characters long.',})

    user_uuid: str = get_user_uuid_by_event(event)
    # 更新はログイン必須
    if not user_uuid:
        return create_common_return_array(401, {'message': 'session timeout.',})

    user_data: dict = get_user_data_by_uuid(user_uuid)

    if is_trash:
        return create_common_return_array(401, {'message': 'Unauthorized'})

    # 文字数上限チェック
    if len(body) > get_memo_body_max_len(user_data['plan']):
        return create_common_return_array(401, {'message': 'The body length is up to ' + str(get_memo_body_max_len(user_data['plan'])) + ' characters.', 'is_limit_length': True})


    # 更新時はメモの編集権限があるかチェック
    if memo_id:
        share_settings: dict = get_share_setting_by_memo_id(memo_id)
        share_users: str = ''
        edit_auth: bool = False
        memo_data: dict = get_available_memo_overview(memo_id)

        if share_settings and share_settings['share_type'] == ShareType.EDITABLE.value:
            # シェア時に, 更新権限があるか調べる
            if share_settings['share_scope'] == ShareScope.SPECIFIC_USERS.value:
                share_users = share_settings['share_users'] 
                edit_auth = check_has_auth_memo(user_data, memo_data['user_uuid'], share_users)
            if share_settings['share_scope'] == ShareScope.PUBLIC.value:
                edit_auth = True
        else: # シェア設定がない場合
            edit_auth = check_has_auth_memo(user_data, memo_data['user_uuid'], share_users)
        if not memo_data or not edit_auth:
            print('Unauthorized memo save.')
            print({'user': user_uuid, 'memo_id': memo_id})
            return create_common_return_array(401, {'message': 'Unauthorized.',})
    else:
        # 新規保存時は上限に引っかかっていないか調べる
        memo_count_limit: int = get_memo_count_limit(user_data['plan'])
        if memo_count_limit > 0:
            # メモの数を取得
            memo_ids = get_all_memo_ids(user_uuid)
            trash_memo_ids = get_all_trash_memo_ids(user_uuid)
            if memo_ids is None or trash_memo_ids is None:
                return create_common_return_array(500, {'message': 'Failed to get number of memos.',})
            # メモの上限を超えていたら新規保存せずに終了
            if memo_count_limit <= len(memo_ids) + len(trash_memo_ids):
                return create_common_return_array(403, {'message': 'The maximum number of memos is ' + str(memo_count_limit) + '.',})

    # メモを更新または作成
    saved_uuid: str = save_memo(memo_id, title, description, body, memo_type, user_uuid)
    if saved_uuid is None:
        print('Failed to save.')
        print(params)
        return create_common_return_array(500, {'message': 'Failed to save.',})

    update_relation_result: bool = my_file.update_file_and_memo_relation(saved_uuid, files)
    if update_relation_result == False:
        print('Failed to updare relation.')
        print(params)
        return create_common_return_array(500, {'message': 'Failed to save.',})

    return create_common_return_array(200, {'id': saved_uuid,})

'''
シェア設定を更新する
'''
def update_share_settings_event(event, context):
    if os.environ['EnvName'] != 'Prod':
        print(json.dumps(event))
    user_uuid: str = get_user_uuid_by_event(event)
    if not user_uuid:
        return {
            "statusCode": 401,
            "headers": create_common_header(),
            "body": json.dumps({'message': "session timeout",}),
        }

    params           = json.loads(event['body'] or '{ }')
    memo_id: str     = params['params']['id'] or ''
    share_type: int  = int(params['params']['share']['type']) or 1
    share_scope: int = int(params['params']['share']['scope']) or 1
    share_users: str = params['params']['share']['users'] or ''

    # シェア設定は持ち主しか変更できない
    if not check_is_owner_of_the_memo(memo_id, user_uuid):
        print('Unauthorized memo save.')
        print({'user': user_uuid, 'memo_id': memo_id})
        return {
            'statusCode': 401,
            'headers': create_common_header(),
            'body': json.dumps({'message': 'Unauthorized',}),
        }

    # メモ設定を更新
    share_id: str = update_share_settings(memo_id, share_type, share_scope, share_users)
    if not share_id:
        print('Failed update share setting')
        print({'user': user_uuid, 'memo_id': memo_id, 'type': share_type, 'scope': share_scope, 'users': share_users})
        return {
            'statusCode': 500,
            'headers': create_common_header(),
            'body': json.dumps({'message': 'Unauthorized',}),
        }

    return {
        "statusCode": 200,
        "headers": create_common_header(),
        "body": json.dumps({'share_id': share_id,}),
    }

def get_memo_data_by_share_id(event, context):
    if os.environ['EnvName'] != 'Prod':
        print(json.dumps(event))
    
    share_id: str = None
    if 'queryStringParameters' in event:
        share_id: str = event['queryStringParameters'].get('share_id')
    
    # メモのシェア設定を取得
    share_settings: dict = get_share_setting_by_share_id(share_id)
    share_scope: int = int(share_settings['share_scope'])

    # メモのデータを取得
    memo_data: dict = get_memo_data(share_settings['memo_id'])
    is_no_auth: bool = False
    if share_scope == ShareScope.PUBLIC.value:
        is_no_auth = False
    elif share_scope == ShareScope.SPECIFIC_USERS.value:
        # ログイン中のユーザ情報を取得
        user_uuid: str = get_user_uuid_by_event(event)
        user_data: dict = get_user_data_by_uuid(user_uuid)
        if not user_data or not user_uuid:
            is_no_auth = True
        # 取得権限があるか調べる
        is_no_auth = not check_has_auth_memo(user_data, memo_data['user_uuid'], share_settings['share_users'])
    
    if is_no_auth:
        return {
            'statusCode': 401,
            'headers': create_common_header(),
            'body': json.dumps({'message': 'Unauthorized',}),
        }
    
    # 権限があるので取得
    return {
        "statusCode": 200,
        "headers": create_common_header(),
        "body": json.dumps({'memo': memo_data,}, default=decimal_default_proc),
    }

def delete_memo_event(event, context):
    if os.environ['EnvName'] != 'Prod':
        print(json.dumps(event))
    
    httpMethod = str.upper(event['httpMethod'])
    resource = str.lower(event['resource'])
    
    if httpMethod == 'POST':
        if resource == '/to_trash_memo':
            return to_trash_memo_event(event, context)
        elif resource == '/delete_memo':
            return hard_delete_memo_event(event, context)
        elif resource == '/restore_memo':
            return restore_memo_event(event, context)
        elif resource == '/truncate_trash_memo':
            return truncate_trash_memo_event(event, context)
    return create_common_return_array(404, {'message': 'Not Found',})


'''
完全に見れない状態にするdelete
'''
def hard_delete_memo_event(event, context):
    params = json.loads(event['body'] or '{ }')
    if not params or not params.get('params'):
        return create_common_return_array(406, {'message': "Failed to delete memo.",})

    memo_id_list = params['params'].get('memo_id_list')
    if not memo_id_list:
        return create_common_return_array(406, {'message': "Failed to delete memo.",})
    
    if len(memo_id_list) > MULTIPLE_SELECT_MEMO_LIMIT:
        print('Limit: len: ' + str(len(memo_id_list)) + ' limit: ' + str(MULTIPLE_SELECT_MEMO_LIMIT))
        return create_common_return_array(406, {'message': "The maximum number of selections is " + str(MULTIPLE_SELECT_MEMO_LIMIT) + ".",})

    # 重複消去
    memo_id_list = list(set(memo_id_list))

    user_uuid: str = get_user_uuid_by_event(event)
    if not user_uuid:
        return create_common_return_array(401, {'message': "Failed to delete memo.",})

    # 先に全てのメモが持ち主と一致しているか調べる
    for memo_id in memo_id_list:
        # メモの持ち主と一致してるか調べる
        if not check_is_owner_of_the_memo(memo_id, user_uuid):
            print('Unauthorized hard delete operation. ' + str(memo_id_list) + user_uuid)
            return create_common_return_array(401, {'message': "Unauthorized",})

    for memo_id in memo_id_list:
        # メモそのものの情報を削除
        if not delete_memo(memo_id):
            print("failed to delete memo: " + memo_id)
            return create_common_return_array(500, {'message': "Failed to delete memo.",})
        # メモとファイルの紐付けを削除
        if not my_file.delete_file_and_memo_relation_by_memo_id(memo_id):
            print("failed to delete memo and file relations: " + memo_id)
            return create_common_return_array(500, {'message': "Failed to delete memo.",})
        # メモとタグの紐付けを削除
        if not my_tag.delete_tag_relations_by_memo_id(memo_id):
            print("failed to delete memo and tag relations: " + memo_id)
            return create_common_return_array(500, {'message': "Failed to delete memo.",})

    return create_common_return_array(200, {'message': 'success',})

def truncate_trash_memo_event(event, context):
    user_uuid: str = get_user_uuid_by_event(event)
    if not user_uuid:
        return create_common_return_array(401, {'message': "Failed to delete memo.",})
    
    # ゴミ箱の全てのメモを取得する
    trash_memo_ids = get_all_trash_memo_ids(user_uuid)

    # 削除
    for memo_id in trash_memo_ids:
        # メモそのものの情報を削除
        if not delete_memo(memo_id):
            print("failed to delete memo: " + memo_id)
            return create_common_return_array(500, {'message': "Failed to delete memo.",})
        # メモとファイルの紐付けを削除
        if not my_file.delete_file_and_memo_relation_by_memo_id(memo_id):
            print("failed to delete memo and file relations: " + memo_id)
            return create_common_return_array(500, {'message': "Failed to delete memo.",})
        # メモとタグの紐付けを削除
        if not my_tag.delete_tag_relations_by_memo_id(memo_id):
            print("failed to delete memo and tag relations: " + memo_id)
            return create_common_return_array(500, {'message': "Failed to delete memo.",})

    return create_common_return_array(200, {'message': 'success',})


'''
メモをゴミ箱に移動する
'''
def to_trash_memo_event(event, content):
    user_uuid: str = get_user_uuid_by_event(event)
    if not user_uuid:
        print('do not input uuid')
        return create_common_return_array(401, {'message': "Failed to delete memo.",})

    params = json.loads(event['body'] or '{ }')
    if not params or not params.get('params'):
        return create_common_return_array(406, {'message': "Insufficient input.",})

    memo_id_list = params['params'].get('memo_id_list')
    if not memo_id_list:
        print('Insufficient input')
        return create_common_return_array(406, {'message': "Insufficient input.",})
    
    if len(memo_id_list) > MULTIPLE_SELECT_MEMO_LIMIT:
        print('Limit: len: ' + str(len(memo_id_list)) + ' limit: ' + str(MULTIPLE_SELECT_MEMO_LIMIT))
        return create_common_return_array(406, {'message': "The maximum number of selections is " + str(MULTIPLE_SELECT_MEMO_LIMIT) + ".",})
    
    # 重複消去
    memo_id_list = list(set(memo_id_list))

    # 先に全件持ち主のものか調べる
    for memo_id in memo_id_list:
        if not check_is_owner_of_the_memo(memo_id, user_uuid):
            print('Unauthorized trash operation. ' + str(memo_id_list) + user_uuid)
            return create_common_return_array(401, {'message': "Unauthorized",})

    for memo_id in memo_id_list:
        # メモそのものの情報をゴミ箱に
        # シェア設定は物理削除
        if not move_trash_memo(memo_id):
            print('Failed to trash memo: ' + memo_id)
            return create_common_return_array(500, {'message': "Failed to delete memo.",})
        # 紐付け周りはそのまま

    return create_common_return_array(200, {'message': 'success',})

'''
ゴミ箱から戻す
'''
def restore_memo_event(event, context):
    user_uuid: str = get_user_uuid_by_event(event)
    if not user_uuid:
        print('do not input uuid')
        return create_common_return_array(401, {'message': "Failed to restore memo.",})

    params = json.loads(event['body'] or '{ }')
    if not params or not params.get('params'):
        print('Insufficient input')
        return create_common_return_array(406, {'message': "Insufficient input.",})

    memo_id_list = params['params'].get('memo_id_list')
    if not memo_id_list:
        print('Insufficient input')
        return create_common_return_array(406, {'message': "Insufficient input.",})
    
    if len(memo_id_list) > MULTIPLE_SELECT_MEMO_LIMIT:
        print('Limit: len: ' + str(len(memo_id_list)) + ' limit: ' + str(MULTIPLE_SELECT_MEMO_LIMIT))
        return create_common_return_array(406, {'message': "The maximum number of selections is " + str(MULTIPLE_SELECT_MEMO_LIMIT) + ".",})

    # 重複消去
    memo_id_list = list(set(memo_id_list))

    # 先に全件持ち主のものか調べる
    for memo_id in memo_id_list:
        if not check_is_owner_of_the_memo(memo_id, user_uuid):
            print('Unauthorized restore operation. ' + str(memo_id_list) + user_uuid)
            return create_common_return_array(401, {'message': "Unauthorized",})

    for memo_id in memo_id_list:
        # メモそのものの情報をゴミ箱に
        # シェア設定は物理削除
        if not restore_memo(memo_id):
            print('Failed to restore memo: ' + memo_id)
            return create_common_return_array(500, {'message': "Failed to restore memo.",})
        # 紐付け周りはそのまま

    return create_common_return_array(200, {'message': 'success',})


def switch_pinned_event(event, context):
    if os.environ['EnvName'] != 'Prod':
        print(json.dumps(event))
    user_uuid: str = get_user_uuid_by_event(event)
    if not user_uuid:
        return create_common_return_array(401, {'message': "session timeout.",})

    params = json.loads(event['body'] or '{ }')
    if not params or not params.get('params'):
        return create_common_return_array(406, {'message': "Failed to pinned memo.",})
        
    memo_id: str = params['params']['id'] or ''

    if not memo_id:
        print('no memo id')
        return create_common_return_array(406, {'message': "Failed to pinned memo.",})

    memo_overview = get_memo_overview(memo_id)

    if not memo_overview:
        print('not found memo')
        return create_common_return_array(404, {'message': "Failed to pinned memo.",})

    # ピン設定は持ち主しか変更できない
    if not check_id_owner_of_the_memo_by_data(memo_overview, user_uuid):
        print('Unauthorized memo save.')
        print({'user': user_uuid, 'memo_id': memo_id})
        return create_common_return_array(401, {'message': "Unauthorized",})

    now_pinned_type = memo_overview.get('pinned_type', PinnedType.NO_PINNED.value)
    new_pinned_type = PinnedType.PINNED.value if now_pinned_type != PinnedType.PINNED.value else PinnedType.NO_PINNED.value

    if not update_pinned_memo(memo_id, new_pinned_type):
        print('failed to update pinned memo')
        return create_common_return_array(500, {'message': "Failed to pinned memo.",})
    return create_common_return_array(200, {'message': "updated.", 'pinned_type': new_pinned_type})

