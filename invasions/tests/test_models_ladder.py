"""Tests for IrusLadder pure model."""

import pytest
from irus.models.ladder import IrusLadder
from irus.models.ladderrank import IrusLadderRank
from pydantic import ValidationError


class TestIrusLadder:
    """Test suite for IrusLadder model."""

    @pytest.fixture
    def sample_ranks(self):
        """Fixture providing sample ladder ranks."""
        return [
            IrusLadderRank(
                invasion_name="brightwood-20240301",
                rank="01",
                player="Player1",
                score=1000,
                kills=10,
                deaths=2,
                assists=5,
                heals=20,
                damage=15000,
                member=True,
                ladder=True,
            ),
            IrusLadderRank(
                invasion_name="brightwood-20240301",
                rank="02",
                player="Player2",
                score=800,
                kills=8,
                deaths=3,
                assists=4,
                heals=15,
                damage=12000,
                member=False,
                ladder=True,
            ),
            IrusLadderRank(
                invasion_name="brightwood-20240301",
                rank="03",
                player="Player3",
                score=600,
                kills=6,
                deaths=4,
                assists=3,
                heals=10,
                damage=9000,
                member=True,
                ladder=True,
            ),
        ]

    def test_basic_creation(self, sample_ranks):
        """Test basic ladder creation."""
        ladder = IrusLadder(invasion_name="brightwood-20240301", ranks=sample_ranks)

        assert ladder.invasion_name == "brightwood-20240301"
        assert len(ladder.ranks) == 3
        assert ladder.count == 3
        assert ladder.member_count == 2  # Player1 and Player3 are members

    def test_creation_empty_ranks(self):
        """Test ladder creation with empty ranks list."""
        ladder = IrusLadder(invasion_name="brightwood-20240301")

        assert ladder.invasion_name == "brightwood-20240301"
        assert len(ladder.ranks) == 0
        assert ladder.count == 0
        assert ladder.member_count == 0

    def test_invasion_name_validation(self):
        """Test invasion name validation."""
        # Valid names
        valid_names = ["brightwood-20240301", "test", "a" * 100]
        for name in valid_names:
            ladder = IrusLadder(invasion_name=name)
            assert ladder.invasion_name == name.strip()

        # Invalid names
        invalid_names = ["", "   ", "a" * 101]
        for invalid_name in invalid_names:
            with pytest.raises(ValidationError):
                IrusLadder(invasion_name=invalid_name)

    def test_ranks_invasion_validation(self, sample_ranks):
        """Test that ranks must belong to the same invasion."""
        # All ranks match - should work
        ladder = IrusLadder(invasion_name="brightwood-20240301", ranks=sample_ranks)
        assert len(ladder.ranks) == 3

        # Mismatched invasion - should fail
        mismatched_rank = IrusLadderRank(
            invasion_name="different-invasion", rank="01", player="MismatchedPlayer"
        )

        with pytest.raises(
            ValidationError, match="belongs to invasion different-invasion"
        ):
            IrusLadder(invasion_name="brightwood-20240301", ranks=[mismatched_rank])

    def test_computed_properties(self, sample_ranks):
        """Test computed properties."""
        ladder = IrusLadder(invasion_name="brightwood-20240301", ranks=sample_ranks)

        assert ladder.count == 3
        assert (
            ladder.member_count == 2
        )  # Only Player1 and Player3 are members with scores > 0

    def test_get_rank_by_position(self, sample_ranks):
        """Test getting rank by position."""
        ladder = IrusLadder(invasion_name="brightwood-20240301", ranks=sample_ranks)

        # Valid positions
        rank1 = ladder.get_rank_by_position(1)
        assert rank1 is not None
        assert rank1.player == "Player1"
        assert rank1.rank == "01"

        rank2 = ladder.get_rank_by_position(2)
        assert rank2 is not None
        assert rank2.player == "Player2"
        assert rank2.rank == "02"

        # Invalid position
        rank_none = ladder.get_rank_by_position(99)
        assert rank_none is None

    def test_get_member_rank(self, sample_ranks):
        """Test getting rank for company members."""
        ladder = IrusLadder(invasion_name="brightwood-20240301", ranks=sample_ranks)

        # Member with score > 0
        member_rank = ladder.get_member_rank("Player1")
        assert member_rank is not None
        assert member_rank.player == "Player1"
        assert member_rank.member is True

        # Non-member
        non_member_rank = ladder.get_member_rank("Player2")
        assert non_member_rank is None

        # Non-existent player
        not_found = ladder.get_member_rank("NonExistentPlayer")
        assert not_found is None

    def test_get_member_rank_with_roster_entries(self):
        """Test member rank filtering with roster entries (score = 0)."""
        ranks = [
            IrusLadderRank(
                invasion_name="test",
                rank="01",
                player="ActiveMember",
                score=1000,  # Scored in invasion
                member=True,
                ladder=True,
            ),
            IrusLadderRank(
                invasion_name="test",
                rank="02",
                player="RosterMember",
                score=0,  # Just on roster, didn't score
                member=True,
                ladder=False,  # From roster
            ),
        ]

        ladder = IrusLadder(invasion_name="test", ranks=ranks)

        # Active member should be found
        active = ladder.get_member_rank("ActiveMember")
        assert active is not None
        assert active.player == "ActiveMember"

        # Roster member should also be found (ladder=False allows score=0)
        roster = ladder.get_member_rank("RosterMember")
        assert roster is not None
        assert roster.player == "RosterMember"

    def test_contiguous_from_1_until(self):
        """Test contiguous rank checking."""
        # Contiguous ranks 1, 2, 3
        ranks = [
            IrusLadderRank(invasion_name="test", rank="01", player="P1"),
            IrusLadderRank(invasion_name="test", rank="02", player="P2"),
            IrusLadderRank(invasion_name="test", rank="03", player="P3"),
        ]
        ladder = IrusLadder(invasion_name="test", ranks=ranks)
        assert ladder.contiguous_from_1_until() == 3

        # Gap at rank 2
        ranks = [
            IrusLadderRank(invasion_name="test", rank="01", player="P1"),
            IrusLadderRank(
                invasion_name="test", rank="03", player="P3"
            ),  # Missing rank 2
        ]
        ladder = IrusLadder(invasion_name="test", ranks=ranks)
        assert ladder.contiguous_from_1_until() == 1

        # Starts at rank 5
        ranks = [
            IrusLadderRank(invasion_name="test", rank="05", player="P5"),
            IrusLadderRank(invasion_name="test", rank="06", player="P6"),
        ]
        ladder = IrusLadder(invasion_name="test", ranks=ranks)
        assert ladder.contiguous_from_1_until() == 0  # No rank 1

        # Empty ladder
        ladder = IrusLadder(invasion_name="test", ranks=[])
        assert ladder.contiguous_from_1_until() == 0

    def test_list_members(self, sample_ranks):
        """Test formatted member listing."""
        ladder = IrusLadder(invasion_name="brightwood-20240301", ranks=sample_ranks)

        # Members only
        member_list = ladder.list_members(member_only=True)
        assert "[01] Player1" in member_list
        assert "[03] Player3" in member_list
        assert "[02] Player2" not in member_list  # Not a member

        # All players
        all_list = ladder.list_members(member_only=False)
        assert "[01] Player1" in all_list
        assert "[02] Player2" in all_list
        assert "[03] Player3" in all_list

    def test_list_members_with_status_indicators(self):
        """Test member listing with error/adjusted indicators."""
        ranks = [
            IrusLadderRank(
                invasion_name="test",
                rank="01",
                player="NormalPlayer",
                member=True,
            ),
            IrusLadderRank(
                invasion_name="test",
                rank="02",
                player="AdjustedPlayer",
                member=True,
                adjusted=True,
            ),
            IrusLadderRank(
                invasion_name="test",
                rank="03",
                player="ErrorPlayer",
                member=True,
                error=True,
            ),
        ]

        ladder = IrusLadder(invasion_name="test", ranks=ranks)
        member_list = ladder.list_members()

        assert "[01] NormalPlayer" in member_list
        assert "*[02] AdjustedPlayer*" in member_list
        assert "**[03] ErrorPlayer**" in member_list

    def test_to_csv(self, sample_ranks):
        """Test CSV export."""
        ladder = IrusLadder(invasion_name="brightwood-20240301", ranks=sample_ranks)

        csv_output = ladder.to_csv()
        lines = csv_output.split("\n")

        assert "ladder for invasion brightwood-20240301" in lines[0]
        assert "rank,player,score,kills,deaths,assists,heals,damage,scan" in lines[1]
        assert "01,Player1,1000,10,2,5,20,15000,ok" in lines[2]
        assert "02,Player2,800,8,3,4,15,12000,ok" in lines[3]
        assert "03,Player3,600,6,4,3,10,9000,ok" in lines[4]

    def test_to_csv_with_status_indicators(self):
        """Test CSV export with scan status indicators."""
        ranks = [
            IrusLadderRank(
                invasion_name="test",
                rank="01",
                player="NormalPlayer",
            ),
            IrusLadderRank(
                invasion_name="test",
                rank="02",
                player="AdjustedPlayer",
                adjusted=True,
            ),
            IrusLadderRank(
                invasion_name="test",
                rank="03",
                player="ErrorPlayer",
                error=True,
            ),
        ]

        ladder = IrusLadder(invasion_name="test", ranks=ranks)
        csv_output = ladder.to_csv()

        assert "01,NormalPlayer,0,0,0,0,0,0,ok" in csv_output
        assert "02,AdjustedPlayer,0,0,0,0,0,0,adjusted" in csv_output
        assert "03,ErrorPlayer,0,0,0,0,0,0,error" in csv_output

    def test_to_markdown(self, sample_ranks):
        """Test Markdown export."""
        ladder = IrusLadder(invasion_name="brightwood-20240301", ranks=sample_ranks)

        markdown = ladder.to_markdown()
        assert "# Ladder" in markdown
        assert "Ranks: 3" in markdown
        assert "Invasion: brightwood-20240301" in markdown

    def test_post(self, sample_ranks):
        """Test Discord post formatting."""
        ladder = IrusLadder(invasion_name="brightwood-20240301", ranks=sample_ranks)

        post_lines = ladder.post()
        assert "Invasion: brightwood-20240301" in post_lines
        assert "Ranks: 3" in post_lines

        # Should include header
        header_found = any("Rank Player" in line for line in post_lines)
        assert header_found

        # Should include all players
        assert any("Player1" in line for line in post_lines)
        assert any("Player2" in line for line in post_lines)
        assert any("Player3" in line for line in post_lines)

        # Should include footer
        footer_found = any("*Member*:" in line for line in post_lines)
        assert footer_found

    def test_str(self, sample_ranks):
        """Test string summary."""
        ladder = IrusLadder(invasion_name="brightwood-20240301", ranks=sample_ranks)

        summary = ladder.str()
        assert "brightwood-20240301" in summary
        assert "3 rank(s)" in summary
        assert "2 member(s)" in summary

    def test_ranks_sorted_in_post_and_csv(self):
        """Test that ranks are sorted by position in output methods."""
        # Create ranks in random order
        ranks = [
            IrusLadderRank(
                invasion_name="test", rank="03", player="Player3", score=300
            ),
            IrusLadderRank(
                invasion_name="test", rank="01", player="Player1", score=500
            ),
            IrusLadderRank(
                invasion_name="test", rank="02", player="Player2", score=400
            ),
        ]

        ladder = IrusLadder(invasion_name="test", ranks=ranks)

        # CSV should be sorted
        csv_output = ladder.to_csv()
        lines = csv_output.split("\n")[2:5]  # Skip header lines
        assert "01,Player1" in lines[0]
        assert "02,Player2" in lines[1]
        assert "03,Player3" in lines[2]

        # Post should be sorted
        post_lines = ladder.post()
        player_lines = [
            line
            for line in post_lines
            if "Player" in line and "Rank Player" not in line
        ]
        assert "Player1" in player_lines[0]
        assert "Player2" in player_lines[1]
        assert "Player3" in player_lines[2]

    def test_model_config(self):
        """Test that model validation is strict."""
        # Extra fields should be forbidden
        with pytest.raises(ValidationError):
            IrusLadder(invasion_name="test", ranks=[], invalid_field="should_fail")

    def test_empty_ladder_operations(self):
        """Test operations on empty ladder."""
        ladder = IrusLadder(invasion_name="test")

        assert ladder.count == 0
        assert ladder.member_count == 0
        assert ladder.get_rank_by_position(1) is None
        assert ladder.get_member_rank("AnyPlayer") is None
        assert ladder.contiguous_from_1_until() == 0
        assert ladder.list_members() == ""

        # CSV and other formats should still work
        csv_output = ladder.to_csv()
        assert "test" in csv_output
        assert "rank,player,score" in csv_output

        markdown = ladder.to_markdown()
        assert "Ranks: 0" in markdown

    @pytest.mark.parametrize(
        "member_count,expected",
        [
            (0, 0),  # No members
            (1, 1),  # One member
            (3, 3),  # Multiple members
        ],
    )
    def test_member_count_calculation(self, member_count, expected):
        """Test member count calculation."""
        ranks = []
        for i in range(member_count):
            ranks.append(
                IrusLadderRank(
                    invasion_name="test",
                    rank=f"{i + 1:02d}",
                    player=f"Member{i + 1}",
                    score=100,  # Non-zero score
                    member=True,
                    ladder=True,
                )
            )

        # Add some non-members
        for i in range(2):
            ranks.append(
                IrusLadderRank(
                    invasion_name="test",
                    rank=f"{member_count + i + 1:02d}",
                    player=f"NonMember{i + 1}",
                    score=100,
                    member=False,
                    ladder=True,
                )
            )

        ladder = IrusLadder(invasion_name="test", ranks=ranks)
        assert ladder.member_count == expected
