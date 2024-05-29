import boto3
from botocore.exceptions import ClientError
from boto3.dynamodb.conditions import Key
import os
from datetime import datetime
import json

# table details
dynamodb = boto3.resource('dynamodb')
table_name = os.environ['TABLE_NAME']
table = dynamodb.Table(table_name)

# downloader step function
state_machine = boto3.client('stepfunctions')
step_function_arn = os.environ.get('PROCESS_STEP_FUNC')
webhook_url = os.environ.get('WEBHOOK_URL')

def invasion_list(options:list) -> str:
    print(f'invasion_list: {options}')

    now = datetime.now()
    month = now.month
    year = now.year

    for o in options:
        if o["name"] == "month":
            month = int(o["value"])
        elif o["name"] == "year":
            year = int(o["value"])

    zero_month = '{0:02d}'.format(month)
    date = f'{year}{zero_month}'

    response = table.query(KeyConditionExpression=Key('invasion').eq('#invasion') & Key('id').begins_with(date),
                           ProjectionExpression='id')
    print(response)

    msg = ''
    if not response.get('Items', None):
        msg = f'No invasions found for month of {date}'
    else:
        msg = f'# Invasion List for {date}\n'
        for i in response["Items"]:
            msg += f'- {i["id"]}\n'
    
    return msg


def register_invasion(day:int, month:int, year:int, settlement:str, win:bool, notes:str = None) -> str:
    print(f'register_invasion: {day}, {month}, {year}, {settlement}, {win}, {notes}')

    zero_month = '{0:02d}'.format(month)
    zero_day = '{0:02d}'.format(day)
    date = f'{year}{zero_month}{zero_day}'
    folder = date + '-' + settlement

    print(f'Add #invasion object for {folder}')
    item = {
        'invasion': f'#invasion',
        'id': folder,
        'settlememt': settlement,
        'win': win,
        'date': int(date),
        'year': year,
        'month': month,
        'day': day
    }
    if notes:
        item['notes'] = notes
    table.put_item(Item=item)

    return item


def invasion_add(options:list) -> str:
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

    item = register_invasion(day=day,
                             month=month,
                             year=year,
                             settlement=settlement,
                             win=win,
                             notes=notes)

    return f'Registered invasion {item['id']}'


def invasion_screenshots(id: str, token: str, options:list, resolved:dict, folder:str, process:str) -> str:
    print(f'invasion_screenshots:\nid: {id}\ntoken: {token}\noptions: {options}\nresolved: {resolved}')

    cmd = {
        'post': f'{webhook_url}/{id}/{token}',
        'invasion': 'tbd',
        'folder': 'tbd',
        'files': [],
        'process': process,
        'month': 'tbd'
    }

    for o in options:
        if o["name"] == "invasion":
            cmd['invasion'] = o["value"]
        elif o["name"].startswith("file"):
            cmd['files'].append({
                "name": o["name"],
                "attachment": o["value"]
            })

    if process == "Ladder" or process == "Download":
        cmd['folder'] = 'ladders/' + cmd['invasion'] + '/'
    elif process == "Roster":
        cmd['folder'] = 'boards/' + cmd['invasion'] + '/'
    else:
        raise Exception('invasion_screenshots: Unknown process')

    cmd['month'] = cmd['invasion'][:6]

    for a in cmd['files']:
        a['filename'] = resolved['attachments'][a['attachment']]['filename']
        a['url'] = resolved['attachments'][a['attachment']]['url']

    print(cmd)
    try:
        state_machine.start_execution(
            stateMachineArn=step_function_arn,
            input=json.dumps(cmd)
        )
    except ClientError as e:
        return f'Failed to call downloader step function: {e}'

    return f'In Progress: Downloading and processing screenshot(s)'


def invasion_all(id: str, token: str, options:list, resolved:dict, process:str) -> str:
    print(f'invasion_all:\nid: {id}\ntoken: {token}\noptions: {options}\nresolved: {resolved}\nprocess: {process}')

    item = invasion_add(options['options'])
    invasion_screenshots(id, token, options['options'], resolved, process)
    return f'In Progress: Registered invasion {item['id']}, next download file(s)'


def invasion_cmd(id:str, token:str, options:dict, resolved: dict) -> str:
    print(f'invasion_cmd: {options}')
    name = options['name']
    if name == 'list':
        return invasion_list(options['options'])
    elif name == 'add':
        return invasion_add(options['options'])
    elif name == 'ladder':
        return invasion_screenshots(id, token, options['options'], resolved, 'Download')
    elif name == 'screenshots':
        return invasion_screenshots(id, token, options['options'], resolved, 'Ladder')
    elif name == 'roster':
        return invasion_screenshots(id, token, options['options'], resolved, 'Roster')
    else:
        print(f'Invalid command {name}')
        return f'Invalid command {name}'
