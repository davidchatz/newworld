"""Unit tests for Invasion Lambda function."""

from unittest.mock import Mock, patch

import pytest
from aws_lambda_powertools.utilities.typing import LambdaContext
from irus.container import IrusContainer


class TestInvasionLambda:
    """Test suite for Invasion Lambda function."""

    @pytest.fixture
    def container(self):
        """Create test container with mocked dependencies."""
        return IrusContainer.create_unit()

    @pytest.fixture
    def lambda_context(self):
        """Create mock Lambda context."""
        context = Mock(spec=LambdaContext)
        context.function_name = "test-invasion-function"
        context.aws_request_id = "test-request-id"
        context.remaining_time_in_millis = 30000
        return context

    @pytest.fixture
    def invasion_event(self):
        """Invasion Lambda event structure."""
        return {"invasion": "99151228-ef"}

    @patch("src.invasion.invasion.IrusContainer.default")
    def test_successful_invasion_report(
        self, mock_container, container, lambda_context, invasion_event
    ):
        """Test successful invasion report generation."""
        # Arrange
        mock_container.return_value = container

        mock_invasion = Mock()
        mock_invasion.name = "99151228-ef"

        mock_ladder = Mock()
        mock_ladder.count.return_value = 50
        mock_ladder.members.return_value = 25
        mock_ladder.list.side_effect = (
            lambda member: "Member list" if member else "Non-member list"
        )
        mock_ladder.contiguous_from_1_until.return_value = 50

        mock_report = Mock()
        mock_report.msg = "https://s3.amazonaws.com/bucket/report.csv"

        # Import after setting up mocks
        from src.invasion.invasion import lambda_handler

        with patch(
            "src.invasion.invasion.IrusInvasion.from_table", return_value=mock_invasion
        ):
            with patch(
                "src.invasion.invasion.IrusLadder.from_invasion",
                return_value=mock_ladder,
            ):
                with patch(
                    "src.invasion.invasion.IrusReport.from_invasion",
                    return_value=mock_report,
                ):
                    # Act
                    response = lambda_handler(invasion_event, lambda_context)

        # Assert
        assert response["statusCode"] == 200
        body = response["body"]
        assert body["name"] == "99151228-ef"
        assert body["ranks"] == 50
        assert body["members"] == 25
        assert body["memberlist"] == "Member list"
        assert body["nonmemberlist"] == "Non-member list"
        assert body["contiguous"] == "Yes"
        assert "s3.amazonaws.com" in body["url"]

    @patch("src.invasion.invasion.IrusContainer.default")
    def test_incomplete_ladder_warning(
        self, mock_container, container, lambda_context, invasion_event
    ):
        """Test warning when ladder appears incomplete."""
        # Arrange
        mock_container.return_value = container

        mock_invasion = Mock()
        mock_invasion.name = "99151228-ef"

        mock_ladder = Mock()
        mock_ladder.count.return_value = 50
        mock_ladder.members.return_value = 25
        mock_ladder.list.side_effect = (
            lambda member: "Member list" if member else "Non-member list"
        )
        mock_ladder.contiguous_from_1_until.return_value = 30  # Less than total count

        mock_report = Mock()
        mock_report.msg = "https://s3.amazonaws.com/bucket/report.csv"

        # Import after setting up mocks
        from src.invasion.invasion import lambda_handler

        with patch(
            "src.invasion.invasion.IrusInvasion.from_table", return_value=mock_invasion
        ):
            with patch(
                "src.invasion.invasion.IrusLadder.from_invasion",
                return_value=mock_ladder,
            ):
                with patch(
                    "src.invasion.invasion.IrusReport.from_invasion",
                    return_value=mock_report,
                ):
                    # Act
                    response = lambda_handler(invasion_event, lambda_context)

        # Assert
        assert response["statusCode"] == 200
        body = response["body"]
        assert body["name"] == "99151228-ef"
        assert body["ranks"] == 50
        assert body["members"] == 25
        assert "Ladder may be incomplete" in body["contiguous"]
        assert "starting from rank 30" in body["contiguous"]

    @patch("src.invasion.invasion.IrusContainer.default")
    @patch("src.invasion.invasion.IrusInvasion.from_table")
    def test_invasion_not_found(
        self, mock_from_table, mock_container, container, lambda_context, invasion_event
    ):
        """Test handling when invasion is not found."""
        # Arrange
        mock_container.return_value = container
        mock_from_table.side_effect = ValueError("Invasion not found")

        # Import after setting up mocks
        from src.invasion.invasion import lambda_handler

        # Act
        response = lambda_handler(invasion_event, lambda_context)

        # Assert
        assert response["statusCode"] == 500
        assert "Error generating report" in response["body"]["url"]
        assert "99151228-ef" in response["body"]["url"]

    @patch("src.invasion.invasion.IrusContainer.default")
    def test_ladder_processing_error(
        self, mock_container, container, lambda_context, invasion_event
    ):
        """Test handling of ladder processing errors."""
        # Arrange
        mock_container.return_value = container

        mock_invasion = Mock()
        mock_invasion.name = "99151228-ef"

        # Import after setting up mocks
        from src.invasion.invasion import lambda_handler

        with patch(
            "src.invasion.invasion.IrusInvasion.from_table", return_value=mock_invasion
        ):
            with patch(
                "src.invasion.invasion.IrusLadder.from_invasion",
                side_effect=Exception("Ladder error"),
            ):
                # Act
                response = lambda_handler(invasion_event, lambda_context)

        # Assert
        assert response["statusCode"] == 500
        assert "Error generating report" in response["body"]["url"]
        assert "Ladder error" in response["body"]["url"]

    @patch("src.invasion.invasion.IrusContainer.default")
    def test_report_generation_error(
        self, mock_container, container, lambda_context, invasion_event
    ):
        """Test handling of report generation errors."""
        # Arrange
        mock_container.return_value = container

        mock_invasion = Mock()
        mock_invasion.name = "99151228-ef"

        mock_ladder = Mock()
        mock_ladder.count.return_value = 50
        mock_ladder.members.return_value = 25
        mock_ladder.list.side_effect = (
            lambda member: "Member list" if member else "Non-member list"
        )
        mock_ladder.contiguous_from_1_until.return_value = 50

        # Import after setting up mocks
        from src.invasion.invasion import lambda_handler

        with patch(
            "src.invasion.invasion.IrusInvasion.from_table", return_value=mock_invasion
        ):
            with patch(
                "src.invasion.invasion.IrusLadder.from_invasion",
                return_value=mock_ladder,
            ):
                with patch(
                    "src.invasion.invasion.IrusReport.from_invasion",
                    side_effect=Exception("Report error"),
                ):
                    # Act
                    response = lambda_handler(invasion_event, lambda_context)

        # Assert
        assert response["statusCode"] == 500
        assert "Error generating report" in response["body"]["url"]
        assert "Report error" in response["body"]["url"]

    @patch("src.invasion.invasion.IrusContainer.default")
    def test_zero_members_scenario(
        self, mock_container, container, lambda_context, invasion_event
    ):
        """Test scenario with zero members in invasion."""
        # Arrange
        mock_container.return_value = container

        mock_invasion = Mock()
        mock_invasion.name = "99151228-ef"

        mock_ladder = Mock()
        mock_ladder.count.return_value = 30
        mock_ladder.members.return_value = 0  # No members
        mock_ladder.list.side_effect = (
            lambda member: "" if member else "All non-members"
        )
        mock_ladder.contiguous_from_1_until.return_value = 30

        mock_report = Mock()
        mock_report.msg = "https://s3.amazonaws.com/bucket/report.csv"

        # Import after setting up mocks
        from src.invasion.invasion import lambda_handler

        with patch(
            "src.invasion.invasion.IrusInvasion.from_table", return_value=mock_invasion
        ):
            with patch(
                "src.invasion.invasion.IrusLadder.from_invasion",
                return_value=mock_ladder,
            ):
                with patch(
                    "src.invasion.invasion.IrusReport.from_invasion",
                    return_value=mock_report,
                ):
                    # Act
                    response = lambda_handler(invasion_event, lambda_context)

        # Assert
        assert response["statusCode"] == 200
        body = response["body"]
        assert body["members"] == 0
        assert body["memberlist"] == ""
        assert body["nonmemberlist"] == "All non-members"

    @patch("src.invasion.invasion.IrusContainer.default")
    def test_all_members_scenario(
        self, mock_container, container, lambda_context, invasion_event
    ):
        """Test scenario where all participants are members."""
        # Arrange
        mock_container.return_value = container

        mock_invasion = Mock()
        mock_invasion.name = "99151228-ef"

        mock_ladder = Mock()
        mock_ladder.count.return_value = 25
        mock_ladder.members.return_value = 25  # All are members
        mock_ladder.list.side_effect = lambda member: "All members" if member else ""
        mock_ladder.contiguous_from_1_until.return_value = 25

        mock_report = Mock()
        mock_report.msg = "https://s3.amazonaws.com/bucket/report.csv"

        # Import after setting up mocks
        from src.invasion.invasion import lambda_handler

        with patch(
            "src.invasion.invasion.IrusInvasion.from_table", return_value=mock_invasion
        ):
            with patch(
                "src.invasion.invasion.IrusLadder.from_invasion",
                return_value=mock_ladder,
            ):
                with patch(
                    "src.invasion.invasion.IrusReport.from_invasion",
                    return_value=mock_report,
                ):
                    # Act
                    response = lambda_handler(invasion_event, lambda_context)

        # Assert
        assert response["statusCode"] == 200
        body = response["body"]
        assert body["ranks"] == 25
        assert body["members"] == 25
        assert body["memberlist"] == "All members"
        assert body["nonmemberlist"] == ""

    @patch("src.invasion.invasion.IrusContainer.default")
    def test_response_template_structure(
        self, mock_container, container, lambda_context, invasion_event
    ):
        """Test that response follows expected template structure."""
        # Arrange
        mock_container.return_value = container

        mock_invasion = Mock()
        mock_invasion.name = "99151228-ef"

        mock_ladder = Mock()
        mock_ladder.count.return_value = 40
        mock_ladder.members.return_value = 15
        mock_ladder.list.side_effect = (
            lambda member: "Members" if member else "Non-members"
        )
        mock_ladder.contiguous_from_1_until.return_value = 40

        mock_report = Mock()
        mock_report.msg = "https://s3.amazonaws.com/bucket/report.csv"

        # Import after setting up mocks
        from src.invasion.invasion import lambda_handler

        with patch(
            "src.invasion.invasion.IrusInvasion.from_table", return_value=mock_invasion
        ):
            with patch(
                "src.invasion.invasion.IrusLadder.from_invasion",
                return_value=mock_ladder,
            ):
                with patch(
                    "src.invasion.invasion.IrusReport.from_invasion",
                    return_value=mock_report,
                ):
                    # Act
                    response = lambda_handler(invasion_event, lambda_context)

        # Assert
        assert response["statusCode"] == 200
        body = response["body"]

        # Check all required template fields are present
        required_fields = [
            "template",
            "name",
            "ranks",
            "members",
            "memberlist",
            "nonmemberlist",
            "contiguous",
            "url",
        ]
        for field in required_fields:
            assert field in body

        # Check template string format
        assert "Report for Invasion {}" in body["template"]
        assert "Ranks: {}" in body["template"]
        assert "Members ({}): {}" in body["template"]
