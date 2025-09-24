"""Test modern pytest setup and fixtures."""

import pytest


class TestModernSetup:
    """Test that our modern testing setup works correctly."""

    def test_basic_fixture_usage(self, sample_member_data, sample_invasion_data):
        """Test that our basic fixtures work."""
        assert "id" in sample_member_data
        assert "faction" in sample_member_data
        assert sample_member_data["faction"] in ["Marauders", "Syndicate", "Covenant"]

        assert "settlement" in sample_invasion_data
        assert "win" in sample_invasion_data
        assert isinstance(sample_invasion_data["win"], bool)

    def test_settlement_parametrized_fixture(self, settlement_test_data):
        """Test parametrized fixture for settlements."""
        assert "settlement" in settlement_test_data
        assert "name" in settlement_test_data
        assert settlement_test_data["settlement"] in ["ef", "ww", "bw"]

    def test_faction_parametrized_fixture(self, faction_test_data):
        """Test parametrized fixture for factions."""
        assert faction_test_data in ["Marauders", "Syndicate", "Covenant"]

    @pytest.mark.unit
    def test_mock_dynamodb_fixture(self, mock_dynamodb_table):
        """Test that DynamoDB mocking works."""
        # Test that we can interact with the mocked table
        table = mock_dynamodb_table
        assert table.table_name == "test-irus-table"

        # Test putting and getting an item
        test_item = {"invasion": "#test", "id": "test-item", "data": "test-data"}
        table.put_item(Item=test_item)

        response = table.get_item(Key={"invasion": "#test", "id": "test-item"})
        assert "Item" in response
        assert response["Item"]["data"] == "test-data"

    @pytest.mark.unit
    def test_mock_s3_fixture(self, mock_s3_bucket):
        """Test that S3 mocking works."""
        s3_client, bucket_name = mock_s3_bucket
        assert bucket_name == "test-irus-bucket"

        # Test putting and getting an object
        s3_client.put_object(
            Bucket=bucket_name, Key="test-object", Body=b"test content"
        )

        response = s3_client.get_object(Bucket=bucket_name, Key="test-object")
        assert response["Body"].read() == b"test content"

    @pytest.mark.unit
    def test_discord_interaction_mock(self, mock_discord_interaction):
        """Test that Discord interaction mocking works."""
        interaction = mock_discord_interaction
        assert interaction.user.id == 12345
        assert interaction.guild.id == 67890

        # Test that we can call methods
        interaction.response.send_message("test message")
        interaction.response.send_message.assert_called_once_with("test message")

    @pytest.mark.unit
    def test_aws_error_simulation(self, simulate_aws_error):
        """Test that AWS error simulation works."""
        error = simulate_aws_error("DynamoDB", "ResourceNotFoundException")
        assert error.response["Error"]["Code"] == "ResourceNotFoundException"
        assert "DynamoDB" in error.response["Error"]["Message"]

    @pytest.mark.unit
    def test_performance_timer(self, performance_timer):
        """Test that performance timing fixture works."""
        import time

        timer = performance_timer
        timer.start()
        time.sleep(0.01)  # Sleep for 10ms
        timer.stop()

        assert timer.elapsed is not None
        assert timer.elapsed >= 0.01  # Should be at least 10ms

    @pytest.mark.unit
    def test_temp_file_fixture(self, temp_file_path):
        """Test that temporary file fixture works."""
        import os

        # Write to the temp file
        with open(temp_file_path, "w") as f:
            f.write("test content")

        # Read it back
        with open(temp_file_path) as f:
            content = f.read()

        assert content == "test content"
        assert os.path.exists(temp_file_path)

    @pytest.mark.unit
    def test_clean_environment_fixture(self, clean_environment):
        """Test that environment cleaning fixture works."""
        import os

        # Set a test environment variable
        os.environ["TEST_VAR"] = "test_value"
        assert os.environ.get("TEST_VAR") == "test_value"

        # After test, fixture should clean up (verified by next test)

    @pytest.mark.unit
    def test_environment_was_cleaned(self):
        """Test that previous test's environment was cleaned up."""
        import os

        # This should not exist from the previous test
        assert os.environ.get("TEST_VAR") is None

    @pytest.mark.mock
    def test_pytest_mock_plugin(self, mocker):
        """Test that pytest-mock plugin works."""
        # Create a mock using mocker fixture
        mock_func = mocker.Mock(return_value="mocked")
        result = mock_func("test")

        assert result == "mocked"
        mock_func.assert_called_once_with("test")

    def test_sample_data_consistency(self, sample_member_item, sample_invasion_item):
        """Test that sample data items have expected structure."""
        # Test member item
        assert sample_member_item["invasion"] == "#member"
        assert "id" in sample_member_item
        assert "faction" in sample_member_item
        assert "admin" in sample_member_item
        assert "salary" in sample_member_item
        assert "start" in sample_member_item

        # Test invasion item
        assert sample_invasion_item["invasion"] == "#invasion"
        assert "id" in sample_invasion_item
        assert "settlement" in sample_invasion_item
        assert "win" in sample_invasion_item
        assert "date" in sample_invasion_item
        assert "year" in sample_invasion_item
        assert "month" in sample_invasion_item
        assert "day" in sample_invasion_item
