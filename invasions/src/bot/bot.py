import json
import os
#import pprint
from datetime import datetime
from nacl.signing import VerifyKey
from nacl.exceptions import BadSignatureError
from aws_lambda_powertools.utilities.typing import LambdaContext
import irus
from irus import IrusInvasion, IrusInvasionList, IrusMember, IrusMemberList, IrusLadder, IrusSecrets, IrusFiles, IrusProcess, IrusResources, IrusReport, IrusMonth, IrusPostTable

discord_cmd = os.environ['DISCORD_CMD']


#
# Help text
#

help_text = {}
help_text['help'] = f'''
# Invasions R Us Stats

Bot for capturing, tracking and reporting invasion stats for the Invasions R Us company.

Settlements are specified using an abrieviation:
- Brightwood: bw
- Brimstone Sands: bs
- Cutlass Keys: ck
- Ebonscale Reach: er
- Edengrove: eg
- Everfall: ef
- Monarchs Bluff: mb
- Mourningdale: md
- Reekwater: rw
- Restless Shore: rs
- Weavers Fen: wf
- Windsward: ww

### /{discord_cmd} ladder *settlement win file1 [files] [date] [notes]*

Register an invasion, upload one or more ladder screen shots and generate reports. This commands should be used when the entire ladder is captured as a single image, or when there are less than seven screen shots (ie when the invasion was not full). The command requires the settlement name, was it a win, and will default to today's date if no other date is specified.

### /{discord_cmd} ladders *settlement win file1 ... file7 [date] [notes]*

Register an invasion, upload seven ladder screen shots and generate reports after a near full/full invasion. This command should be used when seven individual screen shots were used to capture the ladder. The command requires the settlement name, was it a win, and will default to today's date if no other date is specified.

### /{discord_cmd} roster *settlement win file1 [date] [notes]*

Register an invasion where only the war board roster was captured. If only a war board roster screen was captured, use this command to register the invasion. The command requires the settlement name, was it a win, and will default to today's date if no other date is specified.

### /{discord_cmd} invasion help

Get help for commands showing stats on an invasion

### /{discord_cmd} member help

Get help for command to add, edit, remove and list company members.

### /{discord_cmd} report help

Get help for command to generate reports for the current or previous months.
'''

help_text['invasion'] = f'''
# Invasions R Us Stats - Invasion Commands

Bot commands for creating, updating and listing invasions. Typically you would use the /{discord_cmd} ladder or /{discord_cmd} ladders commands, but sometimes you may need to add another screenshot.

Invasions are identified using the date and settlement abrieviation (*YYYYMMDD-SS*). For example `20240918-ef` is an invasion in Everfall on 18 September 2024.

### /{discord_cmd} invasion add *settlement win [date] [notes]*

Register a new invasion for *settlement*, without uploading any screenshots. This will default to today's date if another date is not specified.

### /{discord_cmd} invasion list *[month] [year]*

List all invasions for the current or specified month and year.

### /{discord_cmd} invasion ladder *invasion file*

For the specified invasion, upload and process single ladder file. 

### /{discord_cmd} invasion board *invasion file*

For the specified invasion, upload and process single war roster file.

### /{discord_cmd} invasion screenshots *invasion file1 ... file7*

For the specified invasion, upload and process seven screen shots of the ladder.

### /{discord_cmd} invasion rank *invasion rank*

Display the ladder entry for *rank*

### /{discord_cmd} invasion edit *invasion rank [new_rank] [member] [player] [score]*

Edit a row in a ladder, adjusting one or more of the rank, member flag, player name or score. This may be needed if the scan failed to correctly identify some characters in the image. If changing the rank, this command will overwrite the existing entry at that position.
'''


help_text['member'] = f'''
# Invasions R Us Stats - Member Commands

Bot commands for registering company members to determine which player stats to track.

### /{discord_cmd} member add *name faction [discord-name] [date] [admin] [notes]*

Add a new member to the company specify their New World character name and faction, starting from today (unless another date is specified). The *discord-name* and *admin* flag are ignored at this time.

### /{discord_cmd} member list

List all registered company members at this time.

### /{discord_cmd} member remove *player*

Remove *player* as a company member from this date.
'''

help_text['report'] = f'''
# Invasions R Us Stats - Report Commands

Generate reports as CSV files and display summary in discord.

### /{discord_cmd} report invasion *invasion*

Generate the report for a specific invasion. Invasions are identified using the date and settlement abrieviation (*YYYYMMDD-SS*). For example `20240918-ef` is an invasion in Everfall on 18 September 2024.

### /{discord_cmd} report month *[month] [year]*

Generate the invasion statistics report for the current (default) or specified month and year.

### /{discord_cmd} report member *player [month] [year]*

Generate a summary report for a specific player for the current (default) or specified month and year.

### /{discord_cmd} report members *[month] [year]*

Generate a summary report for all current members for the current (default) or specified month and year.
'''


#
# Authenticate Requests
# Verify raises exception if it fails
#
logger = IrusResources.logger()
app_id = IrusSecrets.app_id()
role_id = IrusSecrets.role_id()
process = IrusProcess()
post_table = IrusPostTable()

def verify_signature(event):
    body = event['body']
    auth_sig = event['headers'].get('x-signature-ed25519')
    auth_ts  = event['headers'].get('x-signature-timestamp')

    # message = auth_ts.encode() + body.encode()
    verify_key = VerifyKey(IrusSecrets.public_key_bytes())
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
    win = True

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
    
    return item


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


def invasion_edit_cmd(options:list) -> str:
    logger.info(f'invasion_edit: {options}')

    invasion = None
    rank = None
    new_rank = None
    member = None
    player = None
    score = None

    try:
        for o in options:
            if o["name"] == "invasion":
                invasion = IrusInvasion.from_table(o["value"])
            elif o["name"] == "rank":
                rank = int(o["value"])
            elif o["name"] == "new_rank":
                new_rank = int(o["value"])
            elif o["name"] == "member":
                member = bool(o["value"])
            elif o["name"] == "player":
                player = o["value"]
            elif o["name"] == "score":
                score = int(o["value"])                
    except ValueError as e:
        logger.info(e)
        return str(e)
    
    ladder = IrusLadder.from_invasion(invasion)
    return ladder.edit(rank=rank, new_rank=new_rank, member=member, player=player, score=score)
    

def invasion_rank_cmd(options:list) -> str:
    logger.info(f'invasion_edit: {options}')

    invasion = None
    rank = None

    try:
        for o in options:
            for o in options:
                if o["name"] == "invasion":
                    invasion = IrusInvasion.from_table(o["value"])
                elif o["name"] == "rank":
                    rank = int(o["value"])             
    except ValueError as e:
        logger.info(e)
        return str(e)

    ladder = IrusLadder.from_invasion(invasion)
    row = ladder.rank(rank)
    if row is None:
        return f'No rank {rank} in invasion {invasion.name}'
    else:
        return row.str()


def invasion_cmd(id:str, token:str, options:dict, resolved: dict) -> str:
    logger.info(f'invasion_cmd: {options}')
    name = options['name']
    if name == 'help':
        return help_text['invasion']
    elif name == 'list':
        return invasion_list_cmd(options['options'])
    elif name == 'edit':
        return invasion_edit_cmd(options['options'])
    elif name == 'rank':
        return invasion_rank_cmd(options['options'])
    elif name == 'add':
        return invasion_add_cmd(options['options']).markdown()
    elif name == 'ladder' or name == 'screenshots':
        return invasion_download_cmd(id, token, options['options'], resolved, 'Ladder')
    elif name == 'roster':
        return invasion_download_cmd(id, token, options['options'], resolved, 'Roster')
    else:
        logger.error(f'Invalid command {name}')
        return f'Invalid command {name}'


def invasion_process(id: str, token: str, invasion: IrusInvasion, options:list, resolved:dict, method:str) -> str:
    logger.info(f'invasion_process:\nid: {id}\ntoken: {token}\noptions: {options}\nresolved: {resolved}\nmethod: {method}')

    files = IrusFiles()

    try:
        for o in options:
            if o["name"].startswith("file"):
                files.append(name = o["name"], attachment = o["value"])
    except ValueError as e:
        logger.info(e)
        return str(e)

    files.update(resolved['attachments'])

    return process.start(id, token, invasion, files, method)


#
# Member Commands
#

def member_list_cmd() -> str:
    return IrusMemberList().markdown()


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
    mesg = member.str()
    mesg += irus.update_invasions_for_new_member(member)
    logger.info(f'member_add_cmd: {mesg}')

    return mesg


def member_remove_cmd(options:list) -> str:

    player = None
    for o in options:
        if o["name"] == "player":
            player = o["value"]

    try:
        member = IrusMember.from_table(player)
    except ValueError:
        return f'*Member {player} not found*'
    return member.remove()


def member_cmd(options:dict, resolved: dict) -> str:
    logger.info(f'member_cmd: {options}')

    name = options['name']
    if name == 'help':
        return help_text['member']
    elif name == 'list':
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

    stats = IrusMonth.from_invasion_stats(month = month, year = year)
    report = IrusReport.from_month(stats)
    return stats.str() + report.msg


def report_invasion_cmd(options:list) -> str:

    name = None
    for o in options:
        if o["name"] == "invasion":
            name = o["value"]

    if not name:
        return 'Missing invasion from request'

    invasion = IrusInvasion.from_table(name)
    ladder = IrusLadder.from_invasion(invasion)
    report = IrusReport.from_invasion(ladder)
    return f"# Report for Invasion {name}\n" + report.msg


def report_member_cmd(options:list) -> str:

    now = datetime.now()
    month = now.month
    year = now.year
    member = None
    report = None

    for o in options:
        if o["name"] == "player":
            player = o["value"]
        elif o["name"] == "month":
            month = o["value"]
        elif o["name"] == "year":
            year = o["value"]

    try:
        member = IrusMember.from_table(player)
    except:
        mesg = f'*Member {player} not found*'

    if member:
        mesg = f'# Report for {player}\n'
        mesg += member.str()
        try:
            report = IrusMonth.from_table(month, year)
        except:
            mesg = f'*No monthly stats for {player} during {month}/{year}*'

        if report:
            mesg += report.member_stats(player)

    logger.debug(mesg)
    return mesg


def report_members_cmd(options:list) -> str:
    now = datetime.now().strftime("%Y%m%d%H%M%S")
    members = IrusMemberList()
    logger.debug(f'report_members_cmd: {members}')
    report = IrusReport.from_members(timestamp = now, report = members.csv())
    return f"# Report of current members\n" + report.msg


def report_cmd(options:dict, resolved: dict) -> str:
    logger.info(f'report_cmd: {options}')

    name = options['name']
    if name == 'help':
        return help_text['report']
    elif name == 'month':
        return report_month_cmd(options['options'])
    elif name == 'invasion':
        return report_invasion_cmd(options['options'])
    elif name == 'member':
        return report_member_cmd(options['options'])
    elif name == 'members':
        return report_members_cmd(options['options'])
    else:
        logger.error(f'Invalid command {name}')
        return f'Invalid command {name}'

#
# Display reports using multiple webhook posts
#

def display_month_cmd(id: str, token: str) -> str:
    return "Not implemented yet"

def display_invasion_cmd(id: str, token: str) -> str:
    return "Not implemented yet"

def display_member_cmd(id: str, token: str) -> str:
    return "Not implemented yet"

def display_members_cmd(id: str, token: str) -> str:
    now = datetime.now().strftime("%Y%m%d%H%M%S")
    members = IrusMemberList()
    logger.debug(f'report_members_cmd: {members}')
    return post_table.start(id, token, members.post(), '# Company Members')


def display_cmd(id: str, token: str, options:dict, resolved: dict) -> str:
    logger.info(f'report_cmd: {options}')

    name = options['name']
    if name == 'help':
        return help_text['display']
    elif name == 'month':
        return display_month_cmd(id, token, options['options'])
    elif name == 'invasion':
        return display_invasion_cmd(id, token, options['options'])
    elif name == 'member':
        return display_member_cmd(id, token, options['options'])
    elif name == 'members':
        return display_members_cmd(id, token)
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
    admin = False

    try: 
        verify_signature(event)
        logger.debug("Signature verified")

        body = json.loads(event['body'])
        if body["type"] == 1:
            data = ({'type': 1})

        elif body["type"] == 2 and body["data"]["name"] == discord_cmd:
            logger.debug(f'body: {body["data"]}')
            subcommand = body["data"]["options"][0]
            logger.debug(f'subcommand: {subcommand}')
            resolved = body["data"]["resolved"] if "resolved" in body["data"] else None
            roles = body["member"]["roles"]
            admin = role_id in roles
            logger.debug(f'admin: {admin} roles: {roles}')

            if admin:
                if subcommand["name"] == "help":
                    content = help_text["help"]
                elif subcommand["name"] == "invasion":
                    content = invasion_cmd(app_id, body['token'], subcommand["options"][0], resolved)
                elif subcommand["name"] == "ladders" or subcommand["name"] == "ladder":
                    invasion = invasion_add_cmd(subcommand["options"])
                    invasion_process(app_id, body['token'], invasion, subcommand["options"], resolved, 'Ladder')
                    content = f'In Progress: Registered invasion {invasion.name}, next download file(s)'
                elif subcommand["name"] == "roster":
                    invasion = invasion_add_cmd(subcommand["options"])
                    invasion_process(app_id, body['token'], invasion, subcommand["options"], resolved, 'Roster')
                    content = f'In Progress: Registered invasion {invasion.name}, next download file(s)'
                elif subcommand["name"] == "report":
                    content = report_cmd(subcommand["options"][0], resolved)
                elif subcommand["name"] == "display":
                    display_cmd(app_id, body['token'], subcommand["options"][0], resolved)
                    content = f'In Progress:'
                elif subcommand["name"] == "member":
                    content = member_cmd(subcommand["options"][0], resolved)
                else:
                    content = f'Unexpected subcommand {subcommand["name"]}'            
            else:
                if subcommand["name"] == "help":
                    content = help_text["report"]
                elif subcommand["name"] == "report":
                    content = report_cmd(subcommand["options"][0], resolved)
                elif subcommand["name"] == "display":
                    content = display_cmd(app_id, body['token'], subcommand["options"][0], resolved)
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
          