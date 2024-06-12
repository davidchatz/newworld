import os
import boto3
from aws_lambda_powertools import Logger

class IrusResources:

    logger = None
    s3 = None
    s3_resource = None
    bucket_name = None
    dynamodb = None
    table_name = None
    table = None
    state_machine = None
    step_function_arn = None
    textract = None
    webhook_url = None

    def __init__(self):

        if not self.webhook_url:
            self.logger = Logger()

            # get bucket name of environment
            self.s3 = boto3.client('s3')
            self.s3_resource = boto3.resource('s3')
            self.bucket_name = os.environ.get('BUCKET_NAME')
            self.logger.debug(f'bucket name: {self.bucket_name}')

            # table details
            self.dynamodb = boto3.resource('dynamodb')
            self.table_name = os.environ['TABLE_NAME']
            self.table = self.dynamodb.Table(self.table_name)
            self.logger.debug(f'table name: {self.table_name}')

            # downloader step function
            self.state_machine = boto3.client('stepfunctions')
            self.step_function_arn = os.environ.get('PROCESS_STEP_FUNC')
            self.logger.debug(f'step function arn: {self.step_function_arn}')

            # textract to scan images
            self.textract = boto3.client('textract')

            self.webhook_url = os.environ.get('WEBHOOK_URL')
            self.logger.debug(f'webhook url: {self.webhook_url}')


class IrusSecrets:

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

