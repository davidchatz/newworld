#!/usr/bin/env python3
"""
Deployment configuration helper for deploy.sh script.
Extracts configuration values for bash consumption.
"""

import sys
from pathlib import Path

# Add the invasions directory to the path so we can import config
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config import get_config


def main():
    if len(sys.argv) != 3:
        print("Usage: python deploy_config.py <environment> <key>", file=sys.stderr)
        print("Environment: dev|prod", file=sys.stderr)
        print(
            "Keys: aws_profile, aws_region, stack_name, ssm_prefix, log_level",
            file=sys.stderr,
        )
        sys.exit(1)

    environment = sys.argv[1]
    key = sys.argv[2]

    try:
        config = get_config(environment)

        if key == "aws_profile":
            print(config.get_aws_profile())
        elif key == "aws_region":
            print(config.get_aws_region())
        elif key == "stack_name":
            print(config.get_stack_name())
        elif key == "ssm_prefix":
            print(config.get_ssm_prefix())
        elif key == "log_level":
            print(config.get_general_setting("log_level", "INFO").upper())
        elif key == "sam_capabilities":
            sam_config = config.get_sam_config()
            print(
                sam_config.get("capabilities", "CAPABILITY_IAM CAPABILITY_AUTO_EXPAND")
            )
        elif key == "sam_confirm_changeset":
            sam_config = config.get_sam_config()
            print(str(sam_config.get("confirm_changeset", False)).lower())
        elif key == "sam_fail_on_empty_changeset":
            sam_config = config.get_sam_config()
            print(str(sam_config.get("fail_on_empty_changeset", False)).lower())
        elif key == "sam_resolve_s3":
            sam_config = config.get_sam_config()
            print(str(sam_config.get("resolve_s3", True)).lower())
        elif key == "sam_cached":
            sam_config = config.get_sam_config()
            print(str(sam_config.get("cached", True)).lower())
        elif key == "sam_parallel":
            sam_config = config.get_sam_config()
            print(str(sam_config.get("parallel", True)).lower())
        else:
            print(f"Unknown key: {key}", file=sys.stderr)
            sys.exit(1)

    except Exception as e:
        print(f"Error getting config: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
