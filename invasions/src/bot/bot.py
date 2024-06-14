import json
import os
#import pprint
from datetime import datetime
from nacl.signing import VerifyKey
from nacl.exceptions import BadSignatureError
from aws_lambda_powertools.utilities.typing import LambdaContext
from irus import IrusInvasion, IrusInvasionList, IrusMember, IrusMemberList, IrusLadderRank, IrusSecrets, IrusFiles, IrusProcess, IrusResources


discord_cmd = os.environ['DISCORD_CMD']

#
# Authenticate Requests
# Verify raises exception if it fails
#
resources = IrusResources()
logger = resources.logger
secrets = IrusSecrets()
process = IrusProcess()

def verify_signature(event):
    body = event['body']
    auth_sig = event['headers'].get('x-signature-ed25519')
    auth_ts  = event['headers'].get('x-signature-timestamp')

    # message = auth_ts.encode() + body.encode()
    verify_key = VerifyKey(secrets.public_key_bytes)
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

    return IrusInvasionList.from_month(month=month, year=year).markdown()


def invasion_add_cmd(options:list) -> IrusInvasion:
    logger.info(f'invasion_add: {options}')

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

    item = IrusInvasion.from_user(day=day,
                              month=month,
                              year=year,
                              settlement=settlement,
                              win=win,
                              notes=notes)
    
    return item.markdown()


def invasion_download_cmd(id: str, token: str, options:list, resolved:dict, method:str) -> str:
    logger.info(f'invasion_download_cmd:\nid: {id}\ntoken: {token}\noptions: {options}\nresolved: {resolved}\nmethod: {method}')

    invasion = None
    files = IrusFiles()

    try:
        for o in options:
            if o["name"] == "invasion":
                invasion = IrusInvasion.from_table(o["value"])
            elif o["name"].startswith("file"):
                files.append(name = o["name"], attachment = o["value"])
    except ValueError as e:
        logger.info(e)
        return str(e)

    files.update(resolved['attachments'])

    return process.start(id, token, invasion, files, method)


def invasion_cmd(id:str, token:str, options:dict, resolved: dict) -> str:
    logger.info(f'invasion_cmd: {options}')
    name = options['name']
    if name == 'list':
        return invasion_list_cmd(options['options'])
    elif name == 'add':
        return str(invasion_add_cmd(options['options']))
    elif name == 'ladder' or name == 'screenshots':
        return invasion_download_cmd(id, token, options['options'], resolved, 'Ladder')
    elif name == 'roster':
        return invasion_download_cmd(id, token, options['options'], resolved, 'Roster')
    else:
        logger.error(f'Invalid command {name}')
        return f'Invalid command {name}'

#
# Member Commands
#

def member_list_cmd() -> str:
    return IrusMemberList().markdown()


def update_invasions(member: IrusMember) -> str:
    logger.info(f'Ladder.update_invasions: {member}')
    invasionlist = IrusInvasionList.from_start(member.start)
    logger.debug(f'Invasions on or after {invasionlist.start}: {str(invasionlist)}')

    if invasionlist.count() == 0:
        mesg = f'\nNo invasions found to update\n'
    else:
        mesg = f'\n## Member flag updated in these invasions:\n'
        for i in invasionlist.invasions:
            try:
                ladder = IrusLadderRank.from_invasion_for_member(i, member)
                logger.debug(f'LadderRank.from_invasion_for_member: {ladder}')
                mesg += f'- {i.name} rank {ladder.rank}\n'
                ladder.update_membership(True)
            except ValueError:
                pass

    logger.info(mesg)
    return mesg


def member_add_cmd(options:list) -> str:

    now = datetime.now()
    month = now.month
    year = now.year
    day = now.day
    admin = False
    notes = None
    discord = None
    salary = True

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
        elif o["name"] == "salary":
            salary = bool(o["value"])

    member = IrusMember.from_user(player=player,
                                day=day,
                                month=month,
                                year=year,
                                faction=faction,
                                discord=discord,
                                admin=admin,
                                salary=salary,
                                notes=notes)
    mesg = str(member)
    mesg += update_invasions(member)

    return mesg


def member_remove_cmd(options:list) -> str:

    player = None
    for o in options:
        if o["name"] == "player":
            player = o["value"]

    try:
        member = IrusMember.from_table(player)
    except ValueError:
        return f'Member {player} not found'
    return member.remove()


def member_cmd(options:dict, resolved: dict) -> str:
    logger.info(f'member_cmd: {options}')

    name = options['name']
    if name == 'list':
        return member_list_cmd()
    elif name == 'add':
        return member_add_cmd(options['options'])
    elif name == 'remove':
        return member_remove_cmd(options['options'])
    else:
        logger.error(f'Invalid command {name}')
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

    logger.error('Not implemented')
    return 'Not implemented'
    # return layer.remote_month(month, year)


def report_invasion_cmd(options:list) -> str:

    invasion = None
    for o in options:
        if o["name"] == "invasion":
            invasion = o["value"]

    if not invasion:
        return 'Missing invasion from request'

    logger.error('Not implemented')
    return 'Not implemented'
    # return layer.report_invasion(invasion)


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

    logger.error('Not implemented')
    return 'Not implemented'
    # return layer.report_member(player, month, year)


def report_cmd(options:dict, resolved: dict) -> str:
    logger.info(f'report_cmd: {options}')

    name = options['name']
    if name == 'month':
        return report_month_cmd(options['options'])
    elif name == 'invasion':
        return report_invasion_cmd(options['options'])
    elif name == 'member':
        return report_member_cmd(options['options'])
    else:
        logger.error(f'Invalid command {name}')
        return f'Invalid command {name}'

#
# Command switch and package results as required by Discord
#

@logger.inject_lambda_context(log_event=True)
def lambda_handler(event: dict, context: LambdaContext):

    status = 200
    headers = {
        "Content-Type": "application/json"
    }
    data = None
    content = None

    try: 
        verify_signature(event)
        logger.debug("Signature verified")

        body = json.loads(event['body'])
        if body["type"] == 1:
            data = ({'type': 1})

        elif body["type"] == 2 and body["data"]["name"] == discord_cmd:
            logger.debug(f'body: {body["data"]}')
            subcommand = body["data"]["options"][0]
            resolved = body["data"]["resolved"] if "resolved" in body["data"] else None

            if subcommand["name"] == "invasion":
                content = invasion_cmd(secrets.app_id, body['token'], subcommand["options"][0], resolved)
            elif subcommand["name"] == "ladders":
                invasion = invasion_add_cmd(subcommand["options"][0]["options"])
                invasion_download_cmd(secrets.app_id, body['token'], subcommand["options"][0], resolved, 'Ladder')
                content = f'In Progress: Registered invasion {invasion.name}, next download file(s)'
            elif subcommand["name"] == "roster":
                invasion = invasion_add_cmd(subcommand["options"][0]["options"])
                invasion_download_cmd(secrets.app_id, body['token'], subcommand["options"][0], resolved, 'Roster')
                content = f'In Progress: Registered invasion {invasion.name}, next download file(s)'
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
        logger.info(f"Bad Signature: {e}")
        content = f"Bad Signature: {e}"
    
    except Exception as e:
        status = 401
        logger.error(f"Unexpected exception: {e}")
        content = f"Unexpected exception: {e}"

    finally:
        logger.debug(f"content: {content}")
    
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

        logger.info(f"data: {json.dumps(data)}")
        return {
            "statusCode": status,
            "headers": headers,
            "body": json.dumps(data)
        }
          