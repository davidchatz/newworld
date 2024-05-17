import json
import boto3
import os
import bot_result
import bot_reports
import pprint

from nacl.signing import VerifyKey
from nacl.exceptions import BadSignatureError

ssm = boto3.client('ssm')
public_key_path = os.environ['PUBLIC_KEY_PATH']
public_key = ssm.get_parameter(Name=public_key_path, WithDecryption=True)['Parameter']['Value']
public_key_bytes = bytes.fromhex(public_key)

def verify_signature(event):
    body = event['body']
    auth_sig = event['headers'].get('x-signature-ed25519')
    auth_ts  = event['headers'].get('x-signature-timestamp')

    # message = auth_ts.encode() + body.encode()
    verify_key = VerifyKey(public_key_bytes)
    verify_key.verify(f'{auth_ts}{body}'.encode(), bytes.fromhex(auth_sig))


def lambda_handler(event, context):
    print(f"event {event}") # debug print

    # response = bot_result.Result()

    status = 200
    headers = {
        "Content-Type": "application/json"
    }
    data = None
    content = None

    try: 
        verify_signature(event)
        print("Signature verified") # debug print

        body = json.loads(event['body'])
        if body["type"] == 1:
            data = ({'type': 1})
        elif body["type"] == 2:
            name = body["data"]["name"]
            if name == "echo":
                content = body["data"]["options"][0]["value"]
            elif name == "invasions":
                content = bot_reports.invasions()
            else:
                content = f'Unknown command {name}'
        else:
            content = f'Unexpected interaction type {body["type"]}'

    except (BadSignatureError) as e:
        status = 401
        content = f"Bad Signature: {e}"
    
    except Exception as e:
        status = 401
        content = f"Unexpected exception: {e}"

    finally:
        # print(f"response: {response}")
        # print(f"response.result: {response.result}")
        # pprint.pprint(f"response {response}")
        # return response.result
    
        if data is None:
            data = {
                'type': 4, 
                'data': { 
                    'tts': False,
                    'content': content,
                    'embeds': [],
                    'allowed_mentions': {}
                }
            }

        print(f"data: {data}")
        return {
            "statusCode": status,
            "headers": headers,
            "body": json.dumps(data)
        }