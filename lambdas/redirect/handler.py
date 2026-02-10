import json
import boto3
import time

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('UrlMappings')

def lambda_handler(event, context):
    short_code = event['pathParameters']['short_code']
    response = table.get_item(Key={'short_code': short_code})

    if 'Item' not in response:
        return {'statusCode': 404, 'body': json.dumps({'error': 'Not Found'})}

    item = response['Item']
    # Check expiration
    expiration = item.get('expiration_time', 0)
    if expiration > 0 and expiration < time.time():
        return {'statusCode': 410, 'body': json.dumps({'error': 'Expired'})}

    return {
        'statusCode': 301,
        'headers': {'Location': item['long_url']}
    }