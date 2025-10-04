from decimal import Decimal

from .container import IrusContainer
from .models.invasion import IrusInvasion
from .repositories.invasion import InvasionRepository


class IrusInvasionList:
    """Service for managing invasion collections with dependency injection.

    This class follows the same pattern as IrusMemberList, providing factory
    methods for convenient construction with data loading.

    Example:
        >>> # Using factory method (recommended)
        >>> invasion_list = IrusInvasionList.from_month(3, 2024)
        >>>
        >>> # Or create empty and load manually
        >>> invasion_list = IrusInvasionList()
        >>> invasion_list.load_from_month(3, 2024)
    """

    def __init__(self, container: IrusContainer | None = None):
        """Initialize invasion list service.

        Args:
            container: Dependency injection container. Uses default if None.
        """
        self._container = container or IrusContainer.default()
        self._logger = self._container.logger()
        self._repository = InvasionRepository(self._container)

        # Internal state for loaded invasions
        self.invasions: list[IrusInvasion] = []
        self.start: Decimal = Decimal(0)

    @classmethod
    def from_month(
        cls, month: int, year: int, container: IrusContainer | None = None
    ) -> "IrusInvasionList":
        """Create invasion list for a specific month.

        Factory method that creates an instance and loads data in one step.

        Args:
            month: Month (1-12)
            year: Year (YYYY)
            container: Optional dependency injection container

        Returns:
            IrusInvasionList instance with invasions loaded for the specified month

        Example:
            >>> invasion_list = IrusInvasionList.from_month(3, 2024)
            >>> print(f"Found {invasion_list.count()} invasions")
        """
        instance = cls(container)
        instance.load_from_month(month, year)
        return instance

    @classmethod
    def from_start(
        cls, start: int, container: IrusContainer | None = None
    ) -> "IrusInvasionList":
        """Create invasion list from a start date.

        Factory method that creates an instance and loads data from start date forward.

        Args:
            start: Start date in YYYYMMDD format
            container: Optional dependency injection container

        Returns:
            IrusInvasionList instance with invasions loaded from start date

        Example:
            >>> invasion_list = IrusInvasionList.from_start(20240301)
            >>> print(f"Found {invasion_list.count()} invasions")
        """
        instance = cls(container)
        instance.load_from_start(start)
        return instance

    def load_from_month(self, month: int, year: int) -> None:
        """Load invasions for a specific month using repository pattern.

        Args:
            month: Month (1-12)
            year: Year (YYYY)
        """
        self._logger.info(f"InvasionList.load_from_month {month}/{year}")
        zero_month = f"{month:02d}"
        start = f"{year}{zero_month}01"

        # Use repository to get invasions by month
        self.invasions = self._repository.get_by_month(year, month)
        self.start = Decimal(start)
        self._logger.debug(f"Found {len(self.invasions)} invasions for {month}/{year}")

    def load_from_start(self, start: int) -> None:
        """Load invasions starting from a specific date using repository pattern.

        Args:
            start: Start date in YYYYMMDD format
        """
        self._logger.info(f"InvasionList.load_from_start {start}")

        # Use repository to get invasions from start date (using large end date for "all after start")
        end_date = 99999999  # Large date to capture all invasions after start
        self.invasions = self._repository.get_by_date_range(start, end_date)
        self.start = Decimal(start)
        self._logger.debug(f"Found {len(self.invasions)} invasions from {start}")

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
