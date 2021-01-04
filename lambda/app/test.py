import json

def post_test(event, context):
    print(json.dumps(event))
    return 'post'

def get_test(event, context):
    print(json.dumps(event))
    return 'get'