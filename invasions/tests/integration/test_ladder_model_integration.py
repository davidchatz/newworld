"""Integration tests for ladder model with real DynamoDB.

These tests validate ladder creation, storage, and export formats
using the 99DDHHMM test data strategy.
"""

import time
from uuid import uuid4

import pytest
from irus.models.ladder import IrusLadder
from irus.models.ladderrank import IrusLadderRank
from irus.repositories.ladder import LadderRepository

from tests.integration.conftest import get_test_date_components


class TestLadderModelIntegration:
    """Integration tests for ladder model operations."""

    @pytest.fixture
    def repository(self, integration_container):
        """Create LadderRepository with real AWS container."""
        return LadderRepository(integration_container)

    @pytest.fixture
    def test_ladder_data(self):
        """Generate unique test ladder data using 99DDHHMM pattern."""
        timestamp = int(time.time())
        date_components = get_test_date_components()

        # Use valid settlement name (invasion format: YYYYMMDD-settlement)
        invasion_name = f"{date_components['date_string']}-bw"

        # Create 3 ranks with unique player names
        ranks = []
        for i in range(1, 4):
            player_unique_id = uuid4().hex[:8]
            rank = IrusLadderRank(
                invasion_name=invasion_name,
                rank=f"{i:02d}",
                player=f"TestPlayer-{timestamp}-{player_unique_id}",
                score=1000 - (i * 100),
                kills=10 - i,
                deaths=i,
                assists=5,
                heals=20 - i,
                damage=15000 - (i * 1000),
                member=True,
                ladder=True,
                adjusted=False,
                error=False,
            )
            ranks.append(rank)

        return {
            "invasion_name": invasion_name,
            "ranks": ranks,
            "timestamp": timestamp,
        }

    def test_save_and_retrieve_ladder(self, repository, test_ladder_data):
        """Test saving a complete ladder to DynamoDB and retrieving it."""
        # Arrange
        ladder = IrusLadder(
            invasion_name=test_ladder_data["invasion_name"],
            ranks=test_ladder_data["ranks"],
        )

        # Act - Save ladder
        repository.save_ladder(ladder)

        # Act - Retrieve ladder
        retrieved_ladder = repository.get_ladder(test_ladder_data["invasion_name"])

        # Assert - Ladder was saved and retrieved correctly
        assert retrieved_ladder is not None
        assert retrieved_ladder.invasion_name == test_ladder_data["invasion_name"]

        # Filter to our test data (database may have other data)
        test_player_names = [r.player for r in test_ladder_data["ranks"]]
        our_ranks = [r for r in retrieved_ladder.ranks if r.player in test_player_names]

        assert len(our_ranks) == 3
        assert retrieved_ladder.count >= 3  # At least our 3 ranks

        # Verify our ranks are ordered correctly
        our_sorted_ranks = sorted(our_ranks, key=lambda r: r.rank_as_int())
        for i, rank in enumerate(our_sorted_ranks):
            assert rank.rank == f"{i + 1:02d}"
            assert rank.invasion_name == test_ladder_data["invasion_name"]

    def test_ladder_csv_export(self, repository, test_ladder_data):
        """Test ladder CSV export format with real data."""
        # Arrange
        ladder = IrusLadder(
            invasion_name=test_ladder_data["invasion_name"],
            ranks=test_ladder_data["ranks"],
        )
        repository.save_ladder(ladder)

        # Act - Retrieve and export to CSV
        retrieved_ladder = repository.get_ladder(test_ladder_data["invasion_name"])
        csv_output = retrieved_ladder.to_csv()

        # Assert - CSV format is correct
        assert f"ladder for invasion {test_ladder_data['invasion_name']}" in csv_output
        assert "rank,player,score,kills,deaths,assists,heals,damage,scan" in csv_output

        # Verify all ranks appear in CSV
        for rank in test_ladder_data["ranks"]:
            assert rank.player in csv_output
            assert str(rank.score) in csv_output

    def test_ladder_markdown_export(self, repository, test_ladder_data):
        """Test ladder markdown export format."""
        # Arrange
        ladder = IrusLadder(
            invasion_name=test_ladder_data["invasion_name"],
            ranks=test_ladder_data["ranks"],
        )
        repository.save_ladder(ladder)

        # Act - Retrieve and export to markdown
        retrieved_ladder = repository.get_ladder(test_ladder_data["invasion_name"])
        markdown_output = retrieved_ladder.to_markdown()

        # Assert - Markdown format is correct
        assert "# Ladder" in markdown_output
        assert "Ranks:" in markdown_output  # Has rank count (may include other data)
        assert test_ladder_data["invasion_name"] in markdown_output

    def test_ladder_discord_post_format(self, repository, test_ladder_data):
        """Test ladder Discord post format."""
        # Arrange
        ladder = IrusLadder(
            invasion_name=test_ladder_data["invasion_name"],
            ranks=test_ladder_data["ranks"],
        )
        repository.save_ladder(ladder)

        # Act - Retrieve and format for Discord
        retrieved_ladder = repository.get_ladder(test_ladder_data["invasion_name"])
        discord_lines = retrieved_ladder.post()

        # Assert - Discord format is correct
        assert isinstance(discord_lines, list)
        assert len(discord_lines) > 0
        assert any(test_ladder_data["invasion_name"] in line for line in discord_lines)
        assert any(
            "Ranks:" in line for line in discord_lines
        )  # Has rank count (may include other data)

        # Verify all players appear in output
        discord_output = "\n".join(discord_lines)
        for rank in test_ladder_data["ranks"]:
            assert rank.player in discord_output

    def test_ladder_member_filtering(self, repository, test_ladder_data):
        """Test filtering ladder ranks to only members."""
        # Arrange - Add non-member rank
        non_member_rank = IrusLadderRank(
            invasion_name=test_ladder_data["invasion_name"],
            rank="04",
            player=f"NonMember-{int(time.time())}-{uuid4().hex[:8]}",
            score=500,
            kills=3,
            deaths=2,
            assists=1,
            heals=5,
            damage=8000,
            member=False,  # Not a member
            ladder=True,
            adjusted=False,
            error=False,
        )

        ladder = IrusLadder(
            invasion_name=test_ladder_data["invasion_name"],
            ranks=test_ladder_data["ranks"] + [non_member_rank],
        )
        repository.save_ladder(ladder)

        # Act - Retrieve ladder
        retrieved_ladder = repository.get_ladder(test_ladder_data["invasion_name"])

        # Assert - Member count only includes members
        assert retrieved_ladder.count == 4  # Total ranks including non-member
        assert retrieved_ladder.member_count == 3  # Only members with score > 0

        # Verify list_members filtering
        member_list = retrieved_ladder.list_members(member_only=True)
        assert non_member_rank.player not in member_list
        for rank in test_ladder_data["ranks"]:
            assert rank.player in member_list

    def test_ladder_member_stats_aggregation(self, repository):
        """Test aggregating stats across ladder members."""
        # Arrange - Create unique test data for this test
        timestamp = int(time.time())
        date_components = get_test_date_components()
        invasion_name = f"{date_components['date_string']}-{timestamp}-stats"

        # Create 3 ranks with unique player names
        ranks = []
        for i in range(1, 4):
            player_unique_id = uuid4().hex[:8]
            rank = IrusLadderRank(
                invasion_name=invasion_name,
                rank=f"{i:02d}",
                player=f"TestPlayer-{timestamp}-{player_unique_id}",
                score=1000 - (i * 100),
                kills=10 - i,
                deaths=i,
                assists=5,
                heals=20 - i,
                damage=15000 - (i * 1000),
                member=True,
                ladder=True,
                adjusted=False,
                error=False,
            )
            ranks.append(rank)

        ladder = IrusLadder(invasion_name=invasion_name, ranks=ranks)
        repository.save_ladder(ladder)

        # Act - Retrieve ladder
        retrieved_ladder = repository.get_ladder(invasion_name)

        # Assert - Verify computed properties
        assert retrieved_ladder.count == 3
        assert retrieved_ladder.member_count == 3

        # Verify rank lookups work
        first_rank = retrieved_ladder.get_rank_by_position(1)
        assert first_rank is not None
        assert first_rank.rank == "01"

        # Verify member lookup works
        test_player = ranks[0].player
        member_rank = retrieved_ladder.get_member_rank(test_player)
        assert member_rank is not None
        assert member_rank.player == test_player

    def test_ladder_with_zero_score_member(self, repository):
        """Test handling of members with ladder=true but score=0."""
        # Arrange - Create unique test data
        timestamp = int(time.time())
        date_components = get_test_date_components()
        invasion_name = f"{date_components['date_string']}-ef"  # Valid settlement name

        # Member with score=0 and ladder=true should not count
        zero_score_rank = IrusLadderRank(
            invasion_name=invasion_name,
            rank="01",
            player=f"ZeroScorePlayer-{timestamp}-{uuid4().hex[:8]}",
            score=0,
            kills=0,
            deaths=0,
            assists=0,
            heals=0,
            damage=0,
            member=True,
            ladder=True,  # ladder=true with score=0 means didn't score
            adjusted=False,
            error=False,
        )

        ladder = IrusLadder(invasion_name=invasion_name, ranks=[zero_score_rank])
        repository.save_ladder(ladder)

        # Act - Retrieve ladder
        retrieved_ladder = repository.get_ladder(invasion_name)

        # Assert - Member with score=0 should NOT be counted in member_count
        # Filter to our test data (database may have other data)
        our_rank = [
            r for r in retrieved_ladder.ranks if r.player == zero_score_rank.player
        ]
        assert len(our_rank) == 1  # Our rank exists

        # Verify zero-score member counting logic
        # Note: member_count may include other members, so we check the specific rank
        assert our_rank[0].score == 0
        assert our_rank[0].ladder is True
        # The get_member_rank should NOT return this player (score=0 with ladder=true)
        assert retrieved_ladder.get_member_rank(zero_score_rank.player) is None

    def test_delete_ladder(self, repository, test_ladder_data):
        """Test deleting a complete ladder from DynamoDB."""
        # Arrange - Create and save ladder
        ladder = IrusLadder(
            invasion_name=test_ladder_data["invasion_name"],
            ranks=test_ladder_data["ranks"],
        )
        repository.save_ladder(ladder)

        # Verify it exists
        assert repository.get_ladder(test_ladder_data["invasion_name"]) is not None

        # Act - Delete ladder
        deleted = repository.delete_ladder(test_ladder_data["invasion_name"])

        # Assert - Ladder was deleted
        assert deleted is True
        assert repository.get_ladder(test_ladder_data["invasion_name"]) is None

    def test_get_nonexistent_ladder(self, repository):
        """Test retrieving a ladder that doesn't exist."""
        # Arrange
        timestamp = int(time.time())
        date_components = get_test_date_components()
        nonexistent_invasion = f"{date_components['date_string']}-{timestamp}-fake"

        # Act
        result = repository.get_ladder(nonexistent_invasion)

        # Assert
        assert result is None
