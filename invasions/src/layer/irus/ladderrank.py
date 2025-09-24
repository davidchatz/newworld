"""Backward compatibility facade for IrusLadderRank.

This module provides backward compatibility for the legacy IrusLadderRank class
while internally using the new repository pattern architecture.

DEPRECATED: This facade is provided for backward compatibility only.
New code should use irus.models.ladderrank.IrusLadderRank and irus.repositories.ladder.LadderRepository directly.
"""

import warnings

from .models.ladderrank import IrusLadderRank as PureLadderRank
from .repositories.ladder import LadderRepository

# Issue deprecation warning when this module is imported
warnings.warn(
    "irus.ladderrank module is deprecated. Use irus.models.ladderrank.IrusLadderRank and "
    "irus.repositories.ladder.LadderRepository instead.",
    DeprecationWarning,
    stacklevel=2,
)


class IrusLadderRank:
    """Legacy IrusLadderRank class for backward compatibility.

    This class wraps the new repository pattern implementation to maintain
    backward compatibility with existing code.

    DEPRECATED: Use irus.models.ladderrank.IrusLadderRank and irus.repositories.ladder.LadderRepository instead.
    """

    def __init__(self, invasion, item: dict):
        """Initialize from invasion and item dictionary (legacy API).

        Args:
            invasion: Invasion object (legacy)
            item: DynamoDB item dictionary
        """
        # Extract invasion name from invasion object
        invasion_name = getattr(invasion, "name", str(invasion))

        # Create the pure model from the item
        self._model = PureLadderRank(
            invasion_name=invasion_name,
            rank=item.get("rank", "01"),
            player=item.get("player", ""),
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

        # Store invasion reference for legacy compatibility
        self.invasion = invasion

        # Create repository for database operations
        self._repository = LadderRepository()

    @property
    def rank(self) -> str:
        """Get rank position."""
        return self._model.rank

    @rank.setter
    def rank(self, value: str):
        """Set rank position."""
        self._model.rank = f"{int(value):02d}" if value.isdigit() else value

    @property
    def player(self) -> str:
        """Get player name."""
        return self._model.player

    @player.setter
    def player(self, value: str):
        """Set player name."""
        self._model.player = value

    @property
    def score(self) -> int:
        """Get score."""
        return self._model.score

    @score.setter
    def score(self, value: int):
        """Set score."""
        self._model.score = int(value)

    @property
    def kills(self) -> int:
        """Get kills."""
        return self._model.kills

    @kills.setter
    def kills(self, value: int):
        """Set kills."""
        self._model.kills = int(value)

    @property
    def deaths(self) -> int:
        """Get deaths."""
        return self._model.deaths

    @deaths.setter
    def deaths(self, value: int):
        """Set deaths."""
        self._model.deaths = int(value)

    @property
    def assists(self) -> int:
        """Get assists."""
        return self._model.assists

    @assists.setter
    def assists(self, value: int):
        """Set assists."""
        self._model.assists = int(value)

    @property
    def heals(self) -> int:
        """Get heals."""
        return self._model.heals

    @heals.setter
    def heals(self, value: int):
        """Set heals."""
        self._model.heals = int(value)

    @property
    def damage(self) -> int:
        """Get damage."""
        return self._model.damage

    @damage.setter
    def damage(self, value: int):
        """Set damage."""
        self._model.damage = int(value)

    @property
    def member(self) -> bool:
        """Get member status."""
        return self._model.member

    @member.setter
    def member(self, value: bool):
        """Set member status."""
        self._model.member = bool(value)

    @property
    def ladder(self) -> bool:
        """Get ladder status."""
        return self._model.ladder

    @ladder.setter
    def ladder(self, value: bool):
        """Set ladder status."""
        self._model.ladder = bool(value)

    @property
    def adjusted(self) -> bool:
        """Get adjusted status."""
        return self._model.adjusted

    @adjusted.setter
    def adjusted(self, value: bool):
        """Set adjusted status."""
        self._model.adjusted = bool(value)

    @property
    def error(self) -> bool:
        """Get error status."""
        return self._model.error

    @error.setter
    def error(self, value: bool):
        """Set error status."""
        self._model.error = bool(value)

    def invasion_key(self) -> str:
        """Get DynamoDB invasion key (legacy compatibility)."""
        return f"#ladder#{self._model.invasion_name}"

    def item(self) -> dict:
        """Get item dictionary for DynamoDB (legacy compatibility)."""
        return self._model.to_dict()

    def __dict__(self) -> dict:
        """Get dictionary representation (legacy compatibility)."""
        return self._model.to_dict()

    @classmethod
    def from_roster(cls, invasion, rank: int, player: str):
        """Create ladder rank from roster data (legacy compatibility)."""
        item = {
            "rank": f"{rank:02d}",
            "player": player,
            "score": 0,
            "kills": 0,
            "deaths": 0,
            "assists": 0,
            "heals": 0,
            "damage": 0,
            "member": True,
            "ladder": False,
            "adjusted": False,
            "error": False,
        }
        return cls(invasion=invasion, item=item)

    @classmethod
    def from_invasion_for_member(cls, invasion, member):
        """Get ladder rank for a specific member (legacy compatibility)."""
        repository = LadderRepository()
        invasion_name = getattr(invasion, "name", str(invasion))
        player_name = getattr(member, "player", str(member))

        rank = repository.get_rank_by_player(invasion_name, player_name)
        if rank is None:
            raise ValueError(
                f"Player {player_name} not found in invasion {invasion_name}"
            )

        # Convert back to legacy format
        item = rank.to_dict()
        item["rank"] = item["id"]  # Legacy expects 'rank' field
        return cls(invasion, item)

    def __str__(self):
        """String representation (legacy compatibility)."""
        return (
            f"{self.rank} {self.player} {self.score} {self.kills} {self.deaths} "
            f"{self.assists} {self.heals} {self.damage} {self.member} {self.ladder} "
            f"{self.adjusted} {self.error}"
        )

    @staticmethod
    def header() -> str:
        """Get header string (legacy compatibility)."""
        return PureLadderRank.header()

    @staticmethod
    def footer() -> str:
        """Get footer string (legacy compatibility)."""
        return PureLadderRank.footer()

    def post(self) -> str:
        """Format for posting (legacy compatibility)."""
        return self._model.post()

    def str(self) -> str:
        """Format as markdown string (legacy compatibility)."""
        return self._model.str()

    def update_membership(self, member: bool):
        """Update membership status (legacy compatibility)."""
        self.member = member
        self._repository.update_rank_membership(
            self._model.invasion_name, self._model.rank, member
        )

    def update_item(self):
        """Save to database (legacy compatibility)."""
        self._repository.save_rank(self._model)

    def delete_item(self):
        """Delete from database (legacy compatibility)."""
        self._repository.delete_rank(self._model.invasion_name, self._model.rank)
