import boto3
from botocore.exceptions import ClientError
import os
import urllib
import invasion


dynamodb = boto3.resource('dynamodb')
table_name = os.environ['TABLE_NAME']
table = dynamodb.Table(table_name)



# define lambda handler that gets S3 bucket and key from event and calls import_table
def lambda_handler(event, context):
    # get bucket and key from event
    bucket = event['Records'][0]['s3']['bucket']['name']
    # key = event['Records'][0]['s3']['object']['key']
    key = urllib.parse.unquote_plus(event['Records'][0]['s3']['object']['key'])
    folders = key.split('/')

    if len(folders) != 3:
        print(f'Skipping {key} as it is not in the correct format, expecting ladders/(invasion)/(filename).')
        raise Exception(f'Skipping {key} as it is not in the correct format')
    if folders[0] != 'ladders':
        print(f'Skipping {key} as it is not in the correct format, expecting ladders/(invasion)/(filename).')
        raise Exception(f'Skipping {key} as it is not in the correct format')

    invasion = folders[1]
    print(f'{bucket}/{key} (invasion: {invasion})')

    table = dynamodb.Table(table_name)

    # call import_table
    response = tablescan.import_table(bucket, key)
    table_blocks, blocks_map = tablescan.extract_blocks(response)

    if len(table_blocks) == 0:
        print(f'No table found in {bucket}/{key}')
        raise Exception(f'No table found in {bucket}/{key}')
    elif len(table_blocks) > 1:
        print(f'No table found in {bucket}/{key}')
        raise Exception(f'No table found in {bucket}/{key}')

    result = generate_table(table_blocks[0], blocks_map)
    insert_db(table, invasion, result, key)

    return f"Updates applied for invasion {invasion}"
