import json
import boto3
import urllib.parse
import time
import calendar
import os
import re
from botocore.exceptions import ClientError

# ---------- AWS resources ----------
dynamodb = boto3.resource('dynamodb')
mappings_table = dynamodb.Table(os.environ["MAPPINGS_TABLE"])
counters_table = dynamodb.Table(os.environ["COUNTERS_TABLE"])

# ---------- Constants ----------
BASE62 = '0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ'
ALIAS_PATTERN = re.compile(r"^[A-Za-z0-9_-]+$")
MAX_ALIAS_LENGTH = 64
EXPIRATION_FMT = "%Y-%m-%dT%H:%M:%SZ"

# ---------- Helper functions ----------
def build_cors_headers(event):
    origin = (event.get("headers") or {}).get("origin") or (event.get("headers") or {}).get("Origin")
    return {
        "Access-Control-Allow-Origin": origin or "*",
        "Vary": "Origin",
        "Access-Control-Allow-Methods": "POST,OPTIONS",
        "Access-Control-Allow-Headers": "Content-Type,Authorization",
        "Content-Type": "application/json",
    }

def make_response(status_code, body_dict=None, headers=None):
    response = {
        "statusCode": status_code,
        "headers": headers or {},
    }
    if body_dict is not None:
        response["body"] = json.dumps(body_dict)
    return response

# ---------- Parsing / validation ----------
def decode_body(event):
    raw_body = event.get("body") or "{}"
    if raw_body and event.get("isBase64Encoded"):
        import base64
        raw_body = base64.b64decode(raw_body).decode("utf-8")
    return raw_body

def parse_json_body(raw_body):
    try:
        return json.loads(raw_body)
    except json.JSONDecodeError as e:
        raise ValueError("Invalid JSON body") from e

def validate_long_url(long_url):
    if not long_url:
        raise ValueError("Missing \"long_url\" in request body")
    parsed = urllib.parse.urlparse(long_url)
    if not parsed.scheme in ('http', 'https'):
        raise ValueError("Invalid URL. Must start with http:// or https://")

def validate_custom_alias(custom_alias):
    if not custom_alias:
        return
    if not ALIAS_PATTERN.match(custom_alias):
        raise ValueError("Invalid custom alias. Only letters, digits, hyphens, and underscores allowed")
    if len(custom_alias) > MAX_ALIAS_LENGTH:
        raise ValueError(f"Custom alias too long. Maximum length is {MAX_ALIAS_LENGTH} characters")

def parse_expiration_date(expiration_date):
    if not expiration_date:
        return None
    try:
        return int(calendar.timegm(time.strptime(expiration_date, EXPIRATION_FMT)))
    except ValueError as e:
        raise ValueError("Invalid expiration date.") from e

# ---------- Short code generation ----------
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

def next_counter_value():
    ensure_counter_exists()
    update_response = counters_table.update_item(
        Key={'counter_id': 'url_counter'},
        UpdateExpression='ADD #val :inc',
        ExpressionAttributeNames={'#val': 'value'},
        ExpressionAttributeValues={':inc': 1},
        ReturnValues='UPDATED_NEW'
    )
    return int(update_response['Attributes']['value'])

def is_alias_taken(custom_alias):
    db_response = mappings_table.get_item(Key={'short_code': custom_alias})
    return 'Item' in db_response

def generate_short_code(custom_alias=None):
    if custom_alias:
        validate_custom_alias(custom_alias)
        if is_alias_taken(custom_alias):
            raise RuntimeError("Custom alias already taken")
        return custom_alias
    return encode_base62(next_counter_value())

# ---------- Persistence / URL building ----------
def put_mapping(short_code, long_url, expiration_time):
    item = {
        "short_code": short_code,
        "long_url": long_url,
        "creation_time": time.strftime(EXPIRATION_FMT, time.gmtime()),
    }
    if expiration_time:
        item["expiration_time"] = expiration_time

    mappings_table.put_item(Item=item)


def build_short_url(event, short_code):
    domain = event["requestContext"]["domainName"]
    stage = event["requestContext"]["stage"]
    return f"https://{domain}/{stage}/r/{short_code}"

def lambda_handler(event, context):
    headers = build_cors_headers(event)

    if event.get("httpMethod") == "OPTIONS":
        return make_response(204, headers=headers)

    try:
        body = parse_json_body(decode_body(event))
        long_url = body.get('long_url')
        validate_long_url(long_url)
        custom_alias = body.get('custom_alias')
        expiration_date = body.get('expiration_date')
        expiration_time = parse_expiration_date(expiration_date)
        short_code = generate_short_code(custom_alias)
        put_mapping(short_code, long_url, expiration_time)
        short_url = build_short_url(event, short_code)
        response_body = {
            "short_url": short_url,
        }
        if custom_alias:
            response_body["custom_alias"] = custom_alias
        else:
            response_body["short_code"] = short_code
        if expiration_date:
            response_body["expiration_date"] = expiration_date
        return make_response(201, response_body, headers)

    except ValueError as e:
        return make_response(400, {'error': str(e)}, headers)
    
    except RuntimeError as e:
        if str(e) == "Custom alias already taken":
            return make_response(409, {'error': str(e)}, headers)
        return make_response(500, {'error': 'An unexpected error occurred'}, headers)
    
    except Exception:
        return make_response(500, {"error": "An unexpected error occurred"}, headers)
