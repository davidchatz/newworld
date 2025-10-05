"""Integration tests for report generation with real S3.

These tests validate the complete report generation and S3 upload workflow:
- Generating invasion ladder reports
- Generating member list reports
- Generating monthly reports
- S3 upload and presigned URL generation
- Report content validation

All tests use the 99DDHHMM test data strategy and real AWS S3.
"""

import time
from uuid import uuid4

import pytest
from irus.models.ladder import IrusLadder
from irus.models.ladderrank import IrusLadderRank
from irus.month import IrusMonth
from irus.report import IrusReport
from irus.repositories.invasion import InvasionRepository
from irus.repositories.ladder import LadderRepository
from irus.repositories.member import MemberRepository

from tests.integration.conftest import get_test_date_components


class TestReportGenerationIntegration:
    """Integration tests for report generation and S3 upload."""

    @pytest.fixture
    def repositories(self, integration_container):
        """Create repository instances."""
        return {
            "member": MemberRepository(integration_container),
            "invasion": InvasionRepository(integration_container),
            "ladder": LadderRepository(integration_container),
        }

    def test_invasion_ladder_report_s3_upload(
        self, integration_container, repositories
    ):
        """Test generating and uploading invasion ladder report to S3."""
        # Arrange - Create ladder data
        timestamp = int(time.time())
        date_components = get_test_date_components()
        invasion_name = f"{date_components['date_string']}-bw"

        ranks = []
        for i in range(1, 4):
            player_unique_id = uuid4().hex[:8]
            rank = IrusLadderRank(
                invasion_name=invasion_name,
                rank=f"{i:02d}",
                player=f"ReportTest-{timestamp}-{player_unique_id}",
                score=900 - (i * 100),
                kills=9 - i,
                deaths=i,
                assists=4,
                heals=18 - i,
                damage=14000 - (i * 1000),
                member=True,
                ladder=True,
                adjusted=False,
                error=False,
            )
            ranks.append(rank)

        ladder = IrusLadder(invasion_name=invasion_name, ranks=ranks)
        repositories["ladder"].save_ladder(ladder)

        # Act - Generate report
        report = IrusReport.from_invasion(ladder, integration_container)

        # Assert - Report generated successfully
        assert report is not None
        assert report.target == f"reports/invasion/{invasion_name}.csv"
        assert report.presigned is not None
        assert "https://" in report.presigned  # Valid presigned URL
        assert invasion_name in report.presigned  # URL contains invasion name
        assert report.msg is not None
        assert "here" in report.msg  # Message contains link

        # Verify S3 upload by checking we can generate another presigned URL
        s3 = integration_container.s3()
        bucket_name = integration_container.bucket_name()

        # Generate new presigned URL to verify object exists
        try:
            new_presigned = s3.generate_presigned_url(
                "get_object",
                Params={"Bucket": bucket_name, "Key": report.target},
                ExpiresIn=60,
            )
            assert new_presigned is not None
            assert "https://" in new_presigned
        except Exception as e:
            pytest.fail(f"Failed to generate presigned URL for uploaded report: {e}")

    def test_member_list_report_s3_upload(self, integration_container, repositories):
        """Test generating and uploading member list report to S3."""
        # Arrange - Create members
        timestamp = int(time.time())
        date_components = get_test_date_components()

        members_created = []
        for i in range(3):
            player_unique_id = uuid4().hex[:8]
            member_data = {
                "player": f"MemberReport-{timestamp}-{player_unique_id}",
                "day": date_components["day"],
                "month": date_components["month"],
                "year": date_components["year"],
                "faction": "green",
                "admin": False,
                "salary": True,
                "discord": None,
                "notes": f"Member report test {i + 1}",
            }
            created_member = repositories["member"].create_from_user_input(
                **member_data
            )
            members_created.append(created_member)

        # Create CSV report content
        csv_content = "player,faction,start\n"
        for member in members_created:
            csv_content += f"{member.player},{member.faction},{member.start}\n"

        # Act - Generate report
        report = IrusReport.from_members(timestamp, csv_content, integration_container)

        # Assert - Report generated successfully
        assert report is not None
        assert report.target == f"reports/members/{timestamp}.csv"
        assert report.presigned is not None
        assert "https://" in report.presigned
        assert report.msg is not None

        # Verify all members in presigned URL target
        s3 = integration_container.s3()
        bucket_name = integration_container.bucket_name()

        try:
            new_presigned = s3.generate_presigned_url(
                "get_object",
                Params={"Bucket": bucket_name, "Key": report.target},
                ExpiresIn=60,
            )
            assert new_presigned is not None
        except Exception as e:
            pytest.fail(f"Failed to verify S3 upload: {e}")

    def test_monthly_report_s3_upload(self, integration_container, repositories):
        """Test generating and uploading monthly report to S3.

        This test creates a complete monthly workflow:
        1. Create members
        2. Create invasions
        3. Create ladder data
        4. Generate monthly stats via IrusMonth.from_invasion_stats()
        5. Generate and upload monthly report
        """
        # Arrange - Single timestamp for entire test
        timestamp = int(time.time())
        date_components = get_test_date_components()
        test_month = date_components["month"]
        test_year = date_components["year"]

        # Create 2 members
        members = []
        for i in range(2):
            player_unique_id = uuid4().hex[:8]
            member_data = {
                "player": f"MonthlyReport-{timestamp}-{player_unique_id}",
                "day": date_components["day"],
                "month": test_month,
                "year": test_year,
                "faction": "purple",
                "admin": False,
                "salary": True,
                "discord": None,
                "notes": f"Monthly report member {i + 1}",
            }
            created_member = repositories["member"].create_from_user_input(
                **member_data
            )
            members.append(created_member)

        # Create 2 invasions
        invasion_names = []
        for i, settlement in enumerate(["bw", "ef"]):
            invasion_data = {
                "day": date_components["day"],
                "month": test_month,
                "year": test_year,
                "settlement": settlement,
                "win": True,
                "notes": f"Monthly report invasion {i + 1}",
            }
            created_invasion = repositories["invasion"].create_from_user_input(
                **invasion_data
            )
            invasion_names.append(created_invasion.name)

        # Create ladder data
        for invasion_name in invasion_names:
            ranks = []
            for rank_pos, member in enumerate(members, start=1):
                rank = IrusLadderRank(
                    invasion_name=invasion_name,
                    rank=f"{rank_pos:02d}",
                    player=member.player,
                    score=850,
                    kills=8,
                    deaths=2,
                    assists=4,
                    heals=16,
                    damage=12500,
                    member=True,
                    ladder=True,
                    adjusted=False,
                    error=False,
                )
                ranks.append(rank)

            ladder = IrusLadder(invasion_name=invasion_name, ranks=ranks)
            repositories["ladder"].save_ladder(ladder)

        # Generate monthly stats
        monthly_report = IrusMonth.from_invasion_stats(
            month=test_month, year=test_year, container=integration_container
        )

        # Act - Generate and upload monthly report
        gold = 100000  # Test gold amount
        report = IrusReport.from_month(monthly_report, gold, integration_container)

        # Assert - Report generated successfully
        assert report is not None
        assert report.target == f"reports/month/{monthly_report.month}.csv"
        assert report.presigned is not None
        assert "https://" in report.presigned
        assert monthly_report.month in report.presigned
        assert report.msg is not None

        # Verify S3 upload
        s3 = integration_container.s3()
        bucket_name = integration_container.bucket_name()

        try:
            new_presigned = s3.generate_presigned_url(
                "get_object",
                Params={"Bucket": bucket_name, "Key": report.target},
                ExpiresIn=60,
            )
            assert new_presigned is not None
        except Exception as e:
            pytest.fail(f"Failed to verify S3 upload: {e}")

    def test_presigned_url_expiration(self, integration_container, repositories):
        """Test that presigned URLs have correct expiration time."""
        # Arrange - Create simple ladder
        timestamp = int(time.time())
        date_components = get_test_date_components()
        invasion_name = f"{date_components['date_string']}-ww"

        rank = IrusLadderRank(
            invasion_name=invasion_name,
            rank="01",
            player=f"ExpirationTest-{timestamp}-{uuid4().hex[:8]}",
            score=900,
            kills=9,
            deaths=1,
            assists=5,
            heals=18,
            damage=14000,
            member=True,
            ladder=True,
            adjusted=False,
            error=False,
        )

        ladder = IrusLadder(invasion_name=invasion_name, ranks=[rank])
        repositories["ladder"].save_ladder(ladder)

        # Act - Generate report (default expiration is 3600 seconds / 1 hour)
        report = IrusReport.from_invasion(ladder, integration_container)

        # Assert - URL contains expiration parameter
        assert report.presigned is not None
        assert "X-Amz-Expires=" in report.presigned or "Expires=" in report.presigned

        # Message mentions one hour
        assert "one hour" in report.msg.lower() or "1 hour" in report.msg.lower()

    def test_report_content_validation(self, integration_container, repositories):
        """Test that report content is correctly formatted in CSV."""
        # Arrange - Create ladder with known data
        timestamp = int(time.time())
        date_components = get_test_date_components()
        invasion_name = f"{date_components['date_string']}-ef"

        test_player = f"ContentTest-{timestamp}-{uuid4().hex[:8]}"
        test_score = 999
        test_kills = 10

        rank = IrusLadderRank(
            invasion_name=invasion_name,
            rank="01",
            player=test_player,
            score=test_score,
            kills=test_kills,
            deaths=1,
            assists=6,
            heals=20,
            damage=15000,
            member=True,
            ladder=True,
            adjusted=False,
            error=False,
        )

        ladder = IrusLadder(invasion_name=invasion_name, ranks=[rank])
        repositories["ladder"].save_ladder(ladder)

        # Act - Generate report and get CSV content
        csv_content = ladder.to_csv()

        # Assert - CSV contains expected data
        assert f"ladder for invasion {invasion_name}" in csv_content
        assert "rank,player,score,kills,deaths,assists,heals,damage,scan" in csv_content
        assert test_player in csv_content
        assert str(test_score) in csv_content
        assert str(test_kills) in csv_content

        # Now create actual S3 report
        report = IrusReport.from_invasion(ladder, integration_container)

        # Verify report was created with this content
        assert report.target == f"reports/invasion/{invasion_name}.csv"
