"""Integration test configuration that dynamically discovers AWS resources."""

import os
from pathlib import Path

import pytest
import toml


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
    """Load integration test configuration."""
    config = load_config()
    env = os.environ.get("TEST_ENV", "dev")

    if env not in config["environments"]:
        pytest.skip(f"Environment '{env}' not found in configuration")

    env_config = config["environments"][env]

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
