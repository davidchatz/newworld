import boto3
from botocore.exceptions import ClientError
from boto3.dynamodb.conditions import Key, Attr
import os
from datetime import datetime
import urllib3

# get bucket name of environment
s3 = boto3.client('s3')
s3_resource = boto3.resource('s3')
bucket_name = os.environ.get('BUCKET_NAME')

# table details
dynamodb = boto3.resource('dynamodb')
table_name = os.environ['TABLE_NAME']
table = dynamodb.Table(table_name)


def member_list() -> str:
    print(f'member list:')

    now = datetime.now()
    month = now.month
    year = now.year
    day = now.day
    zero_month = '{0:02d}'.format(month)
    zero_day = '{0:02d}'.format(day)
    date = f'{year}{zero_month}{zero_day}'

    response = table.query(KeyConditionExpression=Key('invasion').eq('#member'))
    print(response)

    if not response.get('Items', None):
        mesg = f'No members found'
    else:
        items = response["Items"]

        body = f"player,faction,start\n"
        for player in items:
            body += '{id},{faction},{start}\n'.format_map(player)

        filename = f'members/{date}.csv'
        print(f'Writing member list to {bucket_name}/{filename}')
        s3_resource.Object(bucket_name, filename).put(Body=body)

        print(f'Generating presigned URL for {filename}')
        try:
            presigned = s3.generate_presigned_url('get_object', Params={'Bucket': bucket_name, 'Key': filename}, ExpiresIn=3600)
            mesg = f'# {len(items)} Members\nDownload the report (for 1 hour) from **[here]({presigned})**'
        except ClientError as e:
            print(e)
            mesg = f'Error generating presigned URL for {filename}: {e}'

    return mesg

def register_member(player:str, day:int, month:int, year:int, faction:str, discord:str, admin:bool, notes:str) -> str:
    print(f'register_member: {player} {day} {month} {year} {faction} {discord}')

    zero_month = '{0:02d}'.format(month)
    zero_day = '{0:02d}'.format(day)
    start = f'{year}{zero_month}{zero_day}'

    timestamp = datetime.today().strftime('%Y%m%d%H%M%S')

    additem = {
        'invasion': '#memberevent',
        'id': timestamp,
        'event': "add",
        'player': player,
        'faction': faction,
        'admin': admin,
        'start': start
    }

    if discord:
        additem['discord'] = discord
    if notes:
        additem['notes'] = notes

    memberitem = {
        'invasion': '#member',
        'id': player,
        'faction': faction,
        'admin': admin,
        'event': timestamp,
        'start': start
    }

    if discord:
        memberitem['discord'] = discord
    if notes:
        memberitem['notes'] = notes

    # Add event for adding this member and update list of members
    table.put_item(Item=additem)
    table.put_item(Item=memberitem)

    return f'# New member {player}\nFaction: {faction}\nStarting {start}\nAdmin {admin}'


def member_add(options:list) -> str:
    print(f'member add: {options}')

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

    return register_member(player=player,
                           day=day,
                           month=month,
                           year=year,
                           faction=faction,
                           discord=discord,
                           admin=admin,
                           notes=notes)


def member_remove(options:list) -> str:
    print(f'member remove: {options}')

    for o in options:
        if o["name"] == "player":
            player = o["value"]

    timestamp = datetime.today().strftime('%Y%m%d%H%M%S')

    item = {
        'invasion': f'#memberevent',
        'id': timestamp,
        'event': "delete",
        'player': player
    }

    response = table.delete_item(Key={'invasion': f'#member', 'id': player}, ReturnValues='ALL_OLD')
    if 'Attributes' in response:
        mesg = f'# Removed member {player}'
        table.put_item(Item=item)
    else:
        mesg = f'Member {player} not found, nothing to remove'

    return mesg


def member_cmd(options:dict, resolved: dict) -> str:
    print(f'member_cmd: {options}')

    try:
        name = options['name']
        if name == 'list':
            return member_list()
        elif name == 'add':
            return member_add(options['options'])
        elif name == 'remove':
            return member_remove(options['options'])
        else:
            print(f'Invalid command {name}')
            return f'Invalid command {name}'
    except Exception as e:
        print(f'Member command error: {e}')
        return f'Member command error: {e}'

# # define lambda handler that takes an invasion name and calls create_folder
# def lambda_handler(event, context):

#     body = ""
#     statusCode = 200
#     headers = {
#         "Content-Type": "application/json"
#     }

#     print(event)

#     try:
#         # get current member list
#         if event['httpMethod'] == 'GET' and event['resource'] == '/members':

#             response = table.query(KeyConditionExpression=Key('invasion').eq('#member'),
#                                    ProjectionExpression='id')
#             # set body to id and labels
#             print(response)
        
#             if not response.get('Items', None):
#                 statusCode = 404
#                 body = f'No members found'
#             else:
#                 items = response["Items"]
#                 body = f"Members {len(items)}: "
#                 if len(items) > 0:
#                     body += items.pop(0)["id"]
#                     for player in items:
#                         body += ", " + player["id"]

#         # if routeKey is GET /, set body to a list of all invasions from table
#         elif event['httpMethod'] == 'GET' and event['resource'] == '/members/{player}':

#             player = event['pathParameters']['player']
#             response = table.get_item(Key={"invasion": "#member", "id": player})
#             print(response)
        
#             if not 'Item' in response:
#                 statusCode = 404
#                 body = f'Member {player} not found'
#             else:
#                 body = str(response["Item"])

#         elif event['httpMethod'] == 'POST' and event['resource'] == '/members/add':
#             # add or update a member
#             request = json.loads(event['body'])
#             timestamp = datetime.today().strftime('%Y%m%d%H%M%S')

#             player = request['player']
#             faction = request['faction']
#             discord = request['discord'] if 'discord' in request else None
#             start = request['start'] if 'start' in request else datetime.today().strftime('%Y%m%d')
#             notes = request['notes'] if 'notes' in event else None
#             admin = request['admin'] == True if 'admin' in request else False

#             additem = {
#                 'invasion': '#memberevent',
#                 'id': timestamp,
#                 'event': "add",
#                 'player': player,
#                 'faction': faction,
#                 'admin': admin
#             }

#             if discord:
#                 additem['discord'] = discord
#             if notes:
#                 additem['notes'] = notes

#             memberitem = {
#                 'invasion': '#member',
#                 'id': player,
#                 'faction': faction,
#                 'admin': admin,
#                 'event': timestamp,
#                 'start': start
#             }

#             if discord:
#                 memberitem['discord'] = discord
#             if notes:
#                 memberitem['notes'] = notes

#             # Add event for adding this member and update list of members
#             table.put_item(Item=additem)
#             table.put_item(Item=memberitem)
#             body = f'Added member {player} faction {faction} starting {start} admin {admin}'

#         elif event['httpMethod'] == 'DELETE' and event['resource'] == '/members/{player}':
#             # add or update a member
#             player = event['pathParameters']['player']
#             timestamp = datetime.today().strftime('%Y%m%d%H%M%S')

#             item = {
#                 'invasion': f'#memberevent',
#                 'id': timestamp,
#                 'event': "delete",
#                 'player': player
#             }

#             response = table.delete_item(Key={'invasion': f'#member', 'id': player}, ReturnValues='ALL_OLD')
#             if 'Attributes' in response:
#                 body = f'Deleted member {player}: {response["Attributes"]}'
#                 table.put_item(Item=item)
#             else:
#                 body = f'Member {player} not found, nothing to delete'

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


