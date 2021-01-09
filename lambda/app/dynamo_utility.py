from decimal import Decimal

def dict2dynamoformat(orig_dict):
    """辞書配列をDynamoDB用に変換する"""
    ret_dict = {}
    for k, v in orig_dict.items():
        ret_dict[k] = to_dynamo_format(v)
    return ret_dict

def to_dynamo_format(v):
    """dict2dynamoformatの変換部分でSet系の型は未対応"""
    if type(v) is str:
        return {'S': v}
    if type(v) is Decimal:
        return {'N': str(float(v))}
    if type(v) is int:
        return {'N': str(v)}
    if type(v) is bool:
        return {'BOOL': v}
    if type(v) is list:
        return {'L': [to_dynamo_format(a) for a in v]}
    if type(v) is dict:
        return {'M': dict2dynamoformat(v)}