import os
import boto3
import boto3.session
import pytest
from decimal import Decimal
from aws_lambda_powertools import Logger
from ..irus import Member, MemberList

logger = Logger(service="test_irus_member", level="INFO", correlation_id=True)
profile = os.environ["PROFILE"]
session = boto3.session.Session(profile_name=profile)
dynamodb = session.resource('dynamodb')
table_name = os.environ['TABLE_NAME']
table = dynamodb.Table(table_name)


@pytest.fixture
def memberlist_init():
    fred = Member.from_user(player="fred", day=2, month=5, year=2024, faction="green", admin=False, salary=True)
    mary = Member.from_user(player="mary", day=3, month=5, year=2024, faction="purple", admin=False, salary=True)
    paul = Member.from_user(player="paul", day=4, month=5, year=2024, faction="yellow", admin=False, salary=True)
    members = MemberList()
    yield members
    paul.remove()
    mary.remove()
    fred.remove()


def test_memberlist_init(memberlist_init):
    assert memberlist_init.count() == 3
    assert memberlist_init.get(0).player == "fred"
    assert memberlist_init.get(1).player == "mary"
    assert memberlist_init.get(2).player == "paul"
