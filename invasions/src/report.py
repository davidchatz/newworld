import json
import boto3
from botocore.exceptions import ClientError
from boto3.dynamodb.conditions import Key, Attr
import os

# create client to DynamoDB service
dynamodb = boto3.resource('dynamodb')
table_name = os.environ['TABLE_NAME']

def lambda_handler(event, context):
    # Log the event argument for debugging and for use in local development.
    print(json.dumps(event))

    # initialise body, statusCode and headers for response
    body = ""
    statusCode = 200
    headers = {
        "Content-Type": "application/json"
    }

    # in a try block route on the event routeKey
    try:
        table = dynamodb.Table(table_name)

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

        # else if routeKey is GET /ladder/{invasion}, set body to ladder items
        elif event['httpMethod'] == 'GET' and event['resource'] == '/ladder/{invasion}':
            # get item from DynamoDB table_name with id from pathParameters
            invasion = event['pathParameters']['invasion']
            response = table.query(KeyConditionExpression=Key('invasion').eq(f'#ladder#{invasion}'))
            # set body to id and labels
            print(response)
        
            if not response.get('Items', None):
                statusCode = 404
                body = f'Item {invasion} not found'
            else:
                body = str(response["Items"])

        # else if routeKey is GET /csv/{invasion}, return ladder items as comma separated values
        elif event['httpMethod'] == 'GET' and event['resource'] == '/csv/{invasion}':
            # get item from DynamoDB table_name with id from pathParameters
            invasion = event['pathParameters']['invasion']
            response = table.query(KeyConditionExpression=Key('invasion').eq(f'#ladder#{invasion}'))            

            if not response.get('Items', None):
                statusCode = 404
                body = f'Item {invasion} not found'
            else:
                headers = {
                    "Content-Type": "text/csv"
                }
                body = "Rank,Name,Score,Kills,Assists,Deaths,Heals,Damage\n"
                for row in response["Items"]:
                    body += '{id},{name},{score},{assists},{deaths},{heals},{damage}\n'.format_map(row)

        # else raise exception for unexpected route
        else:
             raise Exception(f"Unsupported route: {event['httpMethod']} {event['resource']}") 
            
    # catch KeyError for no route specified
    except KeyError as e:
        statusCode = 400
        body = { 'error': f'No route specified: {e}' }

    # catch generic ClientError and return message
    except ClientError as e:
        statusCode = 400
        body = { 'error': e.response['Error']['Message'] }

    # catch anything as
    except Exception as e:
        statusCode = 400
        body = { 'error': f"Other exception: {e}" }
        
    finally:

        # return body, statusCode and headers
        return {
            'statusCode': statusCode,
            'headers': headers,
            'body': json.dumps(body)
        }