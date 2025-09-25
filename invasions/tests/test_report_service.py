"""Tests for IrusReport service class."""

from unittest.mock import Mock, patch

import pytest
from botocore.exceptions import ClientError
from irus.container import IrusContainer
from irus.models.invasion import IrusInvasion
from irus.models.ladder import IrusLadder
from irus.models.ladderrank import IrusLadderRank
from irus.report import IrusReport


class TestIrusReport:
    """Test suite for IrusReport class."""

    @pytest.fixture
    def mock_s3(self):
        """Create mock S3 client."""
        mock_s3 = Mock()
        mock_s3.put_object.return_value = {"ETag": "test-etag"}
        mock_s3.generate_presigned_url.return_value = (
            "https://test-bucket.s3.amazonaws.com/test-key?presigned=true"
        )
        return mock_s3

    @pytest.fixture
    def container(self, mock_s3):
        """Create test container with mocked dependencies."""
        mock_container = IrusContainer.create_test()
        mock_container.s3 = Mock(return_value=mock_s3)
        mock_container.bucket_name = Mock(return_value="test-bucket")
        return mock_container

    @pytest.fixture
    def sample_ladder(self):
        """Create sample ladder for testing."""
        invasion = IrusInvasion(
            name="20240301-bw",
            settlement="bw",
            win=True,
            date=20240301,
            year=2024,
            month=3,
            day=1,
        )

        ranks = [
            IrusLadderRank(
                invasion_name="20240301-bw",
                rank="01",
                player="Player1",
                score=1500,
                kills=25,
                assists=10,
                deaths=5,
                heals=2000,
                damage=50000,
                member=True,
                ladder=True,
                adjusted=False,
                error=False,
            ),
            IrusLadderRank(
                invasion_name="20240301-bw",
                rank="02",
                player="Player2",
                score=1400,
                kills=20,
                assists=8,
                deaths=7,
                heals=1800,
                damage=45000,
                member=True,
                ladder=True,
                adjusted=False,
                error=False,
            ),
        ]

        return IrusLadder(invasion_name=invasion.name, ranks=ranks)

    def test_init_success(self, container, mock_s3):
        """Test IrusReport initialization and upload."""
        report_content = "test,report,content\n1,2,3"

        report = IrusReport("test-path/", "test-report.csv", report_content, container)

        # Verify properties set correctly
        assert report.target == "test-path/test-report.csv"
        assert (
            report.presigned
            == "https://test-bucket.s3.amazonaws.com/test-key?presigned=true"
        )
        assert (
            "Report can be downloaded from **[here](https://test-bucket.s3.amazonaws.com/test-key?presigned=true)** for one hour."
            in report.msg
        )

        # Verify S3 operations called
        mock_s3.put_object.assert_called_once_with(
            Bucket="test-bucket", Key="test-path/test-report.csv", Body=report_content
        )
        mock_s3.generate_presigned_url.assert_called_once_with(
            "get_object",
            Params={"Bucket": "test-bucket", "Key": "test-path/test-report.csv"},
            ExpiresIn=3600,
        )

    def test_init_default_container(self, mock_s3):
        """Test IrusReport initialization with default container."""
        with patch.object(IrusContainer, "default") as mock_default:
            mock_container = Mock(spec=IrusContainer)
            mock_container.logger.return_value = Mock()
            mock_container.s3.return_value = mock_s3
            mock_container.bucket_name.return_value = "default-bucket"
            mock_default.return_value = mock_container

            report = IrusReport("path/", "file.csv", "content")

            assert report._container is mock_container
            mock_default.assert_called_once()

    def test_init_s3_put_object_error(self, container, mock_s3):
        """Test handling of S3 put_object errors."""
        error = ClientError(
            error_response={
                "Error": {"Code": "AccessDenied", "Message": "Access Denied"}
            },
            operation_name="PutObject",
        )
        mock_s3.put_object.side_effect = error

        with pytest.raises(ClientError):
            IrusReport("test-path/", "test-report.csv", "content", container)

    def test_init_presigned_url_error(self, container, mock_s3):
        """Test handling of presigned URL generation errors."""
        error = ClientError(
            error_response={
                "Error": {"Code": "InvalidRequest", "Message": "Invalid request"}
            },
            operation_name="GeneratePresignedUrl",
        )
        mock_s3.generate_presigned_url.side_effect = error

        with pytest.raises(ClientError):
            IrusReport("test-path/", "test-report.csv", "content", container)

    def test_from_invasion_success(self, container, mock_s3):
        """Test creating report from invasion ladder data."""
        # Create a mock ladder with required attributes
        sample_ladder = Mock()
        sample_ladder.invasion.name = "20240301-bw"
        sample_ladder.csv.return_value = "invasion,csv,data\n1,2,3"

        report = IrusReport.from_invasion(sample_ladder, container)

        # Verify correct path and filename
        assert report.target == "reports/invasion/20240301-bw.csv"

        # Verify S3 upload called with CSV data
        mock_s3.put_object.assert_called_once_with(
            Bucket="test-bucket",
            Key="reports/invasion/20240301-bw.csv",
            Body="invasion,csv,data\n1,2,3",
        )
        sample_ladder.csv.assert_called_once()

    def test_from_invasion_default_container(self, mock_s3):
        """Test from_invasion with default container."""
        # Create a mock ladder with required attributes
        sample_ladder = Mock()
        sample_ladder.invasion.name = "20240301-bw"
        sample_ladder.csv.return_value = "csv,data"

        with patch.object(IrusContainer, "default") as mock_default:
            mock_container = Mock(spec=IrusContainer)
            mock_container.logger.return_value = Mock()
            mock_container.s3.return_value = mock_s3
            mock_container.bucket_name.return_value = "default-bucket"
            mock_default.return_value = mock_container

            report = IrusReport.from_invasion(sample_ladder)

            assert report._container is mock_container
            mock_default.assert_called_once()

    def test_from_members_success(self, container, mock_s3):
        """Test creating report from member data."""
        timestamp = 1709251200  # March 1, 2024
        report_content = "player,faction,start\nPlayer1,yellow,20240101"

        report = IrusReport.from_members(timestamp, report_content, container)

        # Verify correct path and filename
        assert report.target == "reports/members/1709251200.csv"

        # Verify S3 upload called with member data
        mock_s3.put_object.assert_called_once_with(
            Bucket="test-bucket",
            Key="reports/members/1709251200.csv",
            Body=report_content,
        )

    def test_from_members_default_container(self, mock_s3):
        """Test from_members with default container."""
        with patch.object(IrusContainer, "default") as mock_default:
            mock_container = Mock(spec=IrusContainer)
            mock_container.logger.return_value = Mock()
            mock_container.s3.return_value = mock_s3
            mock_container.bucket_name.return_value = "default-bucket"
            mock_default.return_value = mock_container

            report = IrusReport.from_members(123456, "csv,data")

            assert report._container is mock_container
            mock_default.assert_called_once()

    def test_from_month_success(self, container, mock_s3):
        """Test creating report from monthly data."""
        # Create mock month object
        mock_month = Mock()
        mock_month.month = "202403"
        mock_month.csv2.return_value = "month,csv,data\n202403,stats,here"

        gold_amount = 50000
        report = IrusReport.from_month(mock_month, gold_amount, container)

        # Verify correct path and filename
        assert report.target == "reports/month/202403.csv"

        # Verify month's csv2 method called with gold amount
        mock_month.csv2.assert_called_once_with(gold_amount)

        # Verify S3 upload called with monthly data
        mock_s3.put_object.assert_called_once_with(
            Bucket="test-bucket",
            Key="reports/month/202403.csv",
            Body="month,csv,data\n202403,stats,here",
        )

    def test_from_month_default_container(self, mock_s3):
        """Test from_month with default container."""
        mock_month = Mock()
        mock_month.month = "202403"
        mock_month.csv2.return_value = "csv,data"

        with patch.object(IrusContainer, "default") as mock_default:
            mock_container = Mock(spec=IrusContainer)
            mock_container.logger.return_value = Mock()
            mock_container.s3.return_value = mock_s3
            mock_container.bucket_name.return_value = "default-bucket"
            mock_default.return_value = mock_container

            report = IrusReport.from_month(mock_month, 10000)

            assert report._container is mock_container
            mock_default.assert_called_once()

    def test_factory_methods_logging(self, container, mock_s3):
        """Test that factory methods perform appropriate logging."""
        # Test from_invasion logging
        sample_ladder = Mock()
        sample_ladder.invasion.name = "20240301-bw"
        sample_ladder.csv.return_value = "csv,data"

        IrusReport.from_invasion(sample_ladder, container)

        # Verify logger was called for debug
        assert container.logger().debug.call_count >= 1

        # Reset mock and test from_members logging
        container.logger().debug.reset_mock()
        IrusReport.from_members(123456, "member,data", container)

        # Verify logger was called for debug
        assert container.logger().debug.call_count >= 1

        # Reset mock and test from_month logging
        container.logger().debug.reset_mock()
        mock_month = Mock()
        mock_month.month = "202403"
        mock_month.csv2.return_value = "month,data"

        IrusReport.from_month(mock_month, 10000, container)

        # Verify logger was called for debug
        assert container.logger().debug.call_count >= 1

    def test_presigned_url_expiration(self, container, mock_s3):
        """Test that presigned URLs are generated with correct expiration."""
        IrusReport("test-path/", "test-report.csv", "content", container)

        # Verify presigned URL called with 1 hour expiration
        mock_s3.generate_presigned_url.assert_called_once_with(
            "get_object",
            Params={"Bucket": "test-bucket", "Key": "test-path/test-report.csv"},
            ExpiresIn=3600,
        )

    def test_message_format(self, container, mock_s3):
        """Test that message is formatted correctly."""
        presigned_url = "https://example.com/presigned-url"
        mock_s3.generate_presigned_url.return_value = presigned_url

        report = IrusReport("test-path/", "test-report.csv", "content", container)

        expected_msg = (
            f"Report can be downloaded from **[here]({presigned_url})** for one hour."
        )
        assert report.msg == expected_msg

    def test_path_concatenation(self, container, mock_s3):
        """Test that path and name are concatenated correctly."""
        path = "reports/test/"
        name = "test-file.csv"

        report = IrusReport(path, name, "content", container)

        assert report.target == "reports/test/test-file.csv"

    def test_empty_content_handling(self, container, mock_s3):
        """Test handling of empty report content."""
        report = IrusReport("path/", "empty.csv", "", container)

        # Should still upload empty content
        mock_s3.put_object.assert_called_once_with(
            Bucket="test-bucket", Key="path/empty.csv", Body=""
        )

        # Should still generate presigned URL
        assert report.presigned is not None
        assert report.msg is not None

    def test_special_characters_in_path(self, container, mock_s3):
        """Test handling of special characters in path and name."""
        path = "reports/test-data/"
        name = "report_2024-03-01_final.csv"

        report = IrusReport(path, name, "content", container)

        expected_key = "reports/test-data/report_2024-03-01_final.csv"
        assert report.target == expected_key

        mock_s3.put_object.assert_called_once_with(
            Bucket="test-bucket", Key=expected_key, Body="content"
        )
