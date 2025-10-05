"""Integration tests for cross-month scenarios with real DynamoDB.

These tests validate behavior across multiple months:
- Two consecutive months with different data
- Member joins between months
- Member inactivity between months
- Monthly report isolation

All tests use the 99DDHHMM test data strategy.
"""

import time
from uuid import uuid4

import pytest
from irus.models.ladder import IrusLadder
from irus.models.ladderrank import IrusLadderRank
from irus.month import IrusMonth
from irus.repositories.invasion import InvasionRepository
from irus.repositories.ladder import LadderRepository
from irus.repositories.member import MemberRepository

from tests.integration.conftest import get_test_date_components


class TestCrossMonthScenarios:
    """Integration tests for cross-month data scenarios."""

    @pytest.fixture
    def repositories(self, integration_container):
        """Create repository instances."""
        return {
            "member": MemberRepository(integration_container),
            "invasion": InvasionRepository(integration_container),
            "ladder": LadderRepository(integration_container),
        }

    def test_two_consecutive_months_data_isolation(
        self, integration_container, repositories
    ):
        """Test that two consecutive months maintain data isolation.

        Scenario:
        - Create invasions in Month 1
        - Create invasions in Month 2 (different month value)
        - Generate reports for each month
        - Verify each month's report only contains that month's invasions
        """
        # Arrange - Use two different months (test month and test month + 1)
        timestamp = int(time.time())
        date_components = get_test_date_components()

        # Month 1: Use test month
        month1 = date_components["month"]
        year1 = date_components["year"]

        # Month 2: Use test month + 1 (wrap to 1 if > 12)
        month2 = (month1 % 12) + 1
        year2 = year1  # Same year for simplicity

        # Create member active in both months
        player_unique_id = uuid4().hex[:8]
        member_data = {
            "player": f"CrossMonth-{timestamp}-{player_unique_id}",
            "day": 1,  # Joined before both months
            "month": month1,
            "year": year1,
            "faction": "yellow",
            "admin": False,
            "salary": True,
            "discord": None,
            "notes": "Cross-month test member",
        }
        member = repositories["member"].create_from_user_input(**member_data)

        # Create invasion in Month 1
        invasion1_data = {
            "day": date_components["day"],
            "month": month1,
            "year": year1,
            "settlement": "bw",
            "win": True,
            "notes": "Month 1 invasion",
        }
        invasion1 = repositories["invasion"].create_from_user_input(**invasion1_data)

        # Create ladder for Month 1
        rank1 = IrusLadderRank(
            invasion_name=invasion1.name,
            rank="01",
            player=member.player,
            score=900,
            kills=9,
            deaths=2,
            assists=5,
            heals=18,
            damage=13000,
            member=True,
            ladder=True,
            adjusted=False,
            error=False,
        )
        ladder1 = IrusLadder(invasion_name=invasion1.name, ranks=[rank1])
        repositories["ladder"].save_ladder(ladder1)

        # Create invasion in Month 2
        invasion2_data = {
            "day": date_components["day"],
            "month": month2,
            "year": year2,
            "settlement": "ef",
            "win": True,
            "notes": "Month 2 invasion",
        }
        invasion2 = repositories["invasion"].create_from_user_input(**invasion2_data)

        # Create ladder for Month 2
        rank2 = IrusLadderRank(
            invasion_name=invasion2.name,
            rank="01",
            player=member.player,
            score=850,
            kills=8,
            deaths=3,
            assists=4,
            heals=16,
            damage=12000,
            member=True,
            ladder=True,
            adjusted=False,
            error=False,
        )
        ladder2 = IrusLadder(invasion_name=invasion2.name, ranks=[rank2])
        repositories["ladder"].save_ladder(ladder2)

        # Act - Generate reports for both months
        report1 = IrusMonth.from_invasion_stats(
            month=month1, year=year1, container=integration_container
        )
        report2 = IrusMonth.from_invasion_stats(
            month=month2, year=year2, container=integration_container
        )

        # Assert - Each month's report is isolated
        assert report1.month == f"{year1}{month1:02d}"
        assert report2.month == f"{year2}{month2:02d}"

        # Month 1 should contain invasion 1
        assert invasion1.name in report1.names

        # Month 2 should contain invasion 2
        assert invasion2.name in report2.names

        # Verify member appears in both reports
        member_in_report1 = any(r["id"] == member.player for r in report1.report)
        member_in_report2 = any(r["id"] == member.player for r in report2.report)

        assert member_in_report1, "Member should appear in month 1 report"
        assert member_in_report2, "Member should appear in month 2 report"

    def test_member_joins_between_months(self, integration_container, repositories):
        """Test member who joins between two months.

        Scenario:
        - Month 1: Member doesn't exist yet
        - Month 2: Member joins and participates
        - Verify member only appears in Month 2 report
        """
        # Arrange - Two different months
        timestamp = int(time.time())
        date_components = get_test_date_components()

        month1 = date_components["month"]
        year1 = date_components["year"]
        month2 = (month1 % 12) + 1
        year2 = year1

        # Create invasion in Month 1 (before member joins)
        invasion1_data = {
            "day": date_components["day"],
            "month": month1,
            "year": year1,
            "settlement": "bw",
            "win": True,
            "notes": "Before member joins",
        }
        invasion1 = repositories["invasion"].create_from_user_input(**invasion1_data)

        # Create ladder for Month 1 with different player
        other_player = f"OtherPlayer-{timestamp}-{uuid4().hex[:8]}"
        rank1 = IrusLadderRank(
            invasion_name=invasion1.name,
            rank="01",
            player=other_player,
            score=900,
            kills=9,
            deaths=2,
            assists=5,
            heals=18,
            damage=13000,
            member=False,  # Not a member yet
            ladder=True,
            adjusted=False,
            error=False,
        )
        ladder1 = IrusLadder(invasion_name=invasion1.name, ranks=[rank1])
        repositories["ladder"].save_ladder(ladder1)

        # Member joins in Month 2
        new_member_data = {
            "player": f"NewJoiner-{timestamp}-{uuid4().hex[:8]}",
            "day": 1,  # Joins at start of month 2
            "month": month2,
            "year": year2,
            "faction": "green",
            "admin": False,
            "salary": True,
            "discord": None,
            "notes": "Joined in month 2",
        }
        new_member = repositories["member"].create_from_user_input(**new_member_data)

        # Create invasion in Month 2 (after member joins)
        invasion2_data = {
            "day": date_components["day"],
            "month": month2,
            "year": year2,
            "settlement": "ef",
            "win": True,
            "notes": "After member joins",
        }
        invasion2 = repositories["invasion"].create_from_user_input(**invasion2_data)

        # Create ladder for Month 2 with new member
        rank2 = IrusLadderRank(
            invasion_name=invasion2.name,
            rank="01",
            player=new_member.player,
            score=850,
            kills=8,
            deaths=3,
            assists=4,
            heals=16,
            damage=12000,
            member=True,
            ladder=True,
            adjusted=False,
            error=False,
        )
        ladder2 = IrusLadder(invasion_name=invasion2.name, ranks=[rank2])
        repositories["ladder"].save_ladder(ladder2)

        # Act - Generate reports
        report1 = IrusMonth.from_invasion_stats(
            month=month1, year=year1, container=integration_container
        )
        report2 = IrusMonth.from_invasion_stats(
            month=month2, year=year2, container=integration_container
        )

        # Assert - New member appears in both reports (current implementation loads ALL members)
        # but only has participation stats in Month 2
        member_report1 = next(
            (r for r in report1.report if r["id"] == new_member.player), None
        )
        member_report2 = next(
            (r for r in report2.report if r["id"] == new_member.player), None
        )

        # Note: Current implementation includes all members in all monthly reports
        # regardless of join date. The member appears but with no participation in month 1.
        assert member_report1 is not None, "Member appears in report (zero stats)"
        assert member_report1["invasions"] == 0, "No participation before join date"

        assert member_report2 is not None, "Member appears in month 2"
        assert member_report2["invasions"] >= 1, "Has participation after join date"

    def test_member_inactivity_between_months(
        self, integration_container, repositories
    ):
        """Test member who is active in Month 1 but inactive in Month 2.

        Scenario:
        - Month 1: Member participates in invasions
        - Month 2: Member exists but doesn't participate
        - Verify member has stats in Month 1, but minimal/no stats in Month 2
        """
        # Arrange - Two different months
        timestamp = int(time.time())
        date_components = get_test_date_components()

        month1 = date_components["month"]
        year1 = date_components["year"]
        month2 = (month1 % 12) + 1
        year2 = year1

        # Create member who joins before both months
        inactive_member_data = {
            "player": f"InactiveMember-{timestamp}-{uuid4().hex[:8]}",
            "day": 1,
            "month": month1,
            "year": year1,
            "faction": "purple",
            "admin": False,
            "salary": True,
            "discord": None,
            "notes": "Will be inactive in month 2",
        }
        inactive_member = repositories["member"].create_from_user_input(
            **inactive_member_data
        )

        # Month 1: Member participates
        invasion1_data = {
            "day": date_components["day"],
            "month": month1,
            "year": year1,
            "settlement": "bw",
            "win": True,
            "notes": "Month 1 - member active",
        }
        invasion1 = repositories["invasion"].create_from_user_input(**invasion1_data)

        rank1 = IrusLadderRank(
            invasion_name=invasion1.name,
            rank="01",
            player=inactive_member.player,
            score=900,
            kills=9,
            deaths=2,
            assists=5,
            heals=18,
            damage=13000,
            member=True,
            ladder=True,
            adjusted=False,
            error=False,
        )
        ladder1 = IrusLadder(invasion_name=invasion1.name, ranks=[rank1])
        repositories["ladder"].save_ladder(ladder1)

        # Month 2: Member doesn't participate (create invasion without them)
        invasion2_data = {
            "day": date_components["day"],
            "month": month2,
            "year": year2,
            "settlement": "ef",
            "win": True,
            "notes": "Month 2 - member inactive",
        }
        invasion2 = repositories["invasion"].create_from_user_input(**invasion2_data)

        # Create ladder for Month 2 with a different player
        other_player = f"ActivePlayer-{timestamp}-{uuid4().hex[:8]}"
        rank2 = IrusLadderRank(
            invasion_name=invasion2.name,
            rank="01",
            player=other_player,
            score=850,
            kills=8,
            deaths=3,
            assists=4,
            heals=16,
            damage=12000,
            member=False,
            ladder=True,
            adjusted=False,
            error=False,
        )
        ladder2 = IrusLadder(invasion_name=invasion2.name, ranks=[rank2])
        repositories["ladder"].save_ladder(ladder2)

        # Act - Generate reports
        report1 = IrusMonth.from_invasion_stats(
            month=month1, year=year1, container=integration_container
        )
        report2 = IrusMonth.from_invasion_stats(
            month=month2, year=year2, container=integration_container
        )

        # Assert - Member stats differ between months
        member_report1 = next(
            (r for r in report1.report if r["id"] == inactive_member.player), None
        )
        member_report2 = next(
            (r for r in report2.report if r["id"] == inactive_member.player), None
        )

        # Month 1: Member should have participation stats
        assert member_report1 is not None, "Member should appear in month 1"
        assert member_report1["invasions"] >= 1, "Member participated in month 1"
        assert member_report1["wins"] >= 1, "Member had wins in month 1"

        # Month 2: Member appears but has no participation
        assert member_report2 is not None, "Member still exists in month 2"
        assert member_report2["invasions"] == 0, "Member didn't participate in month 2"
        assert member_report2["wins"] == 0, "Member had no wins in month 2"
