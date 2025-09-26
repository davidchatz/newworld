#!/usr/bin/env python3
"""Script to clean up test data from integration tests."""

import json
import os
import subprocess
import sys
from pathlib import Path

import toml

sys.path.append(os.path.join(os.path.dirname(__file__), "../../src/layer"))


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

        return resources

    except subprocess.CalledProcessError as e:
        print(f"Could not discover stack resources with SAM: {e.stderr}")
        return None
    except Exception as e:
        print(f"Could not discover stack resources: {e}")
        return None


def setup_aws_environment():
    """Set up AWS environment for cleanup script."""
    config = load_config()
    env = os.environ.get("TEST_ENV", "dev")

    # Get environment config
    if "environments" not in config or env not in config["environments"]:
        raise ValueError(f"Environment {env} not found in config")

    env_config = config["environments"][env]

    stack_name = env_config.get("stack_name")
    profile = env_config.get("aws_profile")
    region = env_config.get("aws_region")

    if not all([stack_name, profile, region]):
        raise ValueError("Missing required AWS configuration")

    # Discover resources using SAM
    resources = discover_stack_resources(stack_name, profile, region)
    if not resources or "table_name" not in resources:
        raise ValueError("Could not discover DynamoDB table name from SAM")

    # Set environment variables
    os.environ["TABLE_NAME"] = resources["table_name"]
    os.environ["AWS_PROFILE"] = profile
    os.environ["AWS_REGION"] = region

    print(f"Using table: {resources['table_name']}")
    print(f"Using profile: {profile}")
    print(f"Using region: {region}")

    return resources


def cleanup_test_data():
    """Clean up all test data with year 9999 from DynamoDB tables."""
    print("Starting test data cleanup...")

    # Set up AWS environment
    resources = setup_aws_environment()

    # Import after environment is set up
    from boto3.dynamodb.conditions import Key
    from irus.container import IrusContainer
    from irus.repositories.invasion import InvasionRepository
    from irus.repositories.member import MemberRepository

    # Create container with discovered resources (following STYLE_GUIDE.md testing patterns)
    container = IrusContainer.create_integration(resources)

    # Create repositories using documented pattern (STYLE_GUIDE.md line 346)
    invasion_repo = InvasionRepository(container)
    member_repo = MemberRepository(container)

    # Clean up invasion test data
    response = invasion_repo.table.scan(
        FilterExpression=Key("invasion").eq("#invasion")
    )

    invasion_count = 0
    for item in response.get("Items", []):
        if item["id"].startswith("9999"):
            invasion_repo.table.delete_item(
                Key={"invasion": "#invasion", "id": item["id"]}
            )
            print(f"Deleted test invasion: {item['id']}")
            invasion_count += 1

    # Clean up member test data
    response = member_repo.table.scan(FilterExpression=Key("member").eq("#member"))

    member_count = 0
    for item in response.get("Items", []):
        if item["id"].startswith("9999"):
            member_repo.table.delete_item(Key={"member": "#member", "id": item["id"]})
            print(f"Deleted test member: {item['id']}")
            member_count += 1

    print(
        f"Cleanup complete: {invasion_count} invasions, {member_count} members deleted"
    )


if __name__ == "__main__":
    cleanup_test_data()
