import boto3
from botocore.exceptions import ClientError
from boto3.dynamodb.conditions import Key, Attr
import os
from datetime import datetime
import urllib3
import json

# get bucket name of environment
s3 = boto3.client('s3')
bucket_name = os.environ.get('BUCKET_NAME')

# table details
dynamodb = boto3.resource('dynamodb')
table_name = os.environ['TABLE_NAME']
table = dynamodb.Table(table_name)

# downloader step function
state_machine = boto3.client('stepfunctions')
step_function_arn = os.environ.get('DOWNLOADER_STEP_FUNC')
webhook_url = os.environ.get('WEBHOOK_URL')

pool_mgr = urllib3.PoolManager()

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


# define function that takes an invasion name and creates a folder in bucket
def create_folder(invasion_name):
    print(f'create_folder: {bucket_name}/{invasion_name}')
    s3.put_object(Bucket=bucket_name, Key=(invasion_name + '/'))
    s3.put_object(Bucket=bucket_name, Key=(invasion_name + '/ladder/'))
    s3.put_object(Bucket=bucket_name, Key=(invasion_name + '/discord/'))
    print('Created folder for ' + invasion_name)


def register_invasion(day:int, month:int, year:int, settlement:str, win:bool, notes:str = None) -> str:
    print(f'register_invasion: {day}, {month}, {year}, {settlement}, {win}, {notes}')

    zero_month = '{0:02d}'.format(month)
    zero_day = '{0:02d}'.format(day)
    date = f'{year}{zero_month}{zero_day}'
    folder = date + '-' + settlement

    create_folder(folder)

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

    return f'Created folders for {folder}'


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

    return register_invasion(day=day,
                            month=month,
                            year=year,
                            settlement=settlement,
                            win=win,
                            notes=notes)


def invasion_ladder(options:list, resolved:dict) -> str:
    print(f'invasion_ladder: {options}')

    for o in options:
        if o["name"] == "invasion":
            invasion = o["value"]
        elif o["name"] == "file":
            attachment = o["value"]

    print(f'resolved: {resolved["attachments"][attachment]}')
    # content_type = resolved['attachment']['content_type']
    filename = resolved['attachments'][attachment]['filename']
    url = resolved['attachments'][attachment]['url']
    target = invasion + '/ladder/' + filename

    print(f'Checking {invasion} exists')
    # Check this invasion exists
    try:
        s3.head_object(Bucket=bucket_name, Key=invasion + '/ladder/')
    except ClientError as e:
        if e.response['Error']['Code'] == '404':
            return f'Invasion {invasion} does not exist'

    print(f'Downloading file {filename} from {url}')

    try:
        s3.upload_fileobj(pool_mgr.request('GET', url, preload_content=False), bucket_name, target)
    except Exception as e:
        return f'Error uploading {filename} to {target}: {e}'

    return f'Uploaded screenshot {filename}'


def invasion_screenshots(id: str, token: str, options:list, resolved:dict) -> str:
    print(f'invasion_screenshots:\nid: {id}\ntoken: {token}\noptions: {options}\nresolved: {resolved}')

    cmd = {
        'post': f'{webhook_url}/{id}/{token}',
        'invasion': 'tbd',
        'files': []
    }

    for o in options:
        if o["name"] == "invasion":
            cmd['invasion'] = o["value"]
        elif o["name"].startswith("file"):
            cmd['files'].append({
                "name": o["name"],
                "attachment": o["value"]
            })

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

    return f'In Progress: Downloading and processing screenshots'


def invasion_cmd(id:str, token:str, options:dict, resolved: dict) -> str:
    print(f'invasion_cmd: {options}')
    name = options['name']
    if name == 'list':
        return invasion_list(options['options'])
    elif name == 'add':
        return invasion_add(options['options'])
    elif name == 'ladder':
        return invasion_ladder(options['options'],resolved)
    elif name == 'screenshots':
        return invasion_screenshots(id, token, options['options'],resolved)
    else:
        print(f'Invalid command {name}')
        return f'Invalid command {name}'
