import json
import boto3
import os
import bot_reports
import bot_invasion
import bot_member
#import pprint

from nacl.signing import VerifyKey
from nacl.exceptions import BadSignatureError

ssm = boto3.client('ssm')
public_key_path = os.environ['PUBLIC_KEY_PATH']
public_key = ssm.get_parameter(Name=public_key_path, WithDecryption=True)['Parameter']['Value']
public_key_bytes = bytes.fromhex(public_key)

app_id_path = os.environ['APP_ID_PATH']
app_id = ssm.get_parameter(Name=app_id_path, WithDecryption=True)['Parameter']['Value']

discord_cmd = os.environ['DISCORD_CMD']

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

        elif body["type"] == 2 and body["data"]["name"] == discord_cmd:
            print(f'body: {body["data"]}')
            subcommand = body["data"]["options"][0]
            resolved = body["data"]["resolved"] if "resolved" in body["data"] else None

            if subcommand["name"] == "invasion":
                content = bot_invasion.invasion_cmd(app_id, body['token'], subcommand["options"][0], resolved)
            elif subcommand["name"] == "report":
                content = bot_reports.report_cmd(subcommand["options"][0], resolved)
            elif subcommand["name"] == "member":
                content = bot_member.member_cmd(subcommand["options"][0], resolved)
            else:
                content = f'Unexpected subcommand {subcommand["name"]}'

        else:
            content = f'Unexpected interaction type {body["type"]}'

    except (BadSignatureError) as e:
        status = 401
        print(f"Bad Signature: {e}")
        content = f"Bad Signature: {e}"
    
    except Exception as e:
        status = 401
        print(f"Unexpected exception: {e}")
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
            if content.startswith("In Progress"):
                data['type'] = 5

        print(f"data: {json.dumps(data)}")
        return {
            "statusCode": status,
            "headers": headers,
            "body": json.dumps(data)
        }
          