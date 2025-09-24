#!/usr/bin/env python3
"""
Interactive SSM Parameter Setup Tool

Sets up SSM parameters for Discord bot configuration in the new environment-aware structure:
/irus/{environment}/{parameter_name}

Usage:
    python scripts/setup-ssm-parameters.py [environment]

Environment defaults to 'dev' if not specified.
"""

import sys
from pathlib import Path

import boto3
from botocore.exceptions import ClientError

# Add parent directory to path for config imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config import get_config


def get_existing_parameter(ssm_client, name: str, secure: bool = False) -> str:
    """Get existing parameter value if it exists."""
    try:
        response = ssm_client.get_parameter(Name=name, WithDecryption=secure)
        return response["Parameter"]["Value"]
    except ClientError as e:
        if e.response["Error"]["Code"] == "ParameterNotFound":
            return None
        raise


def prompt_for_parameter(
    param_name: str, description: str, current_value: str = None, secure: bool = False
) -> str:
    """Prompt user for parameter value with description and current value."""
    print(f"\n=== {param_name.upper()} ===")
    print(f"Description: {description}")

    if current_value is not None:
        if secure:
            display_value = (
                "***" + current_value[-4:] if len(current_value) > 4 else "***"
            )
        else:
            display_value = current_value
        print(f"Current value: {display_value}")
    else:
        print("Current value: (not set)")

    if secure:
        import getpass

        prompt_text = (
            f"Enter new {param_name} (or press Enter to keep current): "
            if current_value
            else f"Enter {param_name}: "
        )
        value = getpass.getpass(prompt_text)
    else:
        prompt_text = (
            f"Enter new {param_name} (or press Enter to keep current): "
            if current_value
            else f"Enter {param_name}: "
        )
        value = input(prompt_text).strip()

    # Return current value if user pressed Enter and there's a current value
    if not value and current_value is not None:
        return current_value

    return value


def set_ssm_parameter(
    ssm_client, name: str, value: str, description: str, secure: bool = False
):
    """Set SSM parameter with proper type."""
    param_type = "SecureString" if secure else "String"

    try:
        ssm_client.put_parameter(
            Name=name,
            Value=value,
            Type=param_type,
            Description=description,
            Overwrite=True,
        )
        print(f"✅ Set parameter: {name}")
    except Exception as e:
        print(f"❌ Failed to set {name}: {e}")
        return False

    return True


def main():
    # Get environment from command line or default to dev
    environment = sys.argv[1] if len(sys.argv) > 1 else "dev"

    if environment not in ["dev", "prod", "test"]:
        print("Error: Environment must be one of: dev, prod, test")
        sys.exit(1)

    print(f"Setting up SSM parameters for environment: {environment}")

    # Load configuration
    try:
        config = get_config(environment)
        aws_profile = config.get_aws_profile()
        aws_region = config.get_aws_region()
        ssm_prefix = config.get_ssm_prefix()
    except Exception as e:
        print(f"Error loading configuration: {e}")
        sys.exit(1)

    # Create boto3 session with profile
    try:
        session = boto3.Session(profile_name=aws_profile, region_name=aws_region)
        ssm_client = session.client("ssm")
        print(
            f"✅ Connected to AWS using profile '{aws_profile}' in region '{aws_region}'"
        )
    except Exception as e:
        print(f"❌ Failed to connect to AWS: {e}")
        print(
            f"Make sure profile '{aws_profile}' is configured and you have proper credentials."
        )
        sys.exit(1)

    # Define parameters to set up
    parameters = [
        {
            "name": "publickey",
            "description": "Discord application public key for request verification",
            "secure": False,
            "prompt": "Discord application public key (found in Discord Developer Portal)",
        },
        {
            "name": "appid",
            "description": "Discord application ID",
            "secure": False,
            "prompt": "Discord application ID (found in Discord Developer Portal)",
        },
        {
            "name": "bottoken",
            "description": "Discord bot token for API authentication",
            "secure": True,
            "prompt": "Discord bot token (found in Discord Developer Portal -> Bot section)",
        },
        {
            "name": "serverid",
            "description": "Discord server (guild) ID where bot operates",
            "secure": False,
            "prompt": "Discord server (guild) ID where the bot will operate",
        },
        {
            "name": "roleid",
            "description": "Discord role ID for command access control",
            "secure": False,
            "prompt": "Discord role ID that can use bot commands (optional, leave blank for no restriction)",
        },
    ]

    print(f"\nSSM parameters will be created with prefix: {ssm_prefix}/{environment}/")
    print(
        "\nNote: You can find Discord application settings in the Discord Developer Portal:"
    )
    print("https://discord.com/developers/applications")
    print("\nExisting parameters will be shown. Press Enter to keep current values.")

    input("\nPress Enter to continue or Ctrl+C to cancel...")

    success_count = 0
    total_count = len(parameters)

    # Process each parameter
    for param in parameters:
        param_path = f"{ssm_prefix}/{environment}/{param['name']}"

        # Get existing value
        current_value = get_existing_parameter(ssm_client, param_path, param["secure"])

        # Prompt for value
        value = prompt_for_parameter(
            param["name"], param["prompt"], current_value, param["secure"]
        )

        # Skip if no value provided and it's optional
        if not value and param["name"] in ["roleid"]:
            print(f"⏭️  Skipping {param['name']} (no value provided)")
            if current_value is not None:
                success_count += 1  # Count as success if there was already a value
            continue

        # Validate non-empty for required parameters
        if not value:
            print(f"❌ {param['name']} cannot be empty")
            continue

        # Set parameter (only if value changed or is new)
        if value != current_value:
            if set_ssm_parameter(
                ssm_client, param_path, value, param["description"], param["secure"]
            ):
                success_count += 1
        else:
            print(f"✅ Kept existing value for: {param_path}")
            success_count += 1

    # Summary
    print(f"\n{'=' * 50}")
    print(
        f"Setup complete: {success_count}/{total_count} parameters processed successfully"
    )

    if success_count == total_count:
        print("✅ All parameters configured successfully!")
        print("\nYour parameters are now available at:")
        for param in parameters:
            print(f"  {ssm_prefix}/{environment}/{param['name']}")

        print("\nYou can now deploy your stack with:")
        print(f"  ./deploy.sh deploy {environment}")
    else:
        print("⚠️  Some parameters failed to set. Please review the errors above.")
        sys.exit(1)


if __name__ == "__main__":
    main()
