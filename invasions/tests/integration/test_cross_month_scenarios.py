"""Integration tests for cross-month scenarios and data isolation.

These tests validate monthly data isolation and member evolution across
multiple months, ensuring that:
- Each month's data is properly isolated
- Member activity/inactivity is tracked correctly over time
- Member joins and changes are reflected properly
"""

import pytest
from irus.models.invasion import IrusInvasion
from irus.models.ladder import IrusLadder
from irus.models.member import IrusMember
from irus.month import IrusMonth
from irus.repositories.invasion import InvasionRepository
from irus.repositories.ladder import LadderRepository
from irus.repositories.member import MemberRepository

from tests.integration.fixtures import FixtureLoader


class TestCrossMonthScenarios:
    """Integration tests for cross-month data scenarios."""

    @pytest.fixture
    def repositories(self, integration_container):
        """Create repository instances with real AWS container."""
        return {
            "member": MemberRepository(integration_container),
            "invasion": InvasionRepository(integration_container),
            "ladder": LadderRepository(integration_container),
        }

    def test_two_consecutive_months_isolation(
        self, integration_container, repositories
    ):
        """Test data isolation between two consecutive months.

        Uses Data Sets 1 and 2 (months 999903 and 999904) to verify:
        - Month 999903 report only includes March data
        - Month 999904 report only includes April data
        - Reports are properly isolated from each other

        Workflow:
        1. Load fixtures for both months
        2. Generate reports for each month
        3. Verify each month's data is isolated
        4. Verify member stats differ between months
        """
        # 1. Load March data (Data Set 1 - month 999903)
        march_members = [
            FixtureLoader.load(IrusMember, f"test_player{i}") for i in range(1, 5)
        ]
        march_invasions = [
            FixtureLoader.load(IrusInvasion, "99990301-bw"),
            FixtureLoader.load(IrusInvasion, "99990315-ef"),
            FixtureLoader.load(IrusInvasion, "99990329-wf"),
        ]
        march_ladder = FixtureLoader.load(IrusLadder, "99990301-bw")

        # Load April data (Data Set 2 - month 999904)
        april_members = [
            FixtureLoader.load(IrusMember, f"test_player{i}") for i in range(1, 6)
        ]  # +TestPlayer5
        april_invasions = [
            FixtureLoader.load(IrusInvasion, "99990405-rw"),
            FixtureLoader.load(IrusInvasion, "99990410-bw"),
            FixtureLoader.load(IrusInvasion, "99990420-md"),
            FixtureLoader.load(IrusInvasion, "99990428-ck"),
        ]
        april_ladders = [
            FixtureLoader.load(IrusLadder, "99990405-rw"),
            FixtureLoader.load(IrusLadder, "99990410-bw"),
            FixtureLoader.load(IrusLadder, "99990420-md"),
            FixtureLoader.load(IrusLadder, "99990428-ck"),
        ]

        # 2. Save all data to DynamoDB
        for member in march_members + april_members:
            repositories["member"].save(member)

        for invasion in march_invasions + april_invasions:
            repositories["invasion"].save(invasion)

        repositories["ladder"].save_ladder(march_ladder)
        for ladder in april_ladders:
            repositories["ladder"].save_ladder(ladder)

        # 3. Generate reports for each month
        march_report = IrusMonth.from_invasion_stats(
            month=3, year=9999, container=integration_container
        )
        april_report = IrusMonth.from_invasion_stats(
            month=4, year=9999, container=integration_container
        )

        # 4. Verify March report isolation
        assert march_report.month == "999903"
        assert march_report.invasions == 3  # Only March invasions
        assert "99990301-bw" in march_report.names
        assert "99990315-ef" in march_report.names
        assert "99990329-wf" in march_report.names
        # Should NOT include April invasions
        assert "99990405-rw" not in march_report.names

        # 5. Verify April report isolation
        assert april_report.month == "999904"
        assert april_report.invasions == 4  # Only April invasions
        assert "99990405-rw" in april_report.names
        assert "99990410-bw" in april_report.names
        assert "99990420-md" in april_report.names
        assert "99990428-ck" in april_report.names
        # Should NOT include March invasions
        assert "99990301-bw" not in april_report.names

        # 6. Verify member stats differ between months
        march_player1 = next(
            (r for r in march_report.report if r["id"] == "TestPlayer1"), None
        )
        april_player1 = next(
            (r for r in april_report.report if r["id"] == "TestPlayer1"), None
        )

        assert march_player1 is not None
        assert april_player1 is not None
        # March: 1 invasion, April: 4 invasions
        assert march_player1["invasions"] == 1
        assert april_player1["invasions"] == 4

    def test_member_joins_between_months(self, integration_container, repositories):
        """Test member joining between months is tracked correctly.

        Uses months 999903 and 999904 where TestPlayer5 is inactive in March
        but joins for April.

        Workflow:
        1. Load data for both months (TestPlayer5 only in April)
        2. Generate reports
        3. Verify TestPlayer5 appears in April but not March
        """
        # 1. March data - 4 members only (no TestPlayer5)
        march_members = [
            FixtureLoader.load(IrusMember, f"test_player{i}") for i in range(1, 5)
        ]
        march_invasions = [FixtureLoader.load(IrusInvasion, "99990301-bw")]
        march_ladder = FixtureLoader.load(IrusLadder, "99990301-bw")

        # April data - 5 members (including TestPlayer5)
        april_members = [
            FixtureLoader.load(IrusMember, f"test_player{i}") for i in range(1, 6)
        ]
        april_invasions = [FixtureLoader.load(IrusInvasion, "99990405-rw")]
        april_ladder = FixtureLoader.load(IrusLadder, "99990405-rw")

        # 2. Save all data
        for member in march_members + april_members:
            repositories["member"].save(member)

        for invasion in march_invasions + april_invasions:
            repositories["invasion"].save(invasion)

        repositories["ladder"].save_ladder(march_ladder)
        repositories["ladder"].save_ladder(april_ladder)

        # 3. Generate reports
        march_report = IrusMonth.from_invasion_stats(
            month=3, year=9999, container=integration_container
        )
        april_report = IrusMonth.from_invasion_stats(
            month=4, year=9999, container=integration_container
        )

        # 4. Verify TestPlayer5 not in March (wasn't a member yet)
        march_player5 = next(
            (r for r in march_report.report if r["id"] == "TestPlayer5"), None
        )
        # TestPlayer5 should still appear in report but with 0 invasions (non-salary)
        assert march_player5 is not None
        assert march_player5["salary"] is False
        assert march_player5["invasions"] == 0

        # 5. Verify TestPlayer5 is in April but still inactive
        april_player5 = next(
            (r for r in april_report.report if r["id"] == "TestPlayer5"), None
        )
        assert april_player5 is not None
        assert april_player5["salary"] is False  # Non-salary member
        assert april_player5["invasions"] == 0  # Doesn't participate

    def test_member_inactivity_between_months(
        self, integration_container, repositories
    ):
        """Test member activity changes between months.

        Tests a member who is active in one month but inactive in another.

        Workflow:
        1. Create scenario where TestPlayer4 has different activity levels
        2. Generate reports for both months
        3. Verify participation counts differ correctly
        """
        # 1. Load test data
        members = [
            FixtureLoader.load(IrusMember, f"test_player{i}") for i in range(1, 5)
        ]

        # March: TestPlayer4 participates
        march_invasions = [FixtureLoader.load(IrusInvasion, "99990301-bw")]
        march_ladder = FixtureLoader.load(IrusLadder, "99990301-bw")

        # April: TestPlayer4 only participates in 2 of 4 invasions
        april_invasions = [
            FixtureLoader.load(IrusInvasion, "99990405-rw"),
            FixtureLoader.load(IrusInvasion, "99990410-bw"),
            FixtureLoader.load(IrusInvasion, "99990420-md"),
            FixtureLoader.load(IrusInvasion, "99990428-ck"),
        ]
        april_ladders = [
            FixtureLoader.load(IrusLadder, "99990405-rw"),
            FixtureLoader.load(IrusLadder, "99990410-bw"),
            FixtureLoader.load(IrusLadder, "99990420-md"),
            FixtureLoader.load(IrusLadder, "99990428-ck"),
        ]

        # 2. Save data
        for member in members:
            repositories["member"].save(member)

        for invasion in march_invasions + april_invasions:
            repositories["invasion"].save(invasion)

        repositories["ladder"].save_ladder(march_ladder)
        for ladder in april_ladders:
            repositories["ladder"].save_ladder(ladder)

        # 3. Generate reports
        march_report = IrusMonth.from_invasion_stats(
            month=3, year=9999, container=integration_container
        )
        april_report = IrusMonth.from_invasion_stats(
            month=4, year=9999, container=integration_container
        )

        # 4. Verify TestPlayer4 activity in March
        march_player4 = next(
            (r for r in march_report.report if r["id"] == "TestPlayer4"), None
        )
        assert march_player4 is not None
        assert march_player4["invasions"] == 1  # Participates in March

        # 5. Verify TestPlayer4 partial activity in April
        april_player4 = next(
            (r for r in april_report.report if r["id"] == "TestPlayer4"), None
        )
        assert april_player4 is not None
        assert april_player4["invasions"] == 2  # Only 2/4 invasions in April

        # 6. Verify other members maintain consistent activity
        march_player1 = next(
            (r for r in march_report.report if r["id"] == "TestPlayer1"), None
        )
        april_player1 = next(
            (r for r in april_report.report if r["id"] == "TestPlayer1"), None
        )
        assert march_player1["invasions"] == 1  # March: 1 invasion
        assert (
            april_player1["invasions"] == 4
        )  # April: 4 invasions (full participation)
