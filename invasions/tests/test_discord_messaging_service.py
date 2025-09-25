"""Tests for Discord messaging service."""

import json
from unittest.mock import Mock, patch

import pytest
from botocore.exceptions import ClientError
from irus.container import IrusContainer
from irus.services.discord_messaging import DiscordMessagingService


class TestDiscordMessagingService:
    """Test suite for DiscordMessagingService class."""

    @pytest.fixture
    def container(self):
        """Create test container with mocked dependencies."""
        mock_container = IrusContainer.create_test()
        mock_container.post_step_function_arn = Mock(
            return_value="arn:aws:states:test:post"
        )
        mock_container.webhook_url = Mock(return_value="https://test.webhook.com")

        # Mock state machine
        mock_state_machine = Mock()
        mock_container.state_machine = Mock(return_value=mock_state_machine)

        return mock_container

    @pytest.fixture
    def service(self, container):
        """Create DiscordMessagingService instance with test container."""
        return DiscordMessagingService(container)

    @pytest.fixture
    def sample_table_data(self):
        """Create sample table data for testing."""
        return [
            "Player         Faction Start",
            "TestPlayer1    green   20240301",
            "TestPlayer2    purple  20240315",
            "TestPlayer3    yellow  20240401",
        ]

    def test_init(self, container):
        """Test DiscordMessagingService initialization."""
        service = DiscordMessagingService(container)

        assert service._container is container
        assert service._logger is not None
        assert service._state_machine is not None
        assert service._step_func_arn == "arn:aws:states:test:post"
        assert service._webhook_url == "https://test.webhook.com"

    def test_init_default_container(self):
        """Test DiscordMessagingService initialization with default container."""
        with patch.object(IrusContainer, "default") as mock_default:
            mock_container = Mock(spec=IrusContainer)
            mock_container.logger.return_value = Mock()
            mock_container.state_machine.return_value = Mock()
            mock_container.post_step_function_arn.return_value = "test_arn"
            mock_container.webhook_url.return_value = "test_url"
            mock_default.return_value = mock_container

            service = DiscordMessagingService()

            assert service._container is mock_container
            mock_default.assert_called_once()

    def test_post_table_success(self, service, sample_table_data):
        """Test posting table successfully."""
        result = service.post_table(
            "test_channel", "test_token", sample_table_data, "Test Table"
        )

        # Should return empty string on success
        assert result == ""

        # Verify step function was called
        service._state_machine.start_execution.assert_called_once()
        call_args = service._state_machine.start_execution.call_args

        # Check step function arguments
        assert call_args[1]["stateMachineArn"] == "arn:aws:states:test:post"

        # Parse and verify input data
        input_data = json.loads(call_args[1]["input"])
        assert input_data["post"] == "https://test.webhook.com/test_channel/test_token"
        assert input_data["count"] == 1
        assert len(input_data["msg"]) == 1

        # Check message formatting
        expected_msg = (
            "Test Table\n"
            "`Player         Faction Start`\n"
            "`TestPlayer1    green   20240301`\n"
            "`TestPlayer2    purple  20240315`\n"
            "`TestPlayer3    yellow  20240401`\n"
        )
        assert input_data["msg"][0] == expected_msg

    def test_post_table_large_data(self, service):
        """Test posting table with data that requires message splitting."""
        # Create large table data that will exceed message limit
        large_table = [f"Player{i:03d}      green   2024{i:04d}" for i in range(100)]

        result = service.post_table(
            "test_channel", "test_token", large_table, "Large Table"
        )

        assert result == ""

        # Verify step function was called
        service._state_machine.start_execution.assert_called_once()
        call_args = service._state_machine.start_execution.call_args

        # Parse input data
        input_data = json.loads(call_args[1]["input"])

        # Should have multiple messages due to size limit
        assert input_data["count"] > 1
        assert len(input_data["msg"]) > 1

        # Each message should not exceed Discord's limit
        for msg in input_data["msg"]:
            assert len(msg) <= 2000

    def test_post_table_step_function_error(self, service, sample_table_data):
        """Test handling step function execution errors."""
        # Mock step function to raise ClientError
        error = ClientError(
            error_response={
                "Error": {"Code": "ValidationException", "Message": "Invalid input"}
            },
            operation_name="StartExecution",
        )
        service._state_machine.start_execution.side_effect = error

        result = service.post_table(
            "test_channel", "test_token", sample_table_data, "Test Table"
        )

        assert "Failed to call post table step function:" in result
        assert "ValidationException" in result

    def test_post_simple_message_success(self, service):
        """Test posting simple message successfully."""
        message = "Hello from bot!"
        result = service.post_simple_message("test_channel", "test_token", message)

        assert result == ""

        # Verify step function was called
        service._state_machine.start_execution.assert_called_once()
        call_args = service._state_machine.start_execution.call_args

        # Parse input data
        input_data = json.loads(call_args[1]["input"])
        assert input_data["post"] == "https://test.webhook.com/test_channel/test_token"
        assert input_data["count"] == 1
        assert input_data["msg"] == [message]

    def test_post_simple_message_error(self, service):
        """Test handling errors when posting simple message."""
        error = ClientError(
            error_response={
                "Error": {"Code": "ThrottlingException", "Message": "Rate exceeded"}
            },
            operation_name="StartExecution",
        )
        service._state_machine.start_execution.side_effect = error

        result = service.post_simple_message(
            "test_channel", "test_token", "Test message"
        )

        assert "Failed to call post table step function:" in result
        assert "ThrottlingException" in result

    def test_build_table_command(self, service, sample_table_data):
        """Test building table command payload."""
        cmd = service._build_table_command(
            "channel_id", "token", sample_table_data, "Test"
        )

        assert cmd["post"] == "https://test.webhook.com/channel_id/token"
        assert cmd["count"] == 1
        assert len(cmd["msg"]) == 1
        assert cmd["msg"][0].startswith("Test\n")
        assert "`Player         Faction Start`" in cmd["msg"][0]

    def test_build_table_command_message_splitting(self, service):
        """Test command building with message splitting logic."""
        # Create data that will require splitting
        long_rows = ["A" * 500 for _ in range(10)]  # Each row is 500 chars

        cmd = service._build_table_command(
            "channel_id", "token", long_rows, "Long Table"
        )

        # Should have multiple messages
        assert cmd["count"] > 1
        assert len(cmd["msg"]) > 1

        # Each message should be under the limit
        for msg in cmd["msg"]:
            assert len(msg) <= 2000

    def test_logging_operations(self, service, sample_table_data):
        """Test that operations are logged correctly."""
        service.post_table(
            "test_channel", "test_token", sample_table_data, "Test Table"
        )

        # Verify logging calls were made
        assert service._logger.info.call_count >= 2  # Start and execution logs

        service.post_simple_message("test_channel", "test_token", "Test message")

        # Additional logging for simple message
        assert service._logger.info.call_count >= 3

    def test_large_table_warning(self, service):
        """Test warning log for tables with too many posts."""
        # Create data that will result in more than 4 posts
        large_data = [
            f"Very long row with lots of text to force splitting {i}" * 50
            for i in range(20)
        ]

        result = service.post_table(
            "test_channel", "test_token", large_data, "Large Table"
        )

        assert result == ""

        # Should have logged a warning about too many posts
        service._logger.warning.assert_called()
        warning_call = service._logger.warning.call_args[0][0]
        assert "Too many posts" in warning_call
        assert "Large Table" in warning_call

    def test_empty_table_data(self, service):
        """Test handling empty table data."""
        result = service.post_table("test_channel", "test_token", [], "Empty Table")

        assert result == ""

        # Verify step function was still called
        service._state_machine.start_execution.assert_called_once()
        call_args = service._state_machine.start_execution.call_args

        input_data = json.loads(call_args[1]["input"])
        assert input_data["count"] == 1
        assert len(input_data["msg"]) == 1
        assert input_data["msg"][0] == "Empty Table\n"
