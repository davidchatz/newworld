import os
import boto3
import boto3.session
import pytest
from aws_lambda_powertools import Logger
from ..irus import IrusMember, IrusMemberList

logger = Logger(service="test_irus_memberlist", level="INFO", correlation_id=True)
profile = os.environ["AWS_PROFILE"]
session = boto3.session.Session(profile_name=profile)
dynamodb = session.resource("dynamodb")
table_name = os.environ["TABLE_NAME"]
table = dynamodb.Table(table_name)


@pytest.fixture
def memberlist_init():
    fred = IrusMember.from_user(
        player="fred",
        day=2,
        month=5,
        year=2024,
        faction="green",
        admin=False,
        salary=True,
    )
    mary = IrusMember.from_user(
        player="mary",
        day=3,
        month=5,
        year=2024,
        faction="purple",
        admin=False,
        salary=True,
    )
    paul = IrusMember.from_user(
        player="paul",
        day=4,
        month=5,
        year=2024,
        faction="yellow",
        admin=False,
        salary=True,
    )
    members = IrusMemberList()
    yield members
    paul.remove()
    mary.remove()
    fred.remove()


@pytest.fixture
def memberlist_partial():
    Chatz01 = IrusMember.from_user(
        player="Chatz01",
        day=2,
        month=5,
        year=2024,
        faction="green",
        admin=False,
        salary=True,
    )
    ZelOs = IrusMember.from_user(
        player="ZelOs",
        day=3,
        month=5,
        year=2024,
        faction="purple",
        admin=False,
        salary=True,
    )
    Dave = IrusMember.from_user(
        player="Dave the Farmer",
        day=4,
        month=5,
        year=2024,
        faction="yellow",
        admin=False,
        salary=True,
    )
    members = IrusMemberList()
    yield members
    Chatz01.remove()
    ZelOs.remove()
    Dave.remove()


def test_memberlist_init(memberlist_init):
    assert memberlist_init.count() == 3
    assert memberlist_init.get(0).player == "fred"
    assert memberlist_init.get(1).player == "mary"
    assert memberlist_init.is_member("paul") == "paul"
    assert memberlist_init.is_member("joe") == None
    logger.info(memberlist_init.str())
    logger.info(memberlist_init.csv())


def test_memberlist_partial(memberlist_partial):
    assert memberlist_partial.count() == 3
    assert memberlist_partial.is_member("ChatzO1") == "Chatz01"
    assert memberlist_partial.is_member("Zel0s") == "ZelOs"
    assert memberlist_partial.is_member("Chatz", partial=True) == "Chatz01"
    assert memberlist_partial.is_member("Dave the", partial=True) == "Dave the Farmer"
    logger.info(memberlist_partial.str())
    logger.info(memberlist_partial.csv())
