from decimal import Decimal

from .container import IrusContainer
from .models.invasion import IrusInvasion
from .repositories.invasion import InvasionRepository


class IrusInvasionList:
    """Collection class for managing multiple invasions."""

    def __init__(
        self,
        invasions: list[IrusInvasion],
        start: int,
        container: IrusContainer | None = None,
    ):
        """Initialize invasion list with pure models.

        Args:
            invasions: List of IrusInvasion models
            start: Start date for the collection
            container: Optional container for logging
        """
        self._container = container or IrusContainer.default()
        self._logger = self._container.logger()
        self.invasions = invasions
        self.start = Decimal(start)

    @classmethod
    def from_month(cls, month: int, year: int, container: IrusContainer | None = None):
        """Create invasion list for a specific month using repository pattern."""
        container = container or IrusContainer.default()
        logger = container.logger()
        repository = InvasionRepository(container)

        logger.info(f"InvasionList.from_month {month}/{year}")
        zero_month = f"{month:02d}"
        start = f"{year}{zero_month}01"

        # Use repository to get invasions by month
        invasions = repository.get_by_month(year, month)
        logger.debug(f"Found {len(invasions)} invasions for {month}/{year}")

        return cls(invasions, start, container)

    @classmethod
    def from_start(cls, start: int, container: IrusContainer | None = None):
        """Create invasion list starting from a specific date using repository pattern."""
        container = container or IrusContainer.default()
        logger = container.logger()
        repository = InvasionRepository(container)

        logger.info(f"InvasionList.from_start {start}")

        # Use repository to get invasions from start date (using large end date for "all after start")
        end_date = 99999999  # Large date to capture all invasions after start
        invasions = repository.get_by_date_range(start, end_date)
        logger.debug(f"Found {len(invasions)} invasions from {start}")

        return cls(invasions, start, container)

    def str(self) -> str:
        msg = ""
        if len(self.invasions) > 0:
            msg += self.invasions[0].name
            for i in self.invasions[1:]:
                msg += f",{i.name}"
            msg += "\n"

        return msg

    def markdown(self) -> str:
        msg = f"# Invasions from {self.start}\n"
        if len(self.invasions) == 0:
            msg += "*No invasions found*\n"
        else:
            for i in self.invasions:
                msg += f"- {i.name}\n"

        return msg

    def count(self) -> int:
        return len(self.invasions)

    def range(self) -> range:
        return range(0, len(self.invasions))

    def get(self, index: int) -> IrusInvasion:
        return self.invasions[index]
