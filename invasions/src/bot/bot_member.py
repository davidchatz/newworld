import boto3
from botocore.exceptions import ClientError
from boto3.dynamodb.conditions import Key, Attr
import os
from datetime import datetime

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

def register_member(player:str, day:int, month:int, year:int, faction:str, discord:str, admin:bool, salary: bool, notes:str) -> str:
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
        'start': start,
        'salary': salary
    }

    if discord:
        memberitem['discord'] = discord
    if notes:
        memberitem['notes'] = notes

    # Add event for adding this member and update list of members
    table.put_item(Item=additem)
    table.put_item(Item=memberitem)

    return f'# New member {player}\nFaction: {faction}\nStarting {start}\nAdmin {admin}'


def update_invasions(player:str, day:int, month:int, year:int) -> str:
    print(f'update_invasions: {player} {day} {month} {year}')

    zero_month = '{0:02d}'.format(month)
    zero_day = '{0:02d}'.format(day)
    start = int(f'{year}{zero_month}{zero_day}')

    response = table.query(KeyConditionExpression=Key('invasion').eq('#invasion'),
                           ProjectionExpression='id, #d',
                           FilterExpression=Attr('date').gte(start),
                           ExpressionAttributeNames={'#d': 'date'})
    print(f'Invasions on or after {start}: {response}')

    if not response.get('Items', None):
        mesg = f'\nNo invasions found on or after {start} to update\n'
    else:
        items = response["Items"]
        mesg = f'\n## Member flag updated in these invasions:\n'
        for i in items:
            invasion = i["id"]
            ladder = table.query(KeyConditionExpression=Key('invasion').eq(f'#ladder#{invasion}'),
                                    ProjectionExpression='id, #n, #r',
                                    FilterExpression=Attr('name').eq(player),
                                    ExpressionAttributeNames={'#n': 'name', '#r': 'rank'})

            if ladder.get('Items', None):
                print(f'Ladder for invasion {invasion} with place for {player}: {ladder}')
                rank = ladder["Items"][0]["id"]
                mesg += f'- {invasion} rank {rank}\n'
                update = table.update_item(Key={'invasion': f'#ladder#{invasion}', 'id': rank},
                                           UpdateExpression='set #m = :m',
                                           ExpressionAttributeNames={'#m': 'member'},
                                           ExpressionAttributeValues={':m': True},
                                           ReturnValues='UPDATED_NEW')
                print(f'update_item: #ladder#{invasion} {rank} {update}')

    return mesg


def member_add(options:list) -> str:
    print(f'member add: {options}')

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
            notes = o["value"]        

    mesg = register_member(player=player,
                           day=day,
                           month=month,
                           year=year,
                           faction=faction,
                           discord=discord,
                           admin=admin,
                           salary=salary,
                           notes=notes)
    
    mesg += update_invasions(player=player,
                             day=day,
                             month=month,
                             year=year)

    return mesg

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
