"""Tests for IrusMemberList service."""

from unittest.mock import Mock, patch

import pytest
from irus.container import IrusContainer
from irus.memberlist import IrusMemberList
from irus.models.member import IrusMember


class TestIrusMemberList:
    """Test suite for IrusMemberList service."""

    @pytest.fixture
    def container(self):
        """Create test container with mocked dependencies."""
        return IrusContainer.create_test()

    @pytest.fixture
    def sample_members(self):
        """Create sample members for testing."""
        return [
            IrusMember(player="PlayerGreen1", faction="green", start=20240301),
            IrusMember(player="PlayerGreen2", faction="green", start=20240315),
            IrusMember(player="PlayerPurple1", faction="purple", start=20240401),
            IrusMember(player="PlayerYellow1", faction="yellow", start=20240501),
            IrusMember(
                player="PlayerO", faction="green", start=20240601
            ),  # For O/0 testing
        ]

    @pytest.fixture
    def member_list(self, container, sample_members):
        """Create IrusMemberList with mocked repository."""
        mock_repo = Mock()
        mock_repo.get_all.return_value = sample_members

        with patch("irus.memberlist.MemberRepository", return_value=mock_repo):
            return IrusMemberList(container)

    def test_initialization_loads_members(self, container, sample_members):
        """Test that initialization properly loads members from repository."""
        mock_repo = Mock()
        mock_repo.get_all.return_value = sample_members

        with patch("irus.memberlist.MemberRepository", return_value=mock_repo):
            member_list = IrusMemberList(container)

            mock_repo.get_all.assert_called_once()
            assert len(member_list.members) == 5
            assert member_list.members[0].player == "PlayerGreen1"

    def test_str_representation(self, member_list):
        """Test string representation."""
        assert member_list.str() == "MemberList(count=5)"

    def test_count(self, member_list):
        """Test count method."""
        assert member_list.count() == 5

    def test_csv_output_format(self, member_list):
        """Test CSV output generation and ordering."""
        csv_output = member_list.csv()

        lines = csv_output.strip().split("\n")
        assert lines[0] == "player,faction,start"
        assert len(lines) == 6  # Header + 5 members

        # Verify faction ordering: green, purple, yellow
        assert "PlayerGreen1,green,20240301" in lines
        assert "PlayerPurple1,purple,20240401" in lines
        assert "PlayerYellow1,yellow,20240501" in lines

    def test_markdown_all_factions(self, member_list):
        """Test markdown output for all factions."""
        markdown = member_list.markdown()

        assert "# Member List\n" in markdown
        assert "Count: 5" in markdown
        assert "PlayerGreen1 (green) started 20240301" in markdown
        assert "PlayerPurple1 (purple) started 20240401" in markdown

    def test_markdown_specific_faction(self, member_list):
        """Test markdown output filtered by faction."""
        markdown = member_list.markdown(faction="green")

        assert "# Member List for green\n" in markdown
        assert "Count: 3" in markdown
        assert "PlayerGreen1 (green)" in markdown
        assert "PlayerPurple1" not in markdown  # Should not include other factions

    def test_post_format(self, member_list):
        """Test post format output."""
        post_lines = member_list.post()

        assert post_lines[0] == "Player         Faction Start"
        assert post_lines[-1] == "5 members in clan."

        # Check member entries exist
        player_lines = [
            line for line in post_lines if "Player" in line and "Faction" not in line
        ]
        assert len(player_lines) == 5

    def test_is_member_exact_match(self, member_list):
        """Test exact player name matching."""
        assert member_list.is_member("PlayerGreen1") == "PlayerGreen1"
        assert member_list.is_member("NonExistent") is None

    def test_is_member_o_zero_substitution(self, member_list):
        """Test O/0 character substitution in player names."""
        # Test finding PlayerO by searching for Player0
        assert member_list.is_member("Player0") == "PlayerO"

    def test_is_member_partial_matching(self, member_list):
        """Test partial name matching."""
        # Partial matching should find first match
        assert member_list.is_member("PlayerGreen", partial=True) == "PlayerGreen1"

        # Exact matching should not find partial matches
        assert member_list.is_member("PlayerGreen", partial=False) is None

    def test_get_by_index(self, member_list):
        """Test retrieving members by index."""
        first_member = member_list.get(0)
        assert first_member.player == "PlayerGreen1"
        assert isinstance(first_member, IrusMember)

    def test_range_method(self, member_list):
        """Test range method returns correct range."""
        assert member_list.range() == range(0, 5)

    def test_empty_member_list(self, container):
        """Test behavior with no members."""
        mock_repo = Mock()
        mock_repo.get_all.return_value = []

        with patch("irus.memberlist.MemberRepository", return_value=mock_repo):
            empty_list = IrusMemberList(container)

            assert empty_list.count() == 0
            assert empty_list.str() == "MemberList(count=0)"
            assert empty_list.csv() == "player,faction,start\n"
            assert "Count: 0" in empty_list.markdown()
            assert empty_list.is_member("Anyone") is None

    @pytest.mark.parametrize(
        "faction,expected_count",
        [
            ("green", 3),
            ("purple", 1),
            ("yellow", 1),
            ("nonexistent", 0),
        ],
    )
    def test_faction_filtering(self, member_list, faction, expected_count):
        """Test faction filtering in markdown output."""
        markdown = member_list.markdown(faction=faction)
        assert f"Count: {expected_count}" in markdown
