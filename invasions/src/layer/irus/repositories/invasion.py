"""Repository for invasion data access operations."""

from typing import Any

from ..models.invasion import IrusInvasion
from .base import BaseRepository


class InvasionRepository(BaseRepository[IrusInvasion]):
    """Repository for invasion CRUD operations and business logic."""

    def __init__(self, container=None, table=None, logger=None):
        """Initialize repository with dependency injection.

        Args:
            container: IrusContainer instance (preferred)
            table: DynamoDB table (legacy compatibility)
            logger: Logger instance (legacy compatibility)
        """
        if container is not None:
            # New container-based approach
            super().__init__(container=container)
        elif table is not None or logger is not None:
            # Legacy approach - create container from individual dependencies
            from ..container import IrusContainer

            test_container = IrusContainer.create_test(table=table, logger=logger)
            super().__init__(container=test_container)
        else:
            # Default approach
            super().__init__()

    def save(self, invasion: IrusInvasion) -> IrusInvasion:
        """Save an invasion to the database.

        Args:
            invasion: Invasion instance to save

        Returns:
            The saved invasion instance
        """
        self._log_operation("save", f"invasion {invasion.name}")

        item = invasion.to_dict()

        self.table.put_item(Item=item)
        self._log_debug("save", f"Put {item}")

        return invasion

    def get(self, key: dict[str, Any]) -> IrusInvasion | None:
        """Get an invasion by DynamoDB key.

        Args:
            key: DynamoDB key dictionary

        Returns:
            Invasion instance if found, None otherwise
        """
        self._log_operation("get", f"key {key}")

        response = self.table.get_item(Key=key)

        if "Item" not in response:
            self._log_operation("get", f"Invasion not found for key {key}")
            return None

        return IrusInvasion.from_dict(response["Item"])

    def get_by_name(self, name: str) -> IrusInvasion | None:
        """Get an invasion by name.

        Args:
            name: Invasion name to look up (YYYYMMDD-settlement format)

        Returns:
            Invasion instance if found, None otherwise
        """
        self._log_operation("get_by_name", name)

        key = {"invasion": "#invasion", "id": name}
        return self.get(key)

    def delete(self, key: dict[str, Any]) -> bool:
        """Delete an invasion by DynamoDB key.

        Args:
            key: DynamoDB key dictionary

        Returns:
            True if item was deleted, False if not found
        """
        self._log_operation("delete", f"key {key}")

        response = self.table.delete_item(Key=key, ReturnValues="ALL_OLD")
        was_deleted = "Attributes" in response

        if was_deleted:
            self._log_operation("delete", f"Deleted invasion {key}")
        else:
            self._log_operation("delete", f"Invasion not found for deletion {key}")

        return was_deleted

    def delete_by_name(self, name: str) -> bool:
        """Delete an invasion by name.

        Args:
            name: Invasion name to delete

        Returns:
            True if invasion was deleted, False if not found
        """
        key = {"invasion": "#invasion", "id": name}
        return self.delete(key)

    def create_from_user_input(
        self,
        day: int,
        month: int,
        year: int,
        settlement: str,
        win: bool,
        notes: str | None = None,
    ) -> IrusInvasion:
        """Create a new invasion from user input and save to database.

        This method handles the full workflow of creating an invasion including
        validation and database persistence.

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
        self._log_operation(
            "create_from_user_input",
            f"day={day}, month={month}, year={year}, settlement={settlement}",
        )

        # Create the invasion model (this validates input)
        invasion = IrusInvasion.create_from_user_input(
            day=day, month=month, year=year, settlement=settlement, win=win, notes=notes
        )

        # Check if invasion already exists
        existing = self.get_by_name(invasion.name)
        if existing is not None:
            raise ValueError(f"Invasion {invasion.name} already exists")

        # Save the invasion
        saved_invasion = self.save(invasion)

        self._log_operation(
            "create_from_user_input", f"Created invasion {invasion.name}"
        )
        return saved_invasion

    def get_by_date_range(self, start_date: int, end_date: int) -> list[IrusInvasion]:
        """Get invasions within a date range.

        Args:
            start_date: Start date as YYYYMMDD integer (inclusive)
            end_date: End date as YYYYMMDD integer (inclusive)

        Returns:
            List of invasions within the date range
        """
        self._log_operation("get_by_date_range", f"start={start_date}, end={end_date}")

        # Use scan with filter expression
        from boto3.dynamodb.conditions import Attr, Key

        response = self.table.scan(
            FilterExpression=(
                Key("invasion").eq("#invasion")
                & Attr("date").between(start_date, end_date)
            )
        )

        invasions = []
        for item in response.get("Items", []):
            invasions.append(IrusInvasion.from_dict(item))

        self._log_operation("get_by_date_range", f"Found {len(invasions)} invasions")
        return invasions

    def get_by_month(self, year: int, month: int) -> list[IrusInvasion]:
        """Get all invasions for a specific month.

        Args:
            year: Year (e.g. 2024)
            month: Month (1-12)

        Returns:
            List of invasions for the month
        """
        start_date = int(f"{year}{month:02d}01")

        # Calculate last day of month
        if month == 12:
            next_month = 1
            next_year = year + 1
        else:
            next_month = month + 1
            next_year = year

        from datetime import datetime, timedelta

        last_day = (datetime(next_year, next_month, 1) - timedelta(days=1)).day
        end_date = int(f"{year}{month:02d}{last_day:02d}")

        return self.get_by_date_range(start_date, end_date)

    def get_by_settlement(self, settlement: str) -> list[IrusInvasion]:
        """Get all invasions for a specific settlement.

        Args:
            settlement: Settlement code (e.g. 'bw')

        Returns:
            List of invasions for the settlement
        """
        self._log_operation("get_by_settlement", settlement)

        from boto3.dynamodb.conditions import Attr, Key

        response = self.table.scan(
            FilterExpression=(
                Key("invasion").eq("#invasion")
                & Attr("settlement").eq(settlement.lower())
            )
        )

        invasions = []
        for item in response.get("Items", []):
            invasions.append(IrusInvasion.from_dict(item))

        self._log_operation("get_by_settlement", f"Found {len(invasions)} invasions")
        return invasions
