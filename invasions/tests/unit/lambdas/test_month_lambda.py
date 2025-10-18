"""Unit tests for Month Lambda function."""

from unittest.mock import Mock, patch

import pytest
from aws_lambda_powertools.utilities.typing import LambdaContext
from irus.container import IrusContainer


class TestMonthLambda:
    """Test suite for Month Lambda function."""

    @pytest.fixture
    def container(self):
        """Create test container with mocked dependencies."""
        return IrusContainer.create_unit()

    @pytest.fixture
    def lambda_context(self):
        """Create mock Lambda context."""
        context = Mock(spec=LambdaContext)
        context.function_name = "test-month-function"
        context.aws_request_id = "test-request-id"
        context.remaining_time_in_millis = 30000
        return context

    @pytest.fixture
    def month_event(self):
        """Month Lambda event structure."""
        return {"month": "202403"}

    @pytest.fixture
    def month_event_current_year(self):
        """Month Lambda event for current year."""
        return {"month": "202412"}

    @patch("src.month.month.IrusContainer.default")
    def test_successful_month_report(
        self, mock_container, container, lambda_context, month_event
    ):
        """Test successful monthly report generation."""
        # Arrange
        mock_container.return_value = container

        mock_month_stats = Mock()
        mock_month_stats.invasions = 15
        mock_month_stats.active = 20
        mock_month_stats.participation = 300
        mock_month_stats.report = ["member1", "member2", "member3"]

        mock_report = Mock()
        mock_report.msg = "https://s3.amazonaws.com/bucket/monthly-report.csv"

        # Import after setting up mocks
        from src.month.month import lambda_handler

        with patch(
            "src.month.month.IrusMonth.from_invasion_stats",
            return_value=mock_month_stats,
        ):
            with patch(
                "src.month.month.IrusReport.from_month", return_value=mock_report
            ):
                # Act
                response = lambda_handler(month_event, lambda_context)

        # Assert
        assert response["statusCode"] == 200
        body = response["body"]
        assert body["month"] == "202403"
        assert body["invasions"] == 15
        assert body["active"] == 20
        assert body["members"] == 3
        assert body["participation"] == 300
        assert "s3.amazonaws.com" in body["url"]

    @patch("src.month.month.IrusContainer.default")
    def test_month_parsing_from_event(
        self, mock_container, container, lambda_context, month_event
    ):
        """Test correct parsing of month and year from event."""
        # Arrange
        mock_container.return_value = container

        mock_month_stats = Mock()
        mock_month_stats.invasions = 5
        mock_month_stats.active = 10
        mock_month_stats.participation = 50
        mock_month_stats.report = ["member1"]

        mock_report = Mock()
        mock_report.msg = "https://s3.amazonaws.com/bucket/report.csv"

        # Import after setting up mocks
        from src.month.month import lambda_handler

        with patch(
            "src.month.month.IrusMonth.from_invasion_stats",
            return_value=mock_month_stats,
        ) as mock_from_stats:
            with patch(
                "src.month.month.IrusReport.from_month", return_value=mock_report
            ):
                # Act
                response = lambda_handler(month_event, lambda_context)

        # Assert
        assert response["statusCode"] == 200
        # Verify month and year were parsed correctly (202403 -> month=3, year=2024)
        mock_from_stats.assert_called_once_with(month=3, year=2024)

    @patch("src.month.month.IrusContainer.default")
    def test_zero_invasions_scenario(
        self, mock_container, container, lambda_context, month_event
    ):
        """Test scenario with zero invasions in month."""
        # Arrange
        mock_container.return_value = container

        mock_month_stats = Mock()
        mock_month_stats.invasions = 0
        mock_month_stats.active = 0
        mock_month_stats.participation = 0
        mock_month_stats.report = []

        mock_report = Mock()
        mock_report.msg = "https://s3.amazonaws.com/bucket/empty-report.csv"

        # Import after setting up mocks
        from src.month.month import lambda_handler

        with patch(
            "src.month.month.IrusMonth.from_invasion_stats",
            return_value=mock_month_stats,
        ):
            with patch(
                "src.month.month.IrusReport.from_month", return_value=mock_report
            ):
                # Act
                response = lambda_handler(month_event, lambda_context)

        # Assert
        assert response["statusCode"] == 200
        body = response["body"]
        assert body["invasions"] == 0
        assert body["active"] == 0
        assert body["members"] == 0
        assert body["participation"] == 0

    @patch("src.month.month.IrusContainer.default")
    @patch("src.month.month.IrusMonth.from_invasion_stats")
    def test_month_stats_error(
        self, mock_from_stats, mock_container, container, lambda_context, month_event
    ):
        """Test handling of month statistics generation errors."""
        # Arrange
        mock_container.return_value = container
        mock_from_stats.side_effect = ValueError("No data for month")

        # Import after setting up mocks
        from src.month.month import lambda_handler

        # Act
        response = lambda_handler(month_event, lambda_context)

        # Assert
        assert response["statusCode"] == 500
        assert "Error generating report" in response["body"]["url"]
        assert "202403" in response["body"]["url"]

    @patch("src.month.month.IrusContainer.default")
    def test_report_generation_error(
        self, mock_container, container, lambda_context, month_event
    ):
        """Test handling of report generation errors."""
        # Arrange
        mock_container.return_value = container

        mock_month_stats = Mock()
        mock_month_stats.invasions = 10
        mock_month_stats.active = 15
        mock_month_stats.participation = 150
        mock_month_stats.report = ["member1", "member2"]

        # Import after setting up mocks
        from src.month.month import lambda_handler

        with patch(
            "src.month.month.IrusMonth.from_invasion_stats",
            return_value=mock_month_stats,
        ):
            with patch(
                "src.month.month.IrusReport.from_month",
                side_effect=Exception("S3 upload failed"),
            ):
                # Act
                response = lambda_handler(month_event, lambda_context)

        # Assert
        assert response["statusCode"] == 500
        assert "Error generating report" in response["body"]["url"]
        assert "S3 upload failed" in response["body"]["url"]

    @patch("src.month.month.IrusContainer.default")
    def test_high_activity_month(
        self, mock_container, container, lambda_context, month_event
    ):
        """Test month with high activity levels."""
        # Arrange
        mock_container.return_value = container

        mock_month_stats = Mock()
        mock_month_stats.invasions = 25
        mock_month_stats.active = 45
        mock_month_stats.participation = 800
        mock_month_stats.report = [f"member{i}" for i in range(1, 46)]  # 45 members

        mock_report = Mock()
        mock_report.msg = "https://s3.amazonaws.com/bucket/high-activity-report.csv"

        # Import after setting up mocks
        from src.month.month import lambda_handler

        with patch(
            "src.month.month.IrusMonth.from_invasion_stats",
            return_value=mock_month_stats,
        ):
            with patch(
                "src.month.month.IrusReport.from_month", return_value=mock_report
            ):
                # Act
                response = lambda_handler(month_event, lambda_context)

        # Assert
        assert response["statusCode"] == 200
        body = response["body"]
        assert body["invasions"] == 25
        assert body["active"] == 45
        assert body["members"] == 45
        assert body["participation"] == 800

    @patch("src.month.month.IrusContainer.default")
    def test_response_template_structure(
        self, mock_container, container, lambda_context, month_event
    ):
        """Test that response follows expected template structure."""
        # Arrange
        mock_container.return_value = container

        mock_month_stats = Mock()
        mock_month_stats.invasions = 12
        mock_month_stats.active = 18
        mock_month_stats.participation = 200
        mock_month_stats.report = ["member1", "member2"]

        mock_report = Mock()
        mock_report.msg = "https://s3.amazonaws.com/bucket/report.csv"

        # Import after setting up mocks
        from src.month.month import lambda_handler

        with patch(
            "src.month.month.IrusMonth.from_invasion_stats",
            return_value=mock_month_stats,
        ):
            with patch(
                "src.month.month.IrusReport.from_month", return_value=mock_report
            ):
                # Act
                response = lambda_handler(month_event, lambda_context)

        # Assert
        assert response["statusCode"] == 200
        body = response["body"]

        # Check all required template fields are present
        required_fields = [
            "template",
            "month",
            "invasions",
            "active",
            "members",
            "participation",
            "url",
        ]
        for field in required_fields:
            assert field in body

        # Check template string format
        assert "Report for Month {}" in body["template"]
        assert "Invasions: {}" in body["template"]
        assert "Active Members: {} of {}" in body["template"]
        assert "Participation (sum of members across invasions): {}" in body["template"]

    @patch("src.month.month.IrusContainer.default")
    def test_different_month_formats(self, mock_container, container, lambda_context):
        """Test handling of different month format inputs."""
        # Arrange
        mock_container.return_value = container

        mock_month_stats = Mock()
        mock_month_stats.invasions = 8
        mock_month_stats.active = 12
        mock_month_stats.participation = 100
        mock_month_stats.report = ["member1"]

        mock_report = Mock()
        mock_report.msg = "https://s3.amazonaws.com/bucket/report.csv"

        # Import after setting up mocks
        from src.month.month import lambda_handler

        # Test different month formats
        test_cases = [
            ("202401", 1, 2024),  # January 2024
            ("202412", 12, 2024),  # December 2024
            ("202506", 6, 2025),  # June 2025
        ]

        for month_str, expected_month, expected_year in test_cases:
            event = {"month": month_str}

            with patch(
                "src.month.month.IrusMonth.from_invasion_stats",
                return_value=mock_month_stats,
            ) as mock_from_stats:
                with patch(
                    "src.month.month.IrusReport.from_month", return_value=mock_report
                ):
                    # Act
                    response = lambda_handler(event, lambda_context)

            # Assert
            assert response["statusCode"] == 200
            mock_from_stats.assert_called_with(month=expected_month, year=expected_year)

    @patch("src.month.month.IrusContainer.default")
    def test_gold_parameter_passed_to_report(
        self, mock_container, container, lambda_context, month_event
    ):
        """Test that gold parameter is passed correctly to report generation."""
        # Arrange
        mock_container.return_value = container

        mock_month_stats = Mock()
        mock_month_stats.invasions = 10
        mock_month_stats.active = 15
        mock_month_stats.participation = 150
        mock_month_stats.report = ["member1"]

        mock_report = Mock()
        mock_report.msg = "https://s3.amazonaws.com/bucket/report.csv"

        # Import after setting up mocks
        from src.month.month import lambda_handler

        with patch(
            "src.month.month.IrusMonth.from_invasion_stats",
            return_value=mock_month_stats,
        ):
            with patch(
                "src.month.month.IrusReport.from_month", return_value=mock_report
            ) as mock_report_create:
                # Act
                response = lambda_handler(month_event, lambda_context)

        # Assert
        assert response["statusCode"] == 200
        # Verify gold=0 was passed to report generation
        mock_report_create.assert_called_once_with(mock_month_stats, gold=0)
