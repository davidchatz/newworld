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
    """Clean up all test data starting with "99" from DynamoDB tables.

    SAFETY: Only runs against dev environment. Refuses to run against production.
    """
    print("Starting test data cleanup...")

    # Set up AWS environment
    resources = setup_aws_environment()
    config = load_config()
    env = os.environ.get("TEST_ENV", "dev")

    # SAFETY CHECK: Refuse to run against production
    if env == "prod" or env == "production":
        raise ValueError(
            "SAFETY: Cleanup script cannot run against production environment"
        )

    stack_name = config["environments"][env]["stack_name"]
    table_name = resources.get("table_name", "")

    # SAFETY CHECK: Validate table name contains expected environment marker
    if "dev" not in table_name.lower() and "test" not in table_name.lower():
        raise ValueError(
            f"SAFETY: Table name '{table_name}' does not appear to be a dev/test table. "
            "Refusing to run cleanup."
        )

    print(f"Environment: {env}")
    print(f"Stack: {stack_name}")

    # Import after environment is set up
    from irus.container import IrusContainer

    # Create container with discovered resources (following STYLE_GUIDE.md testing patterns)
    # This also includes safety checks that table_name contains stack_name
    container = IrusContainer.create_integration(resources, stack_name)

    # Clean up all test data (using "99" prefix from conftest.py pattern)
    # Test data has EITHER:
    # - id starting with "99" (invasions/ladders: "99041228-bw")
    # - start field starting with "99" (members with start date like 99041228)
    # - id containing "TestPlayer" (old test data)
    table = container.table()

    print("\nScanning for test data...")
    print("  - Invasions/ladders with id starting with '99'")
    print("  - Members with start date beginning with '99'")
    print("  - Any records with 'TestPlayer' in id")

    # Scan for all test data using multiple patterns
    from boto3.dynamodb.conditions import Attr

    response = table.scan(
        FilterExpression=(
            Attr("id").begins_with("99")  # Invasions/ladders
            | Attr("start").begins_with("99")  # Members with 99DDHHMM start dates
            | Attr("id").contains("TestPlayer")  # Old test data
            | Attr("id").eq("NewMidMonth")  # Specific test member
        )
    )

    total_count = 0
    deleted_items = []

    # Delete in batches
    with table.batch_writer() as batch:
        for item in response.get("Items", []):
            batch.delete_item(Key={"invasion": item["invasion"], "id": item["id"]})
            deleted_items.append(f"{item['invasion']}:{item['id']}")
            total_count += 1
            if total_count % 10 == 0:
                print(f"Deleted {total_count} test records so far...")

    # Handle pagination
    while "LastEvaluatedKey" in response:
        response = table.scan(
            FilterExpression=(
                Attr("id").begins_with("99")
                | Attr("start").begins_with("99")
                | Attr("id").contains("TestPlayer")
                | Attr("id").eq("NewMidMonth")
            ),
            ExclusiveStartKey=response["LastEvaluatedKey"],
        )

        with table.batch_writer() as batch:
            for item in response.get("Items", []):
                batch.delete_item(Key={"invasion": item["invasion"], "id": item["id"]})
                deleted_items.append(f"{item['invasion']}:{item['id']}")
                total_count += 1
                if total_count % 10 == 0:
                    print(f"Deleted {total_count} test records so far...")

    print(f"\n✓ Cleanup complete: {total_count} test records deleted")
    if deleted_items and total_count <= 50:
        print("\nDeleted items (sample):")
        for item in deleted_items[:50]:
            print(f"  - {item}")


if __name__ == "__main__":
    cleanup_test_data()
