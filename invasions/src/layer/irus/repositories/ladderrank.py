"""Repository for ladder rank data access operations."""

from typing import Any

from boto3.dynamodb.conditions import Attr, Key
from botocore.exceptions import ClientError

from ..models.ladderrank import IrusLadderRank
from .base import BaseRepository


class LadderRankRepository(BaseRepository[IrusLadderRank]):
    """Repository for individual ladder rank CRUD operations."""

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

    def save(self, rank: IrusLadderRank) -> IrusLadderRank:
        """Save a ladder rank to the database.

        Args:
            rank: Ladder rank instance to save

        Returns:
            The saved rank instance
        """
        self._log_operation("save", f"rank {rank.rank} player {rank.player}")

        item = rank.to_dict()
        # Add audit timestamp
        item["event"] = self._create_timestamp()

        self.table.put_item(Item=item)
        self._log_debug("save", f"Put {item}")

        return rank

    def get(self, key: dict[str, Any]) -> IrusLadderRank | None:
        """Get a ladder rank by DynamoDB key.

        Args:
            key: DynamoDB key dictionary

        Returns:
            Ladder rank instance if found, None otherwise
        """
        self._log_operation("get", f"key {key}")

        response = self.table.get_item(Key=key)

        if "Item" not in response:
            self._log_operation("get", f"Ladder rank not found for key {key}")
            return None

        # Extract invasion name from key
        invasion_key = key.get("invasion", "")
        invasion_name = (
            invasion_key.replace("#ladder#", "")
            if invasion_key.startswith("#ladder#")
            else invasion_key
        )

        return IrusLadderRank.from_dict(response["Item"], invasion_name)

    def delete(self, key: dict[str, Any]) -> bool:
        """Delete a ladder rank by DynamoDB key.

        Args:
            key: DynamoDB key dictionary

        Returns:
            True if item was deleted, False if not found
        """
        self._log_operation("delete", f"key {key}")

        response = self.table.delete_item(Key=key, ReturnValues="ALL_OLD")
        was_deleted = "Attributes" in response

        if was_deleted:
            self._log_operation("delete", f"Deleted ladder rank {key}")
        else:
            self._log_operation("delete", f"Ladder rank not found for deletion {key}")

        return was_deleted

    def get_by_invasion_and_rank(
        self, invasion_name: str, rank_position: str
    ) -> IrusLadderRank | None:
        """Get ladder rank by invasion and rank position.

        Args:
            invasion_name: Invasion identifier
            rank_position: Rank position (e.g., "01", "02")

        Returns:
            Ladder rank if found, None otherwise
        """
        key = {"invasion": f"#ladder#{invasion_name}", "id": rank_position}
        return self.get(key)

    def get_by_player(self, invasion_name: str, player: str) -> IrusLadderRank | None:
        """Get ladder rank for a specific player in an invasion.

        Args:
            invasion_name: Invasion identifier
            player: Player name

        Returns:
            Ladder rank if found, None otherwise

        Raises:
            ValueError: If player matches multiple entries (data integrity issue)
        """
        self._log_operation(
            "get_by_player", f"invasion {invasion_name} player {player}"
        )

        try:
            response = self.table.query(
                KeyConditionExpression=Key("invasion").eq(f"#ladder#{invasion_name}"),
                FilterExpression=Attr("player").eq(player),
            )

            items = response.get("Items", [])

            if not items:
                self._log_debug(
                    "get_by_player", f"Player {player} not found in {invasion_name}"
                )
                return None

            if len(items) > 1:
                error_msg = f"Player {player} matched multiple times in {invasion_name}"
                self._log_operation("get_by_player", f"ERROR: {error_msg}")
                raise ValueError(error_msg)

            # Convert to ladder rank
            item = items[0]
            return IrusLadderRank.from_dict(item, invasion_name)

        except ClientError as err:
            error_msg = f"Failed to get rank for {player} in {invasion_name}: {err}"
            self._log_operation("get_by_player", error_msg)
            raise ValueError(error_msg) from err

    def update_membership(
        self, invasion_name: str, rank_position: str, is_member: bool
    ) -> bool:
        """Update membership status for a ladder rank.

        Args:
            invasion_name: Invasion identifier
            rank_position: Rank position (e.g., "01", "02")
            is_member: New membership status

        Returns:
            True if update succeeded, False if rank not found

        Raises:
            ValueError: If database operation fails
        """
        self._log_operation(
            "update_membership",
            f"invasion {invasion_name} rank {rank_position} member={is_member}",
        )

        key = {"invasion": f"#ladder#{invasion_name}", "id": rank_position}

        try:
            response = self.table.update_item(
                Key=key,
                UpdateExpression="SET #m = :m",
                ExpressionAttributeNames={"#m": "member"},
                ExpressionAttributeValues={":m": is_member},
                ReturnValues="UPDATED_NEW",
            )

            was_updated = "Attributes" in response
            if was_updated:
                self._log_debug(
                    "update_membership", f"Updated membership: {response['Attributes']}"
                )
            else:
                self._log_operation(
                    "update_membership", f"Rank {rank_position} not found"
                )

            return was_updated

        except ClientError as err:
            error_msg = f"Failed to update membership for rank {rank_position}: {err}"
            self._log_operation("update_membership", error_msg)
            raise ValueError(error_msg) from err

    def delete_by_invasion_and_rank(
        self, invasion_name: str, rank_position: str
    ) -> bool:
        """Delete a ladder rank by invasion and rank position.

        Args:
            invasion_name: Invasion identifier
            rank_position: Rank position (e.g., "01", "02")

        Returns:
            True if rank was deleted, False if not found
        """
        key = {"invasion": f"#ladder#{invasion_name}", "id": rank_position}
        return self.delete(key)

    def list_by_invasion(self, invasion_name: str) -> list[IrusLadderRank]:
        """Get all ladder ranks for an invasion.

        Args:
            invasion_name: Invasion identifier

        Returns:
            List of ladder ranks, sorted by rank position
        """
        self._log_operation("list_by_invasion", f"invasion {invasion_name}")

        try:
            response = self.table.query(
                KeyConditionExpression=Key("invasion").eq(f"#ladder#{invasion_name}")
            )

            ranks = []
            for item in response.get("Items", []):
                rank = IrusLadderRank.from_dict(item, invasion_name)
                ranks.append(rank)

            # Sort by rank position
            ranks.sort(key=lambda r: r.rank_as_int())

            self._log_debug("list_by_invasion", f"Found {len(ranks)} ranks")
            return ranks

        except ClientError as err:
            error_msg = f"Failed to list ranks for {invasion_name}: {err}"
            self._log_operation("list_by_invasion", error_msg)
            raise ValueError(error_msg) from err

    def delete_all_by_invasion(self, invasion_name: str) -> int:
        """Delete all ladder ranks for an invasion.

        Args:
            invasion_name: Invasion identifier

        Returns:
            Number of ranks deleted
        """
        self._log_operation("delete_all_by_invasion", f"invasion {invasion_name}")

        # First get all ranks to delete
        ranks = self.list_by_invasion(invasion_name)
        if not ranks:
            self._log_operation(
                "delete_all_by_invasion", f"No ranks found for {invasion_name}"
            )
            return 0

        try:
            # Delete using batch writer for efficiency
            with self.table.batch_writer() as batch:
                for rank in ranks:
                    batch.delete_item(Key=rank.key())

            count = len(ranks)
            self._log_operation(
                "delete_all_by_invasion", f"Deleted {count} ranks from {invasion_name}"
            )
            return count

        except ClientError as err:
            error_msg = f"Failed to delete ranks for {invasion_name}: {err}"
            self._log_operation("delete_all_by_invasion", error_msg)
            raise ValueError(error_msg) from err

    def save_multiple(self, ranks: list[IrusLadderRank]) -> list[IrusLadderRank]:
        """Save multiple ladder ranks efficiently using batch operations.

        Args:
            ranks: List of ladder ranks to save

        Returns:
            List of saved ranks

        Raises:
            ValueError: If batch operation fails
        """
        if not ranks:
            return []

        self._log_operation("save_multiple", f"Saving {len(ranks)} ranks")

        try:
            # Use batch writer for efficiency
            with self.table.batch_writer() as batch:
                for rank in ranks:
                    item = rank.to_dict()
                    item["event"] = self._create_timestamp()
                    batch.put_item(Item=item)

            self._log_debug("save_multiple", f"Saved {len(ranks)} ranks")
            return ranks

        except ClientError as err:
            error_msg = f"Failed to save multiple ranks: {err}"
            self._log_operation("save_multiple", error_msg)
            raise ValueError(error_msg) from err
