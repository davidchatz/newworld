"""Tests for collection service classes."""

from unittest.mock import Mock, patch

import pytest
from irus.container import IrusContainer
from irus.invasionlist import IrusInvasionList
from irus.memberlist import IrusMemberList
from irus.models.invasion import IrusInvasion
from irus.models.member import IrusMember


class TestIrusInvasionList:
    """Test suite for IrusInvasionList class."""

    @pytest.fixture
    def mock_repository(self):
        """Create mock invasion repository."""
        mock_repo = Mock()
        return mock_repo

    @pytest.fixture
    def container(self, mock_repository):
        """Create test container with mocked dependencies."""
        mock_container = IrusContainer.create_test()

        # Mock the repository creation
        with patch("irus.invasionlist.InvasionRepository") as mock_repo_class:
            mock_repo_class.return_value = mock_repository
            yield mock_container

    @pytest.fixture
    def sample_invasions(self):
        """Create sample invasions for testing."""
        return [
            IrusInvasion(
                name="20240301-bw",
                settlement="bw",
                win=True,
                date=20240301,
                year=2024,
                month=3,
                day=1,
            ),
            IrusInvasion(
                name="20240302-ef",
                settlement="ef",
                win=False,
                date=20240302,
                year=2024,
                month=3,
                day=2,
            ),
        ]

    def test_init(self, sample_invasions):
        """Test IrusInvasionList initialization."""
        invasion_list = IrusInvasionList(sample_invasions, 20240301)

        assert invasion_list.invasions == sample_invasions
        assert invasion_list.start == 20240301
        assert invasion_list._container is not None
        assert invasion_list._logger is not None

    def test_init_with_container(self, sample_invasions, container):
        """Test IrusInvasionList initialization with specific container."""
        invasion_list = IrusInvasionList(sample_invasions, 20240301, container)

        assert invasion_list.invasions == sample_invasions
        assert invasion_list._container is container

    def test_from_month(self, mock_repository, sample_invasions):
        """Test creating invasion list from month using repository."""
        mock_repository.get_by_month.return_value = sample_invasions

        with patch("irus.invasionlist.InvasionRepository") as mock_repo_class:
            mock_repo_class.return_value = mock_repository

            result = IrusInvasionList.from_month(3, 2024)

            assert result.invasions == sample_invasions
            assert result.start == 20240301
            mock_repository.get_by_month.assert_called_once_with(2024, 3)

    def test_from_month_with_container(
        self, mock_repository, sample_invasions, container
    ):
        """Test creating invasion list from month with specific container."""
        mock_repository.get_by_month.return_value = sample_invasions

        with patch("irus.invasionlist.InvasionRepository") as mock_repo_class:
            mock_repo_class.return_value = mock_repository

            result = IrusInvasionList.from_month(3, 2024, container)

            assert result.invasions == sample_invasions
            assert result._container is container
            mock_repo_class.assert_called_once_with(container)

    def test_from_start(self, mock_repository, sample_invasions):
        """Test creating invasion list from start date using repository."""
        mock_repository.get_by_date_range.return_value = sample_invasions

        with patch("irus.invasionlist.InvasionRepository") as mock_repo_class:
            mock_repo_class.return_value = mock_repository

            result = IrusInvasionList.from_start(20240301)

            assert result.invasions == sample_invasions
            assert result.start == 20240301
            mock_repository.get_by_date_range.assert_called_once_with(
                20240301, 99999999
            )

    def test_str_empty(self):
        """Test string representation with empty list."""
        invasion_list = IrusInvasionList([], 20240301)

        result = invasion_list.str()

        assert result == ""

    def test_str_single_invasion(self, sample_invasions):
        """Test string representation with single invasion."""
        invasion_list = IrusInvasionList([sample_invasions[0]], 20240301)

        result = invasion_list.str()

        assert result == "20240301-bw\n"

    def test_str_multiple_invasions(self, sample_invasions):
        """Test string representation with multiple invasions."""
        invasion_list = IrusInvasionList(sample_invasions, 20240301)

        result = invasion_list.str()

        assert result == "20240301-bw,20240302-ef\n"

    def test_markdown_empty(self):
        """Test markdown representation with empty list."""
        invasion_list = IrusInvasionList([], 20240301)

        result = invasion_list.markdown()

        assert "# Invasions from 20240301" in result
        assert "*No invasions found*" in result

    def test_markdown_with_invasions(self, sample_invasions):
        """Test markdown representation with invasions."""
        invasion_list = IrusInvasionList(sample_invasions, 20240301)

        result = invasion_list.markdown()

        assert "# Invasions from 20240301" in result
        assert "- 20240301-bw" in result
        assert "- 20240302-ef" in result

    def test_count(self, sample_invasions):
        """Test counting invasions."""
        invasion_list = IrusInvasionList(sample_invasions, 20240301)

        assert invasion_list.count() == 2

    def test_range(self, sample_invasions):
        """Test getting range of invasions."""
        invasion_list = IrusInvasionList(sample_invasions, 20240301)

        result = invasion_list.range()

        assert list(result) == [0, 1]

    def test_get(self, sample_invasions):
        """Test getting invasion by index."""
        invasion_list = IrusInvasionList(sample_invasions, 20240301)

        assert invasion_list.get(0) == sample_invasions[0]
        assert invasion_list.get(1) == sample_invasions[1]


class TestIrusMemberList:
    """Test suite for IrusMemberList class."""

    @pytest.fixture
    def mock_repository(self):
        """Create mock member repository."""
        mock_repo = Mock()
        return mock_repo

    @pytest.fixture
    def container(self, mock_repository):
        """Create test container with mocked dependencies."""
        mock_container = IrusContainer.create_test()

        # Mock the repository creation
        with patch("irus.memberlist.MemberRepository") as mock_repo_class:
            mock_repo_class.return_value = mock_repository
            yield mock_container

    @pytest.fixture
    def sample_members(self):
        """Create sample members for testing."""
        return [
            IrusMember(
                player="TestPlayer1", faction="yellow", start=20240101, salary=True
            ),
            IrusMember(
                player="TestPlayer2", faction="green", start=20240201, salary=False
            ),
            IrusMember(
                player="TestPlayer3", faction="purple", start=20240115, salary=True
            ),
        ]

    def test_init(self, mock_repository, sample_members, container):
        """Test IrusMemberList initialization."""
        mock_repository.get_all.return_value = sample_members

        with patch("irus.memberlist.MemberRepository") as mock_repo_class:
            mock_repo_class.return_value = mock_repository

            member_list = IrusMemberList(container)

            assert member_list.members == sample_members
            assert member_list._container is container
            mock_repository.get_all.assert_called_once()

    def test_init_empty_members(self, mock_repository, container):
        """Test initialization with no members found."""
        mock_repository.get_all.return_value = []

        with patch("irus.memberlist.MemberRepository") as mock_repo_class:
            mock_repo_class.return_value = mock_repository

            member_list = IrusMemberList(container)

            assert member_list.members == []

    def test_str(self, mock_repository, sample_members, container):
        """Test string representation."""
        mock_repository.get_all.return_value = sample_members

        with patch("irus.memberlist.MemberRepository") as mock_repo_class:
            mock_repo_class.return_value = mock_repository

            member_list = IrusMemberList(container)

            assert member_list.str() == "MemberList(count=3)"

    def test_csv(self, mock_repository, sample_members, container):
        """Test CSV generation ordered by faction."""
        mock_repository.get_all.return_value = sample_members

        with patch("irus.memberlist.MemberRepository") as mock_repo_class:
            mock_repo_class.return_value = mock_repository

            member_list = IrusMemberList(container)
            result = member_list.csv()

            # Should have header
            assert result.startswith("player,faction,start\n")

            # Should be ordered by faction: green, purple, yellow
            lines = result.strip().split("\n")[1:]  # Skip header
            assert "TestPlayer2,green,20240201" in lines
            assert "TestPlayer3,purple,20240115" in lines
            assert "TestPlayer1,yellow,20240101" in lines

    def test_markdown_no_faction_filter(
        self, mock_repository, sample_members, container
    ):
        """Test markdown generation without faction filter."""
        mock_repository.get_all.return_value = sample_members

        with patch("irus.memberlist.MemberRepository") as mock_repo_class:
            mock_repo_class.return_value = mock_repository

            member_list = IrusMemberList(container)
            result = member_list.markdown()

            assert "# Member List" in result
            assert "Count: 3" in result
            assert "TestPlayer1 (yellow) started 20240101" in result
            assert "TestPlayer2 (green) started 20240201" in result
            assert "TestPlayer3 (purple) started 20240115" in result

    def test_markdown_with_faction_filter(
        self, mock_repository, sample_members, container
    ):
        """Test markdown generation with faction filter."""
        mock_repository.get_all.return_value = sample_members

        with patch("irus.memberlist.MemberRepository") as mock_repo_class:
            mock_repo_class.return_value = mock_repository

            member_list = IrusMemberList(container)
            result = member_list.markdown("yellow")

            assert "# Member List for yellow" in result
            assert "Count: 1" in result
            assert "TestPlayer1 (yellow) started 20240101" in result
            assert "TestPlayer2" not in result  # Should be filtered out

    def test_post_no_faction_filter(self, mock_repository, sample_members, container):
        """Test post format generation without faction filter."""
        mock_repository.get_all.return_value = sample_members

        with patch("irus.memberlist.MemberRepository") as mock_repo_class:
            mock_repo_class.return_value = mock_repository

            member_list = IrusMemberList(container)
            result = member_list.post()

            assert "Player         Faction Start" in result
            assert "3 members in clan." in result
            assert "TestPlayer1    yellow  20240101" in result

    def test_post_with_faction_filter(self, mock_repository, sample_members, container):
        """Test post format generation with faction filter."""
        mock_repository.get_all.return_value = sample_members

        with patch("irus.memberlist.MemberRepository") as mock_repo_class:
            mock_repo_class.return_value = mock_repository

            member_list = IrusMemberList(container)
            result = member_list.post("green")

            result_str = "\n".join(result)
            assert "1 members in clan for faction green." in result_str
            assert "TestPlayer2" in result_str
            assert "TestPlayer1" not in result_str  # Should be filtered out

    def test_count(self, mock_repository, sample_members, container):
        """Test counting members."""
        mock_repository.get_all.return_value = sample_members

        with patch("irus.memberlist.MemberRepository") as mock_repo_class:
            mock_repo_class.return_value = mock_repository

            member_list = IrusMemberList(container)

            assert member_list.count() == 3

    def test_range(self, mock_repository, sample_members, container):
        """Test getting range of members."""
        mock_repository.get_all.return_value = sample_members

        with patch("irus.memberlist.MemberRepository") as mock_repo_class:
            mock_repo_class.return_value = mock_repository

            member_list = IrusMemberList(container)
            result = member_list.range()

            assert list(result) == [0, 1, 2]

    def test_get(self, mock_repository, sample_members, container):
        """Test getting member by index."""
        mock_repository.get_all.return_value = sample_members

        with patch("irus.memberlist.MemberRepository") as mock_repo_class:
            mock_repo_class.return_value = mock_repository

            member_list = IrusMemberList(container)

            assert member_list.get(0) == sample_members[0]
            assert member_list.get(1) == sample_members[1]
            assert member_list.get(2) == sample_members[2]

    def test_is_member_exact_match(self, mock_repository, sample_members, container):
        """Test member lookup with exact name match."""
        mock_repository.get_all.return_value = sample_members

        with patch("irus.memberlist.MemberRepository") as mock_repo_class:
            mock_repo_class.return_value = mock_repository

            member_list = IrusMemberList(container)

            assert member_list.is_member("TestPlayer1") == "TestPlayer1"
            assert member_list.is_member("TestPlayer2") == "TestPlayer2"
            assert member_list.is_member("NonExistentPlayer") is None

    def test_is_member_o_zero_substitution(self, mock_repository, container):
        """Test member lookup with O/0 character substitution."""
        # Create member with 'O' in name
        member_with_o = IrusMember(
            player="TestPlayerO", faction="yellow", start=20240101, salary=True
        )
        mock_repository.get_all.return_value = [member_with_o]

        with patch("irus.memberlist.MemberRepository") as mock_repo_class:
            mock_repo_class.return_value = mock_repository

            member_list = IrusMemberList(container)

            # Should find member when searching with '0' instead of 'O'
            assert member_list.is_member("TestPlayer0") == "TestPlayerO"
            # Should also work the other way
            assert member_list.is_member("TestPlayerO") == "TestPlayerO"

    def test_is_member_partial_match(self, mock_repository, sample_members, container):
        """Test member lookup with partial name matching."""
        mock_repository.get_all.return_value = sample_members

        with patch("irus.memberlist.MemberRepository") as mock_repo_class:
            mock_repo_class.return_value = mock_repository

            member_list = IrusMemberList(container)

            # Should find with partial match when partial=True
            assert member_list.is_member("TestPlayer", partial=True) == "TestPlayer1"
            # Should not find with partial match when partial=False (default)
            assert member_list.is_member("TestPlayer", partial=False) is None
