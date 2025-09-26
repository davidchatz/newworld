"""Integration test configuration for real AWS resource testing."""

import os
import time
from datetime import datetime
from pathlib import Path

import pytest
import toml
from irus.container import IrusContainer

# Test isolation constants
TEST_ISOLATION_YEAR_PREFIX = 99  # Test years start with 99


def generate_test_date():
    """Generate unique test date using 99DDHHMM pattern.

    Returns:
        tuple: (year, month, day) where:
            - year = 99DD (99 + day of month)
            - month = HH (hour 00-23, clamped to 1-12 for valid month)
            - day = MM (minute 00-59, clamped to 1-28 for valid day)
    """
    now = datetime.now()

    # Year: 99 + day of month (e.g. 9915 for 15th of month)
    test_year = (TEST_ISOLATION_YEAR_PREFIX * 100) + now.day

    # Month: hour (0-23), but clamp to valid month range (1-12)
    test_month = max(1, min(12, now.hour if now.hour > 0 else 1))

    # Day: minute (0-59), but clamp to valid day range (1-28)
    test_day = max(1, min(28, now.minute if now.minute > 0 else 1))

    return test_year, test_month, test_day


def get_test_date_components():
    """Get test date components for consistent use across tests.

    Returns:
        dict: Contains 'year', 'month', 'day', 'date_string', and 'date_int' keys
    """
    year, month, day = generate_test_date()
    date_string = f"{year}{month:02d}{day:02d}"
    return {
        "year": year,
        "month": month,
        "day": day,
        "date_string": date_string,
        "date_int": int(date_string),
    }


def is_test_date(date_value):
    """Check if a date value uses our test date pattern.

    Args:
        date_value: Date to check (int or string)

    Returns:
        bool: True if date uses test pattern
    """
    date_str = str(date_value)
    return date_str.startswith(str(TEST_ISOLATION_YEAR_PREFIX))


def load_config():
    """Load configuration from TOML files."""
    invasions_dir = Path(__file__).parent.parent.parent

    # Load base config
    config_path = invasions_dir / "config.toml"
    config = toml.load(config_path)

    # Load local overrides if they exist
    local_config_path = invasions_dir / "config-local.toml"
    if local_config_path.exists():
        local_config = toml.load(local_config_path)

        # Deep merge local config into base config
        def deep_merge(base_dict, override_dict):
            for key, value in override_dict.items():
                if (
                    key in base_dict
                    and isinstance(base_dict[key], dict)
                    and isinstance(value, dict)
                ):
                    deep_merge(base_dict[key], value)
                else:
                    base_dict[key] = value

        deep_merge(config, local_config)

    return config


def discover_stack_resources(stack_name: str, profile: str, region: str):
    """Discover AWS resources using SAM CLI."""
    import json
    import subprocess

    try:
        # Use SAM to get stack outputs
        cmd = [
            "sam",
            "list",
            "stack-outputs",
            "--stack-name",
            stack_name,
            "--profile",
            profile,
            "--region",
            region,
            "--output",
            "json",
        ]

        result = subprocess.run(cmd, capture_output=True, text=True, check=True)  # noqa: S603
        outputs = json.loads(result.stdout)

        resources = {}

        # Map SAM outputs to resource names
        for output in outputs:
            output_key = output.get("OutputKey", "")
            output_value = output.get("OutputValue", "")

            if output_key == "Table":
                resources["table_name"] = output_value
            elif output_key == "Bucket":
                resources["bucket_name"] = output_value
            elif output_key == "ProcessStepFunctionArn":
                resources["process_step_function_arn"] = output_value
            elif output_key == "PostTableStepFunctionArn":
                resources["post_step_function_arn"] = output_value

        # Add default webhook URL for testing
        resources["webhook_url"] = "https://test.webhook.com"

        return resources

    except subprocess.CalledProcessError as e:
        pytest.skip(f"Could not discover stack resources with SAM: {e.stderr}")
    except Exception as e:
        pytest.skip(f"Could not discover stack resources: {e}")


@pytest.fixture(scope="session")
def integration_config():
    """Load integration test configuration and set AWS environment."""
    config = load_config()
    env = os.environ.get("TEST_ENV", "dev")

    if env not in config["environments"]:
        pytest.skip(f"Environment '{env}' not found in configuration")

    env_config = config["environments"][env]

    # Automatically set AWS environment variables from config
    # This eliminates the need to set AWS_PROFILE on command line
    os.environ["AWS_PROFILE"] = env_config["aws_profile"]
    os.environ["AWS_DEFAULT_REGION"] = env_config["aws_region"]

    return {
        "environment": env,
        "aws_profile": env_config["aws_profile"],
        "aws_region": env_config["aws_region"],
        "stack_name": env_config["stack_name"],
        "ssm_prefix": env_config["ssm_prefix"],
    }


@pytest.fixture(scope="session")
def aws_resources(integration_config):
    """Discover AWS resources for testing."""
    resources = discover_stack_resources(
        integration_config["stack_name"],
        integration_config["aws_profile"],
        integration_config["aws_region"],
    )

    # Add default webhook URL for testing
    resources["webhook_url"] = "https://test.webhook.com"

    return resources


@pytest.fixture(scope="session")
def integration_container(integration_config, aws_resources):
    """Container configured for integration testing with real AWS resources.

    This creates a container using SAM-discovered resources with safety checks
    based on the configured stack name.
    """
    import boto3

    # Use the proper create_integration method with stack name from config
    container = IrusContainer.create_integration(
        aws_resources, integration_config["stack_name"]
    )

    # Configure session with discovered profile and region
    container._session = boto3.session.Session(
        profile_name=integration_config["aws_profile"],
        region_name=integration_config["aws_region"],
    )

    return container


@pytest.fixture
def test_member_data():
    """Generate unique test member data using 99DDHHMM pattern.

    Each test gets a unique member to avoid conflicts between parallel tests.
    Uses actual MemberRepository.create_from_user_input() API.
    """
    timestamp = int(time.time())
    date_components = get_test_date_components()

    return {
        "player": f"TestPlayer-{timestamp}",
        "day": date_components["day"],
        "month": date_components["month"],
        "year": date_components["year"],
        "faction": "yellow",
        "admin": False,
        "salary": True,
        "discord": None,
        "notes": "Integration test member",
    }


@pytest.fixture
def test_member_expectations(test_member_data):
    """Helper fixture providing expected values for member tests."""
    date_components = get_test_date_components()
    return {"expected_start_date": date_components["date_int"]}


@pytest.fixture
def test_invasion_data():
    """Generate unique test invasion data using 99DDHHMM pattern.

    Uses actual InvasionRepository.create_from_user_input() API.
    Uses unique date based on current time to avoid conflicts.
    """
    timestamp = int(time.time())
    date_components = get_test_date_components()

    return {
        "day": date_components["day"],
        "month": date_components["month"],
        "year": date_components["year"],
        "settlement": "ef",
        "win": True,
        "notes": f"Integration test invasion {timestamp}",
    }


@pytest.fixture
def test_invasion_expectations(test_invasion_data):
    """Helper fixture providing expected values for invasion tests."""
    date_components = get_test_date_components()
    return {"expected_date": date_components["date_int"]}


@pytest.fixture(autouse=True)
def cleanup_test_data(integration_container):
    """Automatically cleanup test data after each test.

    This fixture runs after each test to clean up any test-dated records
    using the test date pattern.
    """
    yield  # Run the test

    # Cleanup happens here after the test
    # Use the test date pattern to identify what to delete
    test_date_prefix = str(TEST_ISOLATION_YEAR_PREFIX)

    try:
        table = integration_container.table()

        # Scan for test records using the test date pattern
        response = table.scan(
            FilterExpression="begins_with(id, :test_prefix)",
            ExpressionAttributeValues={":test_prefix": test_date_prefix}
        )

        # Delete test records in batches
        with table.batch_writer() as batch:
            for item in response.get("Items", []):
                batch.delete_item(
                    Key={
                        "invasion": item["invasion"],
                        "id": item["id"]
                    }
                )

        # Handle pagination if needed
        while "LastEvaluatedKey" in response:
            response = table.scan(
                FilterExpression="begins_with(id, :test_prefix)",
                ExpressionAttributeValues={":test_prefix": test_date_prefix},
                ExclusiveStartKey=response["LastEvaluatedKey"]
            )

            with table.batch_writer() as batch:
                for item in response.get("Items", []):
                    batch.delete_item(
                        Key={
                            "invasion": item["invasion"],
                            "id": item["id"]
                        }
                    )

    except Exception as e:
        # Don't fail tests due to cleanup issues
        print(f"Warning: Test cleanup failed: {e}")
