"""Integration tests for Bot Lambda function."""

import json
import os
import time
from unittest.mock import patch
from uuid import uuid4

import pytest
from aws_lambda_powertools.utilities.typing import LambdaContext
from irus.container import IrusContainer

from tests.integration.conftest import get_test_date_components


class TestBotLambdaIntegration:
    """Integration test suite for Bot Lambda function."""

    @pytest.fixture
    def lambda_context(self):
        """Create mock Lambda context."""
        from unittest.mock import Mock

        context = Mock(spec=LambdaContext)
        context.function_name = "irus-dev-bot"
        context.aws_request_id = f"test-{uuid4().hex}"
        context.remaining_time_in_millis = 30000
        return context

    @pytest.fixture
    def discord_member_add_event(self):
        """Discord event for member add command with unique test data."""
        timestamp = int(time.time())
        unique_id = uuid4().hex[:8]
        date_components = get_test_date_components()

        return {
            "body": json.dumps(
                {
                    "type": 2,
                    "data": {
                        "name": "irus",
                        "options": [
                            {
                                "name": "member",
                                "options": [
                                    {
                                        "name": "add",
                                        "options": [
                                            {
                                                "name": "player",
                                                "value": f"TestPlayer-{timestamp}-{unique_id}",
                                            },
                                            {"name": "faction", "value": "yellow"},
                                            {
                                                "name": "day",
                                                "value": date_components["day"],
                                            },
                                            {
                                                "name": "month",
                                                "value": date_components["month"],
                                            },
                                            {
                                                "name": "year",
                                                "value": date_components["year"],
                                            },
                                        ],
                                    }
                                ],
                            }
                        ],
                    },
                    "member": {
                        "roles": [os.environ.get("DISCORD_ADMIN_ROLE_ID", "admin_role")]
                    },
                    "token": "test_interaction_token",
                }
            ),
            "headers": {
                "x-signature-ed25519": "test_signature",
                "x-signature-timestamp": str(int(time.time())),
            },
        }

    @pytest.fixture
    def discord_invasion_add_event(self):
        """Discord event for invasion add command with unique test data."""
        date_components = get_test_date_components()

        return {
            "body": json.dumps(
                {
                    "type": 2,
                    "data": {
                        "name": "irus",
                        "options": [
                            {
                                "name": "invasion",
                                "options": [
                                    {
                                        "name": "add",
                                        "options": [
                                            {"name": "settlement", "value": "ef"},
                                            {"name": "win", "value": True},
                                            {
                                                "name": "day",
                                                "value": date_components["day"],
                                            },
                                            {
                                                "name": "month",
                                                "value": date_components["month"],
                                            },
                                            {
                                                "name": "year",
                                                "value": date_components["year"],
                                            },
                                            {
                                                "name": "notes",
                                                "value": "Integration test invasion",
                                            },
                                        ],
                                    }
                                ],
                            }
                        ],
                    },
                    "member": {
                        "roles": [os.environ.get("DISCORD_ADMIN_ROLE_ID", "admin_role")]
                    },
                    "token": "test_interaction_token",
                }
            ),
            "headers": {
                "x-signature-ed25519": "test_signature",
                "x-signature-timestamp": str(int(time.time())),
            },
        }

    @pytest.fixture
    def discord_report_month_event(self):
        """Discord event for monthly report command."""
        date_components = get_test_date_components()

        return {
            "body": json.dumps(
                {
                    "type": 2,
                    "data": {
                        "name": "irus",
                        "options": [
                            {
                                "name": "report",
                                "options": [
                                    {
                                        "name": "month",
                                        "options": [
                                            {
                                                "name": "month",
                                                "value": date_components["month"],
                                            },
                                            {
                                                "name": "year",
                                                "value": date_components["year"],
                                            },
                                        ],
                                    }
                                ],
                            }
                        ],
                    },
                    "member": {
                        "roles": ["regular_user_role"]
                    },  # Regular user can access reports
                    "token": "test_interaction_token",
                }
            ),
            "headers": {
                "x-signature-ed25519": "test_signature",
                "x-signature-timestamp": str(int(time.time())),
            },
        }

    @patch.dict(os.environ, {"DISCORD_CMD": "irus"})
    @patch("src.bot.bot.verify_signature")
    def test_member_add_end_to_end(
        self,
        mock_verify,
        integration_container,
        lambda_context,
        discord_member_add_event,
    ):
        """Test complete member add workflow with real AWS resources."""
        # Arrange - Set container as default for Lambda
        IrusContainer.set_default(integration_container)
        mock_verify.return_value = None  # Mock signature verification for testing

        # Import after setting up environment and container
        from src.bot.bot import lambda_handler

        # Act
        response = lambda_handler(discord_member_add_event, lambda_context)

        # Assert
        assert response["statusCode"] == 200
        response_data = json.loads(response["body"])
        assert response_data["type"] == 4

        # Extract player name from event
        event_body = json.loads(discord_member_add_event["body"])
        player_name = None
        for option in event_body["data"]["options"][0]["options"][0]["options"]:
            if option["name"] == "player":
                player_name = option["value"]
                break

        # Verify member was actually created in DynamoDB
        from irus.repositories.member import MemberRepository

        member_repo = MemberRepository(integration_container)
        created_member = member_repo.get_by_player(player_name)

        assert created_member is not None
        assert created_member.player == player_name
        assert created_member.faction == "yellow"

        # Verify response contains success message
        assert player_name in response_data["data"]["content"]
        assert "added" in response_data["data"]["content"].lower()

    @patch.dict(os.environ, {"DISCORD_CMD": "irus"})
    @patch("src.bot.bot.verify_signature")
    def test_invasion_add_end_to_end(
        self,
        mock_verify,
        integration_container,
        lambda_context,
        discord_invasion_add_event,
    ):
        """Test complete invasion add workflow with real AWS resources."""
        # Arrange
        IrusContainer.set_default(integration_container)
        mock_verify.return_value = None

        # Import after setting up environment and container
        from src.bot.bot import lambda_handler

        # Act
        response = lambda_handler(discord_invasion_add_event, lambda_context)

        # Assert
        assert response["statusCode"] == 200
        response_data = json.loads(response["body"])
        assert response_data["type"] == 4

        # Extract invasion details from event
        event_body = json.loads(discord_invasion_add_event["body"])
        settlement = None
        day = month = year = None
        for option in event_body["data"]["options"][0]["options"][0]["options"]:
            if option["name"] == "settlement":
                settlement = option["value"]
            elif option["name"] == "day":
                day = option["value"]
            elif option["name"] == "month":
                month = option["value"]
            elif option["name"] == "year":
                year = option["value"]

        # Construct expected invasion name
        date_str = f"{year}{month:02d}{day:02d}"
        invasion_name = f"{date_str}-{settlement}"

        # Verify invasion was created in DynamoDB
        from irus.repositories.invasion import InvasionRepository

        invasion_repo = InvasionRepository(integration_container)
        created_invasion = invasion_repo.get_by_name(invasion_name)

        assert created_invasion is not None
        assert created_invasion.name == invasion_name
        assert created_invasion.settlement == settlement
        assert created_invasion.win is True

        # Verify response contains invasion name
        assert invasion_name in response_data["data"]["content"]

    @patch.dict(os.environ, {"DISCORD_CMD": "irus"})
    @patch("src.bot.bot.verify_signature")
    def test_report_month_command(
        self,
        mock_verify,
        integration_container,
        lambda_context,
        discord_report_month_event,
    ):
        """Test monthly report command with real AWS resources."""
        # Arrange
        IrusContainer.set_default(integration_container)
        mock_verify.return_value = None

        # Import after setting up environment and container
        from src.bot.bot import lambda_handler

        # Act
        response = lambda_handler(discord_report_month_event, lambda_context)

        # Assert
        assert response["statusCode"] == 200
        response_data = json.loads(response["body"])
        assert response_data["type"] == 4

        # Should contain monthly report information
        content = response_data["data"]["content"]
        assert "Monthly Average Stats" in content or "Report for Month" in content

    @patch.dict(os.environ, {"DISCORD_CMD": "irus"})
    @patch("src.bot.bot.verify_signature")
    def test_help_command_integration(
        self, mock_verify, integration_container, lambda_context
    ):
        """Test help command with real container."""
        # Arrange
        IrusContainer.set_default(integration_container)
        mock_verify.return_value = None

        help_event = {
            "body": json.dumps(
                {
                    "type": 2,
                    "data": {"name": "irus", "options": [{"name": "help"}]},
                    "member": {"roles": ["admin_role"]},
                    "token": "test_token",
                }
            ),
            "headers": {
                "x-signature-ed25519": "test_signature",
                "x-signature-timestamp": str(int(time.time())),
            },
        }

        # Import after setting up environment and container
        from src.bot.bot import lambda_handler

        # Act
        response = lambda_handler(help_event, lambda_context)

        # Assert
        assert response["statusCode"] == 200
        response_data = json.loads(response["body"])
        assert response_data["type"] == 4
        assert "Invasions R Us Stats" in response_data["data"]["content"]

    @patch.dict(os.environ, {"DISCORD_CMD": "irus"})
    @patch("src.bot.bot.verify_signature")
    def test_member_list_deprecated_message(
        self, mock_verify, integration_container, lambda_context
    ):
        """Test that member list command shows deprecation message."""
        # Arrange
        IrusContainer.set_default(integration_container)
        mock_verify.return_value = None

        member_list_event = {
            "body": json.dumps(
                {
                    "type": 2,
                    "data": {
                        "name": "irus",
                        "options": [
                            {
                                "name": "member",
                                "options": [{"name": "list", "options": []}],
                            }
                        ],
                    },
                    "member": {"roles": ["admin_role"]},
                    "token": "test_token",
                }
            ),
            "headers": {
                "x-signature-ed25519": "test_signature",
                "x-signature-timestamp": str(int(time.time())),
            },
        }

        # Import after setting up environment and container
        from src.bot.bot import lambda_handler

        # Act
        response = lambda_handler(member_list_event, lambda_context)

        # Assert
        assert response["statusCode"] == 200
        response_data = json.loads(response["body"])
        assert "Deprecated" in response_data["data"]["content"]
        assert "display members" in response_data["data"]["content"]

    @patch.dict(os.environ, {"DISCORD_CMD": "irus"})
    @patch("src.bot.bot.verify_signature")
    def test_unauthorized_user_integration(
        self, mock_verify, integration_container, lambda_context
    ):
        """Test unauthorized user with real container."""
        # Arrange
        IrusContainer.set_default(integration_container)
        mock_verify.return_value = None

        unauthorized_event = {
            "body": json.dumps(
                {
                    "type": 2,
                    "data": {
                        "name": "irus",
                        "options": [
                            {
                                "name": "member",
                                "options": [{"name": "add", "options": []}],
                            }
                        ],
                    },
                    "member": {"roles": ["regular_user_role"]},  # No admin role
                    "token": "test_token",
                }
            ),
            "headers": {
                "x-signature-ed25519": "test_signature",
                "x-signature-timestamp": str(int(time.time())),
            },
        }

        # Import after setting up environment and container
        from src.bot.bot import lambda_handler

        # Act
        response = lambda_handler(unauthorized_event, lambda_context)

        # Assert
        assert response["statusCode"] == 200
        response_data = json.loads(response["body"])
        assert "do not have permissions" in response_data["data"]["content"]

    @patch.dict(os.environ, {"DISCORD_CMD": "irus"})
    def test_signature_verification_integration(
        self, integration_container, lambda_context
    ):
        """Test actual signature verification failure."""
        # Arrange
        IrusContainer.set_default(integration_container)

        # Create event with invalid signature (will fail real verification)
        invalid_signature_event = {
            "body": json.dumps(
                {
                    "type": 2,
                    "data": {"name": "irus", "options": []},
                    "member": {"roles": ["admin_role"]},
                    "token": "test_token",
                }
            ),
            "headers": {
                "x-signature-ed25519": "invalid_signature",
                "x-signature-timestamp": str(int(time.time())),
            },
        }

        # Import after setting up environment and container
        from src.bot.bot import lambda_handler

        # Act
        response = lambda_handler(invalid_signature_event, lambda_context)

        # Assert - Should fail signature verification
        assert response["statusCode"] == 401
        response_data = json.loads(response["body"])
        assert "Bad Signature" in response_data["data"]["content"]
