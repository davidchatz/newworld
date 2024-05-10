import boto3
import os
import json

# get bucket name of environment
bucket_name = os.environ.get('BUCKET_NAME')

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

    create_folder(event['invasion'])
    body = "Created folders for " + event['invasion']

    return {
        'statusCode': statusCode,
        'headers': headers,
        'body': json.dumps(body)
    }


