import boto3
from botocore.exceptions import ClientError
from boto3.dynamodb.conditions import Key, Attr
import os
import json
from datetime import datetime

# table details
dynamodb = boto3.resource('dynamodb')
table_name = os.environ['TABLE_NAME']
table = dynamodb.Table(table_name)


# define lambda handler that takes an invasion name and calls create_folder
def lambda_handler(event, context):

    body = ""
    statusCode = 200
    headers = {
        "Content-Type": "application/json"
    }

    print(event)

    try:
        # get current member list
        if event['httpMethod'] == 'GET' and event['resource'] == '/members':

            response = table.query(KeyConditionExpression=Key('invasion').eq('#member'),
                                   ProjectionExpression='id')
            # set body to id and labels
            print(response)
        
            if not response.get('Items', None):
                statusCode = 404
                body = f'No members found'
            else:
                items = response["Items"]
                body = f"Members {len(items)}: "
                if len(items) > 0:
                    body += items.pop(0)["id"]
                    for player in items:
                        body += ", " + player["id"]

        # if routeKey is GET /, set body to a list of all invasions from table
        elif event['httpMethod'] == 'GET' and event['resource'] == '/members/{player}':

            player = event['pathParameters']['player']
            response = table.get_item(Key={"invasion": "#member", "id": player})
            print(response)
        
            if not 'Item' in response:
                statusCode = 404
                body = f'Member {player} not found'
            else:
                body = str(response["Item"])

        elif event['httpMethod'] == 'POST' and event['resource'] == '/members/add':
            # add or update a member
            request = json.loads(event['body'])
            timestamp = datetime.today().strftime('%Y%m%d%H%M%S')

            player = request['player']
            faction = request['faction']
            discord = request['discord'] if 'discord' in request else None
            start = request['start'] if 'start' in request else datetime.today().strftime('%Y%m%d')
            notes = request['notes'] if 'notes' in event else None
            admin = request['admin'] == True if 'admin' in request else False

            additem = {
                'invasion': '#memberevent',
                'id': timestamp,
                'event': "add",
                'player': player,
                'faction': faction,
                'admin': admin
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
            body = f'Added member {player} faction {faction} starting {start} admin {admin}'

        elif event['httpMethod'] == 'DELETE' and event['resource'] == '/members/{player}':
            # add or update a member
            player = event['pathParameters']['player']
            timestamp = datetime.today().strftime('%Y%m%d%H%M%S')

            item = {
                'invasion': f'#memberevent',
                'id': timestamp,
                'event': "delete",
                'player': player
            }

            response = table.delete_item(Key={'invasion': f'#member', 'id': player}, ReturnValues='ALL_OLD')
            if 'Attributes' in response:
                body = f'Deleted member {player}: {response["Attributes"]}'
                table.put_item(Item=item)
            else:
                body = f'Member {player} not found, nothing to delete'

        else:
            print(f"Unsupported route: {event['httpMethod']} {event['resource']}")
            statusCode = 400
            body = f"Unsupported route: {event['httpMethod']} {event['resource']}"

    except Exception as e:
        print(e)
        raise

    return {
        'statusCode': statusCode,
        'headers': headers,
        'body': json.dumps(body)
    }


