import os
import boto3
from aws_lambda_powertools import Logger

class IrusResources:

    logger = None
    session = None
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
    done = False

    def __init__(self, profile:str = None):

        if self.done == False:
            self.logger = Logger()

            if profile:
                self.session = boto3.session.Session(profile_name=profile)
            else:
                self.session = boto3.session.Session()

            # get bucket name of environment
            self.bucket_name = os.environ.get('BUCKET_NAME')
            if self.bucket_name:
                self.s3 = self.session.client('s3')
                self.s3_resource = self.session.resource('s3')

            self.logger.debug(f'bucket name: {self.bucket_name}')

            # table details
            self.table_name = os.environ.get('TABLE_NAME')
            if self.table_name:
                self.dynamodb = self.session.resource('dynamodb')
                self.table = self.dynamodb.Table(self.table_name)

            self.logger.debug(f'table name: {self.table_name}')

            # downloader step function
            self.step_function_arn = os.environ.get('PROCESS_STEP_FUNC')
            if self.step_function_arn:
                self.state_machine = self.session.client('stepfunctions')
            
            self.logger.debug(f'step function arn: {self.step_function_arn}')

            # textract to scan images
            self.textract = self.session.client('textract')

            self.webhook_url = os.environ.get('WEBHOOK_URL')
            self.logger.debug(f'webhook url: {self.webhook_url}')

            self.done = True


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

