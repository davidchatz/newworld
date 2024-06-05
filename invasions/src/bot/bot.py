import boto3
import json
import os
#import pprint
from datetime import datetime
from nacl.signing import VerifyKey
from nacl.exceptions import BadSignatureError
from irus import Invasion, InvasionList

#
# Authenticate Requests
# Raises exception if it fails
#

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

#
# Invasion Commands
#

def invasion_list_cmd(options:list) -> str:
    now = datetime.now()
    month = now.month
    year = now.year

    for o in options:
        if o["name"] == "month":
            month = int(o["value"])
        elif o["name"] == "year":
            year = int(o["value"])

    return str(InvasionList(month, year))


def invasion_add_cmd(options:list) -> str:
    print(f'invasion_add: {options}')

    notes=None
    now = datetime.now()
    day = now.day
    month = now.month
    year = now.year

    for o in options:
        if o["name"] == "day":
            day = int(o["value"])
        elif o["name"] == "month":
            month = int(o["value"])
        elif o["name"] == "year":
            year = int(o["value"])
        elif o["name"] == "settlement":
            settlement = o["value"]
        elif o["name"] == "win":
            win = bool(["value"])
        elif o["name"] == "notes":
            notes = o["value"]

    item = Invasion.from_user(day=day,
                              month=month,
                              year=year,
                              settlement=settlement,
                              win=win,
                              notes=notes)
    
    return str(item)


def invasion_download_cmd(id: str, token: str, options:list, resolved:dict, folder:str, process:str) -> str:
    print(f'invasion_download_cmd:\nid: {id}\ntoken: {token}\noptions: {options}\nresolved: {resolved}')

    invasion = None
    month = None
    files = []

    for o in options:
        if o["name"] == "invasion":
            invasion = o["value"]
        elif o["name"].startswith("file"):
            files.append({
                "name": o["name"],
                "attachment": o["value"]
            })

    if not (process == "Ladder" or process == "Download" or process == "Roster"):
        raise Exception('invasion_download_cmd: Unknown process')
    if not invasion:
        raise Exception(f'invasion_download_cmd: No invasion specified')

    month = invasion[:6]
    if not month.isnumeric():
        raise Exception(f'invasion_download_cmd: Invasion {invasion} should start with datestamp')

    for a in files:
        a['filename'] = resolved['attachments'][a['attachment']]['filename']
        a['url'] = resolved['attachments'][a['attachment']]['url']

    return layer.invasion_download(id=id,
                                  token=token,
                                  invasion=invasion,
                                  month=month,
                                  files=files,
                                  process=process)



def invasion_cmd(id:str, token:str, options:dict, resolved: dict) -> str:
    print(f'invasion_cmd: {options}')
    name = options['name']
    if name == 'list':
        return invasion_list_cmd(options['options'])
    elif name == 'add':
        return invasion_add_cmd(options['options'])
    elif name == 'ladder':
        return invasion_download_cmd(id, token, options['options'], resolved, 'Download')
    elif name == 'screenshots':
        return invasion_download_cmd(id, token, options['options'], resolved, 'Ladder')
    elif name == 'roster':
        return invasion_download_cmd(id, token, options['options'], resolved, 'Roster')
    else:
        print(f'Invalid command {name}')
        return f'Invalid command {name}'

#
# Member Commands
#

def member_list_cmd() -> str:

    now = datetime.now()
    return layer.member_list(now.day, now.month, now.year)


def member_add_cmd(options:list) -> str:

    now = datetime.now()
    month = now.month
    year = now.year
    day = now.day
    admin = False
    notes = None
    discord = None

    for o in options:
        if o["name"] == "player":
            player = o["value"]
        elif o["name"] == "day":
            day = o["value"]
        elif o["name"] == "month":
            month = o["value"]
        elif o["name"] == "year":
            year = o["value"]
        elif o["name"] == "faction":
            faction = o["value"]
        elif o["name"] == "discord":
            discord = o["value"]
        elif o["name"] == "admin":
            admin = bool(o["value"])
        elif o["name"] == "notes":
            notes = o["value"]

    mesg = layer.register_member(player=player,
                                day=day,
                                month=month,
                                year=year,
                                faction=faction,
                                discord=discord,
                                admin=admin,
                                notes=notes)
    
    mesg += layer.update_invasions(player=player,
                                  day=day,
                                  month=month,
                                  year=year)

    return mesg


def member_remove_cmd(options:list) -> str:

    for o in options:
        if o["name"] == "player":
            player = o["value"]

    return layer.member_remove(player)


def member_cmd(options:dict, resolved: dict) -> str:
    print(f'member_cmd: {options}')

    name = options['name']
    if name == 'list':
        return member_list_cmd()
    elif name == 'add':
        return member_add_cmd(options['options'])
    elif name == 'remove':
        return member_remove_cmd(options['options'])
    else:
        print(f'Invalid command {name}')
        return f'Invalid command {name}'

#
# Report Commands
#

def report_month_cmd(options:list) -> str:

    now = datetime.now()
    month = now.month
    year = now.year

    for o in options:
        if o["name"] == "month":
            month = o["value"]
        elif o["name"] == "year":
            year = o["value"]

    return layer.remote_month(month, year)


def report_invasion_cmd(options:list) -> str:

    invasion = None
    for o in options:
        if o["name"] == "invasion":
            invasion = o["value"]

    if not invasion:
        return 'Missing invasion from request'
    
    return layer.report_invasion(invasion)


def report_member_cmd(options:list) -> str:

    now = datetime.now()
    month = now.month
    year = now.year

    for o in options:
        if o["name"] == "player":
            player = o["value"]
        elif o["name"] == "month":
            month = o["value"]
        elif o["name"] == "year":
            year = o["value"]

    return layer.report_member(player, month, year)


def report_cmd(options:dict, resolved: dict) -> str:
    print(f'report_cmd: {options}')

    name = options['name']
    if name == 'month':
        return report_month_cmd(options['options'])
    elif name == 'invasion':
        return report_invasion_cmd(options['options'])
    elif name == 'member':
        return report_member_cmd(options['options'])
    else:
        print(f'Invalid command {name}')
        return f'Invalid command {name}'

#
# Command switch and package results as required by Discord
#

def lambda_handler(event, context):
    print(f"event {event}") # debug print

    status = 200
    headers = {
        "Content-Type": "application/json"
    }
    data = None
    content = None

    try: 
        verify_signature(event)
        print("Signature verified")

        body = json.loads(event['body'])
        if body["type"] == 1:
            data = ({'type': 1})

        elif body["type"] == 2 and body["data"]["name"] == discord_cmd:
            print(f'body: {body["data"]}')
            subcommand = body["data"]["options"][0]
            resolved = body["data"]["resolved"] if "resolved" in body["data"] else None

            if subcommand["name"] == "invasion":
                content = invasion_cmd(app_id, body['token'], subcommand["options"][0], resolved)
            elif subcommand["name"] == "ladders":
                item = invasion_add_cmd(subcommand["options"][0]["options"])
                invasion_download_cmd(app_id, body['token'], subcommand["options"][0], resolved, 'Ladder')
                content = f'In Progress: Registered invasion {item["id"]}, next download file(s)'
            elif subcommand["name"] == "roster":
                item = invasion_add_cmd(subcommand["options"][0]["options"])
                content = invasion_download_cmd(app_id, body['token'], subcommand["options"][0], resolved, 'Roster')
                content = f'In Progress: Registered invasion {item["id"]}, next download file(s)'
            elif subcommand["name"] == "report":
                content = report_cmd(subcommand["options"][0], resolved)
            elif subcommand["name"] == "member":
                content = member_cmd(subcommand["options"][0], resolved)
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
          