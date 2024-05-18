import boto3
from botocore.exceptions import ClientError
from boto3.dynamodb.conditions import Key, Attr
import os
from datetime import datetime
import urllib3

# get bucket name of environment
s3 = boto3.client('s3')
bucket_name = os.environ.get('BUCKET_NAME')

# table details
dynamodb = boto3.resource('dynamodb')
table_name = os.environ['TABLE_NAME']
table = dynamodb.Table(table_name)

pool_mgr = urllib3.PoolManager()

def invasion_list() -> str:
    print(f'invasion_list:')
    response = table.query(KeyConditionExpression=Key('invasion').eq('#invasion'),
                           ProjectionExpression='id')
    print(response)

    res = ''
    if not response.get('Items', None):
        res = 'No invasions found'
    else:
        res = response["Items"][0]["id"]
        for i in response["Items"][1:]:
            res += ", " + i["id"]
        print(f'str: {res}')
        return res
    
    return res


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


def invasion_today(options:list) -> str:
    print(f'invasion_today: {options}')
    notes=None
    for o in options:
        if o["name"] == "settlement":
            settlement = o["value"]
        elif o["name"] == "win":
            win = bool(["value"])
        elif o["name"] == "notes":
            notes = o["value"]

    now = datetime.now()
    return register_invasion(day=now.day,
                            month=now.month,
                            year=now.year,
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


def invasion_cmd(options:dict, resolved: dict) -> str:
    print(f'invasion_cmd: {options}')
    name = options['name']
    if name == 'list':
        return invasion_list()
    elif name == 'add':
        return invasion_add(options['options'])
    elif name == 'today':
        return invasion_today(options['options'])
    elif name == 'ladder':
        return invasion_ladder(options['options'],resolved)
    else:
        print(f'Invalid command {name}')
        return f'Invalid command {name}'

# define lambda handler that takes an invasion name and calls create_folder
# def lambda_handler(event, context):

#     body = ""
#     statusCode = 200
#     headers = {
#         "Content-Type": "application/json"
#     }

#     print(event)

#     try:
#         # if routeKey is GET /, set body to a list of all invasions from table
#         if event['httpMethod'] == 'GET' and event['resource'] == '/invasions':
#             # get all invasions
#             response = table.query(KeyConditionExpression=Key('invasion').eq('#invasion'),
#                                    ProjectionExpression='id')
#             # set body to id and labels
#             print(response)
        
#             if not response.get('Items', None):
#                 statusCode = 404
#                 body = f'No invasions found'
#             else:
#                 body = str(response["Items"])

#         elif event['httpMethod'] == 'POST' and event['resource'] == '/invasions/add':
#             # register a new invasion
#             request = json.loads(event['body'])
#             year = request['year']
#             month = '{0:02d}'.format(int(request['month']))
#             day = '{0:02d}'.format(int(request['day']))
#             date = f'{year}{month}{day}'
#             settlement = request['settlement']
#             win = request['win']
#             notes = request['notes'] if 'notes' in event else None

#             folder = date + '-' + settlement

#             create_folder(folder)
#             body = f'Created folders for {folder}'

#             item = {
#                 'invasion': f'#invasion',
#                 'id': folder,
#                 'settlememt': settlement,
#                 'win': win,
#                 'date': int(date),
#                 'year': int(year),
#                 'month': int(month),
#                 'day': int(day)
#             }

#             if notes:
#                 item['notes'] = notes

#             # Add row to identify this invasion
#             table.put_item(Item=item)

#         else:
#             print(f"Unsupported route: {event['httpMethod']} {event['resource']}")
#             statusCode = 400
#             body = f"Unsupported route: {event['httpMethod']} {event['resource']}"

#     except Exception as e:
#         print(e)
#         raise

#     return {
#         'statusCode': statusCode,
#         'headers': headers,
#         'body': json.dumps(body)
#     }


