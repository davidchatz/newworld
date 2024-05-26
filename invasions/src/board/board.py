import boto3
from botocore.exceptions import ClientError
from boto3.dynamodb.conditions import Key, Attr
import os
import urllib
from datetime import datetime

textract = boto3.client('textract')
dynamodb = boto3.resource('dynamodb')
table_name = os.environ['TABLE_NAME']
table = dynamodb.Table(table_name)

# define function that takes s3 bucket and key and calls textract to import table
def import_table(bucket, key):
    # call textract
    response = textract.detect_document_text(
        Document={'S3Object': {'Bucket': bucket, 'Name': key}}
    )
    # print(response)
    return response


def reduce_list(table: dict) -> list:
    print(f'reduce_list')
    response = []

    for block in table['Blocks']:
        if block['BlockType'] != 'PAGE':
            text = block['Text']

            if not (text.isnumeric() or text == ':' or text.startswith('GROUP')):
                response.append(text)

    return response


def member_match(candidates: list):
    print(f'member_match')

    matched = []
    unmatched = []

    sorted_candidates = sorted(set(candidates))

    for c in sorted_candidates:
        # Try to an exact match first
        member = table.get_item(Key={'invasion': '#member', 'id': c})
        if 'Item' in member:
            matched.append(c)
        else:
            #Try for a partial match and assume it matches based on prefix
            member = table.query(KeyConditionExpression=Key('invasion').eq('#member') & Key('id').begins_with(c),
                                ProjectionExpression='id')      
            if member['Count'] == 1:
                matched.append(member['Items'][0]['id'])
            else:
                unmatched.append(c)

    sorted_matched = sorted(set(matched))

    print(f'matched ({len(sorted_matched)}): {sorted_matched}')
    print(f'unmatched ({len(unmatched)}): {unmatched}')

    return sorted_matched, unmatched


def insert_db(matched: list, invasion:str):
    print(f'insert_db for {len(matched)} matched members for invasion {invasion}')

    rec = []
    
    rank = 1
    for m in matched:
        rec.append({
            'invasion': f'#ladder#{invasion}',
            'id': '{0:02d}'.format(rank),
            'name': m,
            'score': 0,
            'kills': 0,
            'deaths': 0,
            'assists': 0,
            'heals': 0,
            'damage': 0,
            'member': True,
            'ladder': False             
        })
        rank += 1

    try:
        # Add ladder results from scan
        with table.batch_writer() as batch:
            for r in rec:
                print(r)
                batch.put_item(Item=r)

    except ClientError as err:
        print(err.response['Error']['Message'])
        raise


# define lambda handler that gets S3 bucket and key from event and calls import_table
def lambda_handler(event, context):
    # get bucket and key from event
    bucket = event['Records'][0]['s3']['bucket']['name']
    # key = event['Records'][0]['s3']['object']['key']
    key = urllib.parse.unquote_plus(event['Records'][0]['s3']['object']['key'])
    folders = key.split('/')

    if len(folders) != 3:
        print(f'Skipping {key} as it is not in the correct format, expecting boards/(invasion)/(filename).')
        raise Exception(f'Skipping {key} as it is not in the correct format')
    if folders[0] != 'boards':
        print(f'Skipping {key} as it is not in the correct format, expecting boards/(invasion)/(filename).')
        raise Exception(f'Skipping {key} as it is not in the correct format')

    invasion = folders[1]
    print(f'{bucket}/{key} (invasion: {invasion})')

    # Scan image for any text
    response = import_table(bucket, key)

    # Remove words which are unlikely to be names
    candidates = reduce_list(response)
    print(f'candidates ({len(candidates)}): {candidates}')

    # Match to members
    matched, unmatched = member_match(candidates)

    # Generate records
    records = insert_db(matched, invasion)

    return f"Board import not yet implemented for invasion {invasion}"
