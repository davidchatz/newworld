import os
import boto3
import boto3.session
import pytest
from decimal import Decimal
from aws_lambda_powertools import Logger
from ..irus import LadderRank, Invasion, Member

logger = Logger(service="test_irus_member", level="INFO", correlation_id=True)
profile = os.environ["PROFILE"]
session = boto3.session.Session(profile_name=profile)
dynamodb = session.resource('dynamodb')
table_name = os.environ['TABLE_NAME']
table = dynamodb.Table(table_name)

