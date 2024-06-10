import os
import boto3
from aws_lambda_powertools import Logger

# setup logging
logger = Logger()

# get bucket name of environment
s3 = boto3.client('s3')
s3_resource = boto3.resource('s3')
bucket_name = os.environ.get('BUCKET_NAME')
logger.debug(f'bucket name: {bucket_name}')

# table details
dynamodb = boto3.resource('dynamodb')
table_name = os.environ['TABLE_NAME']
table = dynamodb.Table(table_name)
logger.debug(f'table name: {table_name}')

# downloader step function
state_machine = boto3.client('stepfunctions')
step_function_arn = os.environ.get('PROCESS_STEP_FUNC')
logger.debug(f'step function arn: {step_function_arn}')

webhook_url = os.environ.get('WEBHOOK_URL')
logger.debug(f'webhook url: {webhook_url}')


class Secrets:

    public_key : str = None
    public_key_bytes : bytes = None
    app_id : str = None

    def __init__(self):
        ssm = boto3.client('ssm')
        self.public_key_path = os.environ['PUBLIC_KEY_PATH']
        self.public_key = ssm.get_parameter(Name=self.public_key_path, WithDecryption=True)['Parameter']['Value']
        self.public_key_bytes = bytes.fromhex(self.public_key)
        app_id_path = os.environ['APP_ID_PATH']
        self.app_id = ssm.get_parameter(Name=app_id_path, WithDecryption=True)['Parameter']['Value']

