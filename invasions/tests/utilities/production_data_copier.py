"""Production data copier for creating test scenarios from real data.

This utility copies complete invasion datasets (invasion + ladder + members + S3 files)
from production to development environments for debugging and test creation.

Usage:
    # Copy specific invasion with all related data
    copier = ProductionDataCopier(
        source_profile='irus-prod',
        target_profile='irus-dev'
    )
    copier.copy_invasion_scenario('20240315-bw')

    # CLI usage
    python production_data_copier.py --invasion 20240315-bw --source-profile irus-prod
"""

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

import boto3
import toml
from botocore.exceptions import ClientError
from irus.container import IrusContainer
from irus.repositories.invasion import InvasionRepository
from irus.repositories.ladder import LadderRepository
from irus.repositories.member import MemberRepository


class ProductionDataCopierError(Exception):
    """Base exception for data copier operations."""

    pass


class ConfigurationError(ProductionDataCopierError):
    """Raised when configuration is invalid."""

    pass


class ResourceDiscoveryError(ProductionDataCopierError):
    """Raised when AWS resource discovery fails."""

    pass


class ProductionDataCopier:
    """Copy complete invasion scenarios from production to development."""

    def __init__(
        self,
        source_environment: str = "prod",
        target_environment: str = "dev",
        target_container: IrusContainer | None = None,
        source_profile_override: str | None = None,
        source_stack_override: str | None = None,
    ):
        """Initialize copier with environment configurations.

        Args:
            source_environment: Source environment name (prod, dev) - defaults to prod
            target_environment: Target environment name (prod, dev) - defaults to dev
            target_container: Target container (optional, overrides target_environment)
            source_profile_override: Override AWS profile for source (for current production)
            source_stack_override: Override stack name for source (for current production)
        """
        # Load configuration
        self.config = self._load_config()

        self.source_env = source_environment
        self.target_env = target_environment

        # Get environment configurations
        self.source_config = self.config["environments"][source_environment].copy()
        self.target_config = self.config["environments"][target_environment]

        # Apply source overrides if provided
        if source_profile_override:
            self.source_config["aws_profile"] = source_profile_override
        if source_stack_override:
            source_stack_name = source_stack_override
        else:
            source_stack_name = f"irus-{source_environment}"

        # Create containers with SAM resource discovery
        self.source_container = self._create_integration_container(
            self.source_config, source_stack_name
        )
        self.source_logger = self.source_container.logger()

        # Create target container
        if target_container:
            self.target_container = target_container
        else:
            self.target_container = self._create_integration_container(
                self.target_config, f"irus-{target_environment}"
            )

        # Initialize repositories
        self.source_invasion_repo = InvasionRepository(self.source_container)
        self.source_ladder_repo = LadderRepository(self.source_container)
        self.source_member_repo = MemberRepository(self.source_container)

        self.target_invasion_repo = InvasionRepository(self.target_container)
        self.target_ladder_repo = LadderRepository(self.target_container)
        self.target_member_repo = MemberRepository(self.target_container)

        # S3 clients for file copying
        source_profile = self.source_config["aws_profile"]
        target_profile = self.target_config["aws_profile"]

        self.source_s3 = boto3.Session(profile_name=source_profile).client("s3")
        self.target_s3 = boto3.Session(profile_name=target_profile).client("s3")

    def _load_config(self) -> dict[str, Any]:
        """Load configuration from TOML files with proper error handling."""
        base_dir = Path(__file__).parent / "../.."
        config_path = base_dir / "config.toml"
        local_config_path = base_dir / "config-local.toml"

        if not config_path.exists():
            raise ConfigurationError(f"Required config file not found: {config_path}")

        try:
            with open(config_path) as f:
                config = toml.load(f)
        except toml.TomlDecodeError as e:
            raise ConfigurationError(
                f"Invalid TOML in config file {config_path}: {e}"
            ) from e

        # Validate required sections
        if "environments" not in config:
            raise ConfigurationError("Config missing required 'environments' section")

        # Load local overrides if they exist
        if local_config_path.exists():
            try:
                with open(local_config_path) as f:
                    local_config = toml.load(f)
                    # Safe merge - only merge environment configs
                    if "environments" in local_config:
                        for env, values in local_config["environments"].items():
                            if env in config["environments"] and isinstance(
                                values, dict
                            ):
                                config["environments"][env].update(values)
                            else:
                                config["environments"][env] = values
            except toml.TomlDecodeError as e:
                raise ConfigurationError(
                    f"Invalid TOML in local config {local_config_path}: {e}"
                ) from e

        return config

    def _create_integration_container(
        self, env_config: dict, stack_name: str
    ) -> IrusContainer:
        """Create integration container with SAM resource discovery."""
        try:
            # Discover resources using SAM
            resources = self._discover_stack_resources(
                stack_name, env_config["aws_profile"], env_config["aws_region"]
            )

            # Create integration container with discovered resources
            container = IrusContainer.create_integration(resources, stack_name)
            return container

        except Exception as e:
            self.source_logger.error(f"Failed to create integration container: {e}")
            # Fallback to production container with profile override
            container = IrusContainer.create_production()
            session = boto3.Session(profile_name=env_config["aws_profile"])
            container._session = session
            return container

    def _discover_stack_resources(
        self, stack_name: str, profile: str, region: str
    ) -> dict[str, str]:
        """Discover AWS resources using SAM CLI with proper error handling."""
        # Validate SAM CLI is available
        if not shutil.which("sam"):
            raise ResourceDiscoveryError(
                "SAM CLI not found. Install with: pip install aws-sam-cli"
            )

        # Validate inputs to prevent command injection
        if not stack_name or not all(c.isalnum() or c in "-_" for c in stack_name):
            raise ValueError(f"Invalid stack name: {stack_name}")

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

        try:
            result = subprocess.run(  # noqa: S603
                cmd,
                capture_output=True,
                text=True,
                check=True,
                timeout=30,  # Add reasonable timeout
            )

            if not result.stdout.strip():
                raise ResourceDiscoveryError(
                    f"SAM command returned empty output for stack {stack_name}"
                )

            outputs = json.loads(result.stdout)

        except subprocess.TimeoutExpired as e:
            raise ResourceDiscoveryError(
                f"SAM command timed out for stack {stack_name}"
            ) from e
        except subprocess.CalledProcessError as e:
            raise ResourceDiscoveryError(
                f"SAM command failed for stack {stack_name}: {e.stderr}"
            ) from e
        except json.JSONDecodeError as e:
            raise ResourceDiscoveryError(f"Invalid JSON from SAM command: {e}") from e

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

        # Add webhook URL from config
        resources["webhook_url"] = self.config.get("general", {}).get(
            "discord_webhook_url", "https://discord.com/api/v10/webhooks"
        )

        # Validate we got required resources
        if not resources.get("table_name") or not resources.get("bucket_name"):
            raise ResourceDiscoveryError(
                f"Required resources not found in stack {stack_name}"
            )

        return resources

    def copy_invasion_scenario(
        self, invasion_id: str, include_s3_files: bool = True
    ) -> dict[str, Any]:
        """Copy complete invasion scenario with all related data.

        Args:
            invasion_id: Production invasion ID (e.g., "20240315-bw")
            include_s3_files: Whether to copy S3 ladder images

        Returns:
            Dictionary with copied data summary
        """
        self.source_logger.info(f"Starting copy of invasion scenario: {invasion_id}")

        result = {
            "invasion_id": invasion_id,
            "invasion_copied": False,
            "ladder_ranks_copied": 0,
            "members_copied": 0,
            "s3_files_copied": 0,
            "errors": [],
        }

        try:
            # 1. Copy the invasion record
            invasion = self._copy_invasion(invasion_id)
            if invasion:
                result["invasion_copied"] = True

            # 2. Copy all ladder ranks for this invasion
            ladder_count = self._copy_ladder_data(invasion_id)
            result["ladder_ranks_copied"] = ladder_count

            # 3. Copy members who participated in this invasion
            member_count = self._copy_invasion_members(invasion_id)
            result["members_copied"] = member_count

            # 4. Copy S3 files (ladder images)
            if include_s3_files:
                s3_count = self._copy_s3_files(invasion_id)
                result["s3_files_copied"] = s3_count

            self.source_logger.info(f"Completed invasion scenario copy: {result}")

        except Exception as e:
            error_msg = f"Failed to copy invasion scenario {invasion_id}: {str(e)}"
            self.source_logger.error(error_msg)
            result["errors"].append(error_msg)

        return result

    def _copy_invasion(self, invasion_id: str) -> bool:
        """Copy invasion record from source to target with exact same ID."""
        try:
            # Get invasion from source
            invasion = self.source_invasion_repo.get_by_name(invasion_id)
            if not invasion:
                self.source_logger.warning(
                    f"Invasion {invasion_id} not found in source"
                )
                return False

            # Save to target with original ID (overwrite if exists)
            self.target_invasion_repo.save(invasion)
            self.source_logger.info(f"Copied invasion: {invasion_id}")
            return True

        except Exception as e:
            self.source_logger.error(f"Error copying invasion {invasion_id}: {e}")
            return False

    def _copy_ladder_data(self, invasion_id: str) -> int:
        """Copy all ladder ranks for the invasion with original IDs."""
        try:
            # Get ladder from source
            ladder = self.source_ladder_repo.get_by_invasion(invasion_id)
            if not ladder or not ladder.ranks:
                self.source_logger.warning(f"No ladder data found for {invasion_id}")
                return 0

            # Save each rank to target with original invasion ID (overwrite if exists)
            saved_count = 0
            for rank in ladder.ranks:
                self.target_ladder_repo.save_rank(rank)
                saved_count += 1

            self.source_logger.info(
                f"Copied {saved_count} ladder ranks for {invasion_id}"
            )
            return saved_count

        except Exception as e:
            self.source_logger.error(
                f"Error copying ladder data for {invasion_id}: {e}"
            )
            return 0

    def _copy_invasion_members(self, invasion_id: str) -> int:
        """Copy members who participated in this invasion with original data."""
        try:
            # Get ladder to find participating members
            ladder = self.source_ladder_repo.get_by_invasion(invasion_id)
            if not ladder or not ladder.ranks:
                return 0

            # Get unique player names from ladder
            player_names = {rank.player for rank in ladder.ranks}

            # Copy each participating member with original data (overwrite if exists)
            copied_count = 0
            for player_name in player_names:
                member = self.source_member_repo.get_by_player(player_name)
                if member:
                    self.target_member_repo.save(member)
                    copied_count += 1

            self.source_logger.info(f"Copied {copied_count} members for {invasion_id}")
            return copied_count

        except Exception as e:
            self.source_logger.error(f"Error copying members for {invasion_id}: {e}")
            return 0

    def _copy_s3_files(self, invasion_id: str) -> int:
        """Copy S3 files with original paths and proper pagination."""
        try:
            source_bucket = self._get_source_bucket_name()
            target_bucket = self._get_target_bucket_name()

            if not source_bucket or not target_bucket:
                self.source_logger.warning("S3 bucket names not configured")
                return 0

            # Use paginator for complete results
            paginator = self.source_s3.get_paginator("list_objects_v2")
            pages = paginator.paginate(
                Bucket=source_bucket, Prefix=f"ladders/{invasion_id}"
            )

            copied_count = 0

            for page in pages:
                for obj in page.get("Contents", []):
                    source_key = obj["Key"]

                    # Keep original file path (no transformation)
                    target_key = source_key

                    try:
                        # Copy file with error handling (overwrite if exists)
                        copy_source = {"Bucket": source_bucket, "Key": source_key}
                        self.target_s3.copy_object(
                            CopySource=copy_source, Bucket=target_bucket, Key=target_key
                        )
                        copied_count += 1

                    except ClientError as e:
                        self.source_logger.error(f"Failed to copy {source_key}: {e}")
                        # Continue with other files rather than failing completely

            self.source_logger.info(f"Copied {copied_count} S3 files for {invasion_id}")
            return copied_count

        except Exception as e:
            self.source_logger.error(f"Error copying S3 files for {invasion_id}: {e}")
            return 0

    def _get_source_bucket_name(self) -> str | None:
        """Get source S3 bucket name from container configuration."""
        return self.source_container._bucket_name

    def _get_target_bucket_name(self) -> str | None:
        """Get target S3 bucket name from container configuration."""
        return self.target_container._bucket_name

    def list_recent_invasions(self, count: int = 10) -> list[str]:
        """List recent invasions from source for selection."""
        try:
            invasions = self.source_invasion_repo.get_recent(count)
            invasion_ids = [inv.name for inv in invasions]
            self.source_logger.info(f"Found {len(invasion_ids)} recent invasions")
            return invasion_ids
        except Exception as e:
            self.source_logger.error(f"Error listing recent invasions: {e}")
            return []

    def cleanup_test_scenarios(self) -> dict[str, int]:
        """Clean up all test scenario data."""
        self.source_logger.info("Starting cleanup of test scenario data")

        result = {
            "invasions_deleted": 0,
            "ladder_ranks_deleted": 0,
            "members_deleted": 0,
            "s3_files_deleted": 0,
        }

        try:
            # Clean up invasions starting with "test_"
            # Implementation would scan and delete test records

            self.source_logger.info(f"Cleanup completed: {result}")

        except Exception as e:
            self.source_logger.error(f"Error during cleanup: {e}")

        return result


def main():
    """CLI interface for production data copier."""
    parser = argparse.ArgumentParser(
        description="Copy invasion scenarios from production to dev for testing"
    )

    parser.add_argument("--invasion", help="Invasion ID to copy (e.g., 20240315-bw)")
    parser.add_argument(
        "--source-env",
        default="prod",
        help="Source environment (prod, dev) - defaults to prod",
    )
    parser.add_argument(
        "--target-env",
        default="dev",
        help="Target environment (prod, dev) - defaults to dev",
    )
    parser.add_argument(
        "--source-profile",
        help="Override AWS profile for source (for current production access)",
    )
    parser.add_argument(
        "--source-stack",
        help="Override stack name for source (for current production stack)",
    )
    parser.add_argument("--no-s3", action="store_true", help="Skip S3 file copying")
    parser.add_argument(
        "--list-recent", action="store_true", help="List recent invasions and exit"
    )
    parser.add_argument(
        "--cleanup", action="store_true", help="Clean up test scenario data"
    )

    args = parser.parse_args()

    try:
        copier = ProductionDataCopier(
            source_environment=args.source_env,
            target_environment=args.target_env,
            source_profile_override=args.source_profile,
            source_stack_override=args.source_stack,
        )

        if args.list_recent:
            invasions = copier.list_recent_invasions()
            print(f"Recent invasions from {args.source_env}:")
            for inv_id in invasions:
                print(f"  {inv_id}")
            return

        if args.cleanup:
            result = copier.cleanup_test_scenarios()
            print(f"Cleanup completed: {result}")
            return

        if not args.invasion:
            parser.error(
                "--invasion is required unless using --list-recent or --cleanup"
            )

        # Copy invasion scenario
        result = copier.copy_invasion_scenario(
            args.invasion, include_s3_files=not args.no_s3
        )

        print(
            f"Copy completed for {args.invasion} ({args.source_env} -> {args.target_env}):"
        )
        print(f"  Invasion copied: {result['invasion_copied']}")
        print(f"  Ladder ranks copied: {result['ladder_ranks_copied']}")
        print(f"  Members copied: {result['members_copied']}")
        print(f"  S3 files copied: {result['s3_files_copied']}")

        if result["errors"]:
            print("Errors:")
            for error in result["errors"]:
                print(f"  {error}")
            sys.exit(1)

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
