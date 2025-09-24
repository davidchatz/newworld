"""Pure IrusInvasion data model with Pydantic validation.

This module contains the pure data model for invasion events,
with no AWS dependencies or side effects.
"""

from datetime import datetime
from typing import Any, ClassVar

from pydantic import BaseModel, Field, computed_field, field_validator


class IrusInvasion(BaseModel):
    """New World invasion event data model.

    Represents an invasion event with settlement, outcome, and timing information.
    This is a pure data model with validation only - no persistence logic.

    Attributes:
        name: Unique invasion identifier (YYYYMMDD-settlement format)
        settlement: Settlement code (2-letter abbreviation)
        win: Whether the invasion was won (True) or lost (False)
        date: Date as YYYYMMDD integer
        year: Year component
        month: Month component (1-12)
        day: Day component (1-31)
        notes: Additional notes about the invasion (optional)

    Example:
        >>> invasion = IrusInvasion(
        ...     name="20240301-bw",
        ...     settlement="bw",
        ...     win=True,
        ...     date=20240301,
        ...     year=2024,
        ...     month=3,
        ...     day=1,
        ...     notes="Great coordination!"
        ... )
        >>> invasion.settlement_name
        'Brightwood'
    """

    # Class constant for settlement mapping
    SETTLEMENT_MAP: ClassVar[dict[str, str]] = {
        "bw": "Brightwood",
        "bs": "Brimstone Sands",
        "ck": "Cutlass Keys",
        "er": "Ebonscale Reach",
        "eg": "Edengrove",
        "ef": "Everfall",
        "mb": "Monarchs Bluff",
        "md": "Mourningdale",
        "rw": "Reekwater",
        "rs": "Restless Shore",
        "wf": "Weavers Fen",
        "ww": "Windsward",
    }

    name: str = Field(
        ...,
        description="Unique invasion identifier (YYYYMMDD-settlement format)",
        min_length=8,
        max_length=15,
    )
    settlement: str = Field(..., description="Settlement code (2-letter abbreviation)")
    win: bool = Field(
        ..., description="Whether the invasion was won (True) or lost (False)"
    )
    date: int = Field(
        ..., description="Date as YYYYMMDD integer", ge=20200101, le=99991231
    )
    year: int = Field(..., description="Year component", ge=2020, le=9999)
    month: int = Field(..., description="Month component (1-12)", ge=1, le=12)
    day: int = Field(..., description="Day component (1-31)", ge=1, le=31)
    notes: str | None = Field(
        default=None, description="Additional notes about the invasion", max_length=1000
    )

    @field_validator("settlement")
    @classmethod
    def validate_settlement(cls, v: str) -> str:
        """Validate that settlement is a known settlement code."""
        if v.lower() not in cls.SETTLEMENT_MAP:
            valid_codes = ", ".join(sorted(cls.SETTLEMENT_MAP.keys()))
            raise ValueError(f"Unknown settlement {v}. Valid codes: {valid_codes}")
        return v.lower()

    @field_validator("date")
    @classmethod
    def validate_date_format(cls, v: int) -> int:
        """Validate date format and existence."""
        date_str = str(v)
        if len(date_str) != 8:
            raise ValueError("Date must be YYYYMMDD format (8 digits)")

        try:
            year = int(date_str[:4])
            month = int(date_str[4:6])
            day = int(date_str[6:8])

            # Validate the date exists
            datetime(year, month, day)

        except (ValueError, TypeError) as e:
            raise ValueError(f"Invalid date {v}: {str(e)}") from e

        return v

    @field_validator("name")
    @classmethod
    def validate_name_format(cls, v: str) -> str:
        """Validate invasion name format."""
        if "-" not in v:
            raise ValueError("Invasion name must be in format YYYYMMDD-settlement")

        parts = v.split("-")
        if len(parts) != 2:
            raise ValueError("Invasion name must be in format YYYYMMDD-settlement")

        date_part, settlement_part = parts

        # Validate date part
        if len(date_part) != 8 or not date_part.isdigit():
            raise ValueError("Date part must be YYYYMMDD format")

        # Settlement validation will be handled by settlement field validator
        return v

    @computed_field
    @property
    def settlement_name(self) -> str:
        """Get the full settlement name."""
        return self.SETTLEMENT_MAP[self.settlement]

    def key(self) -> dict[str, str]:
        """Get DynamoDB key for this invasion."""
        return {"invasion": "#invasion", "id": self.name}

    def to_dict(self) -> dict[str, Any]:
        """Convert to DynamoDB item format.

        Returns dictionary compatible with DynamoDB operations.
        """
        item = {
            "invasion": "#invasion",
            "id": self.name,
            "settlement": self.settlement,
            "win": self.win,
            "date": self.date,
            "year": self.year,
            "month": self.month,
            "day": self.day,
        }
        if self.notes is not None:
            item["notes"] = self.notes
        return item

    @classmethod
    def from_dict(cls, item: dict[str, Any]) -> "IrusInvasion":
        """Create IrusInvasion from DynamoDB item dictionary.

        Args:
            item: DynamoDB item with invasion data

        Returns:
            IrusInvasion instance

        Raises:
            ValueError: If required fields are missing or invalid
        """
        return cls(
            name=item["id"],
            settlement=item["settlement"],
            win=bool(item["win"]),
            date=int(item["date"]),
            year=int(item["year"]),
            month=int(item["month"]),
            day=int(item["day"]),
            notes=item.get("notes"),
        )

    @classmethod
    def create_from_user_input(
        cls,
        day: int,
        month: int,
        year: int,
        settlement: str,
        win: bool,
        notes: str | None = None,
    ) -> "IrusInvasion":
        """Create invasion from user input parameters.

        Args:
            day: Day (1-31)
            month: Month (1-12)
            year: Year (e.g. 2024)
            settlement: Settlement code
            win: Whether invasion was won
            notes: Optional notes

        Returns:
            New IrusInvasion instance

        Raises:
            ValueError: If validation fails
        """
        # Validate the date exists
        datetime(year, month, day)

        date = int(f"{year}{month:02d}{day:02d}")
        name = f"{date}-{settlement.lower()}"

        return cls(
            name=name,
            settlement=settlement.lower(),
            win=win,
            date=date,
            year=year,
            month=month,
            day=day,
            notes=notes,
        )

    def __str__(self) -> str:
        """String representation of invasion."""
        msg = f"{self.name}, {self.settlement}, {self.date}, {self.win}"
        if self.notes:
            msg += f", {self.notes}"
        return msg

    def markdown(self) -> str:
        """Format invasion as markdown string."""
        msg = f"## Invasion {self.name}\n"
        msg += f"Settlement: {self.settlement_name}\n"
        msg += f"Date: {self.date}\n"
        msg += f"Win: {self.win}\n"
        if self.notes:
            msg += f"Notes: {self.notes}\n"
        return msg

    def post(self) -> list[str]:
        """Format invasion data as list of strings for Discord posting."""
        msg = [
            f"Invasion: {self.name}",
            f"Settlement: {self.settlement_name}",
            f"Date: {self.date}",
            f"Win: {self.win}",
        ]
        if self.notes:
            msg.append(f"Notes: {self.notes}")
        return msg

    def month_prefix(self) -> str:
        """Get YYYYMM prefix for monthly operations."""
        return f"{self.year}{self.month:02d}"

    def path_ladders(self) -> str:
        """Get S3 path for ladder files."""
        return f"ladders/{self.name}/"

    def path_roster(self) -> str:
        """Get S3 path for roster files."""
        return f"roster/{self.name}/"

    model_config = {
        "validate_assignment": True,
        "use_enum_values": True,
        "extra": "forbid",
    }
