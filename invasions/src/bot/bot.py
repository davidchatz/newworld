import json
import boto3
import os

from nacl.signing import VerifyKey
from nacl.exceptions import BadSignatureError

ssm = boto3.client('ssm')
PUBLIC_KEY_PATH = os.environ['PUBLIC_KEY_PATH']
PUBLIC_KEY = ssm.get_parameter(Name=PUBLIC_KEY_PATH, WithDecryption=True)['Parameter']['Value']

PING_PONG = {"type": 1}
RESPONSE_TYPES =  { 
                    "PONG": 1, 
                    "ACK_NO_SOURCE": 2, 
                    "MESSAGE_NO_SOURCE": 3, 
                    "MESSAGE_WITH_SOURCE": 4, 
                    "ACK_WITH_SOURCE": 5
                  }

def verify_signature(event):
    body = event['body']
    auth_sig = event['headers'].get('x-signature-ed25519')
    auth_ts  = event['headers'].get('x-signature-timestamp')
    
    message = auth_ts.encode() + body.encode()
    verify_key = VerifyKey(bytes.fromhex(PUBLIC_KEY))
    verify_key.verify(f'{auth_ts}{body}'.encode(), bytes.fromhex(auth_sig))

def lambda_handler(event, context):
    print(f"event {event}") # debug print

    try: 
        verify_signature(event)
        body = json.loads(event['body'])
        if body["type"] == 1:
            return {
             'statusCode': 200, 
             'body': json.dumps({'type': 1})
         } 
    except (BadSignatureError) as e:
        return {
             'statusCode': 401, 
             'body': json.dumps("Bad Signature")
         }