"""Repository for ladder collection operations."""

from botocore.exceptions import ClientError

from ..models.ladder import IrusLadder
from ..models.ladderrank import IrusLadderRank
from .ladderrank import LadderRankRepository


class LadderRepository:
    """Repository for ladder collection operations and business logic.

    This repository manages collections of ladder ranks and provides
    high-level operations for entire ladders. It delegates individual
    rank operations to LadderRankRepository.
    """

    def __init__(self, container=None, table=None, logger=None):
        """Initialize repository with dependency injection.

        Args:
            container: IrusContainer instance (preferred)
            table: DynamoDB table (legacy compatibility)
            logger: Logger instance (legacy compatibility)
        """
        # Initialize the rank repository for individual operations
        self._rank_repo = LadderRankRepository(
            container=container, table=table, logger=logger
        )

        # Store container reference for our own operations
        if container is not None:
            self._container = container
        elif table is not None or logger is not None:
            from ..container import IrusContainer

            self._container = IrusContainer.create_test(table=table, logger=logger)
        else:
            from ..container import IrusContainer

            self._container = IrusContainer.create_production()

    @property
    def container(self):
        """Get dependency container."""
        return self._container

    @property
    def table(self):
        """Get DynamoDB table."""
        return self.container.table()

    @property
    def logger(self):
        """Get logger."""
        return self.container.logger()

    def _log_operation(self, operation: str, details: str):
        """Log repository operation."""
        self.logger.info(f"LadderRepository.{operation}: {details}")

    def _log_debug(self, operation: str, details: str):
        """Log debug information."""
        self.logger.debug(f"LadderRepository.{operation}: {details}")

    def _create_timestamp(self) -> str:
        """Create timestamp string for audit trail."""
        from datetime import datetime

        return datetime.utcnow().isoformat() + "Z"

    def save_ladder(self, ladder: IrusLadder) -> IrusLadder:
        """Save an entire ladder to the database.

        Args:
            ladder: Ladder instance to save

        Returns:
            The saved ladder instance

        Raises:
            ValueError: If database operation fails
        """
        self._log_operation("save_ladder", f"invasion {ladder.invasion_name}")

        # Delegate to rank repository for efficient batch save
        self._rank_repo.save_multiple(ladder.ranks)

        self._log_debug("save_ladder", f"Saved {len(ladder.ranks)} ranks")
        return ladder

    def save_rank(self, rank: IrusLadderRank) -> IrusLadderRank:
        """Save a single ladder rank to the database.

        Args:
            rank: Ladder rank instance to save

        Returns:
            The saved rank instance
        """
        # Delegate to rank repository
        return self._rank_repo.save(rank)

    def get_ladder(self, invasion_name: str) -> IrusLadder | None:
        """Get complete ladder for an invasion.

        Args:
            invasion_name: Invasion identifier

        Returns:
            IrusLadder instance if found, None if no ranks exist
        """
        self._log_operation("get_ladder", f"invasion {invasion_name}")

        # Delegate to rank repository to get all ranks
        ranks = self._rank_repo.list_by_invasion(invasion_name)

        if not ranks:
            self._log_operation("get_ladder", f"No ladder found for {invasion_name}")
            return None

        return IrusLadder(invasion_name=invasion_name, ranks=ranks)

    def get_rank_by_player(
        self, invasion_name: str, player: str
    ) -> IrusLadderRank | None:
        """Get a specific player's rank from an invasion ladder.

        Args:
            invasion_name: Invasion identifier
            player: Player name

        Returns:
            IrusLadderRank if found, None otherwise

        Raises:
            ValueError: If player matches multiple entries (data integrity issue)
        """
        # Delegate to rank repository
        return self._rank_repo.get_by_player(invasion_name, player)

    def delete_ladder(self, invasion_name: str) -> bool:
        """Delete entire ladder for an invasion.

        Args:
            invasion_name: Invasion identifier

        Returns:
            True if any ranks were deleted, False if no ladder existed
        """
        self._log_operation("delete_ladder", f"invasion {invasion_name}")

        # Delegate to rank repository for batch delete
        deleted_count = self._rank_repo.delete_all_by_invasion(invasion_name)

        if deleted_count > 0:
            self._log_operation(
                "delete_ladder", f"Deleted {deleted_count} ranks from {invasion_name}"
            )
            return True
        else:
            self._log_operation(
                "delete_ladder", f"No ladder found to delete for {invasion_name}"
            )
            return False

    def delete_rank(self, invasion_name: str, rank_position: str) -> bool:
        """Delete a specific rank from a ladder.

        Args:
            invasion_name: Invasion identifier
            rank_position: Rank position (e.g., "01", "02")

        Returns:
            True if rank was deleted, False if not found
        """
        # Delegate to rank repository
        return self._rank_repo.delete_by_invasion_and_rank(invasion_name, rank_position)

    def update_rank_membership(
        self, invasion_name: str, rank_position: str, is_member: bool
    ) -> bool:
        """Update membership status for a specific rank.

        Args:
            invasion_name: Invasion identifier
            rank_position: Rank position (e.g., "01", "02")
            is_member: New membership status

        Returns:
            True if update succeeded, False if rank not found

        Raises:
            ValueError: If database operation fails
        """
        # Delegate to rank repository
        return self._rank_repo.update_membership(
            invasion_name, rank_position, is_member
        )

    def create_upload_record(self, invasion_name: str, upload_key: str) -> None:
        """Create a record of ladder upload for audit purposes.

        Args:
            invasion_name: Invasion identifier
            upload_key: Key identifying the upload (e.g., S3 key, "csv")
        """
        self._log_operation(
            "create_upload_record", f"invasion {invasion_name} key {upload_key}"
        )

        upload_item = {
            "invasion": f"#upload#{invasion_name}",
            "id": upload_key,
            "event": self._create_timestamp(),
        }

        try:
            self.table.put_item(Item=upload_item)
            self._log_debug(
                "create_upload_record", f"Created upload record {upload_item}"
            )

        except ClientError as err:
            # Log but don't fail - upload records are for audit only
            self._log_operation(
                "create_upload_record", f"Failed to create upload record: {err}"
            )

    def save_ladder_from_processing(
        self, ladder: IrusLadder, upload_key: str
    ) -> IrusLadder:
        """Save ladder data from image/CSV processing with upload tracking.

        This is a convenience method that combines ladder saving with upload record creation.

        Args:
            ladder: Processed ladder data
            upload_key: Upload identifier for audit trail

        Returns:
            The saved ladder instance

        Raises:
            ValueError: If save operation fails
        """
        self._log_operation(
            "save_ladder_from_processing",
            f"invasion {ladder.invasion_name} key {upload_key}",
        )

        # Create upload record first (for audit trail)
        self.create_upload_record(ladder.invasion_name, upload_key)

        # Save the ladder
        return self.save_ladder(ladder)
