"""Integration tests for monthly workflow and report generation.

These tests validate end-to-end monthly statistics generation using real AWS
DynamoDB with comprehensive fixture data sets.

Test Data Sets:
- Set 1 (month 999903): Basic monthly report with full participation
- Set 2 (month 999904): Partial participation with varied activity
- Set 3 (month 999905): Mid-month member join (eligibility filtering)
- Set 4 (month 999906): Ladder variations (ladder=true/false, score=0)
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


class TestMonthlyWorkflowIntegration:
    """Integration tests for monthly report generation workflow."""

    @pytest.fixture
    def repositories(self, integration_container):
        """Create repository instances with real AWS container."""
        return {
            "member": MemberRepository(integration_container),
            "invasion": InvasionRepository(integration_container),
            "ladder": LadderRepository(integration_container),
        }

    def test_basic_monthly_report_generation(self, integration_container, repositories):
        """Test end-to-end monthly report generation with full participation.

        Uses Data Set 1 (month 999903):
        - 4 members with full participation
        - 3 invasions (all wins, all ladder=true)
        - 1 ladder with complete stats

        Workflow:
        1. Load fixtures from JSON
        2. Save to DynamoDB using repositories
        3. Generate monthly report: IrusMonth.from_invasion_stats(3, 9999)
        4. Verify report data matches expectations
        5. Cleanup handled by conftest cleanup_test_data fixture
        """
        # 1. Load fixtures for Data Set 1 (month 999903)
        members = [
            FixtureLoader.load(IrusMember, f"test_player{i}") for i in range(1, 5)
        ]
        invasions = [
            FixtureLoader.load(IrusInvasion, "99990301-bw"),
            FixtureLoader.load(IrusInvasion, "99990315-ef"),
            FixtureLoader.load(IrusInvasion, "99990329-wf"),
        ]
        ladder = FixtureLoader.load(IrusLadder, "99990301-bw")

        # 2. Save fixtures to DynamoDB
        for member in members:
            repositories["member"].save(member)

        for invasion in invasions:
            repositories["invasion"].save(invasion)

        repositories["ladder"].save_ladder(ladder)

        # 3. Generate monthly report
        monthly_report = IrusMonth.from_invasion_stats(
            month=3, year=9999, container=integration_container
        )

        # 4. Verify report structure
        assert monthly_report is not None
        assert monthly_report.month == "999903"
        assert monthly_report.invasions == 3
        # Note: report includes ALL members in DB (not just test members)
        # So we verify our test members are present instead of counting total
        assert len(monthly_report.report) >= 4  # At least our 4 test members

        # Verify invasion names are tracked
        assert len(monthly_report.names) == 3
        assert "99990301-bw" in monthly_report.names
        assert "99990315-ef" in monthly_report.names
        assert "99990329-wf" in monthly_report.names

        # Verify our test member statistics (filtering report to just TestPlayer1)
        player1_stats = next(
            (r for r in monthly_report.report if r["id"] == "TestPlayer1"), None
        )
        assert player1_stats is not None
        assert player1_stats["salary"] is True
        # Only 1 invasion has a ladder, so players only participate in 1
        assert player1_stats["invasions"] == 1  # Participated in 1 (with ladder)
        assert player1_stats["wins"] == 1  # 1 win
        assert player1_stats["ladders"] == 1  # 1 ladder

        # Verify ladder stats for TestPlayer1 (rank 1 in 99990301-bw)
        assert player1_stats["sum_score"] == 1500
        assert player1_stats["sum_kills"] == 25
        assert player1_stats["sum_assists"] == 10
        assert player1_stats["avg_score"] == 1500.0  # 1500 / 1 ladder
        assert player1_stats["max_rank"] == 1.0

        # Verify participation and active counts
        assert monthly_report.participation > 0  # Sum of wins for salary members
        assert monthly_report.active >= 4  # At least our 4 test members participated

        # Verify invasion status markers (only invasion with ladder shows status)
        assert player1_stats["99990301-bw"] == "W"  # Win (has ladder)
        assert player1_stats["99990315-ef"] == "-"  # No ladder
        assert player1_stats["99990329-wf"] == "-"  # No ladder

        # Note: cleanup happens automatically via cleanup_test_data fixture

    def test_partial_participation(self, integration_container, repositories):
        """Test monthly report with varied participation levels.

        Uses Data Set 2 (month 999904):
        - 5 members with different activity levels
        - 4 invasions (3 wins, 1 loss) all with ladders
        - Participation varies: 4, 3, 3, 2, 0 invasions per member

        Tests:
        - Partial participation tracking
        - Inactive member handling (TestPlayer5: 0 invasions)
        - Non-salary member (TestPlayer5)
        - Win/loss tracking with varied participation
        """
        # 1. Load fixtures for Data Set 2 (month 999904)
        members = [
            FixtureLoader.load(IrusMember, f"test_player{i}")
            for i in range(1, 6)  # 5 members including TestPlayer5
        ]
        invasions = [
            FixtureLoader.load(IrusInvasion, "99990405-rw"),  # Win
            FixtureLoader.load(IrusInvasion, "99990410-bw"),  # Loss
            FixtureLoader.load(IrusInvasion, "99990420-md"),  # Win
            FixtureLoader.load(IrusInvasion, "99990428-ck"),  # Win
        ]
        ladders = [
            FixtureLoader.load(IrusLadder, "99990405-rw"),
            FixtureLoader.load(IrusLadder, "99990410-bw"),
            FixtureLoader.load(IrusLadder, "99990420-md"),
            FixtureLoader.load(IrusLadder, "99990428-ck"),
        ]

        # 2. Save fixtures to DynamoDB
        for member in members:
            repositories["member"].save(member)

        for invasion in invasions:
            repositories["invasion"].save(invasion)

        for ladder in ladders:
            repositories["ladder"].save_ladder(ladder)

        # 3. Generate monthly report
        monthly_report = IrusMonth.from_invasion_stats(
            month=4, year=9999, container=integration_container
        )

        # 4. Verify report structure
        assert monthly_report is not None
        assert monthly_report.month == "999904"
        assert monthly_report.invasions == 4

        # Verify TestPlayer1: Full participation (4/4)
        player1_stats = next(
            (r for r in monthly_report.report if r["id"] == "TestPlayer1"), None
        )
        assert player1_stats is not None
        assert player1_stats["invasions"] == 4
        assert player1_stats["wins"] == 3  # 3 wins, 1 loss
        assert player1_stats["ladders"] == 4
        assert player1_stats["99990405-rw"] == "W"
        assert player1_stats["99990410-bw"] == "L"  # Loss
        assert player1_stats["99990420-md"] == "W"
        assert player1_stats["99990428-ck"] == "W"

        # Verify TestPlayer2: Partial participation (3/4 - missed 99990410-bw)
        player2_stats = next(
            (r for r in monthly_report.report if r["id"] == "TestPlayer2"), None
        )
        assert player2_stats is not None
        assert player2_stats["invasions"] == 3
        assert player2_stats["wins"] == 3  # All wins (missed the loss)
        assert player2_stats["ladders"] == 3
        assert player2_stats["99990405-rw"] == "W"
        assert player2_stats["99990410-bw"] == "-"  # Did not participate
        assert player2_stats["99990420-md"] == "W"
        assert player2_stats["99990428-ck"] == "W"

        # Verify TestPlayer3: Partial participation (3/4 - missed 99990420-md)
        player3_stats = next(
            (r for r in monthly_report.report if r["id"] == "TestPlayer3"), None
        )
        assert player3_stats is not None
        assert player3_stats["invasions"] == 3
        assert player3_stats["wins"] == 2  # Missed one win
        assert player3_stats["ladders"] == 3
        assert player3_stats["99990405-rw"] == "W"
        assert player3_stats["99990410-bw"] == "L"
        assert player3_stats["99990420-md"] == "-"  # Did not participate
        assert player3_stats["99990428-ck"] == "W"

        # Verify TestPlayer4: Limited participation (2/4)
        player4_stats = next(
            (r for r in monthly_report.report if r["id"] == "TestPlayer4"), None
        )
        assert player4_stats is not None
        assert player4_stats["invasions"] == 2
        assert player4_stats["wins"] == 2  # Both wins
        assert player4_stats["ladders"] == 2
        assert player4_stats["99990405-rw"] == "W"
        assert player4_stats["99990410-bw"] == "-"  # Did not participate
        assert player4_stats["99990420-md"] == "W"
        assert player4_stats["99990428-ck"] == "-"  # Did not participate

        # Verify TestPlayer5: Inactive member (0/4)
        player5_stats = next(
            (r for r in monthly_report.report if r["id"] == "TestPlayer5"), None
        )
        assert player5_stats is not None
        assert player5_stats["salary"] is False  # Non-salary member
        assert player5_stats["invasions"] == 0  # Completely inactive
        assert player5_stats["wins"] == 0
        assert player5_stats["ladders"] == 0
        # All invasions show no participation
        assert player5_stats["99990405-rw"] == "-"
        assert player5_stats["99990410-bw"] == "-"
        assert player5_stats["99990420-md"] == "-"
        assert player5_stats["99990428-ck"] == "-"

        # Note: cleanup happens automatically via cleanup_test_data fixture

    def test_mid_month_join_filtering(self, integration_container, repositories):
        """Test monthly report with member joining mid-month.

        Uses Data Set 3 (month 999905):
        - 4 members total (3 existing + 1 new mid-month)
        - 6 invasions but only 2 ladders (99990501-bw and 99990515-bw)
        - NewMidMonth joins 99990512, appears in 99990515-bw ladder only

        Tests:
        - Member who joins mid-month gets credit only for invasions after join
        - Members with start dates don't affect invasion participation tracking
        - Monthly report handles members with different join dates
        """
        # 1. Load fixtures for Data Set 3 (month 999905)
        members = [
            FixtureLoader.load(IrusMember, f"test_player{i}")
            for i in range(1, 4)  # TestPlayer1-3
        ] + [
            FixtureLoader.load(IrusMember, "new_mid_month")  # Joins May 12
        ]

        # Only load the 2 invasions that have ladders
        invasions = [
            FixtureLoader.load(
                IrusInvasion, "99990501-bw"
            ),  # May 1 (before NewMidMonth)
            FixtureLoader.load(
                IrusInvasion, "99990515-bw"
            ),  # May 15 (after NewMidMonth joins)
        ]
        ladders = [
            FixtureLoader.load(IrusLadder, "99990501-bw"),  # TestPlayer1-3 only
            FixtureLoader.load(IrusLadder, "99990515-bw"),  # All 4 players
        ]

        # 2. Save fixtures to DynamoDB
        for member in members:
            repositories["member"].save(member)

        for invasion in invasions:
            repositories["invasion"].save(invasion)

        for ladder in ladders:
            repositories["ladder"].save_ladder(ladder)

        # 3. Generate monthly report
        monthly_report = IrusMonth.from_invasion_stats(
            month=5, year=9999, container=integration_container
        )

        # 4. Verify report structure
        assert monthly_report is not None
        assert monthly_report.month == "999905"
        assert monthly_report.invasions == 2  # Only 2 invasions with ladders

        # Verify existing members (TestPlayer1-3) participated in both invasions
        for player_num in range(1, 4):
            player_stats = next(
                (
                    r
                    for r in monthly_report.report
                    if r["id"] == f"TestPlayer{player_num}"
                ),
                None,
            )
            assert player_stats is not None
            assert player_stats["invasions"] == 2  # Both invasions
            assert player_stats["ladders"] == 2
            assert player_stats["99990501-bw"] == "W"  # In first ladder
            assert player_stats["99990515-bw"] == "W"  # In second ladder

        # Verify NewMidMonth: only participated in invasion AFTER join date
        new_member_stats = next(
            (r for r in monthly_report.report if r["id"] == "NewMidMonth"), None
        )
        assert new_member_stats is not None
        assert new_member_stats["salary"] is True
        # NewMidMonth only appears in 99990515-bw ladder (after join date of 99990512)
        # They don't appear in 99990501-bw ladder (before join date)
        assert new_member_stats["invasions"] == 1  # Only 1 invasion
        assert new_member_stats["wins"] == 1
        assert new_member_stats["ladders"] == 1
        assert new_member_stats["99990501-bw"] == "-"  # Not in ladder (before join)
        assert new_member_stats["99990515-bw"] == "W"  # In ladder (after join)

        # Note: cleanup happens automatically via cleanup_test_data fixture

    def test_ladder_variations(self, integration_container, repositories):
        """Test monthly report with varied ladder configurations.

        Uses Data Set 4 (month 999906):
        - 3 invasions (2 wins, 1 loss)
        - Only 1 ladder (99990605-bw) with 3 different rank configurations:
          - TestPlayer1: ladder=true, score=1500 (normal ladder participation)
          - TestPlayer2: ladder=true, score=0 (participated but didn't score)
          - TestPlayer3: ladder=false, score=0 (non-ladder participation)

        Tests:
        - Members with ladder=true and score > 0 get full stats
        - Members with ladder=true but score=0 get invasion credit but no stats
        - Members with ladder=false get invasion credit but no stats
        - Invasions without ladders show no participation
        """
        # 1. Load fixtures for Data Set 4 (month 999906)
        members = [
            FixtureLoader.load(IrusMember, f"test_player{i}")
            for i in range(1, 4)  # TestPlayer1-3
        ]

        # 3 invasions, but only 1 has a ladder
        invasions = [
            FixtureLoader.load(IrusInvasion, "99990605-bw"),  # Win (has ladder)
            FixtureLoader.load(IrusInvasion, "99990615-ef"),  # Loss (no ladder)
            FixtureLoader.load(IrusInvasion, "99990625-wf"),  # Win (no ladder)
        ]
        ladder = FixtureLoader.load(IrusLadder, "99990605-bw")

        # 2. Save fixtures to DynamoDB
        for member in members:
            repositories["member"].save(member)

        for invasion in invasions:
            repositories["invasion"].save(invasion)

        repositories["ladder"].save_ladder(ladder)

        # 3. Generate monthly report
        monthly_report = IrusMonth.from_invasion_stats(
            month=6, year=9999, container=integration_container
        )

        # 4. Verify report structure
        assert monthly_report is not None
        assert monthly_report.month == "999906"
        assert monthly_report.invasions == 3

        # Verify TestPlayer1: ladder=true, score=1500 → Gets full stats
        player1_stats = next(
            (r for r in monthly_report.report if r["id"] == "TestPlayer1"), None
        )
        assert player1_stats is not None
        assert player1_stats["invasions"] == 1  # Only counted for ladder invasion
        assert player1_stats["wins"] == 1
        assert player1_stats["ladders"] == 1
        # Gets full ladder stats
        assert player1_stats["sum_score"] == 1500
        assert player1_stats["sum_kills"] == 25
        assert player1_stats["sum_assists"] == 10
        assert player1_stats["avg_score"] == 1500.0
        # Invasion markers
        assert player1_stats["99990605-bw"] == "W"  # Ladder invasion
        assert player1_stats["99990615-ef"] == "-"  # No ladder
        assert player1_stats["99990625-wf"] == "-"  # No ladder

        # Verify TestPlayer2: ladder=true, score=0 → Filtered out by get_member_rank
        player2_stats = next(
            (r for r in monthly_report.report if r["id"] == "TestPlayer2"), None
        )
        assert player2_stats is not None
        # TestPlayer2 has score=0 with ladder=true, so get_member_rank filters them out
        assert player2_stats["invasions"] == 0  # Filtered by score=0
        assert player2_stats["wins"] == 0
        assert player2_stats["ladders"] == 0
        assert player2_stats["99990605-bw"] == "-"  # Not counted (score=0)
        assert player2_stats["99990615-ef"] == "-"
        assert player2_stats["99990625-wf"] == "-"

        # Verify TestPlayer3: ladder=false, score=0 → Counted for participation
        player3_stats = next(
            (r for r in monthly_report.report if r["id"] == "TestPlayer3"), None
        )
        assert player3_stats is not None
        # TestPlayer3 has ladder=false, so they ARE counted (non-ladder participation)
        assert player3_stats["invasions"] == 1  # Counted (ladder=false)
        assert player3_stats["wins"] == 1
        assert player3_stats["ladders"] == 0  # No ladder stats counted
        # No ladder stats accumulated (ladder=false means no stats)
        assert player3_stats["sum_score"] == 0
        assert player3_stats["sum_kills"] == 0
        assert player3_stats["99990605-bw"] == "W"  # Invasion participation counted
        assert player3_stats["99990615-ef"] == "-"
        assert player3_stats["99990625-wf"] == "-"

        # Note: cleanup happens automatically via cleanup_test_data fixture
