import os
import boto3
import boto3.session
import pytest
from aws_lambda_powertools import Logger
from ..irus import IrusInvasion, IrusInvasion, IrusMember, IrusMemberList, IrusLadder

logger = Logger(service="test_irus_invasion", level="INFO", correlation_id=True)
profile = os.environ["AWS_PROFILE"]
session = boto3.session.Session(profile_name=profile)
dynamodb = session.resource('dynamodb')
table_name = os.environ['TABLE_NAME']
table = dynamodb.Table(table_name)
s3 = session.resource('s3')
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
    members = IrusMemberList()

    ladder = IrusLadder.from_ladder_image(invasion, members, bucket_name, f'{invasion.path_ladders()}one.png')
    logger.debug(f'Ladder {ladder}')

    yield ladder
    invasion.delete_from_table()
    Chatz01.remove()
    Stuggy.remove()


@pytest.fixture
def generate_fourth_ladder():
    invasion = IrusInvasion.from_user(day=11, month=6, year=2024, settlement='rw', win=True)
    logger.debug(f'Invasion {invasion}')

    Chatz01 = IrusMember.from_user(player = "Chatz01", day=1, month=5, year=2024, faction= "purple", admin=False, salary=True)
    Stuggy = IrusMember.from_user(player = "Stuggy", day=1, month=5, year=2024, faction= "green", admin=True, salary=True)
    Zel0s = IrusMember.from_user(player = "Zel0s", day=1, month=5, year=2024, faction= "yellow", admin=False, salary=True)
    SunnieGal = IrusMember.from_user(player = "SunnieGal", day=1, month=5, year=2024, faction= "purple", admin=False, salary=False)
    members = IrusMemberList()

    ladder = IrusLadder.from_ladder_image(invasion, members, bucket_name, f'{invasion.path_ladders()}four.png')
    logger.debug(f'Ladder {ladder}')

    yield ladder
    invasion.delete_from_table()
    Chatz01.remove()
    Stuggy.remove()
    Zel0s.remove()
    SunnieGal.remove()


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

    members = IrusMemberList()

    for f in ['one.png', 'two.png', 'three.png', 'four.png', 'five.png', 'six.png', 'seven.png', 'eight.png']:
        ladder = IrusLadder.from_ladder_image(invasion, members, bucket_name, f'{invasion.path_ladders()}{f}')
        logger.debug(f'Ladder {ladder}')

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
    assert generate_first_ladder is not None
    assert generate_first_ladder.invasion is not None
    logger.info(generate_first_ladder.csv())
    assert generate_first_ladder.count() == 8
    assert generate_first_ladder.members() == 2
    assert generate_first_ladder.is_contiguous_from_1() == True


def test_generate_fourth_ladder(generate_fourth_ladder):
    assert generate_fourth_ladder is not None
    assert generate_fourth_ladder.invasion is not None
    logger.info(generate_fourth_ladder.csv())
    assert generate_fourth_ladder.count() == 4
    assert generate_fourth_ladder.members() == 2
    assert generate_fourth_ladder.is_contiguous_from_1() == False


def test_generate_invasion_ladders(generate_invasion_ladders):
    assert generate_invasion_ladders is not None
    assert generate_invasion_ladders.invasion is not None
    logger.info(generate_invasion_ladders.csv())
    assert generate_invasion_ladders.count() == 52
    assert generate_invasion_ladders.members() == 5
    assert generate_invasion_ladders.is_contiguous_from_1() == True