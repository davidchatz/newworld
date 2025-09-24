"""Tests for IrusLadderRank pure model."""

import pytest
from irus.models.ladderrank import IrusLadderRank
from pydantic import ValidationError


class TestIrusLadderRank:
    """Test suite for IrusLadderRank model."""

    def test_basic_creation(self):
        """Test basic ladder rank creation."""
        rank = IrusLadderRank(
            invasion_name="brightwood-20240301",
            rank="01",
            player="TestPlayer",
            score=1000,
            kills=10,
            deaths=2,
            assists=5,
            heals=20,
            damage=15000,
            member=True,
            ladder=True,
            adjusted=False,
            error=False,
        )

        assert rank.invasion_name == "brightwood-20240301"
        assert rank.rank == "01"
        assert rank.player == "TestPlayer"
        assert rank.score == 1000
        assert rank.kills == 10
        assert rank.deaths == 2
        assert rank.assists == 5
        assert rank.heals == 20
        assert rank.damage == 15000
        assert rank.member is True
        assert rank.ladder is True
        assert rank.adjusted is False
        assert rank.error is False

    def test_creation_with_defaults(self):
        """Test ladder rank creation with default values."""
        rank = IrusLadderRank(
            invasion_name="brightwood-20240301",
            rank="05",
            player="TestPlayer",
        )

        assert rank.invasion_name == "brightwood-20240301"
        assert rank.rank == "05"
        assert rank.player == "TestPlayer"
        assert rank.score == 0
        assert rank.kills == 0
        assert rank.deaths == 0
        assert rank.assists == 0
        assert rank.heals == 0
        assert rank.damage == 0
        assert rank.member is False
        assert rank.ladder is False
        assert rank.adjusted is False
        assert rank.error is False

    def test_rank_validation(self):
        """Test rank format validation."""
        # Valid ranks
        valid_ranks = ["01", "05", "10", "50", "99"]
        for rank_str in valid_ranks:
            rank = IrusLadderRank(
                invasion_name="test", rank=rank_str, player="TestPlayer"
            )
            assert rank.rank == rank_str

        # Invalid ranks
        invalid_ranks = ["1", "0", "100", "ab", "", "001"]
        for invalid_rank in invalid_ranks:
            with pytest.raises(ValidationError):
                IrusLadderRank(
                    invasion_name="test", rank=invalid_rank, player="TestPlayer"
                )

    def test_player_name_validation(self):
        """Test player name validation."""
        # Valid names
        valid_names = ["TestPlayer", "Player With Spaces", "Player123", "A" * 50]
        for name in valid_names:
            rank = IrusLadderRank(invasion_name="test", rank="01", player=name)
            assert rank.player == name.strip()

        # Invalid names
        invalid_names = ["", "   ", "A" * 51]
        for invalid_name in invalid_names:
            with pytest.raises(ValidationError):
                IrusLadderRank(invasion_name="test", rank="01", player=invalid_name)

    def test_invasion_name_validation(self):
        """Test invasion name validation."""
        # Valid names
        valid_names = ["brightwood-20240301", "test", "a" * 100]
        for name in valid_names:
            rank = IrusLadderRank(invasion_name=name, rank="01", player="TestPlayer")
            assert rank.invasion_name == name.strip()

        # Invalid names
        invalid_names = ["", "   ", "a" * 101]
        for invalid_name in invalid_names:
            with pytest.raises(ValidationError):
                IrusLadderRank(
                    invasion_name=invalid_name, rank="01", player="TestPlayer"
                )

    def test_numeric_field_validation(self):
        """Test validation of numeric fields."""
        # Valid positive numbers
        rank = IrusLadderRank(
            invasion_name="test",
            rank="01",
            player="TestPlayer",
            score=1000,
            kills=50,
            deaths=5,
            assists=25,
            heals=100,
            damage=20000,
        )
        assert rank.score == 1000
        assert rank.kills == 50
        assert rank.deaths == 5
        assert rank.assists == 25
        assert rank.heals == 100
        assert rank.damage == 20000

        # Zero values should be valid
        rank = IrusLadderRank(
            invasion_name="test",
            rank="01",
            player="TestPlayer",
            score=0,
            kills=0,
            deaths=0,
            assists=0,
            heals=0,
            damage=0,
        )
        assert all(
            getattr(rank, field) == 0
            for field in ["score", "kills", "deaths", "assists", "heals", "damage"]
        )

        # Negative values should be invalid
        numeric_fields = ["score", "kills", "deaths", "assists", "heals", "damage"]
        for field in numeric_fields:
            with pytest.raises(ValidationError):
                IrusLadderRank(
                    invasion_name="test", rank="01", player="TestPlayer", **{field: -1}
                )

    def test_key_method(self):
        """Test DynamoDB key generation."""
        rank = IrusLadderRank(
            invasion_name="brightwood-20240301", rank="05", player="TestPlayer"
        )

        key = rank.key()
        expected = {"invasion": "#ladder#brightwood-20240301", "id": "05"}
        assert key == expected

    def test_to_dict(self):
        """Test conversion to DynamoDB item format."""
        rank = IrusLadderRank(
            invasion_name="brightwood-20240301",
            rank="05",
            player="TestPlayer",
            score=1000,
            kills=10,
            deaths=2,
            assists=5,
            heals=20,
            damage=15000,
            member=True,
            ladder=True,
            adjusted=False,
            error=False,
        )

        item = rank.to_dict()
        expected = {
            "invasion": "#ladder#brightwood-20240301",
            "id": "05",
            "member": True,
            "player": "TestPlayer",
            "score": 1000,
            "kills": 10,
            "deaths": 2,
            "assists": 5,
            "heals": 20,
            "damage": 15000,
            "ladder": True,
            "adjusted": False,
            "error": False,
        }
        assert item == expected

    def test_from_dict(self):
        """Test creation from DynamoDB item."""
        item = {
            "invasion": "#ladder#brightwood-20240301",
            "id": "05",
            "player": "TestPlayer",
            "score": 1000,
            "kills": 10,
            "deaths": 2,
            "assists": 5,
            "heals": 20,
            "damage": 15000,
            "member": True,
            "ladder": True,
            "adjusted": False,
            "error": False,
        }

        rank = IrusLadderRank.from_dict(item, "brightwood-20240301")

        assert rank.invasion_name == "brightwood-20240301"
        assert rank.rank == "05"
        assert rank.player == "TestPlayer"
        assert rank.score == 1000
        assert rank.kills == 10
        assert rank.deaths == 2
        assert rank.assists == 5
        assert rank.heals == 20
        assert rank.damage == 15000
        assert rank.member is True
        assert rank.ladder is True
        assert rank.adjusted is False
        assert rank.error is False

    def test_from_dict_with_missing_fields(self):
        """Test creation from DynamoDB item with missing optional fields."""
        item = {
            "invasion": "#ladder#brightwood-20240301",
            "id": "05",
            "player": "TestPlayer",
        }

        rank = IrusLadderRank.from_dict(item, "brightwood-20240301")

        assert rank.invasion_name == "brightwood-20240301"
        assert rank.rank == "05"
        assert rank.player == "TestPlayer"
        assert rank.score == 0
        assert rank.kills == 0
        assert rank.deaths == 0
        assert rank.assists == 0
        assert rank.heals == 0
        assert rank.damage == 0
        assert rank.member is False
        assert rank.ladder is False
        assert rank.adjusted is False
        assert rank.error is False

    def test_from_roster(self):
        """Test creation from roster data."""
        rank = IrusLadderRank.from_roster("brightwood-20240301", 5, "TestPlayer")

        assert rank.invasion_name == "brightwood-20240301"
        assert rank.rank == "05"
        assert rank.player == "TestPlayer"
        assert rank.score == 0
        assert rank.kills == 0
        assert rank.deaths == 0
        assert rank.assists == 0
        assert rank.heals == 0
        assert rank.damage == 0
        assert rank.member is True  # Roster entries are always members
        assert rank.ladder is False  # Roster entries are not from ladder
        assert rank.adjusted is False
        assert rank.error is False

    def test_rank_as_int(self):
        """Test rank_as_int method."""
        rank = IrusLadderRank(invasion_name="test", rank="05", player="TestPlayer")
        assert rank.rank_as_int() == 5

        rank = IrusLadderRank(invasion_name="test", rank="15", player="TestPlayer")
        assert rank.rank_as_int() == 15

    def test_post_formatting(self):
        """Test post method formatting."""
        rank = IrusLadderRank(
            invasion_name="test",
            rank="05",
            player="TestPlayer",
            score=1000,
            kills=10,
            deaths=2,
            assists=5,
            heals=20,
            damage=15000,
            member=True,
            ladder=True,
            adjusted=False,
            error=False,
        )

        post_str = rank.post()
        # Should be formatted for Discord display
        assert "05" in post_str
        assert "TestPlayer" in post_str
        assert "1000" in post_str
        assert "True" in post_str
        assert "False" in post_str

    def test_str_formatting(self):
        """Test str method formatting."""
        rank = IrusLadderRank(
            invasion_name="test",
            rank="05",
            player="TestPlayer",
            score=1000,
            kills=10,
            deaths=2,
            assists=5,
            heals=20,
            damage=15000,
            member=True,
            ladder=True,
            adjusted=False,
            error=False,
        )

        str_output = rank.str()
        # Should include header, data, and footer
        assert "Rank Player" in str_output
        assert "TestPlayer" in str_output
        assert "*Member*:" in str_output

    def test_static_methods(self):
        """Test static header and footer methods."""
        header = IrusLadderRank.header()
        footer = IrusLadderRank.footer()

        assert "Rank" in header
        assert "Player" in header
        assert "Score" in header
        assert "Member" in header

        assert "*Member*:" in footer
        assert "*Ladder*:" in footer
        assert "*Adjusted*:" in footer
        assert "*Error*:" in footer

    def test_model_config(self):
        """Test that model validation is strict."""
        # Extra fields should be forbidden
        with pytest.raises(ValidationError):
            IrusLadderRank(
                invasion_name="test",
                rank="01",
                player="TestPlayer",
                invalid_field="should_fail",
            )

    @pytest.mark.parametrize(
        "rank_str,expected_int",
        [
            ("01", 1),
            ("05", 5),
            ("10", 10),
            ("25", 25),
            ("99", 99),
        ],
    )
    def test_rank_formatting(self, rank_str, expected_int):
        """Test rank formatting and conversion."""
        rank = IrusLadderRank(invasion_name="test", rank=rank_str, player="TestPlayer")
        assert rank.rank == rank_str
        assert rank.rank_as_int() == expected_int
