"""Pure IrusMember data model with Pydantic validation.

This module contains the pure data model for company members,
with no AWS dependencies or side effects.
"""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field, field_validator


class IrusMember(BaseModel):
    """New World company member data model.

    Represents a player's membership in the company with their faction,
    administrative status, salary eligibility, and contact information.
    This is a pure data model with validation only - no persistence logic.

    Attributes:
        start: Start date as YYYYMMDD integer
        player: Player name (unique identifier)
        faction: Player's faction (covenant, marauders, syndicate)
        admin: Whether player has administrative privileges
        salary: Whether player is eligible for company salary
        discord: Discord username/ID (optional)
        notes: Additional notes about the player (optional)

    Example:
        >>> member = IrusMember(
        ...     start=20240301,
        ...     player="TestPlayer",
        ...     faction="covenant",
        ...     admin=False,
        ...     salary=True,
        ...     discord="testplayer#1234"
        ... )
        >>> member.player
        'TestPlayer'
        >>> member.faction
        'covenant'
    """

    start: int = Field(
        ...,
        description="Member start date as YYYYMMDD integer",
        ge=20200101,  # Game release was in 2021, so 2020 is reasonable lower bound
        le=99991231,  # Reasonable upper bound
    )
    player: str = Field(
        ...,
        description="Player name (unique identifier)",
        min_length=1,
        max_length=50,  # New World character name limit
    )
    faction: str = Field(..., description="Player's faction")
    admin: bool = Field(
        default=False, description="Whether player has administrative privileges"
    )
    salary: bool = Field(
        default=False, description="Whether player is eligible for company salary"
    )
    discord: str | None = Field(
        default=None, description="Discord username/ID", max_length=100
    )
    notes: str | None = Field(
        default=None, description="Additional notes about the player", max_length=500
    )

    @field_validator("faction")
    @classmethod
    def validate_faction(cls, v: str) -> str:
        """Validate that faction is one of the three valid New World factions."""
        valid_factions = {"covenant", "marauders", "syndicate"}
        if v.lower() not in valid_factions:
            raise ValueError(f"Faction must be one of: {', '.join(valid_factions)}")
        return v.lower()

    @field_validator("player")
    @classmethod
    def validate_player_name(cls, v: str) -> str:
        """Validate player name format."""
        if not v.strip():
            raise ValueError("Player name cannot be empty or whitespace only")
        return v.strip()

    @field_validator("start")
    @classmethod
    def validate_start_date(cls, v: int) -> int:
        """Validate start date format."""
        start_str = str(v)
        if len(start_str) != 8:
            raise ValueError("Start date must be YYYYMMDD format (8 digits)")

        try:
            year = int(start_str[:4])
            month = int(start_str[4:6])
            day = int(start_str[6:8])

            # Basic validation
            if not (1 <= month <= 12):
                raise ValueError(f"Invalid month: {month}")
            if not (1 <= day <= 31):
                raise ValueError(f"Invalid day: {day}")

            # Validate the date exists
            datetime(year, month, day)

        except (ValueError, TypeError) as e:
            raise ValueError(f"Invalid start date {v}: {str(e)}") from e

        return v

    def key(self) -> dict[str, str]:
        """Get DynamoDB key for this member."""
        return {"invasion": "#member", "id": self.player}

    def to_dict(self) -> dict[str, Any]:
        """Convert to DynamoDB item format.

        Returns dictionary compatible with DynamoDB operations.
        """
        item = {
            "invasion": "#member",
            "id": self.player,
            "start": self.start,
            "faction": self.faction,
            "admin": self.admin,
            "salary": self.salary,
        }
        if self.discord is not None:
            item["discord"] = self.discord
        if self.notes is not None:
            item["notes"] = self.notes
        return item

    @classmethod
    def from_dict(cls, item: dict[str, Any]) -> "IrusMember":
        """Create IrusMember from DynamoDB item dictionary.

        Args:
            item: DynamoDB item with member data

        Returns:
            IrusMember instance

        Raises:
            ValueError: If required fields are missing or invalid
        """
        return cls(
            start=int(item["start"]),
            player=item["id"],
            faction=item["faction"],
            admin=bool(item["admin"]),
            salary=bool(item["salary"]),
            discord=item.get("discord"),
            notes=item.get("notes"),
        )

    @staticmethod
    def create_start_date(day: int, month: int, year: int) -> int:
        """Create a start date integer from day, month, year components.

        Args:
            day: Day (1-31)
            month: Month (1-12)
            year: Year (e.g. 2024)

        Returns:
            Start date as YYYYMMDD integer

        Raises:
            ValueError: If date is invalid
        """
        # Validate the date
        datetime(year, month, day)

        return int(f"{year}{month:02d}{day:02d}")

    def str(self) -> str:
        """Format member as markdown string."""
        return (
            f"## Member {self.player}\n"
            f"Faction: {self.faction}\n"
            f"Starting {self.start}\n"
            f"Admin {self.admin}\n"
        )

    def post(self) -> list[str]:
        """Format member data as list of strings for Discord posting."""
        msg = [
            f"Faction: {self.faction}",
            f"Starting: {self.start}",
            f"Admin: {self.admin}",
            f"Earns salary: {self.salary}",
        ]
        if self.notes and len(self.notes) > 0:
            msg.append(f"Notes: {self.notes}")
        return msg

    model_config = {
        "validate_assignment": True,
        "use_enum_values": True,
        "extra": "forbid",
    }
