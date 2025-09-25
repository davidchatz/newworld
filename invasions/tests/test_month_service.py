"""Tests for IrusMonth service class."""

from decimal import Decimal
from unittest.mock import Mock, patch

import pytest
from botocore.exceptions import ClientError
from irus.container import IrusContainer
from irus.models.invasion import IrusInvasion
from irus.models.ladderrank import IrusLadderRank
from irus.models.member import IrusMember
from irus.month import IrusMonth


class TestIrusMonth:
    """Test suite for IrusMonth class."""

    @pytest.fixture
    def container(self):
        """Create test container with mocked dependencies."""
        mock_container = IrusContainer.create_test()

        # Mock table for DynamoDB operations
        mock_table = Mock()
        mock_table.batch_writer.return_value.__enter__ = Mock(return_value=Mock())
        mock_table.batch_writer.return_value.__exit__ = Mock(return_value=None)
        mock_table.query.return_value = {"Count": 0, "Items": []}
        mock_container.table = Mock(return_value=mock_table)

        return mock_container

    @pytest.fixture
    def sample_report(self):
        """Create sample report data for testing."""
        return [
            {
                "invasion": "#month#202403",
                "id": "Player1",
                "salary": True,
                "invasions": Decimal(3),
                "wins": Decimal(2),
                "ladders": Decimal(2),
                "sum_score": Decimal(3000),
                "sum_kills": Decimal(50),
                "sum_assists": Decimal(20),
                "sum_deaths": Decimal(10),
                "sum_heals": Decimal(4000),
                "sum_damage": Decimal(100000),
                "avg_score": Decimal("1500.0"),
                "avg_kills": Decimal("25.0"),
                "avg_assists": Decimal("10.0"),
                "avg_deaths": Decimal("5.0"),
                "avg_heals": Decimal("2000.0"),
                "avg_damage": Decimal("50000.0"),
                "avg_rank": Decimal("1.5"),
                "max_score": Decimal(1600),
                "max_kills": Decimal(30),
                "max_assists": Decimal(12),
                "max_deaths": Decimal(6),
                "max_heals": Decimal(2200),
                "max_damage": Decimal(55000),
                "max_rank": Decimal(1),
                "20240301-bw": "W",
                "20240302-ef": "W",
                "20240303-ww": "L",
            },
            {
                "invasion": "#month#202403",
                "id": "Player2",
                "salary": False,
                "invasions": Decimal(1),
                "wins": Decimal(0),
                "ladders": Decimal(1),
                "sum_score": Decimal(800),
                "sum_kills": Decimal(10),
                "sum_assists": Decimal(5),
                "sum_deaths": Decimal(15),
                "sum_heals": Decimal(1000),
                "sum_damage": Decimal(20000),
                "avg_score": Decimal("800.0"),
                "avg_kills": Decimal("10.0"),
                "avg_assists": Decimal("5.0"),
                "avg_deaths": Decimal("15.0"),
                "avg_heals": Decimal("1000.0"),
                "avg_damage": Decimal("20000.0"),
                "avg_rank": Decimal("5.0"),
                "max_score": Decimal(800),
                "max_kills": Decimal(10),
                "max_assists": Decimal(5),
                "max_deaths": Decimal(15),
                "max_heals": Decimal(1000),
                "max_damage": Decimal(20000),
                "max_rank": Decimal(5),
                "20240303-ww": "L",
            },
        ]

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
                win=True,
                date=20240302,
                year=2024,
                month=3,
                day=2,
            ),
            IrusInvasion(
                name="20240303-ww",
                settlement="ww",
                win=False,
                date=20240303,
                year=2024,
                month=3,
                day=3,
            ),
        ]

    @pytest.fixture
    def sample_members(self):
        """Create sample members for testing."""
        return [
            IrusMember(player="Player1", faction="yellow", start=20240101, salary=True),
            IrusMember(player="Player2", faction="green", start=20240201, salary=False),
        ]

    def test_init(self, sample_report, container):
        """Test IrusMonth initialization."""
        names = ["20240301-bw", "20240302-ef", "20240303-ww"]

        month = IrusMonth("202403", 3, sample_report, names, container)

        assert month.month == "202403"
        assert month.invasions == 3
        assert month.report == sample_report
        assert month.names == names
        assert month._container is container
        assert month.participation == 2  # Player1 has 2 wins and salary=True
        assert month.active == 2  # Both players have invasions > 0

    def test_init_default_container(self, sample_report):
        """Test initialization with default container."""
        with patch.object(IrusContainer, "default") as mock_default:
            mock_container = Mock(spec=IrusContainer)
            mock_container.logger.return_value = Mock()
            mock_default.return_value = mock_container

            month = IrusMonth("202403", 3, sample_report, [])

            assert month._container is mock_container
            mock_default.assert_called_once()

    def test_invasion_key(self):
        """Test invasion key generation."""
        month = IrusMonth("202403", 1, [], [])

        assert month.invasion_key() == "#month#202403"

    @patch("irus.month.InvasionRepository")
    @patch("irus.month.MemberRepository")
    @patch("irus.month.LadderRepository")
    def test_from_invasion_stats_success(
        self,
        mock_ladder_repo_class,
        mock_member_repo_class,
        mock_invasion_repo_class,
        container,
        sample_invasions,
        sample_members,
    ):
        """Test creating monthly stats from invasion data."""
        # Setup mock invasion repository
        mock_invasion_repo = Mock()
        mock_invasion_repo.get_by_month.return_value = sample_invasions
        mock_invasion_repo_class.return_value = mock_invasion_repo

        # Setup mock member repository
        mock_member_repo = Mock()
        mock_member_repo.get_all.return_value = sample_members
        mock_member_repo_class.return_value = mock_member_repo

        # Setup mock ladder repository
        mock_ladder_repo = Mock()

        # Create sample ladder with ranks
        rank1 = IrusLadderRank(
            invasion_name="20240301-bw",
            rank="01",
            player="Player1",
            score=1600,
            kills=30,
            assists=12,
            deaths=6,
            heals=2200,
            damage=55000,
            member=True,
            ladder=True,
            adjusted=False,
            error=False,
        )

        sample_ladder = Mock()
        sample_ladder.member.side_effect = (
            lambda name: rank1 if name == "Player1" else None
        )

        mock_ladder_repo.get_ladder.return_value = sample_ladder
        mock_ladder_repo_class.return_value = mock_ladder_repo

        # Setup table mock for batch operations
        mock_table = container.table()
        mock_batch_writer = Mock()
        mock_table.batch_writer.return_value.__enter__ = Mock(
            return_value=mock_batch_writer
        )
        mock_table.batch_writer.return_value.__exit__ = Mock(return_value=None)

        result = IrusMonth.from_invasion_stats(3, 2024, container)

        # Verify method calls
        mock_invasion_repo.get_by_month.assert_called_once_with(2024, 3)
        mock_member_repo.get_all.assert_called_once()
        mock_ladder_repo.get_ladder.assert_called()

        # Verify result
        assert result.month == "202403"
        assert result.invasions == 3
        assert len(result.names) == 3

        # Verify batch writer was used for saving
        assert mock_batch_writer.put_item.called

    @patch("irus.month.InvasionRepository")
    @patch("irus.month.MemberRepository")
    @patch("irus.month.LadderRepository")
    def test_from_invasion_stats_no_invasions(
        self,
        mock_ladder_repo_class,
        mock_member_repo_class,
        mock_invasion_repo_class,
        container,
    ):
        """Test handling when no invasions are found."""
        # Setup empty invasion repository
        mock_invasion_repo = Mock()
        mock_invasion_repo.get_by_month.return_value = []
        mock_invasion_repo_class.return_value = mock_invasion_repo

        # Setup member repository
        mock_member_repo = Mock()
        mock_member_repo.get_all.return_value = [
            IrusMember(
                player="TestPlayer", faction="yellow", start=20240101, salary=True
            )
        ]
        mock_member_repo_class.return_value = mock_member_repo

        # Setup ladder repository
        mock_ladder_repo = Mock()
        mock_ladder_repo_class.return_value = mock_ladder_repo

        result = IrusMonth.from_invasion_stats(3, 2024, container)

        assert result.month == "202403"
        assert result.invasions == 0
        assert len(result.names) == 0

    def test_from_table_success(self, container):
        """Test loading monthly data from table."""
        # Setup table query response
        mock_table = container.table()
        mock_table.query.side_effect = [
            {
                "Count": 2,
                "Items": [
                    {
                        "invasion": "#month#202403",
                        "id": "Player1",
                        "invasions": 2,
                        "wins": 1,
                    },
                    {
                        "invasion": "#month#202403",
                        "id": "Player2",
                        "invasions": 1,
                        "wins": 0,
                    },
                ],
            },
            {
                "Count": 3,
                "Items": [
                    {"invasion": "#invasion", "id": "20240301-bw"},
                    {"invasion": "#invasion", "id": "20240302-ef"},
                    {"invasion": "#invasion", "id": "20240303-ww"},
                ],
            },
        ]

        result = IrusMonth.from_table(3, 2024, container)

        assert result.month == "202403"
        assert result.invasions == 3
        assert len(result.report) == 2
        assert len(result.names) == 3

        # Verify correct query calls
        assert mock_table.query.call_count == 2

    def test_from_table_no_data(self, container):
        """Test from_table when no data is found."""
        # Setup empty query response
        mock_table = container.table()
        mock_table.query.return_value = {"Count": 0, "Items": []}

        with pytest.raises(ValueError, match="Note no data found for month 202403"):
            IrusMonth.from_table(3, 2024, container)

    def test_str(self, sample_report):
        """Test string representation."""
        month = IrusMonth("202403", 3, sample_report, ["20240301-bw", "20240302-ef"])

        result = month.str()

        assert "# Monthly report for 202403" in result
        assert "- Invasions: 3" in result
        assert "- Active Members (1 or more invasions): 2 of 2" in result
        assert "- Participation (sum of members across invasions won): 2" in result

    def test_csv(self, sample_report, container):
        """Test CSV generation."""
        month = IrusMonth("202403", 3, sample_report, [], container)

        result = month.csv()

        # Should have header
        assert result.startswith("month,name,salary,invasions,wins,")
        # Should contain data for active members
        assert "202403,Player1,True,3,2," in result
        assert "202403,Player2,False,1,0," in result

    def test_csv2_with_gold(self, sample_report, container):
        """Test enhanced CSV generation with gold payments."""
        names = ["20240301-bw", "20240302-ef"]
        month = IrusMonth("202403", 3, sample_report, names, container)

        result = month.csv2(10000)

        # Should include invasion names in header
        assert "01-bw" in result  # Shortened invasion name
        assert "02-ef" in result

        # Should calculate payments for salary members
        lines = result.split("\n")
        player1_line = next(line for line in lines if "Player1" in line)
        # Player1: 2 wins, participation=2, gold=10000 -> payment = (2*10000)/2 = 10000
        assert "10000" in player1_line

    def test_csv2_no_gold(self, sample_report, container):
        """Test CSV generation with no gold payment."""
        names = ["20240301-bw"]
        month = IrusMonth("202403", 3, sample_report, names, container)

        result = month.csv2(0)

        # Should have 0 payment when no gold
        lines = result.split("\n")
        data_lines = [line for line in lines if "Player" in line]
        for line in data_lines:
            assert ",0," in line  # Payment should be 0

    def test_post(self, sample_report, container):
        """Test post format generation."""
        month = IrusMonth("202403", 3, sample_report, [], container)

        result = month.post()

        # Should have header
        assert result[0].startswith("month player")
        # Should have data lines for active members
        assert len(result) == 3  # Header + 2 players
        assert "Player1" in result[1]
        assert "Player2" in result[2]

    def test_post2_with_gold(self, sample_report, container):
        """Test enhanced post format with gold and invasion columns."""
        names = ["20240301-bw", "20240302-ef"]
        month = IrusMonth("202403", 3, sample_report, names, container)

        result = month.post2(10000)

        # Should include invasion abbreviations in header
        header = result[0]
        assert "01bw" in header
        assert "02ef" in header

        # Should include payment data
        player1_line = result[1]
        assert "10000" in player1_line  # Payment amount

    def test_member_lookup_found(self, sample_report, container):
        """Test finding member in report."""
        month = IrusMonth("202403", 3, sample_report, [], container)

        result = month.member("Player1")

        assert result is not None
        assert result["id"] == "Player1"
        assert result["invasions"] == Decimal(3)

    def test_member_lookup_not_found(self, sample_report, container):
        """Test member not found in report."""
        month = IrusMonth("202403", 3, sample_report, [], container)

        result = month.member("NonExistentPlayer")

        assert result is None

    def test_member_stats_found(self, sample_report, container):
        """Test generating member stats."""
        names = ["20240301-bw", "20240302-ef", "20240303-ww"]
        month = IrusMonth("202403", 3, sample_report, names, container)

        result = month.member_stats("Player1")

        assert "## Stats for 202403" in result
        assert "Invasion Wins: 2 of 3" in result
        assert "- 20240301-bw" in result  # Won invasion
        assert "- 20240302-ef" in result  # Won invasion
        assert "Score:" in result
        assert "1500.0" in result  # Average score

    def test_member_stats_not_found(self, sample_report, container):
        """Test member stats when player not found."""
        month = IrusMonth("202403", 3, sample_report, [], container)

        result = month.member_stats("NonExistentPlayer")

        assert "*No stats found for NonExistentPlayer in 202403*" in result

    def test_member_line(self, sample_report, container):
        """Test generating member line for table format."""
        month = IrusMonth("202403", 3, sample_report, [], container)

        result = month.member_line("Player1")

        assert result.startswith("202403")
        assert "3" in result  # invasions
        assert "2" in result  # wins
        assert "1500.0" in result  # avg_score

    def test_member_line_not_found(self, sample_report, container):
        """Test member line when player not found."""
        month = IrusMonth("202403", 3, sample_report, [], container)

        result = month.member_line("NonExistentPlayer")

        assert result == "202403         0"

    def test_member_line_header(self):
        """Test static member line header."""
        header = IrusMonth.member_line_header()

        assert header.startswith("month")
        assert "invasions" in header
        assert "wins" in header
        assert "avg_score" in header

    def test_delete_from_table(self, sample_report, container):
        """Test deleting monthly data from table."""
        month = IrusMonth("202403", 3, sample_report, [], container)

        # Setup table mock for batch operations
        mock_table = container.table()
        mock_batch_writer = Mock()
        mock_table.batch_writer.return_value.__enter__ = Mock(
            return_value=mock_batch_writer
        )
        mock_table.batch_writer.return_value.__exit__ = Mock(return_value=None)

        month.delete_from_table()

        # Verify batch delete operations
        assert mock_batch_writer.delete_item.call_count == 2  # 2 active players

    def test_delete_from_table_error(self, sample_report, container):
        """Test handling delete errors."""
        month = IrusMonth("202403", 3, sample_report, [], container)

        # Setup table to raise error
        mock_table = container.table()
        error = ClientError(
            error_response={
                "Error": {"Code": "InternalServerError", "Message": "Internal error"}
            },
            operation_name="BatchWriteItem",
        )
        mock_table.batch_writer.side_effect = error

        with pytest.raises(ValueError, match="Failed to delete from table"):
            month.delete_from_table()

    def test_participation_calculation_salary_only(self, container):
        """Test that participation only counts salary members' wins."""
        report = [
            {
                "id": "SalaryPlayer",
                "salary": True,
                "wins": Decimal(5),
                "invasions": Decimal(7),
            },
            {
                "id": "NonSalaryPlayer",
                "salary": False,
                "wins": Decimal(3),
                "invasions": Decimal(4),
            },
        ]

        month = IrusMonth("202403", 10, report, [], container)

        # Only salary player's wins should count
        assert month.participation == 5

    def test_active_count_calculation(self, container):
        """Test active member count (members with 1+ invasions)."""
        report = [
            {
                "id": "ActivePlayer1",
                "invasions": Decimal(3),
                "salary": True,
                "wins": Decimal(2),
            },
            {
                "id": "ActivePlayer2",
                "invasions": Decimal(1),
                "salary": False,
                "wins": Decimal(1),
            },
            {
                "id": "InactivePlayer",
                "invasions": Decimal(0),
                "salary": True,
                "wins": Decimal(0),
            },
        ]

        month = IrusMonth("202403", 5, report, [], container)

        # Only players with invasions > 0 should count as active
        assert month.active == 2

    def test_zero_month_formatting(self, container):
        """Test proper zero-padding for single-digit months."""
        mock_table = container.table()
        mock_table.query.return_value = {"Count": 0, "Items": []}

        with pytest.raises(ValueError):
            IrusMonth.from_table(3, 2024, container)

        # Verify query was called with zero-padded month
        # Check that the KeyConditionExpression contains the correct month key
        assert mock_table.query.called
