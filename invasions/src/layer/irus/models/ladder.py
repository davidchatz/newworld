"""Pure IrusLadder data model with Pydantic validation.

This module contains the pure data model for invasion ladders,
with no AWS dependencies or side effects.
"""

from pydantic import BaseModel, Field, computed_field, field_validator

from .ladderrank import IrusLadderRank


class IrusLadder(BaseModel):
    """Invasion ladder data model.

    Represents a complete invasion ladder containing multiple player rankings.
    This is a pure data container with validation only - no persistence logic.

    Attributes:
        invasion_name: The invasion identifier this ladder belongs to
        ranks: List of ladder rank entries, ordered by rank

    Example:
        >>> rank1 = IrusLadderRank(
        ...     invasion_name="brightwood-20240301",
        ...     rank="01",
        ...     player="Player1",
        ...     score=1000,
        ...     member=True,
        ...     ladder=True
        ... )
        >>> rank2 = IrusLadderRank(
        ...     invasion_name="brightwood-20240301",
        ...     rank="02",
        ...     player="Player2",
        ...     score=800,
        ...     member=False,
        ...     ladder=True
        ... )
        >>> ladder = IrusLadder(
        ...     invasion_name="brightwood-20240301",
        ...     ranks=[rank1, rank2]
        ... )
        >>> ladder.count
        2
        >>> ladder.member_count
        1
    """

    invasion_name: str = Field(
        ...,
        description="Invasion identifier this ladder belongs to",
        min_length=1,
        max_length=100,
    )
    ranks: list[IrusLadderRank] = Field(
        default_factory=list,
        description="List of ladder rank entries",
    )

    @field_validator("invasion_name")
    @classmethod
    def validate_invasion_name(cls, v: str) -> str:
        """Validate invasion name format."""
        if not v.strip():
            raise ValueError("Invasion name cannot be empty or whitespace only")
        return v.strip()

    @field_validator("ranks")
    @classmethod
    def validate_ranks_invasion_match(
        cls, v: list[IrusLadderRank], info
    ) -> list[IrusLadderRank]:
        """Validate that all ranks belong to the same invasion."""
        if not hasattr(info, "data") or "invasion_name" not in info.data:
            return v  # Skip validation if invasion_name not available yet

        invasion_name = info.data["invasion_name"]
        for rank in v:
            if rank.invasion_name != invasion_name:
                raise ValueError(
                    f"Rank for {rank.player} belongs to invasion {rank.invasion_name}, "
                    f"expected {invasion_name}"
                )
        return v

    @computed_field
    @property
    def count(self) -> int:
        """Total number of ranks in ladder."""
        return len(self.ranks)

    @computed_field
    @property
    def member_count(self) -> int:
        """Count of company members who scored in the invasion."""
        return sum(
            1
            for rank in self.ranks
            if rank.member and (not rank.ladder or rank.score > 0)
        )

    def get_rank_by_position(self, position: int) -> IrusLadderRank | None:
        """Get rank entry by rank position.

        Args:
            position: Rank position (1-based)

        Returns:
            IrusLadderRank if found, None otherwise
        """
        for rank in self.ranks:
            if rank.rank_as_int() == position:
                return rank
        return None

    def get_member_rank(self, player: str) -> IrusLadderRank | None:
        """Get rank entry for a company member.

        Only returns ranks for company members who scored in the invasion.

        Args:
            player: Player name

        Returns:
            IrusLadderRank if found, None otherwise
        """
        for rank in self.ranks:
            if (
                rank.player == player
                and rank.member
                and (not rank.ladder or rank.score > 0)
            ):
                return rank
        return None

    def contiguous_from_1_until(self) -> int:
        """Find how many ranks are contiguous starting from rank 1.

        Returns:
            Number of contiguous ranks from position 1
        """
        expected_rank = 1
        for rank in sorted(self.ranks, key=lambda r: r.rank_as_int()):
            if rank.rank_as_int() != expected_rank:
                return expected_rank - 1
            expected_rank += 1
        return expected_rank - 1

    def list_members(self, member_only: bool = True) -> str:
        """Get formatted list of players.

        Args:
            member_only: If True, only include company members

        Returns:
            Comma-separated string of player names with status indicators
        """
        message = ""
        for rank in self.ranks:
            if not member_only or rank.member:
                prefix = ""
                suffix = ""

                if rank.error:
                    prefix = "**"
                    suffix = "**"
                elif rank.adjusted:
                    prefix = "*"
                    suffix = "*"

                message += f"{prefix}[{rank.rank}] {rank.player}{suffix}, "

        return message.rstrip(", ")

    def to_csv(self) -> str:
        """Export ladder to CSV format.

        Returns:
            CSV string with ladder data
        """
        lines = [
            f"ladder for invasion {self.invasion_name}",
            "rank,player,score,kills,deaths,assists,heals,damage,scan",
        ]

        for rank in sorted(self.ranks, key=lambda r: r.rank_as_int()):
            scan_status = (
                "error" if rank.error else ("adjusted" if rank.adjusted else "ok")
            )
            lines.append(
                f"{rank.rank},{rank.player},{rank.score},{rank.kills},"
                f"{rank.deaths},{rank.assists},{rank.heals},{rank.damage},{scan_status}"
            )

        return "\n".join(lines)

    def to_markdown(self) -> str:
        """Export ladder to markdown format.

        Returns:
            Markdown string with ladder summary
        """
        return f"# Ladder\nRanks: {self.count}\nInvasion: {self.invasion_name}\n"

    def post(self) -> list[str]:
        """Format ladder data for Discord posting.

        Returns:
            List of strings formatted for Discord
        """
        lines = [
            f"Invasion: {self.invasion_name}",
            f"Ranks: {self.count}",
            IrusLadderRank.header(),
        ]

        for rank in sorted(self.ranks, key=lambda r: r.rank_as_int()):
            lines.append(rank.post())

        lines.append(IrusLadderRank.footer())
        return lines

    def str(self) -> str:
        """Format ladder summary as string."""
        return (
            f"Ladder for invasion {self.invasion_name} with "
            f"{self.count} rank(s) including {self.member_count} member(s)"
        )

    model_config = {
        "validate_assignment": True,
        "use_enum_values": True,
        "extra": "forbid",
    }
