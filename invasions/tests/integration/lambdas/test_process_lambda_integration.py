"""Integration tests for Process Lambda function."""

import json
import time
from unittest.mock import Mock, patch
from uuid import uuid4

import pytest
from aws_lambda_powertools.utilities.typing import LambdaContext
from irus.container import IrusContainer

from tests.integration.conftest import get_test_date_components


class TestProcessLambdaIntegration:
    """Integration test suite for Process Lambda function."""

    @pytest.fixture
    def lambda_context(self):
        """Create mock Lambda context."""
        context = Mock(spec=LambdaContext)
        context.function_name = "irus-dev-process"
        context.aws_request_id = f"test-{uuid4().hex}"
        context.remaining_time_in_millis = 300000  # 5 minutes for processing
        return context

    @pytest.fixture
    def test_invasion_setup(self, integration_container):
        """Set up a test invasion for processing."""
        date_components = get_test_date_components()

        # Create invasion in database
        from irus.repositories.invasion import InvasionRepository

        invasion_repo = InvasionRepository(integration_container)

        invasion = invasion_repo.create_from_user_input(
            day=date_components["day"],
            month=date_components["month"],
            year=date_components["year"],
            settlement="ef",
            win=True,
            notes="Integration test invasion for processing",
        )

        return invasion

    @pytest.fixture
    def process_event_ladder(self, test_invasion_setup):
        """Process Lambda event for ladder processing with real invasion."""
        return {
            "invasion": test_invasion_setup.name,
            "filename": "test_ladder.png",
            "url": "https://cdn.discordapp.com/attachments/123/456/test_ladder.png",
            "folder": f"invasions/{test_invasion_setup.name}/",
            "process": "Ladder",
        }

    @pytest.fixture
    def process_event_roster(self, test_invasion_setup):
        """Process Lambda event for roster processing with real invasion."""
        return {
            "invasion": test_invasion_setup.name,
            "filename": "test_roster.png",
            "url": "https://cdn.discordapp.com/attachments/123/456/test_roster.png",
            "folder": f"invasions/{test_invasion_setup.name}/",
            "process": "Roster",
        }

    @patch("src.process.process.pool_mgr")
    def test_successful_ladder_processing_integration(
        self,
        mock_pool,
        integration_container,
        lambda_context,
        process_event_ladder,
        test_invasion_setup,
    ):
        """Test successful ladder processing with real AWS resources."""
        # Arrange
        IrusContainer.set_default(integration_container)

        # Mock HTTP download to return fake PNG data
        mock_response = Mock()
        mock_response.read.return_value = b"\x89PNG\r\n\x1a\n" + b"fake_png_data" * 100
        mock_pool.request.return_value = mock_response

        # Mock the OCR processing since we don't have real image processing in tests
        mock_ladder = Mock()
        mock_ladder.str.return_value = "Processed 25 ranks, 15 members from test image"

        # Import after setting up container
        from src.process.process import lambda_handler

        with patch(
            "src.process.process.IrusLadder.from_ladder_image", return_value=mock_ladder
        ):
            # Act
            response = lambda_handler(process_event_ladder, lambda_context)

        # Assert
        assert response["statusCode"] == 200
        response_body = json.loads(response["body"])
        assert "Successful download of test_ladder.png" in response_body
        assert "Processed 25 ranks, 15 members" in response_body

        # Verify file was uploaded to S3
        s3_resource = integration_container.s3_resource()
        bucket_name = integration_container.bucket_name()

        # Check if file exists in S3 (it should have been uploaded)
        try:
            s3_resource.Object(
                bucket_name, f"invasions/{test_invasion_setup.name}/test_ladder.png"
            ).load()
            file_exists = True
        except s3_resource.meta.client.exceptions.NoSuchKey:
            file_exists = False

        assert file_exists, "File should have been uploaded to S3"

    @patch("src.process.process.pool_mgr")
    def test_successful_roster_processing_integration(
        self,
        mock_pool,
        integration_container,
        lambda_context,
        process_event_roster,
        test_invasion_setup,
    ):
        """Test successful roster processing with real AWS resources."""
        # Arrange
        IrusContainer.set_default(integration_container)

        # Mock HTTP download
        mock_response = Mock()
        mock_response.read.return_value = (
            b"\x89PNG\r\n\x1a\n" + b"fake_roster_data" * 100
        )
        mock_pool.request.return_value = mock_response

        # Mock the OCR processing
        mock_ladder = Mock()
        mock_ladder.str.return_value = "Processed roster with 20 members"

        # Import after setting up container
        from src.process.process import lambda_handler

        with patch(
            "src.process.process.IrusLadder.from_roster_image", return_value=mock_ladder
        ):
            # Act
            response = lambda_handler(process_event_roster, lambda_context)

        # Assert
        assert response["statusCode"] == 200
        response_body = json.loads(response["body"])
        assert "Successful download of test_roster.png" in response_body
        assert "Processed roster with 20 members" in response_body

    def test_invalid_file_type_integration(
        self, integration_container, lambda_context, process_event_ladder
    ):
        """Test handling of invalid file types with real container."""
        # Arrange
        IrusContainer.set_default(integration_container)
        process_event_ladder["filename"] = "document.pdf"

        # Import after setting up container
        from src.process.process import lambda_handler

        # Act
        response = lambda_handler(process_event_ladder, lambda_context)

        # Assert
        assert response["statusCode"] == 400
        response_body = json.loads(response["body"])
        assert "not a PNG file" in response_body

    @patch("src.process.process.pool_mgr")
    def test_download_failure_integration(
        self, mock_pool, integration_container, lambda_context, process_event_ladder
    ):
        """Test handling of download failures with real S3."""
        # Arrange
        IrusContainer.set_default(integration_container)

        # Mock HTTP request to fail
        mock_pool.request.side_effect = Exception("Network timeout")

        # Import after setting up container
        from src.process.process import lambda_handler

        # Act
        response = lambda_handler(process_event_ladder, lambda_context)

        # Assert
        assert response["statusCode"] == 400
        response_body = json.loads(response["body"])
        assert "Error downloading" in response_body
        assert "Network timeout" in response_body

    def test_invasion_not_found_integration(
        self, integration_container, lambda_context
    ):
        """Test handling when invasion doesn't exist in real DynamoDB."""
        # Arrange
        IrusContainer.set_default(integration_container)

        # Create event with non-existent invasion
        nonexistent_event = {
            "invasion": "99999999-nonexistent",
            "filename": "test.png",
            "url": "https://example.com/test.png",
            "folder": "invasions/99999999-nonexistent/",
            "process": "Ladder",
        }

        # Import after setting up container
        from src.process.process import lambda_handler

        with patch("src.process.process.pool_mgr"):
            # Act
            response = lambda_handler(nonexistent_event, lambda_context)

        # Assert
        assert response["statusCode"] == 400
        response_body = json.loads(response["body"])
        assert "Error importing ladder" in response_body

    @patch("src.process.process.pool_mgr")
    def test_s3_upload_with_real_bucket(
        self,
        mock_pool,
        integration_container,
        lambda_context,
        process_event_ladder,
        test_invasion_setup,
    ):
        """Test S3 upload functionality with real bucket."""
        # Arrange
        IrusContainer.set_default(integration_container)

        # Mock HTTP download with small PNG data
        mock_response = Mock()
        mock_response.read.return_value = b"\x89PNG\r\n\x1a\n" + b"test_data"
        mock_pool.request.return_value = mock_response

        # Import after setting up container
        from src.process.process import lambda_handler

        # Mock the OCR processing to avoid complexity
        with patch(
            "src.process.process.IrusLadder.from_ladder_image"
        ) as mock_ladder_create:
            mock_ladder = Mock()
            mock_ladder.str.return_value = "Test processing complete"
            mock_ladder_create.return_value = mock_ladder

            # Act
            response = lambda_handler(process_event_ladder, lambda_context)

        # Assert successful upload
        assert response["statusCode"] == 200

        # Verify file was actually uploaded to S3
        s3_resource = integration_container.s3_resource()
        bucket_name = integration_container.bucket_name()
        expected_key = f"invasions/{test_invasion_setup.name}/test_ladder.png"

        # Check file exists and has content
        try:
            obj = s3_resource.Object(bucket_name, expected_key)
            obj.load()
            content = obj.get()["Body"].read()
            assert len(content) > 0
            assert content.startswith(b"\x89PNG")  # PNG header
        except Exception as e:
            pytest.fail(f"File should exist in S3: {e}")

    @patch("src.process.process.pool_mgr")
    def test_member_list_integration(
        self,
        mock_pool,
        integration_container,
        lambda_context,
        process_event_ladder,
        test_invasion_setup,
    ):
        """Test that member list is properly loaded from real DynamoDB."""
        # Arrange
        IrusContainer.set_default(integration_container)

        # Create a test member first
        timestamp = int(time.time())
        unique_id = uuid4().hex[:8]
        test_player = f"TestPlayer-{timestamp}-{unique_id}"

        from irus.repositories.member import MemberRepository

        member_repo = MemberRepository(integration_container)
        date_components = get_test_date_components()

        member_repo.create_from_user_input(
            player=test_player,
            day=date_components["day"],
            month=date_components["month"],
            year=date_components["year"],
            faction="yellow",
            admin=False,
            salary=True,
        )

        # Mock HTTP download
        mock_response = Mock()
        mock_response.read.return_value = b"\x89PNG\r\n\x1a\n" + b"test_data"
        mock_pool.request.return_value = mock_response

        # Import after setting up container
        from src.process.process import lambda_handler

        # Capture the member list passed to ladder processing
        captured_member_list = None

        def capture_member_list(invasion, member_list, bucket, key):
            nonlocal captured_member_list
            captured_member_list = member_list
            mock_ladder = Mock()
            mock_ladder.str.return_value = "Processing complete"
            return mock_ladder

        with patch(
            "src.process.process.IrusLadder.from_ladder_image",
            side_effect=capture_member_list,
        ):
            # Act
            response = lambda_handler(process_event_ladder, lambda_context)

        # Assert
        assert response["statusCode"] == 200
        assert captured_member_list is not None

        # Verify our test member is in the member list
        member_found = False
        for member in captured_member_list.members:
            if member.player == test_player:
                member_found = True
                break

        assert member_found, f"Test member {test_player} should be in member list"

    @patch("src.process.process.pool_mgr")
    def test_bucket_name_from_integration_container(
        self,
        mock_pool,
        integration_container,
        lambda_context,
        process_event_ladder,
        test_invasion_setup,
    ):
        """Test that bucket name comes from integration container configuration."""
        # Arrange
        IrusContainer.set_default(integration_container)

        # Mock HTTP download
        mock_response = Mock()
        mock_response.read.return_value = b"\x89PNG\r\n\x1a\n" + b"test_data"
        mock_pool.request.return_value = mock_response

        # Import after setting up container
        from src.process.process import lambda_handler

        # Capture bucket name used in processing
        captured_bucket_name = None

        def capture_bucket_name(invasion, member_list, bucket_name, key):
            nonlocal captured_bucket_name
            captured_bucket_name = bucket_name
            mock_ladder = Mock()
            mock_ladder.str.return_value = "Processing complete"
            return mock_ladder

        with patch(
            "src.process.process.IrusLadder.from_ladder_image",
            side_effect=capture_bucket_name,
        ):
            # Act
            response = lambda_handler(process_event_ladder, lambda_context)

        # Assert
        assert response["statusCode"] == 200
        assert captured_bucket_name is not None

        # Verify bucket name matches container configuration
        expected_bucket = integration_container.bucket_name()
        assert captured_bucket_name == expected_bucket
