from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field, field_validator

from .environ import IrusResources

logger = IrusResources.logger()
table = IrusResources.table()


class IrusMember(BaseModel):
    """New World company member data model.

    Represents a player's membership in the company with their faction,
    administrative status, salary eligibility, and contact information.

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

    def __init__(self, item_or_start=None, **kwargs):
        """Initialize IrusMember with backward compatibility.

        Can be called with:
        1. Dictionary (old API): IrusMember({'start': 20240301, 'id': 'player', ...})
        2. Named parameters (new API): IrusMember(start=20240301, player='player', ...)
        """
        if item_or_start is not None and isinstance(item_or_start, dict) and not kwargs:
            # Old API: called with dictionary
            super().__init__(
                **{
                    "start": int(item_or_start["start"]),
                    "player": item_or_start["id"],
                    "faction": item_or_start["faction"],
                    "admin": bool(item_or_start["admin"]),
                    "salary": bool(item_or_start["salary"]),
                    "discord": item_or_start.get("discord"),
                    "notes": item_or_start.get("notes"),
                }
            )
        else:
            # New API: called with named parameters
            if item_or_start is not None:
                kwargs["start"] = item_or_start
            super().__init__(**kwargs)

    def key(self) -> dict[str, str]:
        """Get DynamoDB key for this member."""
        return {"invasion": "#member", "id": self.player}

    def to_dict(self) -> dict[str, Any]:
        """Convert to DynamoDB item format for backward compatibility."""
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
    def from_user(
        cls,
        player: str,
        day: int,
        month: int,
        year: int,
        faction: str,
        admin: bool,
        salary: bool,
        discord: str | None = None,
        notes: str | None = None,
    ) -> "IrusMember":
        """Create a new member from user input and save to database.

        Args:
            player: Player name
            day: Start day (1-31)
            month: Start month (1-12)
            year: Start year (e.g. 2024)
            faction: Player faction
            admin: Administrative privileges
            salary: Salary eligibility
            discord: Discord username (optional)
            notes: Additional notes (optional)

        Returns:
            New IrusMember instance

        Raises:
            ValueError: If validation fails
        """
        logger.info(f"Member.from_user {player}")

        zero_month = f"{month:02d}"
        zero_day = f"{day:02d}"
        start = int(f"{year}{zero_month}{zero_day}")

        timestamp = datetime.today().strftime("%Y%m%d%H%M%S")

        additem = {
            "invasion": "#memberevent",
            "id": timestamp,
            "event": "add",
            "player": player,
            "faction": faction,
            "admin": admin,
            "salary": salary,
            "start": start,
        }

        if discord:
            additem["discord"] = discord
        if notes:
            additem["notes"] = notes

        memberitem = {
            "invasion": "#member",
            "id": player,
            "faction": faction,
            "admin": admin,
            "salary": salary,
            "event": timestamp,
            "start": start,
        }

        if discord:
            memberitem["discord"] = discord
        if notes:
            memberitem["notes"] = notes

        # Add event for adding this member and update list of members
        table.put_item(Item=additem)
        logger.debug(f"Put {additem}")
        table.put_item(Item=memberitem)
        logger.debug(f"Put {memberitem}")

        return cls.from_dict(memberitem)

    @classmethod
    def from_table(cls, player: str) -> "IrusMember":
        """Load member from DynamoDB table.

        Args:
            player: Player name to look up

        Returns:
            IrusMember instance

        Raises:
            ValueError: If member not found
        """
        logger.info(f"Member.from_table {player}")

        member = table.get_item(Key={"invasion": "#member", "id": player})

        if "Item" not in member:
            logger.info(f"Member {player} not found in table")
            raise ValueError(f"No member found called {player}")

        return cls.from_dict(member["Item"])

    def str(self) -> str:
        """Format member as markdown string."""
        return f"## Member {self.player}\nFaction: {self.faction}\nStarting {self.start}\nAdmin {self.admin}\n"

    def remove(self) -> str:
        """Remove member from database and log the event.

        Returns:
            Status message indicating success or failure

        Raises:
            ValueError: If member is not initialized
        """
        logger.info(f"Member.remove {self.player}")

        if not self.player:
            msg = "Member not initialised or has been removed"
            logger.warning(msg)
            raise ValueError(msg)

        timestamp = datetime.today().strftime("%Y%m%d%H%M%S")

        item = {
            "invasion": "#memberevent",
            "id": timestamp,
            "event": "delete",
            "player": self.player,
        }

        response = table.delete_item(Key=self.key(), ReturnValues="ALL_OLD")
        if "Attributes" in response:
            mesg = f"## Removed member {self.player}"
            table.put_item(Item=item)
            # Note: Cannot modify player field in Pydantic model after creation
            # This would require creating a new instance or using a different approach
        else:
            mesg = f"*Member {self.player} not found, nothing to remove*"

        logger.info(mesg)
        return mesg

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
