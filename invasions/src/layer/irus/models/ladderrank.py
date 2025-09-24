"""Pure IrusLadderRank data model with Pydantic validation.

This module contains the pure data model for invasion ladder rankings,
with no AWS dependencies or side effects.
"""

from typing import Any

from pydantic import BaseModel, Field, field_validator


class IrusLadderRank(BaseModel):
    """Invasion ladder ranking data model.

    Represents a single player's ranking and statistics from an invasion ladder,
    including their rank, score, combat statistics, and metadata about data quality.
    This is a pure data model with validation only - no persistence logic.

    Attributes:
        invasion_name: The invasion identifier this rank belongs to
        rank: Player's rank position (formatted as 2-digit string, e.g. "01", "02")
        player: Player name
        score: Total invasion score
        kills: Number of kills
        deaths: Number of deaths
        assists: Number of assists
        heals: Number of heals performed
        damage: Total damage dealt
        member: Whether player was a company member at time of invasion
        ladder: Whether this data came from a ladder screenshot (vs roster)
        adjusted: Whether this entry was manually corrected
        error: Whether an error was detected in the data

    Example:
        >>> rank = IrusLadderRank(
        ...     invasion_name="brightwood-20240301",
        ...     rank="01",
        ...     player="TestPlayer",
        ...     score=1000,
        ...     kills=10,
        ...     deaths=2,
        ...     assists=5,
        ...     heals=20,
        ...     damage=15000,
        ...     member=True,
        ...     ladder=True,
        ...     adjusted=False,
        ...     error=False
        ... )
        >>> rank.rank
        '01'
        >>> rank.score
        1000
    """

    invasion_name: str = Field(
        ...,
        description="Invasion identifier this rank belongs to",
        min_length=1,
        max_length=100,
    )
    rank: str = Field(
        ...,
        description="Player's rank position (2-digit string)",
        pattern=r"^\d{2}$",
    )
    player: str = Field(
        ...,
        description="Player name",
        min_length=1,
        max_length=50,
    )
    score: int = Field(
        default=0,
        description="Total invasion score",
        ge=0,
    )
    kills: int = Field(
        default=0,
        description="Number of kills",
        ge=0,
    )
    deaths: int = Field(
        default=0,
        description="Number of deaths",
        ge=0,
    )
    assists: int = Field(
        default=0,
        description="Number of assists",
        ge=0,
    )
    heals: int = Field(
        default=0,
        description="Number of heals performed",
        ge=0,
    )
    damage: int = Field(
        default=0,
        description="Total damage dealt",
        ge=0,
    )
    member: bool = Field(
        default=False,
        description="Whether player was a company member at time of invasion",
    )
    ladder: bool = Field(
        default=False,
        description="Whether this data came from a ladder screenshot",
    )
    adjusted: bool = Field(
        default=False,
        description="Whether this entry was manually corrected",
    )
    error: bool = Field(
        default=False,
        description="Whether an error was detected in the data",
    )

    @field_validator("player")
    @classmethod
    def validate_player_name(cls, v: str) -> str:
        """Validate player name format."""
        if not v.strip():
            raise ValueError("Player name cannot be empty or whitespace only")
        return v.strip()

    @field_validator("invasion_name")
    @classmethod
    def validate_invasion_name(cls, v: str) -> str:
        """Validate invasion name format."""
        if not v.strip():
            raise ValueError("Invasion name cannot be empty or whitespace only")
        return v.strip()

    @field_validator("rank")
    @classmethod
    def validate_rank_format(cls, v: str) -> str:
        """Validate rank is properly formatted 2-digit string."""
        if not v.isdigit() or len(v) != 2:
            raise ValueError("Rank must be a 2-digit string (e.g., '01', '10')")

        rank_int = int(v)
        if rank_int < 1 or rank_int > 99:
            raise ValueError("Rank must be between 01 and 99")

        return v

    def key(self) -> dict[str, str]:
        """Get DynamoDB key for this ladder rank."""
        return {"invasion": f"#ladder#{self.invasion_name}", "id": self.rank}

    def to_dict(self) -> dict[str, Any]:
        """Convert to DynamoDB item format.

        Returns dictionary compatible with DynamoDB operations.
        """
        return {
            "invasion": f"#ladder#{self.invasion_name}",
            "id": self.rank,
            "member": self.member,
            "player": self.player,
            "score": self.score,
            "kills": self.kills,
            "deaths": self.deaths,
            "assists": self.assists,
            "heals": self.heals,
            "damage": self.damage,
            "ladder": self.ladder,
            "adjusted": self.adjusted,
            "error": self.error,
        }

    @classmethod
    def from_dict(cls, item: dict[str, Any], invasion_name: str) -> "IrusLadderRank":
        """Create IrusLadderRank from DynamoDB item dictionary.

        Args:
            item: DynamoDB item with ladder rank data
            invasion_name: Invasion name (extracted from item['invasion'])

        Returns:
            IrusLadderRank instance

        Raises:
            ValueError: If required fields are missing or invalid
        """
        return cls(
            invasion_name=invasion_name,
            rank=item["id"],
            player=item["player"],
            score=int(item.get("score", 0)),
            kills=int(item.get("kills", 0)),
            deaths=int(item.get("deaths", 0)),
            assists=int(item.get("assists", 0)),
            heals=int(item.get("heals", 0)),
            damage=int(item.get("damage", 0)),
            member=bool(item.get("member", False)),
            ladder=bool(item.get("ladder", False)),
            adjusted=bool(item.get("adjusted", False)),
            error=bool(item.get("error", False)),
        )

    @classmethod
    def from_roster(
        cls, invasion_name: str, rank: int, player: str
    ) -> "IrusLadderRank":
        """Create ladder rank entry from roster data.

        Args:
            invasion_name: Invasion identifier
            rank: Player rank (will be formatted as 2-digit string)
            player: Player name

        Returns:
            IrusLadderRank instance with roster defaults
        """
        return cls(
            invasion_name=invasion_name,
            rank=f"{rank:02d}",
            player=player,
            score=0,
            kills=0,
            deaths=0,
            assists=0,
            heals=0,
            damage=0,
            member=True,
            ladder=False,
            adjusted=False,
            error=False,
        )

    def rank_as_int(self) -> int:
        """Get rank as integer value."""
        return int(self.rank)

    def post(self) -> str:
        """Format rank data for Discord posting."""
        return (
            f"{self.rank:<4} {self.player:<16} {self.score:>7} "
            f"{self.kills:>5} {self.deaths:>6} {self.assists:>7} "
            f"{self.heals:>7} {self.damage:>7} {str(self.member):<6} "
            f"{str(self.ladder):<6} {str(self.adjusted):<8} {self.error}"
        )

    def str(self) -> str:
        """Format rank as markdown string."""
        header = "**`Rank Player             Score Kills Deaths Assists   Heals  Damage Member Ladder Adjusted Error`**"
        footer = """
*Member*: True if company member
*Ladder*: True if from ladder
*Adjusted*: True if entry corrected by bot or manually, False if unchanged from scan
*Error*: True if error detected but correct value not known
"""
        return f"{header}\n`{self.post()}`\n{footer}\n"

    @staticmethod
    def header() -> str:
        """Get header string for ladder rank display."""
        return "Rank Player             Score Kills Deaths Assists   Heals  Damage Member Ladder Adjusted Error"

    @staticmethod
    def footer() -> str:
        """Get footer explanation for ladder rank display."""
        return """
*Member*: True if company member
*Ladder*: True if from ladder
*Adjusted*: True if entry corrected by bot or manually, False if unchanged from scan
*Error*: True if error detected but correct value not known
"""

    model_config = {
        "validate_assignment": True,
        "use_enum_values": True,
        "extra": "forbid",
    }
