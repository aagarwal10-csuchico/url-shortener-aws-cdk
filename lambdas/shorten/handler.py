import json
import boto3
import urllib.parse
import time
import os
from botocore.exceptions import ClientError

def make_response(status_code, body_dict):
    return {
        "statusCode": status_code,
        "headers": {
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "Content-Type,Authorization",
        },
        "body": json.dumps(body_dict),
    }

dynamodb = boto3.resource('dynamodb')
mappings_table = dynamodb.Table(os.environ["MAPPINGS_TABLE"])
counters_table = dynamodb.Table(os.environ["COUNTERS_TABLE"])

BASE62 = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"

def encode_base62(num):
    if num == 0:
        return BASE62[0]
    arr = []
    base = 62
    while num:
        num, rem = divmod(num, base)
        arr.append(BASE62[int(rem)])
    arr.reverse()
    return ''.join(arr)

def ensure_counter_exists():
    try:
        counters_table.put_item(
            Item={"counter_id": "url_counter", "value": 0},
            ConditionExpression="attribute_not_exists(counter_id)",
        )
    except ClientError as e:
        if e.response["Error"]["Code"] != "ConditionalCheckFailedException":
            raise

def lambda_handler(event, context):
    body = json.loads(event['body'])
    long_url = body.get('long_url')
    custom_alias = body.get('custom_alias')
    expiration_date = body.get('expiration_date')  # Optional ISO string

    # Validate URL
    if not long_url:
        return make_response(400, {'error': 'Missing \"long_url\" in request body'})

    parsed = urllib.parse.urlparse(long_url)
    if not parsed.scheme in ('http', 'https'):
        return make_response(400, {'error': 'Invalid URL'})

    short_code = None
    if custom_alias:
        # Check if alias exists
        db_response = mappings_table.get_item(Key={'short_code': custom_alias})
        if 'Item' in db_response:
            return make_response(409, {'error': 'Custom alias taken'})
        short_code = custom_alias
    else:
        ensure_counter_exists()

        # Atomic increment counter
        update_response = counters_table.update_item(
            Key={'counter_id': 'url_counter'},
            UpdateExpression='ADD #val :inc',
            ExpressionAttributeNames={'#val': 'value'},
            ExpressionAttributeValues={':inc': 1},
            ReturnValues='UPDATED_NEW'
        )
        counter_value = int(update_response['Attributes']['value'])
        short_code = encode_base62(counter_value)

    # Calculate expiration (Unix timestamp)
    expiration_time = None
    if expiration_date:
        expiration_time = int(time.mktime(time.strptime(expiration_date, '%Y-%m-%dT%H:%M:%SZ')))

    # Store mapping
    mappings_table.put_item(Item={
        'short_code': short_code,
        'long_url': long_url,
        'creation_time': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
        'expiration_time': expiration_time if expiration_time else 0  # 0 for no TTL
    })

    domain = event['requestContext']['domainName']
    stage = event["requestContext"].get("stage", "")
    prefix = f"/{stage}" if stage and stage != "$default" else ""
    short_url = f"https://{domain}{prefix}/{short_code}"
    return make_response(201, {'short_url': short_url})
