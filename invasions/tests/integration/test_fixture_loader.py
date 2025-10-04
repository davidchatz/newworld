"""Tests for FixtureLoader utility.

These tests verify that the FixtureLoader correctly loads and saves fixtures,
and that all sample fixtures are valid and loadable.
"""

import pytest
from irus.models.invasion import IrusInvasion
from irus.models.ladder import IrusLadder
from irus.models.member import IrusMember

from tests.integration.fixtures import FixtureLoader


class TestFixtureLoader:
    """Test suite for FixtureLoader utility."""

    def test_load_member_fixture(self):
        """Test loading a member fixture."""
        member = FixtureLoader.load(IrusMember, "test_player1")

        assert member.player == "TestPlayer1"
        assert member.faction == "yellow"
        assert member.start == 99990101
        assert member.salary is True
        assert member.admin is False

    def test_load_invasion_fixture(self):
        """Test loading an invasion fixture."""
        invasion = FixtureLoader.load(IrusInvasion, "99990301-bw")

        assert invasion.name == "99990301-bw"
        assert invasion.settlement == "bw"
        assert invasion.win is True
        assert invasion.date == 99990301
        assert invasion.year == 9999
        assert invasion.month == 3
        assert invasion.day == 1

    def test_load_ladder_fixture(self):
        """Test loading a ladder fixture with ranks."""
        ladder = FixtureLoader.load(IrusLadder, "99990301-bw")

        assert ladder.invasion_name == "99990301-bw"
        assert len(ladder.ranks) == 5

        # Check first rank
        assert ladder.ranks[0].player == "TestPlayer1"
        assert ladder.ranks[0].rank == "01"
        assert ladder.ranks[0].score == 1500
        assert ladder.ranks[0].member is True

        # Check non-member rank
        assert ladder.ranks[4].player == "RandomPlayer1"
        assert ladder.ranks[4].member is False

    def test_fixture_not_found_error(self):
        """Test that loading non-existent fixture raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError) as exc_info:
            FixtureLoader.load(IrusMember, "does_not_exist")

        assert "Fixture not found" in str(exc_info.value)

    def test_save_and_load_roundtrip(self, tmp_path):
        """Test saving and loading a fixture."""
        # Create a member
        member = IrusMember(
            player="RoundtripTest",
            faction="purple",
            start=99990101,
            salary=True,
            admin=False,
        )

        # Temporarily change fixtures directory to temp path
        original_dir = FixtureLoader.FIXTURES_DIR
        try:
            FixtureLoader.FIXTURES_DIR = tmp_path
            (tmp_path / "member").mkdir()

            # Save fixture
            saved_path = FixtureLoader.save(member, "roundtrip_test")
            assert saved_path.exists()

            # Load it back
            loaded_member = FixtureLoader.load(IrusMember, "roundtrip_test")

            # Verify it matches
            assert loaded_member.player == member.player
            assert loaded_member.faction == member.faction
            assert loaded_member.start == member.start
            assert loaded_member.salary == member.salary
            assert loaded_member.admin == member.admin

        finally:
            FixtureLoader.FIXTURES_DIR = original_dir

    def test_list_fixtures(self):
        """Test listing available fixtures."""
        member_fixtures = FixtureLoader.list_fixtures("member")

        assert isinstance(member_fixtures, list)
        assert "test_player1" in member_fixtures
        assert "test_player2" in member_fixtures
        assert len(member_fixtures) >= 4  # At least the 4 test players

    def test_list_fixtures_empty_directory(self):
        """Test listing fixtures from empty/non-existent directory."""
        fixtures = FixtureLoader.list_fixtures("nonexistent")

        assert fixtures == []

    def test_subdir_mapping(self):
        """Test that model classes map to correct subdirectories."""
        assert FixtureLoader._get_subdir(IrusMember) == "member"
        assert FixtureLoader._get_subdir(IrusInvasion) == "invasion"
        assert FixtureLoader._get_subdir(IrusLadder) == "ladder"

    def test_all_member_fixtures_valid(self):
        """Test that all member fixtures are valid and loadable."""
        member_fixtures = FixtureLoader.list_fixtures("member")

        for fixture_name in member_fixtures:
            member = FixtureLoader.load(IrusMember, fixture_name)
            assert member.player is not None
            assert member.faction in ["yellow", "green", "purple"]
            assert isinstance(member.salary, bool)
            assert isinstance(member.admin, bool)

    def test_all_invasion_fixtures_valid(self):
        """Test that all invasion fixtures are valid and loadable."""
        invasion_fixtures = FixtureLoader.list_fixtures("invasion")

        for fixture_name in invasion_fixtures:
            invasion = FixtureLoader.load(IrusInvasion, fixture_name)
            assert invasion.name is not None
            assert invasion.settlement is not None
            assert isinstance(invasion.win, bool)
            assert invasion.year == 9999  # All test data should be year 9999

    def test_all_ladder_fixtures_valid(self):
        """Test that all ladder fixtures are valid and loadable."""
        ladder_fixtures = FixtureLoader.list_fixtures("ladder")

        for fixture_name in ladder_fixtures:
            ladder = FixtureLoader.load(IrusLadder, fixture_name)
            assert ladder.invasion_name is not None
            assert isinstance(ladder.ranks, list)

            # Verify each rank is valid
            for rank in ladder.ranks:
                assert rank.player is not None
                assert rank.invasion_name == ladder.invasion_name


class TestDataSet1Fixtures:
    """Verify Data Set 1 (Basic Month 999903) fixtures are complete and consistent."""

    def test_dataset1_members_exist(self):
        """Test that all 4 members for Data Set 1 exist."""
        expected_members = [
            "test_player1",
            "test_player2",
            "test_player3",
            "test_player4",
        ]

        for member_name in expected_members:
            member = FixtureLoader.load(IrusMember, member_name)
            assert member is not None

    def test_dataset1_invasions_exist(self):
        """Test that all 3 invasions for Data Set 1 exist."""
        expected_invasions = ["99990301-bw", "99990315-ef", "99990329-wf"]

        for invasion_name in expected_invasions:
            invasion = FixtureLoader.load(IrusInvasion, invasion_name)
            assert invasion.year == 9999
            assert invasion.month == 3

    def test_dataset1_ladder_consistency(self):
        """Test that ladder data is consistent with members and invasions."""
        ladder = FixtureLoader.load(IrusLadder, "99990301-bw")

        # All 4 test players should be in the ladder
        ladder_players = [rank.player for rank in ladder.ranks]
        assert "TestPlayer1" in ladder_players
        assert "TestPlayer2" in ladder_players
        assert "TestPlayer3" in ladder_players
        assert "TestPlayer4" in ladder_players

        # Verify member flags are correct
        for rank in ladder.ranks:
            if rank.player.startswith("TestPlayer"):
                assert rank.member is True
            elif rank.player == "RandomPlayer1":
                assert rank.member is False

    def test_dataset1_members_eligible_for_march(self):
        """Test that members' start dates make them eligible for March invasions."""
        members = [
            FixtureLoader.load(IrusMember, f"test_player{i}") for i in range(1, 5)
        ]

        for member in members:
            # All members should start before or during March 9999
            assert member.start <= 99990331

    def test_dataset1_salary_distribution(self):
        """Test that Data Set 1 has correct salary distribution."""
        members = [
            FixtureLoader.load(IrusMember, f"test_player{i}") for i in range(1, 5)
        ]

        salary_members = [m for m in members if m.salary]
        non_salary_members = [m for m in members if not m.salary]

        # Per design: 3 salary, 1 non-salary
        assert len(salary_members) == 3
        assert len(non_salary_members) == 1
        assert non_salary_members[0].player == "TestPlayer4"
