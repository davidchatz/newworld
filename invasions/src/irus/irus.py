import os
import json
import boto3
from botocore.exceptions import ClientError
from boto3.dynamodb.conditions import Key, Attr
from datetime import datetime
from decimal import Decimal, getcontext

# get bucket name of environment
s3 = boto3.client('s3')
s3_resource = boto3.resource('s3')
bucket_name = os.environ.get('BUCKET_NAME')

# table details
dynamodb = boto3.resource('dynamodb')
table_name = os.environ['TABLE_NAME']
table = dynamodb.Table(table_name)

# downloader step function
state_machine = boto3.client('stepfunctions')
step_function_arn = os.environ.get('PROCESS_STEP_FUNC')
webhook_url = os.environ.get('WEBHOOK_URL')


# precision to use for Decimals
prec = Decimal("1.0")


def invasion_list(month:int, year:int) -> str:

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


def invasion_add(day:int, month:int, year:int, settlement:str, win:bool, notes:str = None) -> str:
    print(f'invasion_add: {day}, {month}, {year}, {settlement}, {win}, {notes}')

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


def invasion_download(id: str, token: str, invasion:str, month:str, files:list, process:str) -> str:

    cmd = {
        'post': f'{webhook_url}/{id}/{token}',
        'invasion': invasion,
        'folder': 'tbd',
        'files': files,
        'process': process,
        'month': month
    }

    if process == "Ladder" or process == "Download":
        cmd['folder'] = 'ladders/' + cmd['invasion'] + '/'
    elif process == "Roster":
        cmd['folder'] = 'boards/' + cmd['invasion'] + '/'
    else:
        raise Exception('invasion_download: Unknown process')

    print(cmd)
    try:
        state_machine.start_execution(
            stateMachineArn=step_function_arn,
            input=json.dumps(cmd)
        )
    except ClientError as e:
        return f'Failed to call downloader step function: {e}'

    return f'In Progress: Downloading and processing screenshot(s)'


#
# Member Commands
#

def member_list(day:int, month:int, year:int) -> str:
    print(f'member list: {date}')

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


def member_remove(player:str) -> str:
    print(f'member remove: {player}')

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



def generate_month_report(month:str):
    print(f'generate_month_report for {month}')

    invasions = table.query(KeyConditionExpression=Key('invasion').eq(f'#invasion') & Key('id').begins_with(month),
                            ProjectionExpression='id')            

    members = table.query(KeyConditionExpression=Key('invasion').eq(f'#member'),
                            ProjectionExpression='id')
        
    if not invasions.get('Items', None):
        print(f'No invasions found for {month}')
        return False, f'No invasions found for {month}'

    if not members.get('Items', None):
        print('No members found')
        return False, 'No members found'

    report = []
    for member in members['Items']:
        report.append({'invasion': f'#month#{month}', 'id': member['id'], 'invasions': Decimal(0), 'ladders': Decimal(0),
                        'sum_score': 0, 'sum_kills': 0, 'sum_assists': 0, 'sum_deaths': 0, 'sum_heals': 0, 'sum_damage': 0,
                        'avg_score': Decimal(0.0), 'avg_kills': Decimal(0.0), 'avg_assists': Decimal(0.0), 'avg_deaths': Decimal(0.0), 'avg_heals': Decimal(0.0), 'avg_damage': Decimal(0.0), 'avg_rank': Decimal(0.0),
                        'max_score': Decimal(0.0), 'max_kills': Decimal(0.0), 'max_assists': Decimal(0.0), 'max_deaths': Decimal(0.0), 'max_heals': Decimal(0.0), 'max_damage': Decimal(0.0), 'max_rank': Decimal(100.0)
                    })

    for invasion in invasions["Items"]:
        ladder = table.query(KeyConditionExpression=Key('invasion').eq(f'#ladder#{invasion["id"]}'),
                                FilterExpression=Attr('member').eq(True))
        
        if not ladder.get('Items', None):
            print(f'No members found in ladder for {invasion["id"]}')
            continue

        for row in ladder["Items"]:
            found = False
            for r in report:
                if r["id"] == row["name"]:
                    r["invasions"] += 1
                    if 'ladder' not in row or row['ladder'] == True:
                        r["ladders"] += 1
                        r["sum_score"] += row["score"]
                        r["sum_kills"] += row["kills"]
                        r["sum_assists"] += row["assists"]
                        r["sum_deaths"] += row["deaths"]
                        r["sum_heals"] += row["heals"]
                        r["sum_damage"] += row["damage"]
                        r["avg_rank"] += Decimal(row["id"])
                        r["max_score"] = max(r["max_score"], row["score"])
                        r["max_kills"] = max(r["max_kills"], row["kills"])
                        r["max_assists"] = max(r["max_assists"], row["assists"])
                        r["max_deaths"] = max(r["max_deaths"], row["deaths"])
                        r["max_heals"] = max(r["max_heals"], row["heals"])
                        r["max_damage"] = max(r["max_damage"], row["damage"])
                        r["max_rank"] = min(r["max_rank"], Decimal(row["id"]))
                    else:
                        print(f'Skipping stats for {row["name"]} from non-ladder invasion {invasion["id"]}')
                    found = True
                    break

            if not found:
                print(f'Player {row["name"]} not found in member list, skipping')

    # compute averages
    for r in report:
        if r["ladders"] > 0:
            r["avg_score"] = (r["sum_score"] / r["ladders"]).quantize(prec)
            r["avg_kills"] = (r["sum_kills"] / r["ladders"]).quantize(prec)
            r["avg_assists"] = (r["sum_assists"] / r["ladders"]).quantize(prec)
            r["avg_deaths"] = (r["sum_deaths"] / r["ladders"]).quantize(prec)
            r["avg_heals"] = (r["sum_heals"] / r["ladders"]).quantize(prec)
            r["avg_damage"] = (r["sum_damage"] / r["ladders"]).quantize(prec)
            r["avg_rank"] /= r["ladders"]
            r["avg_rank"] = r["avg_rank"].quantize(prec)

    print(f'computed report: {report}')

    body = 'month,name,invasions,ladders,sum_score,sum_kills,sum_assists,sum_deaths,sum_heals,sum_damage,avg_score,avg_kills,avg_assists,avg_deaths,avg_heals,avg_damage,avg_ranks,max_score,max_kills,max_assists,max_deaths,max_heals,max_damage,max_rank\n'

    count = 0
    participation = 0
    with table.batch_writer() as batch:
        for r in report:
            if r["invasions"] > 0:
                count += 1
                participation += r["ladders"]
                batch.put_item(Item=r)
                body += f'{month},{r["id"]},{r["invasions"]},{r["ladders"]},{r["sum_score"]},{r["sum_kills"]},{r["sum_assists"]},{r["sum_deaths"]},{r["sum_heals"]},{r["sum_damage"]},{r["avg_score"]},{r["avg_kills"]},{r["avg_assists"]},{r["avg_deaths"]},{r["avg_heals"]},{r["avg_damage"]},{r["avg_rank"]},{r["max_score"]},{r["max_kills"]},{r["max_assists"]},{r["max_deaths"]},{r["max_heals"]},{r["max_damage"]},{r["max_rank"]}\n'

    filename = f'month/{month}.csv'
    print(f'Writing ladder to {bucket_name}/{filename}')
    s3_resource.Object(bucket_name, filename).put(Body=body)

    print(f'Report generated for month {month} for {count} active members across {len(invasions["Items"])} invasions')

    mesg = f'- Invasions: {len(invasions["Items"])}\n'
    mesg += f'- Active Members (1 or more invasions): {count}\n'
    mesg += f'- Participation (sum of members across invasions): {participation}'
    return True, mesg


def report_month(month: int, year: int) -> str:
    print(f'report_month: {month} {year}')

    when = f'{year}' + '{0:02d}'.format(month)
    success, mesg = generate_month_report(when)
    print(f'generate_month_report returned {success} {mesg}')

    if success:
        filename = f'month/{when}.csv'
        print(f'Generating presigned URL for {filename}')
        try:
            presigned = s3.generate_presigned_url('get_object', Params={'Bucket': bucket_name, 'Key': filename}, ExpiresIn=3600)
            mesg = f'# {when} Monthly Stats\n{mesg}\n- Download the report (for 1 hour) from **[here]({presigned})**'
        except ClientError as e:
            print(e)
            mesg = f'Error generating presigned URL for {filename}: {e}'

    return mesg


def report_invasion(invasion:str) -> str:
    print(f'report_invasion: {invasion}')

    response = table.query(KeyConditionExpression=Key('invasion').eq(f'#ladder#{invasion}'))            

    if not response.get('Items', None):
        print(f'No ladder found for {invasion}')
        return f'Invasion {invasion} not found'

    members = 0
    pos = 1
    for row in response["Items"]:
        print(row)
        if row["member"]:
            members += 1
        if int(row["id"]) != pos:
            print(f'Missing row {pos}, next row found was {row["id"]}')
            return f'Missing row {pos}, next row found was {row["id"]}. Have all screenshots been uploaded?'
        else:
            pos += 1

    mesg = f'# Invasion {invasion}\nFound {members} members from {pos} participants.'
    print(f'Found {members} members from {pos} participants.')

    body = "Rank,Name,Score,Kills,Assists,Deaths,Heals,Damage,Member\n"
    for row in response["Items"]:
        body += '{id},{name},{score},{kills},{assists},{deaths},{heals},{damage},{member}\n'.format_map(row)
    
    filename = f'reports/{invasion}/{invasion}.csv'
    print(f'Writing invasion report to {bucket_name}/{filename}')
    s3_resource.Object(bucket_name, filename).put(Body=body)

    presigned = s3.generate_presigned_url('get_object', Params={'Bucket': bucket_name, 'Key': filename}, ExpiresIn=3600)

    mesg += f'\Invasion stats can be downloaded (for 1 hour) from **[here]({presigned})**'
    return mesg


def report_member(player:str, month:int, year:int) -> str:
    print(f'report_member: {player} {month} {year}')

    date = f'{year}' + '{0:02d}'.format(month)
    response = table.get_item(Key={'invasion': f'#month#{date}', 'id': player})
    mesg = f'No data found for player {player} in month {date}'

    if 'Item' in response:
        item = response['Item']
        mesg = f'# Player {player} stats for {month}\n'
        mesg += 'Invasions: {invasions}\n'.format_map(item)
        mesg += 'Sum / Max / Average\n'
        mesg += '- Score: {sum_score} / {max_score} / {avg_score}\n'.format_map(item)
        mesg += '- Kills: {sum_kills} / {max_kills} / {avg_kills}\n'.format_map(item)
        mesg += '- Assists: {sum_assists} / {max_assists} / {avg_assists}\n'.format_map(item)
        mesg += '- Deaths: {sum_deaths} / {max_deaths} / {avg_deaths}\n'.format_map(item)
        mesg += '- Heals: {sum_heals} / {max_heals} / {avg_heals}\n'.format_map(item)
        mesg += '- Damage: {sum_damage} / {max_damage} / {avg_damage}\n'.format_map(item)
        
    return mesg
