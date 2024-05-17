import json
import boto3
from botocore.exceptions import ClientError
from boto3.dynamodb.conditions import Key, Attr
import os
from decimal import Decimal, getcontext
from bot_result import Result

# create client to DynamoDB service
dynamodb = boto3.resource('dynamodb')
table_name = os.environ['TABLE_NAME']
table = dynamodb.Table(table_name)

# precision to use for Decimals
prec = Decimal("1.0")

# def invasions() -> Result:
#     query = table.query(KeyConditionExpression=Key('invasion').eq('#invasion'),
#                             ProjectionExpression='id')
#     # set body to id and labels
#     print(query)

#     response = Result()

#     if not query.get('Items', None):
#         response.content(f'No invasions found')
#     else:
#         response.content(query["Items"])

#     print(f'invasions response: {response}')
#     return response

def invasions() -> str:
    query = table.query(KeyConditionExpression=Key('invasion').eq('#invasion'),
                            ProjectionExpression='id')
    # set body to id and labels
    print(query)

    if not query.get('Items', None):
        return 'No invasions found'
    else:
        res = query["Items"][0]["id"]
        for i in query["Items"][1:]:
            res += ", " + i["id"]
        print(f'str: {res}')
        return res


def ladder_invasion(invasion: str) -> Result:
    query = table.query(KeyConditionExpression=Key('invasion').eq(f'#ladder#{invasion}'))
    # set body to id and labels
    print(query)

    response = Result()
    
    if not query.get('Items', None):
        response.status(404)
        response.body(f'Item {invasion} not found')
    else:
        response.body(query["Items"])

    return response

def foo(event, context):
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

        # if routeKey is GET /ladder/{invasion}, set body to ladder items
        if event['httpMethod'] == 'GET' and event['resource'] == '/ladder/{invasion}':
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
                body = "Rank,Name,Score,Kills,Assists,Deaths,Heals,Damage,Member\n"
                for row in response["Items"]:
                    body += '{id},{name},{score},{assists},{deaths},{heals},{damage},{member}\n'.format_map(row)

        # else if routeKey is GET /summary/{invasion}, return ladder items as comma separated values
        elif event['httpMethod'] == 'GET' and event['resource'] == '/summary/{invasion}':
            # get item from DynamoDB table_name with id from pathParameters
            invasion = event['pathParameters']['invasion']
            response = table.query(KeyConditionExpression=Key('invasion').eq(f'#ladder#{invasion}'))            

            if not response.get('Items', None):
                statusCode = 404
                body = f'Item {invasion} not found'
            else:
                members = 0
                pos = 1
                consecutive = True
                for row in response["Items"]:
                    print(row)
                    if row["member"]:
                        members += 1
                    if int(row["id"]) != pos:
                        consecutive = False
                        print(f'Missing row {pos}, found {row["id"]}')
                        pos = int(row["id"])
                    else:
                        pos += 1

                if not consecutive:
                    statusCode = 400
                    body = f'Missing rows in ladder'
                else:
                    body = f'For {invasion} found {members} members from {pos} participants'

        elif event['httpMethod'] == 'GET' and event['resource'] == '/month/{month}':
            # get item from DynamoDB table_name with id from pathParameters
            month = event['pathParameters']['month']

            invasions = table.query(KeyConditionExpression=Key('invasion').eq(f'#invasion') & Key('id').begins_with(month),
                                    ProjectionExpression='id')            

            members = table.query(KeyConditionExpression=Key('invasion').eq(f'#member'),
                                    ProjectionExpression='id')
            
            if not invasions.get('Items', None):
                statusCode = 404
                body = f'No invasions found for {month}'

            elif not members.get('Items', None):
                statusCode = 404
                body = f'No members found'

            else:
                report = []
                for member in members['Items']:
                    report.append({'invasion': f'#month#{month}', 'id': member['id'], 'invasions': Decimal(0), 'score': 0, 'kills': 0, 'assists': 0, 'deaths': 0, 'heals': 0, 'damage': 0,
                                   'avg_score': Decimal(0.0), 'avg_kills': Decimal(0.0), 'avg_assists': Decimal(0.0), 'avg_deaths': Decimal(0.0), 'avg_heals': Decimal(0.0), 'avg_damage': Decimal(0.0), 'avg_rank': Decimal(0.0)})
                #print(f' init report: {report}')

                for invasion in invasions["Items"]:
                    ladder = table.query(KeyConditionExpression=Key('invasion').eq(f'#ladder#{invasion["id"]}'),
                                           FilterExpression=Attr('member').eq(True))
                    
                    if not ladder.get('Items', None):
                        print(f'No members found in ladder for {invasion["id"]}')
                        continue

                    for row in ladder["Items"]:
                        #print(f'row: {row}')
                        found = False
                        for r in report:
                            if r["id"] == row["name"]:
                                #print(f'Updating {r}')
                                r["invasions"] += 1
                                r["score"] += row["score"]
                                r["kills"] += row["kills"]
                                r["assists"] += row["assists"]
                                r["deaths"] += row["deaths"]
                                r["heals"] += row["heals"]
                                r["damage"] += row["damage"]
                                r["avg_rank"] += Decimal(row["id"])
                                found = True
                                break

                        if not found:
                            print(f'Player {row["name"]} not found in member list, skipping')

                # compute averages
                for r in report:
                    if r["invasions"] > 0:
                        r["avg_score"] = r["score"] / r["invasions"]
                        r["avg_score"] = r["avg_score"].quantize(prec)
                        r["avg_kills"] = r["kills"] / r["invasions"]
                        r["avg_kills"] = r["avg_kills"].quantize(prec)
                        r["avg_assists"] = r["assists"] / r["invasions"]
                        r["avg_assists"] = r["avg_assists"].quantize(prec)
                        r["avg_deaths"] = r["deaths"] / r["invasions"]
                        r["avg_deaths"] = r["avg_deaths"].quantize(prec)
                        r["avg_heals"] = r["heals"] / r["invasions"]
                        r["avg_heals"] = r["avg_heals"].quantize(prec)
                        r["avg_damage"] = r["damage"] / r["invasions"]
                        r["avg_damage"] = r["avg_damage"].quantize(prec)
                        r["avg_rank"] /= r["invasions"]
                        r["avg_rank"] = r["avg_rank"].quantize(prec)

                print(f'computed report: {report}')

                with table.batch_writer() as batch:
                    count = 0
                    for r in report:
                        if r["invasions"] > 0:
                            count += 1
                            batch.put_item(Item=r)

                body = f'Report generated for month {month} for {count} active members across {len(invasions["Items"])}'

        # else raise exception for unexpected route
        else:
             raise Exception(f"Unsupported route: {event['httpMethod']} {event['resource']}") 
            
    # catch KeyError for no route specified
    except KeyError as e:
        statusCode = 400
        body = { 'error': f'Missing value: {e}' }

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