"""Unit tests for Bot Lambda function."""

import json
import os
from unittest.mock import Mock, patch

import pytest
from aws_lambda_powertools.utilities.typing import LambdaContext
from irus.container import IrusContainer


class TestBotLambda:
    """Test suite for Bot Lambda function."""

    @pytest.fixture
    def container(self):
        """Create test container with mocked dependencies."""
        return IrusContainer.create_unit()

    @pytest.fixture
    def lambda_context(self):
        """Create mock Lambda context."""
        context = Mock(spec=LambdaContext)
        context.function_name = "test-bot-function"
        context.function_version = "1"
        context.invoked_function_arn = (
            "arn:aws:lambda:us-east-1:123456789012:function:test-bot-function"
        )
        context.memory_limit_in_mb = 128
        context.remaining_time_in_millis = 30000
        context.aws_request_id = "test-request-id"
        return context

    @pytest.fixture
    def discord_event_base(self):
        """Base Discord interaction event structure."""
        return {
            "body": json.dumps(
                {
                    "type": 2,  # APPLICATION_COMMAND
                    "data": {"name": "irus", "options": []},
                    "member": {"roles": ["admin_role_id"]},
                    "token": "test_interaction_token",
                }
            ),
            "headers": {
                "x-signature-ed25519": "test_signature",
                "x-signature-timestamp": "1234567890",
            },
        }

    @pytest.fixture
    def discord_ping_event(self):
        """Discord ping event (type 1)."""
        return {
            "body": json.dumps({"type": 1}),
            "headers": {
                "x-signature-ed25519": "test_signature",
                "x-signature-timestamp": "1234567890",
            },
        }

    @patch.dict(os.environ, {"DISCORD_CMD": "irus"})
    @patch("src.bot.bot.verify_signature")
    @patch("src.bot.bot.IrusContainer.default")
    def test_ping_response(
        self, mock_container, mock_verify, container, lambda_context, discord_ping_event
    ):
        """Test Discord ping response (type 1)."""
        # Arrange
        mock_container.return_value = container
        mock_verify.return_value = None

        # Import after patching environment
        from src.bot.bot import lambda_handler

        # Act
        response = lambda_handler(discord_ping_event, lambda_context)

        # Assert
        assert response["statusCode"] == 200
        response_data = json.loads(response["body"])
        assert response_data["type"] == 1  # PONG response

    @patch.dict(os.environ, {"DISCORD_CMD": "irus"})
    @patch("src.bot.bot.verify_signature")
    @patch("src.bot.bot.IrusContainer.default")
    def test_help_command_admin(
        self, mock_container, mock_verify, container, lambda_context, discord_event_base
    ):
        """Test help command for admin user."""
        # Arrange
        mock_container.return_value = container
        mock_verify.return_value = None

        # Configure Discord event for help command
        event_body = json.loads(discord_event_base["body"])
        event_body["data"]["options"] = [{"name": "help"}]
        discord_event_base["body"] = json.dumps(event_body)

        # Import after patching environment
        from src.bot.bot import lambda_handler

        # Act
        response = lambda_handler(discord_event_base, lambda_context)

        # Assert
        assert response["statusCode"] == 200
        response_data = json.loads(response["body"])
        assert response_data["type"] == 4  # CHANNEL_MESSAGE_WITH_SOURCE
        assert "Invasions R Us Stats" in response_data["data"]["content"]
        assert (
            "ladder" in response_data["data"]["content"]
        )  # Admin help includes ladder command

    @patch.dict(os.environ, {"DISCORD_CMD": "irus"})
    @patch("src.bot.bot.verify_signature")
    @patch("src.bot.bot.IrusContainer.default")
    def test_help_command_regular_user(
        self, mock_container, mock_verify, container, lambda_context, discord_event_base
    ):
        """Test help command for regular user."""
        # Arrange
        mock_container.return_value = container
        mock_verify.return_value = None

        # Remove admin role from user
        event_body = json.loads(discord_event_base["body"])
        event_body["member"]["roles"] = ["regular_user_role"]
        event_body["data"]["options"] = [{"name": "help"}]
        discord_event_base["body"] = json.dumps(event_body)

        # Import after patching environment
        from src.bot.bot import lambda_handler

        # Act
        response = lambda_handler(discord_event_base, lambda_context)

        # Assert
        assert response["statusCode"] == 200
        response_data = json.loads(response["body"])
        assert response_data["type"] == 4
        assert (
            "As a company member" in response_data["data"]["content"]
        )  # User help text

    @patch.dict(os.environ, {"DISCORD_CMD": "irus"})
    @patch("src.bot.bot.verify_signature")
    @patch("src.bot.bot.IrusContainer.default")
    def test_member_add_command(
        self, mock_container, mock_verify, container, lambda_context, discord_event_base
    ):
        """Test member add command processing."""
        # Arrange
        mock_container.return_value = container
        mock_verify.return_value = None

        # Configure Discord event for member add
        event_body = json.loads(discord_event_base["body"])
        event_body["data"]["options"] = [
            {
                "name": "member",
                "options": [
                    {
                        "name": "add",
                        "options": [
                            {"name": "player", "value": "TestPlayer"},
                            {"name": "faction", "value": "yellow"},
                        ],
                    }
                ],
            }
        ]
        discord_event_base["body"] = json.dumps(event_body)

        # Mock member creation
        mock_member = Mock()
        mock_member.str.return_value = "Member TestPlayer added successfully"

        # Import after patching environment
        from src.bot.bot import lambda_handler

        with patch("src.bot.bot.IrusMember.from_user", return_value=mock_member):
            with patch(
                "src.bot.bot.irus.update_invasions_for_new_member", return_value=""
            ):
                # Act
                response = lambda_handler(discord_event_base, lambda_context)

        # Assert
        assert response["statusCode"] == 200
        response_data = json.loads(response["body"])
        assert response_data["type"] == 4  # CHANNEL_MESSAGE_WITH_SOURCE
        assert "TestPlayer added successfully" in response_data["data"]["content"]

    @patch.dict(os.environ, {"DISCORD_CMD": "irus"})
    @patch("src.bot.bot.verify_signature")
    def test_signature_verification_failure(
        self, mock_verify, lambda_context, discord_event_base
    ):
        """Test handling of signature verification failure."""
        # Arrange
        from nacl.exceptions import BadSignatureError

        mock_verify.side_effect = BadSignatureError("Invalid signature")

        # Import after patching environment
        from src.bot.bot import lambda_handler

        # Act
        response = lambda_handler(discord_event_base, lambda_context)

        # Assert
        assert response["statusCode"] == 401
        response_data = json.loads(response["body"])
        assert "Bad Signature" in response_data["data"]["content"]

    @patch.dict(os.environ, {"DISCORD_CMD": "irus"})
    @patch("src.bot.bot.verify_signature")
    @patch("src.bot.bot.IrusContainer.default")
    def test_unauthorized_user_admin_command(
        self, mock_container, mock_verify, container, lambda_context, discord_event_base
    ):
        """Test unauthorized user attempting admin command."""
        # Arrange
        mock_container.return_value = container
        mock_verify.return_value = None

        # Remove admin role from user
        event_body = json.loads(discord_event_base["body"])
        event_body["member"]["roles"] = ["regular_user_role"]
        event_body["data"]["options"] = [
            {"name": "member", "options": [{"name": "add", "options": []}]}
        ]
        discord_event_base["body"] = json.dumps(event_body)

        # Import after patching environment
        from src.bot.bot import lambda_handler

        # Act
        response = lambda_handler(discord_event_base, lambda_context)

        # Assert
        assert response["statusCode"] == 200
        response_data = json.loads(response["body"])
        assert "do not have permissions" in response_data["data"]["content"]

    @patch.dict(os.environ, {"DISCORD_CMD": "irus"})
    @patch("src.bot.bot.verify_signature")
    @patch("src.bot.bot.IrusContainer.default")
    def test_ladder_command_in_progress_response(
        self, mock_container, mock_verify, container, lambda_context, discord_event_base
    ):
        """Test ladder command returns in-progress response."""
        # Arrange
        mock_container.return_value = container
        mock_verify.return_value = None

        # Configure Discord event for ladder command
        event_body = json.loads(discord_event_base["body"])
        event_body["data"]["options"] = [
            {
                "name": "ladder",
                "options": [
                    {"name": "settlement", "value": "ef"},
                    {"name": "win", "value": True},
                    {"name": "file1", "value": "attachment_123"},
                ],
            }
        ]
        event_body["data"]["resolved"] = {
            "attachments": {
                "attachment_123": {
                    "filename": "ladder.png",
                    "url": "https://cdn.discordapp.com/test.png",
                }
            }
        }
        discord_event_base["body"] = json.dumps(event_body)

        # Mock invasion creation and process start
        mock_invasion = Mock()
        mock_invasion.name = "20241228-ef"

        # Import after patching environment
        from src.bot.bot import lambda_handler

        with patch("src.bot.bot.invasion_add_cmd", return_value=mock_invasion):
            with patch("src.bot.bot.invasion_process", return_value="Process started"):
                # Act
                response = lambda_handler(discord_event_base, lambda_context)

        # Assert
        assert response["statusCode"] == 200
        response_data = json.loads(response["body"])
        assert response_data["type"] == 5  # DEFERRED_CHANNEL_MESSAGE_WITH_SOURCE
        assert "In Progress" in response_data["data"]["content"]
        assert "20241228-ef" in response_data["data"]["content"]

    @patch.dict(os.environ, {"DISCORD_CMD": "irus"})
    @patch("src.bot.bot.verify_signature")
    @patch("src.bot.bot.IrusContainer.default")
    def test_unexpected_command(
        self, mock_container, mock_verify, container, lambda_context, discord_event_base
    ):
        """Test handling of unexpected command."""
        # Arrange
        mock_container.return_value = container
        mock_verify.return_value = None

        # Configure Discord event with unknown command
        event_body = json.loads(discord_event_base["body"])
        event_body["data"]["options"] = [{"name": "unknown_command"}]
        discord_event_base["body"] = json.dumps(event_body)

        # Import after patching environment
        from src.bot.bot import lambda_handler

        # Act
        response = lambda_handler(discord_event_base, lambda_context)

        # Assert
        assert response["statusCode"] == 200
        response_data = json.loads(response["body"])
        assert "Unexpected command" in response_data["data"]["content"]

    @patch.dict(os.environ, {"DISCORD_CMD": "irus"})
    @patch("src.bot.bot.verify_signature")
    def test_unexpected_exception(
        self, mock_verify, lambda_context, discord_event_base
    ):
        """Test handling of unexpected exceptions."""
        # Arrange
        mock_verify.side_effect = Exception("Unexpected error")

        # Import after patching environment
        from src.bot.bot import lambda_handler

        # Act
        response = lambda_handler(discord_event_base, lambda_context)

        # Assert
        assert response["statusCode"] == 401
        response_data = json.loads(response["body"])
        assert "Unexpected exception" in response_data["data"]["content"]
