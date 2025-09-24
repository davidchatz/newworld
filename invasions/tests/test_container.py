"""Tests for IrusContainer dependency injection."""

import os
from unittest.mock import Mock, patch

import pytest
from irus.container import IrusContainer


class TestIrusContainer:
    """Test suite for IrusContainer."""

    def test_create_test_container(self):
        """Test creating a test container with mocks."""
        mock_table = Mock()
        mock_logger = Mock()
        mock_s3 = Mock()

        container = IrusContainer.create_test(
            table=mock_table, logger=mock_logger, s3=mock_s3
        )

        assert container.table() == mock_table
        assert container.logger() == mock_logger
        assert container.s3() == mock_s3
        assert container.bucket_name() == "test-bucket"
        assert container.table_name() == "test-table"

    def test_create_test_container_with_defaults(self):
        """Test creating test container with default mocks."""
        container = IrusContainer.create_test()

        # Should get mock objects that conform to protocols
        table = container.table()
        logger = container.logger()
        s3 = container.s3()

        # Basic interface checks (mocks will accept any method call)
        assert hasattr(table, "get_item")
        assert hasattr(logger, "info")
        assert hasattr(s3, "get_object")

    def test_set_and_get_default(self):
        """Test setting and getting default container."""
        mock_table = Mock()
        test_container = IrusContainer.create_test(table=mock_table)

        IrusContainer.set_default(test_container)
        default = IrusContainer.default()

        assert default == test_container
        assert default.table() == mock_table

    def test_default_creates_production_container(self):
        """Test that default() creates production container when none set."""
        # Reset default
        IrusContainer.set_default(None)
        IrusContainer._default_instance = None

        with patch.object(IrusContainer, "create_production") as mock_create:
            mock_container = Mock()
            mock_create.return_value = mock_container

            result = IrusContainer.default()

            mock_create.assert_called_once()
            assert result == mock_container

    def test_test_context_manager(self):
        """Test using container as context manager."""
        mock_table = Mock()
        original_default = IrusContainer._default_instance

        with IrusContainer.test_context(table=mock_table) as container:
            # Inside context, default should be the test container
            current_default = IrusContainer.default()
            assert current_default == container
            assert current_default.table() == mock_table

        # After context, default should be restored
        assert IrusContainer._default_instance == original_default

    def test_lazy_loading_production_table(self):
        """Test lazy loading of production table."""
        container = IrusContainer.create_production()

        with patch.object(container, "_get_session") as mock_session:
            mock_dynamodb = Mock()
            mock_table = Mock()
            mock_session.return_value.resource.return_value = mock_dynamodb
            mock_dynamodb.Table.return_value = mock_table

            with patch.dict(os.environ, {"TABLE_NAME": "prod-table"}):
                result = container.table()

                mock_session.assert_called_once()
                mock_session.return_value.resource.assert_called_once_with("dynamodb")
                mock_dynamodb.Table.assert_called_once_with("prod-table")
                assert result == mock_table

    def test_lazy_loading_production_logger(self):
        """Test lazy loading of production logger."""
        container = IrusContainer.create_production()

        with patch("aws_lambda_powertools.Logger") as mock_logger_class:
            mock_logger = Mock()
            mock_logger_class.return_value = mock_logger

            result = container.logger()

            mock_logger_class.assert_called_once()
            assert result == mock_logger

    def test_environment_variable_table_name(self):
        """Test reading table name from environment."""
        container = IrusContainer.create_production()

        with patch.dict(os.environ, {"TABLE_NAME": "my-table"}):
            result = container.table_name()
            assert result == "my-table"

    def test_environment_variable_table_name_missing(self):
        """Test error when table name environment variable missing."""
        container = IrusContainer.create_production()

        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(
                ValueError, match="TABLE_NAME environment variable is not set"
            ):
                container.table_name()

    def test_environment_variable_bucket_name(self):
        """Test reading bucket name from environment."""
        container = IrusContainer.create_production()

        with patch.dict(os.environ, {"BUCKET_NAME": "my-bucket"}):
            result = container.bucket_name()
            assert result == "my-bucket"

    def test_environment_variable_webhook_url(self):
        """Test reading webhook URL from environment."""
        container = IrusContainer.create_production()

        with patch.dict(
            os.environ, {"WEBHOOK_URL": "https://discord.com/api/webhooks/123"}
        ):
            result = container.webhook_url()
            assert result == "https://discord.com/api/webhooks/123"

    def test_image_contrast_factor_default(self):
        """Test image contrast factor with default value."""
        container = IrusContainer.create_production()

        with patch.dict(os.environ, {}, clear=True):
            result = container.image_contrast_factor()
            assert result == 1.5

    def test_image_contrast_factor_from_env(self):
        """Test image contrast factor from environment."""
        container = IrusContainer.create_production()

        with patch.dict(os.environ, {"IMAGE_CONTRAST_FACTOR": "2.0"}):
            result = container.image_contrast_factor()
            assert result == 2.0

    def test_image_saturation_factor_default(self):
        """Test image saturation factor with default value."""
        container = IrusContainer.create_production()

        with patch.dict(os.environ, {}, clear=True):
            result = container.image_saturation_factor()
            assert result == 0.7

    def test_caching_of_resources(self):
        """Test that resources are cached after first access."""
        mock_table = Mock()
        container = IrusContainer.create_test(table=mock_table)

        # First access
        table1 = container.table()
        # Second access
        table2 = container.table()

        # Should be the same instance
        assert table1 is table2
        assert table1 == mock_table

    def test_reset_clears_cache(self):
        """Test that reset clears cached resources."""
        container = IrusContainer.create_production()

        with patch.object(container, "_get_session") as mock_session:
            mock_dynamodb = Mock()
            mock_table1 = Mock()
            mock_table2 = Mock()
            mock_session.return_value.resource.return_value = mock_dynamodb
            mock_dynamodb.Table.side_effect = [mock_table1, mock_table2]

            with patch.dict(os.environ, {"TABLE_NAME": "test-table"}):
                # First access
                table1 = container.table()
                assert table1 == mock_table1

                # Reset and access again
                container.reset()
                table2 = container.table()
                assert table2 == mock_table2

                # Should be different instances
                assert table1 != table2

    def test_s3_resource_creation(self):
        """Test S3 resource creation."""
        container = IrusContainer.create_production()

        with patch.object(container, "_get_session") as mock_session:
            mock_s3_resource = Mock()
            mock_session.return_value.resource.return_value = mock_s3_resource

            result = container.s3_resource()

            mock_session.assert_called_once()
            mock_session.return_value.resource.assert_called_once_with("s3")
            assert result == mock_s3_resource

    def test_textract_creation(self):
        """Test Textract client creation."""
        container = IrusContainer.create_production()

        with patch.object(container, "_get_session") as mock_session:
            mock_textract = Mock()
            mock_session.return_value.client.return_value = mock_textract

            result = container.textract()

            mock_session.assert_called_once()
            mock_session.return_value.client.assert_called_once_with("textract")
            assert result == mock_textract

    def test_state_machine_creation(self):
        """Test Step Functions client creation."""
        container = IrusContainer.create_production()

        with patch.object(container, "_get_session") as mock_session:
            mock_stepfunctions = Mock()
            mock_session.return_value.client.return_value = mock_stepfunctions

            result = container.state_machine()

            mock_session.assert_called_once()
            mock_session.return_value.client.assert_called_once_with("stepfunctions")
            assert result == mock_stepfunctions
