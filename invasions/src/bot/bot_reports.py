import json
import boto3
from botocore.exceptions import ClientError
from boto3.dynamodb.conditions import Key, Attr
import os
from decimal import Decimal, getcontext
from datetime import datetime

 
# get bucket name of environment
s3 = boto3.client('s3')
s3_resource = boto3.resource('s3')
bucket_name = os.environ.get('BUCKET_NAME')

# create client to DynamoDB service
dynamodb = boto3.resource('dynamodb')
table_name = os.environ['TABLE_NAME']
table = dynamodb.Table(table_name)

# precision to use for Decimals
prec = Decimal("1.0")


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
        report.append({'invasion': f'#month#{month}', 'id': member['id'], 'invasions': Decimal(0),
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
                    found = True
                    break

            if not found:
                print(f'Player {row["name"]} not found in member list, skipping')

    # compute averages
    for r in report:
        if r["invasions"] > 0:
            r["avg_score"] = (r["sum_score"] / r["invasions"]).quantize(prec)
            #r["avg_score"] = r["avg_score"].quantize(prec)
            r["avg_kills"] = (r["sum_kills"] / r["invasions"]).quantize(prec)
            #r["avg_kills"] = r["avg_kills"].quantize(prec)
            r["avg_assists"] = (r["sum_assists"] / r["invasions"]).quantize(prec)
            #r["avg_assists"] = r["avg_assists"].quantize(prec)
            r["avg_deaths"] = (r["sum_deaths"] / r["invasions"]).quantize(prec)
            #r["avg_deaths"] = r["avg_deaths"].quantize(prec)
            r["avg_heals"] = (r["sum_heals"] / r["invasions"]).quantize(prec)
            #r["avg_heals"] = r["avg_heals"].quantize(prec)
            r["avg_damage"] = (r["sum_damage"] / r["invasions"]).quantize(prec)
            #r["avg_damage"] = r["avg_damage"].quantize(prec)
            r["avg_rank"] /= r["invasions"]
            r["avg_rank"] = r["avg_rank"].quantize(prec)

    print(f'computed report: {report}')

    body = 'month,name,invasions,sum_score,sum_kills,sum_assists,sum_deaths,sum_heals,sum_damage,avg_score,avg_kills,avg_assists,avg_deaths,avg_heals,avg_damage,avg_ranks,max_score,max_kills,max_assists,max_deaths,max_heals,max_damage,max_rank\n'

    with table.batch_writer() as batch:
        count = 0
        for r in report:
            if r["invasions"] > 0:
                count += 1
                batch.put_item(Item=r)
                body += f'{month},{r["id"]},{r["invasions"]},{r["sum_score"]},{r["sum_kills"]},{r["sum_assists"]},{r["sum_deaths"]},{r["sum_heals"]},{r["sum_damage"]},{r["avg_score"]},{r["avg_kills"]},{r["avg_assists"]},{r["avg_deaths"]},{r["avg_heals"]},{r["avg_damage"]},{r["avg_rank"]},{r["max_score"]},{r["max_kills"]},{r["max_assists"]},{r["max_deaths"]},{r["max_heals"]},{r["max_damage"]},{r["max_rank"]}\n'

    filename = f'month/{month}.csv'
    print(f'Writing ladder to {bucket_name}/{filename}')
    s3_resource.Object(bucket_name, filename).put(Body=body)

    print(f'Report generated for month {month} for {count} active members across {len(invasions["Items"])} invasions')
    return True, f'Report generated for {count} active members across {len(invasions["Items"])} invasions'


def report_month(options:list) -> str:
    print(f'report_month: {options}')

    now = datetime.now()
    month = now.month
    year = now.year

    for o in options:
        if o["name"] == "month":
            month = o["value"]
        elif o["name"] == "year":
            year = o["value"]

    when = f'{year}' + '{0:02d}'.format(month)
    success, mesg = generate_month_report(when)
    print(f'generate_month_report returned {success} {mesg}')

    if success:
        filename = f'month/{when}.csv'
        print(f'Generating presigned URL for {filename}')
        try:
            presigned = s3.generate_presigned_url('get_object', Params={'Bucket': bucket_name, 'Key': filename}, ExpiresIn=3600)
            mesg = f'# {when} monthly stats\n{mesg}\nDownload the report (for 1 hour) from **[here]({presigned})**'
        except ClientError as e:
            print(e)
            mesg = f'Error generating presigned URL for {filename}: {e}'

    return mesg


def report_invasion(options:list) -> str:
    print(f'report_invasion: {options}')

    invasion = None
    for o in options:
        if o["name"] == "invasion":
            invasion = o["value"]

    if not invasion:
        return 'Missing invasion from request'

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
    
    filename = f'{invasion}/{invasion}.csv'
    print(f'Writing ladder to {bucket_name}/{filename}')
    s3_resource.Object(bucket_name, filename).put(Body=body)

    presigned = s3.generate_presigned_url('get_object', Params={'Bucket': bucket_name, 'Key': filename}, ExpiresIn=3600)

    mesg += f'\nLadder can be downloaded (for 1 hour) from **[here]({presigned})**'
    return mesg


def report_member(options:list) -> str:
    print(f'report_member: {options}')

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

    month = f'{year}' + '{0:02d}'.format(month)
    response = table.get_item(Key={'invasion': f'#month#{month}', 'id': player})
    mesg = f'No data found for player {player} in month {month}'

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


def report_cmd(options:dict, resolved: dict):
    print(f'report_cmd: {options}')

    name = options['name']
    if name == 'month':
        mesg = report_month(options['options'])
    elif name == 'invasion':
        mesg = report_invasion(options['options'])
    elif name == 'member':
        mesg = report_member(options['options'])
    else:
        print(f'Invalid command {name}')
        mesg = f'Invalid command {name}'

    return mesg
