import os
import boto3
import boto3.session
import pytest
import json
from aws_lambda_powertools import Logger
from .lambdaclient import LambdaClient
from irus import IrusInvasion


client = LambdaClient(local=True)

logger = Logger(service="test_download", level="INFO", correlation_id=True)
dynamodb = client.session.resource('dynamodb')
table_name = os.environ['TABLE_NAME']
table = dynamodb.Table(table_name)

s3 = client.session.resource('s3')
test_bucket_name = os.environ['TEST_BUCKET_NAME']
test_bucket = s3.Bucket(test_bucket_name)
bucket_name = os.environ['BUCKET_NAME']
bucket = s3.Bucket(bucket_name)

@pytest.fixture
def download_sample_ladder_file():
    invasion = IrusInvasion.from_user(day=23, month=5, year=2024, settlement='wf', win=True)
    logger.debug(f'Invasion {invasion}')

    url = test_bucket.meta.client.generate_presigned_url(
        'get_object',
        Params={
            'Bucket': test_bucket_name,
            'Key': '20240523-wf/Screenshot_2024-05-23_222523.png'
        })
    logger.debug(f'URL: {url}')

    event = {
        'invasion': invasion.name,
        'filename': 'Screenshot_2024-05-23_222523.png',
        'url': url,
        'folder': f'ladders/{invasion.name}/'
    }
    logger.debug(f'Event: {event}')

    result = client.lambda_client.invoke(FunctionName='Download',
                                         InvocationType='RequestResponse',
                                         Payload=json.dumps(event))
    logger.debug(f'Result: {result}')

    response = json.loads(result['Payload'].read())
    logger.info(f'Result payload: {response}')
    yield response
    invasion.delete_from_table()

def test_download_sample_ladder_file(download_sample_ladder_file):
    assert download_sample_ladder_file['statusCode'] == 200
    assert download_sample_ladder_file['body'] == '"Downloaded Screenshot_2024-05-23_222523.png to ladders/20240523-wf/"'

