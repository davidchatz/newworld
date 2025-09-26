"""Pytest configuration and shared fixtures for Irus testing."""

import os
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock

import boto3
import pytest
from factory import Factory, Faker
from moto import mock_aws

# Load .env file for legacy code compatibility
# This ensures legacy modules that depend on environment variables at import time
# can access the required values (e.g., TABLE_NAME, BUCKET_NAME, etc.)
env_file = Path(__file__).parent.parent / '.env'
if env_file.exists():
    from dotenv import load_dotenv
    load_dotenv(env_file)


# Test environment setup
@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    """Set up test environment variables."""
    os.environ.update(
        {
            "AWS_DEFAULT_REGION": "us-east-1",
            "AWS_ACCESS_KEY_ID": "testing",
            "AWS_SECRET_ACCESS_KEY": "testing",
            "AWS_SECURITY_TOKEN": "testing",
            "AWS_SESSION_TOKEN": "testing",
            "ENVIRONMENT": "test",
            "DYNAMODB_TABLE_NAME": "test-irus-table",
            "S3_BUCKET_NAME": "test-irus-bucket",
        }
    )
    yield
    # Cleanup environment variables if needed
    test_vars = ["ENVIRONMENT", "DYNAMODB_TABLE_NAME", "S3_BUCKET_NAME"]
    for var in test_vars:
        os.environ.pop(var, None)


# AWS Mock fixtures
@pytest.fixture
def mock_dynamodb_table():
    """Create a mocked DynamoDB table for testing."""
    with mock_aws():
        dynamodb = boto3.resource("dynamodb", region_name="us-east-1")

        # Create test table with the structure used by Irus
        table = dynamodb.create_table(
            TableName="test-irus-table",
            KeySchema=[
                {"AttributeName": "invasion", "KeyType": "HASH"},
                {"AttributeName": "id", "KeyType": "RANGE"},
            ],
            AttributeDefinitions=[
                {"AttributeName": "invasion", "AttributeType": "S"},
                {"AttributeName": "id", "AttributeType": "S"},
            ],
            BillingMode="PAY_PER_REQUEST",
        )

        yield table


@pytest.fixture
def mock_s3_bucket():
    """Create a mocked S3 bucket for testing."""
    with mock_aws():
        s3 = boto3.client("s3", region_name="us-east-1")
        bucket_name = "test-irus-bucket"
        s3.create_bucket(Bucket=bucket_name)
        yield s3, bucket_name


@pytest.fixture
def mock_textract():
    """Create a mocked Textract service for testing."""
    with mock_aws():
        textract = boto3.client("textract", region_name="us-east-1")
        yield textract


# Test data factories using factory-boy
class IrusMemberDataFactory(Factory):
    """Factory for creating test IrusMember data."""

    class Meta:
        model = dict

    id = Faker("user_name")
    faction = Faker("random_element", elements=("Marauders", "Syndicate", "Covenant"))
    admin = Faker("boolean", chance_of_getting_true=20)
    salary = Faker("boolean", chance_of_getting_true=30)
    start = Faker("random_int", min=20240101, max=20241231)
    discord = Faker("user_name")
    notes = Faker("sentence", nb_words=5)


class IrusInvasionDataFactory(Factory):
    """Factory for creating test IrusInvasion data."""

    class Meta:
        model = dict

    name = Faker("bothify", text="########-??")
    settlement = Faker(
        "random_element",
        elements=(
            "bw",
            "bs",
            "ck",
            "er",
            "eg",
            "ef",
            "mb",
            "md",
            "rw",
            "rs",
            "wf",
            "ww",
        ),
    )
    win = Faker("boolean")
    date = Faker("random_int", min=20240101, max=20241231)
    year = Faker("random_int", min=2024, max=2024)
    month = Faker("random_int", min=1, max=12)
    day = Faker("random_int", min=1, max=28)
    notes = Faker("sentence", nb_words=8)


# Common test data fixtures
@pytest.fixture
def sample_member_data() -> dict[str, Any]:
    """Provide sample member data for testing."""
    return IrusMemberDataFactory()


@pytest.fixture
def sample_invasion_data() -> dict[str, Any]:
    """Provide sample invasion data for testing."""
    return IrusInvasionDataFactory()


@pytest.fixture
def sample_member_item() -> dict[str, Any]:
    """Provide sample member DynamoDB item for testing."""
    return {
        "invasion": "#member",
        "id": "test_player",
        "faction": "Marauders",
        "admin": False,
        "salary": True,
        "start": 20240101,
        "discord": "testplayer#1234",
        "notes": "Test member for testing purposes",
    }


@pytest.fixture
def sample_invasion_item() -> dict[str, Any]:
    """Provide sample invasion DynamoDB item for testing."""
    return {
        "invasion": "#invasion",
        "id": "20240315-ef",
        "settlement": "ef",
        "win": True,
        "date": 20240315,
        "year": 2024,
        "month": 3,
        "day": 15,
        "notes": "Great invasion with high attendance",
    }


@pytest.fixture
def sample_settlements():
    """Provide list of valid settlements."""
    return ["bw", "bs", "ck", "er", "eg", "ef", "mb", "md", "rw", "rs", "wf", "ww"]


@pytest.fixture
def sample_ladder_image_path(tmp_path) -> str:
    """Provide path to sample ladder image for testing."""
    # Create a dummy image file for testing
    image_path = tmp_path / "sample_ladder.png"
    image_path.write_bytes(b"dummy image data")
    return str(image_path)


# Mock Discord client fixtures
@pytest.fixture
def mock_discord_interaction():
    """Create a mock Discord interaction for testing bot commands."""
    interaction = MagicMock()
    interaction.response.send_message = MagicMock()
    interaction.followup.send = MagicMock()
    interaction.user.id = 12345
    interaction.guild.id = 67890
    return interaction


# Utility fixtures
@pytest.fixture
def clean_environment():
    """Provide a clean environment for tests that modify global state."""
    original_env = os.environ.copy()
    yield
    # Restore original environment
    os.environ.clear()
    os.environ.update(original_env)


@pytest.fixture
def temp_file_path(tmp_path):
    """Provide a temporary file path for testing file operations."""
    file_path = tmp_path / f"test_file_{uuid.uuid4().hex}.txt"
    yield str(file_path)
    # Cleanup handled by tmp_path


# Parametrized test data for settlements
@pytest.fixture(
    params=[
        {"settlement": "ef", "name": "Everfall"},
        {"settlement": "ww", "name": "Windsward"},
        {"settlement": "bw", "name": "Brightwood"},
    ]
)
def settlement_test_data(request):
    """Provide parametrized settlement test data."""
    return request.param


# Parametrized test data for factions
@pytest.fixture(params=["Marauders", "Syndicate", "Covenant"])
def faction_test_data(request):
    """Provide parametrized faction test data."""
    return request.param


# Error simulation fixtures
@pytest.fixture
def simulate_aws_error():
    """Fixture to simulate AWS service errors."""

    def _simulate_error(service_name: str, error_type: str = "ServiceException"):
        from botocore.exceptions import ClientError

        error = ClientError(
            error_response={
                "Error": {
                    "Code": error_type,
                    "Message": f"Simulated {service_name} error for testing",
                }
            },
            operation_name="TestOperation",
        )
        return error

    return _simulate_error


# Performance testing helpers
@pytest.fixture
def performance_timer():
    """Fixture for timing test operations."""
    import time

    class Timer:
        def __init__(self):
            self.start_time = None
            self.end_time = None

        def start(self):
            self.start_time = time.time()

        def stop(self):
            self.end_time = time.time()

        @property
        def elapsed(self):
            if self.start_time and self.end_time:
                return self.end_time - self.start_time
            return None

    return Timer()


# Mock Textract response fixtures
@pytest.fixture
def mock_textract_response():
    """Provide a mock Textract response for testing."""
    return {
        "Blocks": [
            {"BlockType": "LINE", "Id": "1", "Text": "Player1 500", "Confidence": 95.0},
            {"BlockType": "LINE", "Id": "2", "Text": "Player2 450", "Confidence": 93.0},
        ]
    }


# Date/time fixtures for consistent testing
@pytest.fixture
def fixed_datetime():
    """Provide a fixed datetime for consistent testing."""
    return datetime(2024, 3, 15, 12, 0, 0)
