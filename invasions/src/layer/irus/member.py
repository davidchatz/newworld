"""Backward compatibility facade for IrusMember.

This module provides backward compatibility for the legacy IrusMember class
while internally using the new repository pattern architecture.

DEPRECATED: This facade is provided for backward compatibility only.
New code should use irus.models.member.IrusMember and irus.repositories.member.MemberRepository directly.
"""

import warnings
from typing import Any

from .models.member import IrusMember as PureMember
from .repositories.member import MemberRepository

# Issue deprecation warning when this module is imported
warnings.warn(
    "irus.member module is deprecated. Use irus.models.member.IrusMember and "
    "irus.repositories.member.MemberRepository instead.",
    DeprecationWarning,
    stacklevel=2,
)


class IrusMember:
    """Legacy IrusMember class for backward compatibility.

    This class wraps the new repository pattern implementation to maintain
    backward compatibility with existing code.

    DEPRECATED: Use irus.models.member.IrusMember and irus.repositories.member.MemberRepository instead.
    """

    def __init__(self, item: dict[str, Any]):
        """Initialize from dictionary (legacy API).

        Args:
            item: DynamoDB item dictionary
        """
        # Create the pure model from the item
        self._model = PureMember.from_dict(item)
        # Create repository for database operations
        self._repository = MemberRepository()

    @property
    def start(self) -> int:
        """Get start date."""
        return self._model.start

    @property
    def player(self) -> str:
        """Get player name."""
        return self._model.player

    @property
    def faction(self) -> str:
        """Get faction."""
        return self._model.faction

    @property
    def admin(self) -> bool:
        """Get admin status."""
        return self._model.admin

    @property
    def salary(self) -> bool:
        """Get salary eligibility."""
        return self._model.salary

    @property
    def discord(self) -> str | None:
        """Get Discord username."""
        return self._model.discord

    @property
    def notes(self) -> str | None:
        """Get notes."""
        return self._model.notes

    def key(self) -> dict[str, str]:
        """Get DynamoDB key for this member."""
        return self._model.key()

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
            ValueError: If validation fails or member already exists
        """
        repository = MemberRepository()
        pure_member = repository.create_from_user_input(
            player=player,
            day=day,
            month=month,
            year=year,
            faction=faction,
            admin=admin,
            salary=salary,
            discord=discord,
            notes=notes,
        )

        # Convert back to legacy wrapper
        return cls(pure_member.to_dict())

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
        repository = MemberRepository()
        pure_member = repository.get_by_player(player)

        if pure_member is None:
            raise ValueError(f"No member found called {player}")

        # Convert to legacy wrapper
        return cls(pure_member.to_dict())

    def str(self) -> str:
        """Format member as markdown string."""
        return self._model.str()

    def remove(self) -> str:
        """Remove member from database and log the event.

        Returns:
            Status message indicating success or failure
        """
        return self._repository.remove_with_audit(self.player)

    def post(self) -> list[str]:
        """Format member data as list of strings for Discord posting."""
        return self._model.post()


# Re-export for backward compatibility
__all__ = ["IrusMember"]
