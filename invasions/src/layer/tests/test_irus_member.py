import os
import boto3
import boto3.session
import pytest
from decimal import Decimal
from datetime import datetime
from aws_lambda_powertools import Logger
from ..irus import Member

logger = Logger(service="test_irus_member", level="INFO", correlation_id=True)
profile = os.environ["PROFILE"]
session = boto3.session.Session(profile_name=profile)
dynamodb = session.resource('dynamodb')
table_name = os.environ['TABLE_NAME']
table = dynamodb.Table(table_name)


@pytest.fixture
def member_from_user():
    member = Member.from_user(player="fred", day=2, month=5, year=2024, faction="green", admin=False, salary=True)
    yield member
    member.remove()


@pytest.fixture
def member_from_table():
    member = Member.from_user(player="mary", day=3, month=5, year=2024, faction="purple", admin=False, salary=True)
    item = Member.from_table(player="mary")
    yield item
    member.remove()


def test_member_from_user(member_from_user):
    assert member_from_user.player == "fred"
    assert member_from_user.start == 20240502
    assert member_from_user.faction == "green"
    assert member_from_user.admin is False
    assert member_from_user.salary is True
    assert member_from_user.key() == {'invasion': '#member', 'id': 'fred'}
    response = table.get_item(Key=member_from_user.key())
    assert 'Item' in response
    assert 'start' in response['Item']
    assert int(response['Item']['start']) == 20240502


def test_member_from_table(member_from_table):
    assert member_from_table.player == "mary"
    assert member_from_table.start == 20240503
    assert member_from_table.faction == "purple"
    assert member_from_table.admin is False
    assert member_from_table.salary is True
    assert member_from_table.key() == {'invasion': '#member', 'id': 'mary'}


def test_member_remove():
    member = Member.from_user(player="paul", day=4, month=5, year=2024, faction="yellow", admin=False, salary=True)
    key = member.key()
    member.remove()
    response = table.get_item(Key=key)
    assert 'Item' not in response
