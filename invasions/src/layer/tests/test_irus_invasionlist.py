import os
import boto3
import boto3.session
import pytest
from decimal import Decimal
from aws_lambda_powertools import Logger
from ..irus import IrusInvasionList, IrusInvasion

logger = Logger(service="test_irus_invasionlist", level="INFO", correlation_id=True)
profile = os.environ["AWS_PROFILE"]
session = boto3.session.Session(profile_name=profile)
dynamodb = session.resource('dynamodb')
table_name = os.environ['TABLE_NAME']
table = dynamodb.Table(table_name)


@pytest.fixture
def invasionlist_from_month():
    invasion_20240501 = IrusInvasion.from_user(day=1, month=5, year=2024, settlement="ww", win=True)
    invasion_20240502 = IrusInvasion.from_user(day=2, month=5, year=2024, settlement="ck", win=True)
    invasion_20240601 = IrusInvasion.from_user(day=1, month=6, year=2024, settlement="mb", win=True)
    invasions = IrusInvasionList.from_month(month=5, year=2024)
    yield invasions
    invasion_20240501.delete_from_table()
    invasion_20240502.delete_from_table()
    invasion_20240601.delete_from_table()


@pytest.fixture
def invasionlist_from_start():
    invasion_20240501 = IrusInvasion.from_user(day=1, month=5, year=2024, settlement="ww", win=True)
    invasion_20240502 = IrusInvasion.from_user(day=2, month=5, year=2024, settlement="ck", win=True)
    invasion_20240601 = IrusInvasion.from_user(day=1, month=6, year=2024, settlement="mb", win=True)
    invasions = IrusInvasionList.from_start(start=20240502)
    yield invasions
    invasion_20240501.delete_from_table()
    invasion_20240502.delete_from_table()
    invasion_20240601.delete_from_table()


def test_invasionlist_from_month(invasionlist_from_month):
    assert invasionlist_from_month.count() == 2
    assert invasionlist_from_month.start == Decimal('20240501')
    i_20240501 = invasionlist_from_month.get(0)
    assert i_20240501.date == Decimal('20240501')
    i_20240502 = invasionlist_from_month.get(1)
    assert i_20240502.date == Decimal('20240502')


def test_invasionlist_from_start(invasionlist_from_start):
    assert invasionlist_from_start.count() == 2
    assert invasionlist_from_start.start == Decimal('20240502')
    i_20240502 = invasionlist_from_start.get(0)
    assert i_20240502.date == Decimal('20240502')
    i_20240601 = invasionlist_from_start.get(1)
    assert i_20240601.date == Decimal('20240601')