"""Backward compatibility facade for IrusInvasion.

This module provides backward compatibility for the legacy IrusInvasion class
while internally using the new repository pattern architecture.

DEPRECATED: This facade is provided for backward compatibility only.
New code should use irus.models.invasion.IrusInvasion and irus.repositories.invasion.InvasionRepository directly.
"""

import warnings
from typing import Any

from .models.invasion import IrusInvasion as PureInvasion
from .repositories.invasion import InvasionRepository

# Issue deprecation warning when this module is imported
warnings.warn(
    "irus.invasion module is deprecated. Use irus.models.invasion.IrusInvasion and "
    "irus.repositories.invasion.InvasionRepository instead.",
    DeprecationWarning,
    stacklevel=2,
)


class IrusInvasion:
    """Legacy IrusInvasion class for backward compatibility.

    This class wraps the new repository pattern implementation to maintain
    backward compatibility with existing code.

    DEPRECATED: Use irus.models.invasion.IrusInvasion and irus.repositories.invasion.InvasionRepository instead.
    """

    # Re-export settlement map for backward compatibility
    settlement_map = PureInvasion.SETTLEMENT_MAP

    def __init__(
        self,
        name: str,
        settlement: str,
        win: bool,
        date: int,
        year: int,
        month: int,
        day: int,
        notes: str = None,
    ):
        """Initialize from parameters (legacy API).

        Args:
            name: Invasion name
            settlement: Settlement code
            win: Whether invasion was won
            date: Date as YYYYMMDD integer
            year: Year component
            month: Month component
            day: Day component
            notes: Optional notes
        """
        # Create the pure model
        self._model = PureInvasion(
            name=name,
            settlement=settlement,
            win=win,
            date=date,
            year=year,
            month=month,
            day=day,
            notes=notes,
        )
        # Create repository for database operations
        self._repository = InvasionRepository()

    @property
    def name(self) -> str:
        """Get invasion name."""
        return self._model.name

    @property
    def settlement(self) -> str:
        """Get settlement code."""
        return self._model.settlement

    @property
    def win(self) -> bool:
        """Get win status."""
        return self._model.win

    @property
    def date(self) -> int:
        """Get date."""
        return self._model.date

    @property
    def year(self) -> int:
        """Get year."""
        return self._model.year

    @property
    def month(self) -> int:
        """Get month."""
        return self._model.month

    @property
    def day(self) -> int:
        """Get day."""
        return self._model.day

    @property
    def notes(self) -> str | None:
        """Get notes."""
        return self._model.notes

    def key(self) -> dict[str, str]:
        """Get DynamoDB key for this invasion."""
        return self._model.key()

    @classmethod
    def from_user(
        cls,
        day: int,
        month: int,
        year: int,
        settlement: str,
        win: bool,
        notes: str = None,
    ) -> "IrusInvasion":
        """Create a new invasion from user input and save to database.

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
            ValueError: If validation fails or invasion already exists
        """
        repository = InvasionRepository()
        pure_invasion = repository.create_from_user_input(
            day=day, month=month, year=year, settlement=settlement, win=win, notes=notes
        )

        # Convert back to legacy wrapper using the pure model data
        return cls(
            name=pure_invasion.name,
            settlement=pure_invasion.settlement,
            win=pure_invasion.win,
            date=pure_invasion.date,
            year=pure_invasion.year,
            month=pure_invasion.month,
            day=pure_invasion.day,
            notes=pure_invasion.notes,
        )

    @classmethod
    def from_table(cls, name: str) -> "IrusInvasion":
        """Load invasion from DynamoDB table.

        Args:
            name: Invasion name to look up

        Returns:
            IrusInvasion instance

        Raises:
            ValueError: If invasion not found
        """
        repository = InvasionRepository()
        pure_invasion = repository.get_by_name(name)

        if pure_invasion is None:
            raise ValueError(f"No invasion found called {name}")

        # Convert to legacy wrapper
        return cls(
            name=pure_invasion.name,
            settlement=pure_invasion.settlement,
            win=pure_invasion.win,
            date=pure_invasion.date,
            year=pure_invasion.year,
            month=pure_invasion.month,
            day=pure_invasion.day,
            notes=pure_invasion.notes,
        )

    @classmethod
    def from_table_item(cls, item: dict[str, Any]) -> "IrusInvasion":
        """Create invasion from table item dictionary.

        Args:
            item: DynamoDB item dictionary

        Returns:
            IrusInvasion instance
        """
        pure_invasion = PureInvasion.from_dict(item)

        return cls(
            name=pure_invasion.name,
            settlement=pure_invasion.settlement,
            win=pure_invasion.win,
            date=pure_invasion.date,
            year=pure_invasion.year,
            month=pure_invasion.month,
            day=pure_invasion.day,
            notes=pure_invasion.notes,
        )

    def __str__(self) -> str:
        """String representation of invasion."""
        return str(self._model)

    def markdown(self) -> str:
        """Format invasion as markdown string."""
        return self._model.markdown()

    def post(self) -> list[str]:
        """Format invasion data as list of strings for Discord posting."""
        return self._model.post()

    def delete_from_table(self) -> None:
        """Delete invasion from table."""
        self._repository.delete_by_name(self.name)

    def month_prefix(self) -> str:
        """Get YYYYMM prefix for monthly operations."""
        return self._model.month_prefix()

    def path_ladders(self) -> str:
        """Get S3 path for ladder files."""
        return self._model.path_ladders()

    def path_roster(self) -> str:
        """Get S3 path for roster files."""
        return self._model.path_roster()


# Re-export for backward compatibility
__all__ = ["IrusInvasion"]
