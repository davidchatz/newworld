"""Configuration management for the Invasions Discord Bot."""

import os
import toml
from pathlib import Path
from typing import Dict, Any, Optional


class Config:
    """Simple configuration loader that merges config.toml with config-local.toml."""

    def __init__(self, environment: str = "dev"):
        """Initialize configuration for the specified environment.

        Args:
            environment: Target environment ("dev" or "prod")
        """
        self.environment = environment
        self._config = self._load_config()

    def _load_config(self) -> Dict[str, Any]:
        """Load and merge configuration files."""
        config_dir = Path(__file__).parent.parent

        # Load default config
        default_config_path = config_dir / "config.toml"
        if not default_config_path.exists():
            raise FileNotFoundError(f"Default config file not found: {default_config_path}")

        config = toml.load(default_config_path)

        # Load local overrides if they exist
        local_config_path = config_dir / "config-local.toml"
        if local_config_path.exists():
            local_config = toml.load(local_config_path)
            config = self._merge_configs(config, local_config)

        return config

    def _merge_configs(self, base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
        """Deep merge configuration dictionaries."""
        result = base.copy()

        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._merge_configs(result[key], value)
            else:
                result[key] = value

        return result

    def get_environment_config(self) -> Dict[str, Any]:
        """Get configuration for the current environment."""
        if "environments" not in self._config:
            raise KeyError("No environments configuration found")

        if self.environment not in self._config["environments"]:
            raise KeyError(f"Environment '{self.environment}' not found in configuration")

        return self._config["environments"][self.environment]

    def get_aws_profile(self) -> str:
        """Get AWS profile for current environment."""
        env_config = self.get_environment_config()
        return env_config.get("aws_profile", "default")

    def get_aws_region(self) -> str:
        """Get AWS region for current environment."""
        env_config = self.get_environment_config()
        return env_config.get("aws_region", "us-east-1")

    def get_stack_name(self) -> str:
        """Get CloudFormation stack name for current environment."""
        env_config = self.get_environment_config()
        return env_config.get("stack_name", f"irus-{self.environment}")

    def get_ssm_prefix(self) -> str:
        """Get SSM Parameter Store prefix for current environment."""
        env_config = self.get_environment_config()
        return env_config.get("ssm_prefix", f"/irus-{self.environment}")

    def get_sam_config(self) -> Dict[str, Any]:
        """Get SAM deployment configuration for current environment."""
        env_config = self.get_environment_config()
        return env_config.get("sam", {})

    def get_parameter_store_paths(self) -> Dict[str, str]:
        """Get Parameter Store paths with SSM prefix applied."""
        param_config = self._config.get("parameter_store", {})
        ssm_prefix = self.get_ssm_prefix()

        return {
            key: f"{ssm_prefix}/{path}"
            for key, path in param_config.items()
        }

    def get_app_setting(self, key: str, default: Any = None) -> Any:
        """Get application setting value."""
        app_settings = self._config.get("app_settings", {})
        return app_settings.get(key, default)

    def get_general_setting(self, key: str, default: Any = None) -> Any:
        """Get general setting value."""
        general = self._config.get("general", {})
        return general.get(key, default)

    @property
    def timezone(self) -> str:
        """Get timezone setting."""
        return self.get_general_setting("timezone", "Australia/Sydney")

    @property
    def log_level(self) -> str:
        """Get log level setting."""
        return self.get_general_setting("log_level", "INFO")

    @property
    def discord_cmd(self) -> str:
        """Get Discord command name."""
        return self.get_general_setting("discord_cmd", "irus")


def get_config(environment: Optional[str] = None) -> Config:
    """Get configuration instance for the specified environment.

    Args:
        environment: Target environment. If None, uses INVASIONS_ENV env var or defaults to 'dev'
    """
    if environment is None:
        environment = os.getenv("INVASIONS_ENV", "dev")

    return Config(environment)


# Global config instance for convenience
config = get_config()