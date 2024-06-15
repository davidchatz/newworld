import os
import boto3
import boto3.session
import pytest
import json
from aws_lambda_powertools import Logger
from .lambdaclient import LambdaClient
from irus import IrusInvasion, IrusMember, IrusMemberList, IrusLadder


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
def generate_first_ladder():
    invasion = IrusInvasion.from_user(day=11, month=6, year=2024, settlement='rw', win=True)
    logger.debug(f'Invasion {invasion}')

    Chatz01 = IrusMember.from_user(player = "Chatz01", day=1, month=5, year=2024, faction= "purple", admin=False, salary=True)
    Stuggy = IrusMember.from_user(player = "Stuggy", day=1, month=5, year=2024, faction= "green", admin=True, salary=True)

    event = {
        'invasion': invasion.name,
        'filename': 'one.png',
        'url': 'https://bogus.example.com',
        'folder': invasion.path_ladders()
    }

    logger.debug(f'Event: {event}')

    result = client.lambda_client.invoke(FunctionName='Ladder',
                                         InvocationType='RequestResponse',
                                         Payload=json.dumps(event))
    logger.debug(f'Result: {result}')

    response = json.loads(result['Payload'].read())
    logger.info(f'Result payload: {response}')

    yield response
    invasion.delete_from_table()
    Chatz01.remove()
    Stuggy.remove()


@pytest.fixture
def generate_invasion_ladders():
    invasion = IrusInvasion.from_user(day=11, month=6, year=2024, settlement='rw', win=True)
    logger.debug(f'Invasion {invasion}')

    Chatz01 = IrusMember.from_user(player = "Chatz01", day=1, month=5, year=2024, faction= "purple", admin=False, salary=True)
    Stuggy = IrusMember.from_user(player = "Stuggy", day=1, month=5, year=2024, faction= "green", admin=True, salary=True)
    Zel0s = IrusMember.from_user(player = "Zel0s", day=1, month=5, year=2024, faction= "yellow", admin=False, salary=True)
    SunnieGal = IrusMember.from_user(player = "SunnieGal", day=1, month=5, year=2024, faction= "purple", admin=False, salary=False)
    Merkavar = IrusMember.from_user(player = "Merkavar", day=1, month=5, year=2024, faction= "yellow", admin=False, salary=True)
    Fred = IrusMember.from_user(player = "Fred", day=1, month=5, year=2024, faction= "yellow", admin=False, salary=True)

    for f in ['one.png', 'two.png', 'three.png', 'four.png', 'five.png', 'six.png', 'seven.png', 'eight.png']:
        event = {
            'invasion': invasion.name,
            'filename': f,
            'url': 'https://bogus.example.com',
            'folder': invasion.path_ladders()
        }

        logger.debug(f'Event: {event}')

        result = client.lambda_client.invoke(FunctionName='Ladder',
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
    Zel0s.remove()
    SunnieGal.remove()
    Merkavar.remove()
    Fred.remove()


def test_generate_first_ladder(generate_first_ladder):
    assert generate_first_ladder['statusCode'] == 200
    assert generate_first_ladder['body'] == '"Ladder for invasion 20240611-rw of 8 ranks including 2 members"'


def test_generate_invasion_ladders(generate_invasion_ladders):
    assert generate_invasion_ladders is not None
    assert generate_invasion_ladders.invasion is not None
    logger.info(generate_invasion_ladders.csv())
    assert generate_invasion_ladders.count() == 52
    assert generate_invasion_ladders.members() == 5
    assert generate_invasion_ladders.is_contiguous_from_1() == True
