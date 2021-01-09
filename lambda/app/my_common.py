import os
import time
import datetime

def get_api_url():
    if os.environ['EnvName'] == 'Prod':
        return 'https://api.md-memo.tori-blog.net'
    elif os.environ['EnvName'] == 'Stg':
        return 'https://api.stg-md-memo.tori-blog.net'
    elif os.environ['EnvName'] == 'Dev':
        return 'https://api.dev-md-memo.tori-blog.net'
    elif os.environ['EnvName'] == 'Local':
        return 'https://api2.dev-md-memo.tori-blog.net'

def get_page_url():
    if os.environ['EnvName'] == 'Prod':
        return 'https://md-memo.tori-blog.net'
    elif os.environ['EnvName'] == 'Stg':
        return 'https://stg-md-memo.tori-blog.net'
    elif os.environ['EnvName'] == 'Dev':
        return 'http://dev-md-memo.tori-blog.net'
    elif os.environ['EnvName'] == 'Local':
        return 'http://dev-md-memo.tori-blog.net'

def get_domain():
    if os.environ['EnvName'] == 'Prod':
        return 'tori-blog.net'
    elif os.environ['EnvName'] == 'Stg':
        return 'tori-blog.net'
    elif os.environ['EnvName'] == 'Dev':
        return 'tori-blog.net'
    elif os.environ['EnvName'] == 'Local':
        return 'tori-blog.net'

def get_now_string():
    return datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

def get_calced_from_now_string(diff_sec: int):
    return datetime.datetime.fromtimestamp(int(time.time()) - diff_sec).strftime('%Y-%m-%d %H:%M:%S')