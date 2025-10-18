"""Unit tests for Process Lambda function."""

import json
from unittest.mock import Mock, patch

import pytest
from aws_lambda_powertools.utilities.typing import LambdaContext
from irus.container import IrusContainer


class TestProcessLambda:
    """Test suite for Process Lambda function."""

    @pytest.fixture
    def container(self):
        """Create test container with mocked dependencies."""
        return IrusContainer.create_unit()

    @pytest.fixture
    def lambda_context(self):
        """Create mock Lambda context."""
        context = Mock(spec=LambdaContext)
        context.function_name = "test-process-function"
        context.aws_request_id = "test-request-id"
        context.remaining_time_in_millis = 30000
        return context

    @pytest.fixture
    def process_event_ladder(self):
        """Process Lambda event for ladder processing."""
        return {
            "invasion": "99151228-ef",
            "filename": "ladder.png",
            "url": "https://cdn.discordapp.com/attachments/123/456/ladder.png",
            "folder": "invasions/99151228-ef/",
            "process": "Ladder",
        }

    @pytest.fixture
    def process_event_roster(self):
        """Process Lambda event for roster processing."""
        return {
            "invasion": "99151228-ef",
            "filename": "roster.png",
            "url": "https://cdn.discordapp.com/attachments/123/456/roster.png",
            "folder": "invasions/99151228-ef/",
            "process": "Roster",
        }

    @patch("src.process.handler.IrusContainer.default")
    @patch("src.process.handler.pool_mgr")
    def test_successful_ladder_processing(
        self, mock_pool, mock_container, container, lambda_context, process_event_ladder
    ):
        """Test successful ladder image processing."""
        # Arrange
        mock_container.return_value = container

        # Mock S3 upload
        mock_s3 = container.s3()
        mock_s3.upload_fileobj.return_value = None

        # Mock HTTP download
        mock_response = Mock()
        mock_pool.request.return_value = mock_response

        # Mock invasion and ladder processing
        mock_invasion = Mock()
        mock_invasion.name = "99151228-ef"

        mock_ladder = Mock()
        mock_ladder.str.return_value = "Processed 50 ranks, 25 members"

        # Import after setting up mocks
        from src.process.handler import lambda_handler

        with patch(
            "src.process.handler.IrusInvasion.from_table", return_value=mock_invasion
        ):
            with patch("src.process.handler.IrusMemberList"):
                with patch(
                    "src.process.handler.IrusLadder.from_ladder_image",
                    return_value=mock_ladder,
                ):
                    # Act
                    response = lambda_handler(process_event_ladder, lambda_context)

        # Assert
        assert response["statusCode"] == 200
        response_body = json.loads(response["body"])
        assert "Successful download of ladder.png" in response_body
        assert "Processed 50 ranks, 25 members" in response_body

        # Verify S3 upload was called
        mock_s3.upload_fileobj.assert_called_once()

    @patch("src.process.handler.IrusContainer.default")
    @patch("src.process.handler.pool_mgr")
    def test_successful_roster_processing(
        self, mock_pool, mock_container, container, lambda_context, process_event_roster
    ):
        """Test successful roster image processing."""
        # Arrange
        mock_container.return_value = container

        # Mock S3 upload
        mock_s3 = container.s3()
        mock_s3.upload_fileobj.return_value = None

        # Mock HTTP download
        mock_response = Mock()
        mock_pool.request.return_value = mock_response

        # Mock invasion and ladder processing
        mock_invasion = Mock()
        mock_invasion.name = "99151228-ef"

        mock_ladder = Mock()
        mock_ladder.str.return_value = "Processed roster with 30 members"

        # Import after setting up mocks
        from src.process.handler import lambda_handler

        with patch(
            "src.process.handler.IrusInvasion.from_table", return_value=mock_invasion
        ):
            with patch("src.process.handler.IrusMemberList"):
                with patch(
                    "src.process.handler.IrusLadder.from_roster_image",
                    return_value=mock_ladder,
                ):
                    # Act
                    response = lambda_handler(process_event_roster, lambda_context)

        # Assert
        assert response["statusCode"] == 200
        response_body = json.loads(response["body"])
        assert "Successful download of roster.png" in response_body
        assert "Processed roster with 30 members" in response_body

    @patch("src.process.handler.IrusContainer.default")
    def test_invalid_file_type(
        self, mock_container, container, lambda_context, process_event_ladder
    ):
        """Test handling of invalid file types."""
        # Arrange
        mock_container.return_value = container
        process_event_ladder["filename"] = "document.pdf"

        # Import after setting up mocks
        from src.process.handler import lambda_handler

        # Act
        response = lambda_handler(process_event_ladder, lambda_context)

        # Assert
        assert response["statusCode"] == 400
        response_body = json.loads(response["body"])
        assert "not a PNG file" in response_body

    @patch("src.process.handler.IrusContainer.default")
    @patch("src.process.handler.pool_mgr")
    def test_download_failure(
        self, mock_pool, mock_container, container, lambda_context, process_event_ladder
    ):
        """Test handling of download failures."""
        # Arrange
        mock_container.return_value = container
        mock_s3 = container.s3()
        mock_s3.upload_fileobj.side_effect = Exception("Network error")

        # Import after setting up mocks
        from src.process.handler import lambda_handler

        # Act
        response = lambda_handler(process_event_ladder, lambda_context)

        # Assert
        assert response["statusCode"] == 400
        response_body = json.loads(response["body"])
        assert "Error downloading" in response_body

    @patch("src.process.handler.IrusContainer.default")
    @patch("src.process.handler.pool_mgr")
    def test_processing_failure(
        self, mock_pool, mock_container, container, lambda_context, process_event_ladder
    ):
        """Test handling of image processing failures."""
        # Arrange
        mock_container.return_value = container

        # Mock successful download
        mock_s3 = container.s3()
        mock_s3.upload_fileobj.return_value = None
        mock_response = Mock()
        mock_pool.request.return_value = mock_response

        # Mock invasion retrieval
        mock_invasion = Mock()
        mock_invasion.name = "99151228-ef"

        # Import after setting up mocks
        from src.process.handler import lambda_handler

        with patch(
            "src.process.handler.IrusInvasion.from_table", return_value=mock_invasion
        ):
            with patch("src.process.handler.IrusMemberList"):
                with patch(
                    "src.process.handler.IrusLadder.from_ladder_image",
                    side_effect=Exception("OCR failed"),
                ):
                    # Act
                    response = lambda_handler(process_event_ladder, lambda_context)

        # Assert
        assert response["statusCode"] == 400
        response_body = json.loads(response["body"])
        assert "Error importing ladder" in response_body
        assert "OCR failed" in response_body

    @patch("src.process.handler.IrusContainer.default")
    @patch("src.process.handler.pool_mgr")
    def test_unknown_process_type(
        self, mock_pool, mock_container, container, lambda_context, process_event_ladder
    ):
        """Test handling of unknown process types."""
        # Arrange
        mock_container.return_value = container
        process_event_ladder["process"] = "Unknown"

        # Mock successful download
        mock_s3 = container.s3()
        mock_s3.upload_fileobj.return_value = None
        mock_response = Mock()
        mock_pool.request.return_value = mock_response

        # Mock invasion retrieval
        mock_invasion = Mock()
        mock_invasion.name = "99151228-ef"

        # Import after setting up mocks
        from src.process.handler import lambda_handler

        with patch(
            "src.process.handler.IrusInvasion.from_table", return_value=mock_invasion
        ):
            with patch("src.process.handler.IrusMemberList"):
                # Act
                response = lambda_handler(process_event_ladder, lambda_context)

        # Assert
        assert response["statusCode"] == 400
        response_body = json.loads(response["body"])
        assert "Unknown process" in response_body

    @patch("src.process.handler.IrusContainer.default")
    def test_invasion_not_found(
        self, mock_container, container, lambda_context, process_event_ladder
    ):
        """Test handling when invasion is not found."""
        # Arrange
        mock_container.return_value = container

        # Mock successful download
        mock_s3 = container.s3()
        mock_s3.upload_fileobj.return_value = None

        # Import after setting up mocks
        from src.process.handler import lambda_handler

        with patch("src.process.handler.pool_mgr"):
            with patch(
                "src.process.handler.IrusInvasion.from_table",
                side_effect=ValueError("Invasion not found"),
            ):
                # Act
                response = lambda_handler(process_event_ladder, lambda_context)

        # Assert
        assert response["statusCode"] == 400
        response_body = json.loads(response["body"])
        assert "Error importing ladder" in response_body

    @patch("src.process.handler.IrusContainer.default")
    @patch("src.process.handler.pool_mgr")
    def test_bucket_name_from_container(
        self, mock_pool, mock_container, container, lambda_context, process_event_ladder
    ):
        """Test that bucket name is retrieved from container."""
        # Arrange
        mock_container.return_value = container
        container.bucket_name.return_value = "test-bucket"

        # Mock successful processing
        mock_s3 = container.s3()
        mock_s3.upload_fileobj.return_value = None
        mock_response = Mock()
        mock_pool.request.return_value = mock_response

        mock_invasion = Mock()
        mock_invasion.name = "99151228-ef"
        mock_ladder = Mock()
        mock_ladder.str.return_value = "Success"

        # Import after setting up mocks
        from src.process.handler import lambda_handler

        with patch(
            "src.process.handler.IrusInvasion.from_table", return_value=mock_invasion
        ):
            with patch("src.process.handler.IrusMemberList"):
                with patch(
                    "src.process.handler.IrusLadder.from_ladder_image",
                    return_value=mock_ladder,
                ) as mock_ladder_create:
                    # Act
                    response = lambda_handler(process_event_ladder, lambda_context)

        # Assert
        assert response["statusCode"] == 200
        # Verify bucket name was passed to ladder processing
        mock_ladder_create.assert_called_once()
        call_args = mock_ladder_create.call_args[0]
        assert call_args[2] == "test-bucket"  # bucket_name parameter
