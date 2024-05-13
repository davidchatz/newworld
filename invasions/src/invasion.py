import boto3
from botocore.exceptions import ClientError
from boto3.dynamodb.conditions import Key, Attr
import os
import json

# get bucket name of environment
bucket_name = os.environ.get('BUCKET_NAME')

# table details
dynamodb = boto3.resource('dynamodb')
table_name = os.environ['TABLE_NAME']
table = dynamodb.Table(table_name)


# define function that takes an invasion name and creates a folder in bucket
def create_folder(invasion_name):
    s3 = boto3.client('s3')
    s3.put_object(Bucket=bucket_name, Key=(invasion_name + '/'))
    s3.put_object(Bucket=bucket_name, Key=(invasion_name + '/ladder/'))
    s3.put_object(Bucket=bucket_name, Key=(invasion_name + '/discord/'))
    print('Created folder for ' + invasion_name)

# define lambda handler that takes an invasion name and calls create_folder
def lambda_handler(event, context):

    body = ""
    statusCode = 200
    headers = {
        "Content-Type": "application/json"
    }

    print(event)

    try:
        # if routeKey is GET /, set body to a list of all invasions from table
        if event['httpMethod'] == 'GET' and event['resource'] == '/invasions':
            # get all invasions
            response = table.query(KeyConditionExpression=Key('invasion').eq('#invasion'),
                                   ProjectionExpression='id')
            # set body to id and labels
            print(response)
        
            if not response.get('Items', None):
                statusCode = 404
                body = f'No invasions found'
            else:
                body = str(response["Items"])

        elif event['httpMethod'] == 'POST' and event['resource'] == '/invasions/add':
            # register a new invasion
            request = json.loads(event['body'])
            year = request['year']
            month = '{0:02d}'.format(int(request['month']))
            day = '{0:02d}'.format(int(request['day']))
            date = f'{year}{month}{day}'
            settlement = request['settlement']
            win = request['win']
            notes = request['notes'] if 'notes' in event else None

            folder = date + '-' + settlement

            create_folder(folder)
            body = f'Created folders for {folder}'

            item = {
                'invasion': f'#invasion',
                'id': folder,
                'settlememt': settlement,
                'win': win,
                'date': int(date),
                'year': int(year),
                'month': int(month),
                'day': int(day)
            }

            if notes:
                item['notes'] = notes

            # Add row to identify this invasion
            table.put_item(Item=item)

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


