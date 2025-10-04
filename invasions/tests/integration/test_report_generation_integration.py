"""Integration tests for report generation and S3 upload functionality.

These tests validate end-to-end report generation workflows including:
- CSV report creation from various data sources
- S3 upload operations
- Presigned URL generation
- Report download verification
"""

import time

import pytest
import requests
from irus.models.invasion import IrusInvasion
from irus.models.ladder import IrusLadder
from irus.models.member import IrusMember
from irus.month import IrusMonth
from irus.report import IrusReport
from irus.repositories.invasion import InvasionRepository
from irus.repositories.ladder import LadderRepository
from irus.repositories.member import MemberRepository

from tests.integration.fixtures import FixtureLoader


class TestReportGenerationIntegration:
    """Integration tests for report generation and S3 operations."""

    @pytest.fixture
    def repositories(self, integration_container):
        """Create repository instances with real AWS container."""
        return {
            "member": MemberRepository(integration_container),
            "invasion": InvasionRepository(integration_container),
            "ladder": LadderRepository(integration_container),
        }

    def test_monthly_report_s3_upload(self, integration_container, repositories):
        """Test monthly report generation and S3 upload with presigned URL.

        Uses Data Set 1 (month 999903) to generate a monthly CSV report,
        upload to S3, and verify the presigned URL works for download.

        Workflow:
        1. Load fixtures and save to DynamoDB
        2. Generate monthly stats: IrusMonth.from_invasion_stats()
        3. Create report: IrusReport.from_month()
        4. Verify S3 upload and presigned URL
        5. Download report via presigned URL and verify CSV content
        """
        # 1. Load and save fixtures (Data Set 1 - month 999903)
        members = [
            FixtureLoader.load(IrusMember, f"test_player{i}") for i in range(1, 5)
        ]
        invasions = [
            FixtureLoader.load(IrusInvasion, "99990301-bw"),
            FixtureLoader.load(IrusInvasion, "99990315-ef"),
            FixtureLoader.load(IrusInvasion, "99990329-wf"),
        ]
        ladder = FixtureLoader.load(IrusLadder, "99990301-bw")

        for member in members:
            repositories["member"].save(member)
        for invasion in invasions:
            repositories["invasion"].save(invasion)
        repositories["ladder"].save_ladder(ladder)

        # 2. Generate monthly report
        monthly_stats = IrusMonth.from_invasion_stats(
            month=3, year=9999, container=integration_container
        )

        # 3. Create and upload report to S3
        gold_amount = 1000  # Example gold amount for salary calculations
        report = IrusReport.from_month(
            monthly_stats, gold=gold_amount, container=integration_container
        )

        # 4. Verify report properties
        assert report.presigned is not None
        assert report.presigned.startswith("https://")
        assert report.target == "reports/month/999903.csv"
        assert "here" in report.msg
        assert report.presigned in report.msg

        # 5. Verify S3 object exists
        s3 = integration_container.s3()
        bucket_name = integration_container.bucket_name()
        response = s3.head_object(Bucket=bucket_name, Key=report.target)
        assert response["ResponseMetadata"]["HTTPStatusCode"] == 200
        assert response["ContentType"] == "binary/octet-stream"

        # 6. Download report via presigned URL and verify CSV content
        download_response = requests.get(report.presigned, timeout=10)
        assert download_response.status_code == 200

        csv_content = download_response.text
        assert "player" in csv_content.lower()  # CSV header
        assert "TestPlayer1" in csv_content
        assert "999903" in csv_content  # Month appears in report

        # 7. Cleanup: Delete S3 object
        s3.delete_object(Bucket=bucket_name, Key=report.target)

    def test_invasion_ladder_report_s3_upload(
        self, integration_container, repositories
    ):
        """Test invasion ladder report generation and S3 upload.

        Uses Data Set 1 ladder (99990301-bw) to generate an invasion
        ladder CSV report and verify S3 upload.

        Workflow:
        1. Load invasion and ladder fixtures
        2. Create report: IrusReport.from_invasion()
        3. Verify S3 upload and CSV content
        4. Cleanup S3 object
        """
        # 1. Load invasion and ladder fixtures
        invasion = FixtureLoader.load(IrusInvasion, "99990301-bw")
        ladder = FixtureLoader.load(IrusLadder, "99990301-bw")

        repositories["invasion"].save(invasion)
        repositories["ladder"].save_ladder(ladder)

        # 2. Reload ladder from repository (returns modern IrusLadder model)
        ladder_from_db = repositories["ladder"].get_ladder("99990301-bw")

        # 3. Create and upload report to S3
        report = IrusReport.from_invasion(
            ladder_from_db, container=integration_container
        )

        # 4. Verify report properties
        assert report.presigned is not None
        assert report.presigned.startswith("https://")
        assert report.target == "reports/invasion/99990301-bw.csv"

        # 5. Verify S3 object and download CSV
        s3 = integration_container.s3()
        bucket_name = integration_container.bucket_name()

        download_response = requests.get(report.presigned, timeout=10)
        assert download_response.status_code == 200

        csv_content = download_response.text
        # Verify ladder CSV contains player names and stats
        assert "TestPlayer1" in csv_content
        assert "TestPlayer2" in csv_content
        # CSV should have rank/score data
        assert "rank" in csv_content.lower() or "score" in csv_content.lower()

        # 6. Cleanup
        s3.delete_object(Bucket=bucket_name, Key=report.target)

    def test_member_list_report_s3_upload(self, integration_container, repositories):
        """Test member list report generation and S3 upload.

        Creates a member list report using test members and verifies
        S3 upload and CSV content.

        Workflow:
        1. Load member fixtures
        2. Generate member list CSV
        3. Create report: IrusReport.from_members()
        4. Verify S3 upload and CSV content
        5. Cleanup S3 object
        """
        # 1. Load member fixtures
        members = [
            FixtureLoader.load(IrusMember, f"test_player{i}") for i in range(1, 5)
        ]

        for member in members:
            repositories["member"].save(member)

        # 2. Get all members and generate CSV (simulating memberlist.csv())
        member_repo = MemberRepository(integration_container)
        all_members = member_repo.get_all()

        # Filter to our test members
        test_members = [m for m in all_members if m.player.startswith("TestPlayer")]

        # Generate CSV content (simple format for testing)
        csv_lines = ["player,faction,start,salary,admin"]
        for member in test_members:
            csv_lines.append(
                f"{member.player},{member.faction},{member.start},"
                f"{member.salary},{member.admin}"
            )
        member_csv = "\n".join(csv_lines)

        # 3. Create report with timestamp
        timestamp = int(time.time())
        report = IrusReport.from_members(
            timestamp=timestamp, report=member_csv, container=integration_container
        )

        # 4. Verify report properties
        assert report.presigned is not None
        assert report.target == f"reports/members/{timestamp}.csv"

        # 5. Download and verify CSV content
        download_response = requests.get(report.presigned, timeout=10)
        assert download_response.status_code == 200

        csv_content = download_response.text
        assert "TestPlayer1" in csv_content
        assert "TestPlayer4" in csv_content
        assert "faction" in csv_content.lower()

        # 6. Cleanup
        s3 = integration_container.s3()
        bucket_name = integration_container.bucket_name()
        s3.delete_object(Bucket=bucket_name, Key=report.target)

    def test_presigned_url_expiration(self, integration_container):
        """Test presigned URL expiration behavior.

        Verifies that presigned URLs expire correctly (default 1 hour).
        Note: This test doesn't wait for actual expiration but verifies
        the URL format and expiration parameter.

        Workflow:
        1. Create a simple report
        2. Verify presigned URL contains expiration parameter
        3. Verify URL is valid immediately after creation
        4. Cleanup S3 object
        """
        # 1. Create simple report
        test_content = "test,data\n1,2\n"
        timestamp = int(time.time())

        report = IrusReport(
            path="reports/test/",
            name=f"expiration_test_{timestamp}.csv",
            report=test_content,
            container=integration_container,
        )

        # 2. Verify presigned URL format (AWS Signature Version 2 format)
        assert report.presigned is not None
        assert "Expires=" in report.presigned  # Expiration timestamp (SigV2)
        assert "Signature=" in report.presigned  # Signature param (SigV2)
        assert "AWSAccessKeyId=" in report.presigned  # Access key (SigV2)

        # 3. Verify URL works immediately
        download_response = requests.get(report.presigned, timeout=10)
        assert download_response.status_code == 200
        assert download_response.text == test_content

        # 4. Extract and verify expiration time (SigV2 uses Unix timestamp)
        import urllib.parse

        parsed_url = urllib.parse.urlparse(report.presigned)
        query_params = urllib.parse.parse_qs(parsed_url.query)
        # SigV2 format uses Unix timestamp for Expires parameter
        expires_timestamp = int(query_params.get("Expires", ["0"])[0])
        # Verify expiration is ~1 hour in future (3600 seconds)
        time_diff = expires_timestamp - timestamp
        assert 3590 <= time_diff <= 3610  # Allow 10 sec variance

        # 5. Cleanup
        s3 = integration_container.s3()
        bucket_name = integration_container.bucket_name()
        s3.delete_object(Bucket=bucket_name, Key=report.target)
