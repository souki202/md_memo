import json
import boto3
from my_common import *

client = boto3.client('ses')

COMPANY_NAME = 'MD Writer'

temp_mail_body = '''
本サイトにご登録いただき、ありがとうございます。
下記URLをクリックし、登録を完了させてください。

[[[temp_reg_url]]]

本メールに心当たりのない方は、お手数ではございますが、このままこのメールを削除してください。

'''

MAIL_FOOTER = '''
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
発行元 MD Writer

Copyright(C) MD Writer team. All Rights Reserved.
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
'''

def create_temporary_regist_url(temp_token):
    return get_page_url() + '/regist_complete.html?token=' + temp_token

def send_mail(from_view_name, from_mail, to_mail, subject, body):
    client.send_email(
        Source = from_view_name + ' <' + from_mail + '>',
        Destination = {
            'ToAddresses': [
                to_mail,
            ]
        },
        Message = {
            'Subject': {
                'Data': subject,
                'Charset': 'UTF-8'
            },
            'Body': {
                'Text': {
                    'Data': body,
                    'Charset': 'UTF-8'
                }
            }
        }
    )

def send_temporary_regist_mail(to_mail, temp_token):
    body = temp_mail_body + MAIL_FOOTER
    body = body.replace('[[[temp_reg_url]]]', create_temporary_regist_url(temp_token))
    send_mail('noreply', get_mail_from(), to_mail, 'MD Writer 仮登録', body)

def get_mail_from():
    return 'noreply@tori-blog.net'