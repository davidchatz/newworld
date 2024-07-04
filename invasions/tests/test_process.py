import os
import boto3
import boto3.session
import pytest
import json
from aws_lambda_powertools import Logger
from .lambdaclient import LambdaClient
from irus import IrusInvasion, IrusMember, IrusLadder


client = LambdaClient(local=True)

logger = Logger(service="test_process", level="INFO", correlation_id=True)
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

    Chatz01 = IrusMember.from_user(player = "Chatz01", day=1, month=5, year=2024, faction= "purple", admin=False, salary=True)
    Stuggy = IrusMember.from_user(player = "Stuggy", day=1, month=5, year=2024, faction= "green", admin=True, salary=True)

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
        'folder': invasion.path_ladders(),
        'process': 'Ladder'
    }
    logger.debug(f'Event: {event}')

    result = client.lambda_client.invoke(FunctionName='Process',
                                         InvocationType='RequestResponse',
                                         Payload=json.dumps(event))
    logger.debug(f'Result: {result}')

    response = json.loads(result['Payload'].read())
    logger.info(f'Result payload: {response}')
    yield response
    invasion.delete_from_table()
    Chatz01.remove()
    Stuggy.remove()
    test_bucket.delete_objects(Delete={
        'Objects': [
            {
                'Key': f'{invasion.path_ladders()}/Screenshot_2024-05-23_222523.png'
            }
        ],
        'Quiet': True
    })


@pytest.fixture
def download_missing_file():
    invasion = IrusInvasion.from_user(day=23, month=5, year=2024, settlement='wf', win=True)
    logger.debug(f'Invasion {invasion}')

    event = {
        'invasion': invasion.name,
        'filename': 'missing.png',
        'url': 'https://bogus.example.com',
        'folder': invasion.path_ladders(),
        'process': 'Ladder'
    }
    logger.debug(f'Event: {event}')

    result = client.lambda_client.invoke(FunctionName='Process',
                                         InvocationType='RequestResponse',
                                         Payload=json.dumps(event))
    logger.debug(f'Result: {result}')

    response = json.loads(result['Payload'].read())
    logger.info(f'Result payload: {response}')
    yield response
    invasion.delete_from_table()


@pytest.fixture
def download_sample_jpg_file():
    invasion = IrusInvasion.from_user(day=23, month=5, year=2024, settlement='wf', win=True)
    logger.debug(f'Invasion {invasion}')

    url = test_bucket.meta.client.generate_presigned_url(
        'get_object',
        Params={
            'Bucket': test_bucket_name,
            'Key': 'bad/Screenshot_2024-05-23_222523_bad.jpg'
        })
    logger.debug(f'URL: {url}')

    event = {
        'invasion': invasion.name,
        'filename': 'Screenshot_2024-05-23_222523_bad.jpg',
        'url': url,
        'folder': invasion.path_ladders(),
        'process': 'Ladder'
    }
    logger.debug(f'Event: {event}')

    result = client.lambda_client.invoke(FunctionName='Process',
                                         InvocationType='RequestResponse',
                                         Payload=json.dumps(event))
    logger.debug(f'Result: {result}')

    response = json.loads(result['Payload'].read())
    logger.info(f'Result payload: {response}')
    yield response
    invasion.delete_from_table()
    test_bucket.delete_objects(Delete={
        'Objects': [
            {
                'Key': f'{invasion.path_ladders()}/Screenshot_2024-05-23_222523_bad.jpg'
            }
        ],
        'Quiet': True
    })

@pytest.fixture
def generate_invasion_ladders():
    invasion = IrusInvasion.from_user(day=11, month=6, year=2024, settlement='rw', win=True)
    logger.debug(f'Invasion {invasion}')

    Chatz01 = IrusMember.from_user(player = "Chatz01", day=1, month=5, year=2024, faction= "purple", admin=False, salary=True)
    Stuggy = IrusMember.from_user(player = "Stuggy", day=1, month=5, year=2024, faction= "green", admin=True, salary=True)
    TaliMonk = IrusMember.from_user(player = "TaliMonk", day=1, month=5, year=2024, faction= "yellow", admin=False, salary=True)
    kbaz = IrusMember.from_user(player = "kbaz", day=1, month=5, year=2024, faction= "purple", admin=False, salary=False)
    Merkavar = IrusMember.from_user(player = "Merkavar", day=1, month=5, year=2024, faction= "yellow", admin=False, salary=True)
    Fred = IrusMember.from_user(player = "Fred", day=1, month=5, year=2024, faction= "yellow", admin=False, salary=True)

    for f in ['Screenshot_2024-05-23_222523.png', 'Screenshot_2024-05-23_222537.png', 'Screenshot_2024-05-23_222607.png', 'Screenshot_2024-05-23_222625.png', 'Screenshot_2024-05-23_222639.png', 'Screenshot_2024-05-23_222655.png', 'Screenshot_2024-05-23_222705.png']:
        url = test_bucket.meta.client.generate_presigned_url(
            'get_object',
            Params={
                'Bucket': test_bucket_name,
                'Key': f'20240523-wf/{f}'
            })
        logger.debug(f'URL: {url}')

        event = {
            'invasion': invasion.name,
            'filename': f'{f}',
            'url': url,
            'folder': invasion.path_ladders(),
            'process': 'Ladder'
        }
        logger.debug(f'Event: {event}')

        result = client.lambda_client.invoke(FunctionName='Process',
                                            InvocationType='RequestResponse',
                                            Payload=json.dumps(event))
        logger.debug(f'Result: {result}')

        response = json.loads(result['Payload'].read())
        logger.info(f'Result payload: {response}')

    ladders = IrusLadder.from_invasion(invasion)
    yield ladders
    invasion.delete_from_table()
    Chatz01.remove()
    Stuggy.remove()
    TaliMonk.remove()
    kbaz.remove()
    Merkavar.remove()
    Fred.remove()


def test_download_sample_ladder_file(download_sample_ladder_file):
    assert download_sample_ladder_file['statusCode'] == 200
    assert download_sample_ladder_file['body'] == f'"Successful download of Screenshot_2024-05-23_222523.png. Ladder for invasion 20240523-wf with 8 rank(s) including 1 member(s)"'

def test_download_missing_file(download_missing_file):
    logger.info(f'Result: {download_missing_file}')
    assert download_missing_file['statusCode'] == 400

def test_download_sample_jpg_file(download_sample_jpg_file):
    logger.info(f'Result: {download_sample_jpg_file}')
    assert download_sample_jpg_file['statusCode'] == 400

def test_generate_invasion_ladders(generate_invasion_ladders):
    assert generate_invasion_ladders is not None
    assert generate_invasion_ladders.invasion is not None
    logger.info(generate_invasion_ladders.csv())
    assert generate_invasion_ladders.count() == 52
    assert generate_invasion_ladders.members() == 5
    assert generate_invasion_ladders.contiguous_from_1_until() == generate_invasion_ladders.count()