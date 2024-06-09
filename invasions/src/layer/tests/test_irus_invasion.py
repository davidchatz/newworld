import os
import boto3
import boto3.session
import pytest
from decimal import Decimal
from datetime import datetime
from aws_lambda_powertools import Logger
from ..irus import Invasion

logger = Logger(service="test_irus_invasion", level="INFO", correlation_id=True)
profile = os.environ["PROFILE"]
session = boto3.session.Session(profile_name=profile)
dynamodb = session.resource('dynamodb')
table_name = os.environ['TABLE_NAME']
table = dynamodb.Table(table_name)


@pytest.fixture
def invasion_from_user():
    invasion = Invasion.from_user(day=1, month=5, year=2024, settlement="ww", win=True)
    yield invasion
    invasion.delete_from_table()

@pytest.fixture
def invasion_from_table():
    new_invasion = Invasion.from_user(day=2, month=5, year=2024, settlement="ww", win=True)
    invasion = Invasion.from_table(new_invasion.name)
    yield invasion
    new_invasion.delete_from_table()

@pytest.fixture
def invasion_from_table_item():
    new_invasion = Invasion.from_user(day=3, month=5, year=2024, settlement="mb", win=True)
    response = table.get_item(Key={"invasion": "#invasion", "id": "20240503-mb"})
    invasion = Invasion.from_table_item(response['Item'])
    yield invasion
    new_invasion.delete_from_table()


def test_invasion_from_user_name(invasion_from_user):
    assert invasion_from_user.name == "20240501-ww"
    assert invasion_from_user.date == Decimal('20240501')
    assert invasion_from_user.key() == {'invasion': '#invasion', 'id': '20240501-ww'}

    response = table.get_item(Key=invasion_from_user.key())
    assert 'Item' in response
    assert 'date' in response['Item']
    assert int(response['Item']['date']) == 20240501


def test_invasion_from_table(invasion_from_table):
    assert invasion_from_table.name == "20240502-ww"
    assert invasion_from_table.date == Decimal('20240502')


def test_invasion_from_table_item(invasion_from_table_item):
    assert invasion_from_table_item.name == "20240503-mb"
    assert invasion_from_table_item.date == Decimal('20240503')