import json
import boto3

client = boto3.client('ses')

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
