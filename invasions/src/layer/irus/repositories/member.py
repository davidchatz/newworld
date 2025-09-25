"""Repository for member data access operations."""

from typing import Any

from boto3.dynamodb.conditions import Key

from ..models.member import IrusMember
from .base import BaseRepository


class MemberRepository(BaseRepository[IrusMember]):
    """Repository for member CRUD operations and business logic."""

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

    def save(self, member: IrusMember) -> IrusMember:
        """Save a member to the database.

        Args:
            member: Member instance to save

        Returns:
            The saved member instance
        """
        self._log_operation("save", f"member {member.player}")

        item = member.to_dict()
        # Add audit timestamp
        item["event"] = self._create_timestamp()

        self.table.put_item(Item=item)
        self._log_debug("save", f"Put {item}")

        return member

    def get(self, key: dict[str, Any]) -> IrusMember | None:
        """Get a member by DynamoDB key.

        Args:
            key: DynamoDB key dictionary

        Returns:
            Member instance if found, None otherwise
        """
        self._log_operation("get", f"key {key}")

        response = self.table.get_item(Key=key)

        if "Item" not in response:
            self._log_operation("get", f"Member not found for key {key}")
            return None

        return IrusMember.from_dict(response["Item"])

    def get_by_player(self, player: str) -> IrusMember | None:
        """Get a member by player name.

        Args:
            player: Player name to look up

        Returns:
            Member instance if found, None otherwise
        """
        self._log_operation("get_by_player", player)

        key = {"invasion": "#member", "id": player}
        return self.get(key)

    def get_all(self) -> list[IrusMember]:
        """Get all members from the database.

        Returns:
            List of all member instances
        """
        self._log_operation("get_all", "all_members")

        try:
            # Query all members using the partition key
            response = self.table.query(
                KeyConditionExpression=Key("invasion").eq("#member")
            )

            members = []
            for item in response.get("Items", []):
                try:
                    member = IrusMember.model_validate(item)
                    members.append(member)
                except Exception as e:
                    self.logger.warning(f"Failed to parse member item {item}: {e}")
                    continue

            self.logger.info(f"Retrieved {len(members)} members")
            return members

        except Exception as e:
            self.logger.error(f"Failed to get all members: {e}")
            return []

    def delete(self, key: dict[str, Any]) -> bool:
        """Delete a member by DynamoDB key.

        Args:
            key: DynamoDB key dictionary

        Returns:
            True if item was deleted, False if not found
        """
        self._log_operation("delete", f"key {key}")

        response = self.table.delete_item(Key=key, ReturnValues="ALL_OLD")
        was_deleted = "Attributes" in response

        if was_deleted:
            self._log_operation("delete", f"Deleted member {key}")
        else:
            self._log_operation("delete", f"Member not found for deletion {key}")

        return was_deleted

    def delete_by_player(self, player: str) -> bool:
        """Delete a member by player name.

        Args:
            player: Player name to delete

        Returns:
            True if member was deleted, False if not found
        """
        key = {"invasion": "#member", "id": player}
        return self.delete(key)

    def create_from_user_input(
        self,
        player: str,
        day: int,
        month: int,
        year: int,
        faction: str,
        admin: bool,
        salary: bool,
        discord: str | None = None,
        notes: str | None = None,
    ) -> IrusMember:
        """Create a new member from user input and save to database.

        This method handles the full workflow of creating a member including
        audit logging and database persistence.

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
        self._log_operation("create_from_user_input", f"player {player}")

        # Check if member already exists
        existing = self.get_by_player(player)
        if existing is not None:
            raise ValueError(f"Member {player} already exists")

        # Create start date
        start = IrusMember.create_start_date(day, month, year)

        # Create the member model
        member = IrusMember(
            start=start,
            player=player,
            faction=faction,
            admin=admin,
            salary=salary,
            discord=discord,
            notes=notes,
        )

        # Create audit event for member addition
        timestamp = self._create_timestamp()

        add_event = {
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
            add_event["discord"] = discord
        if notes:
            add_event["notes"] = notes

        # Save audit event first
        self.table.put_item(Item=add_event)
        self._log_debug("create_from_user_input", f"Put audit event {add_event}")

        # Save the member
        saved_member = self.save(member)

        self._log_operation("create_from_user_input", f"Created member {player}")
        return saved_member

    def remove_with_audit(self, player: str) -> str:
        """Remove a member with audit logging.

        Args:
            player: Player name to remove

        Returns:
            Status message indicating success or failure

        Raises:
            ValueError: If player name is empty
        """
        self._log_operation("remove_with_audit", f"player {player}")

        if not player or not player.strip():
            msg = "Player name cannot be empty"
            self._log_operation("remove_with_audit", msg)
            raise ValueError(msg)

        # Create audit event for removal
        timestamp = self._create_timestamp()

        remove_event = {
            "invasion": "#memberevent",
            "id": timestamp,
            "event": "delete",
            "player": player,
        }

        # Try to delete the member
        was_deleted = self.delete_by_player(player)

        if was_deleted:
            mesg = f"## Removed member {player}"
            # Only log the removal event if the member actually existed
            self.table.put_item(Item=remove_event)
            self._log_debug("remove_with_audit", f"Put audit event {remove_event}")
        else:
            mesg = f"*Member {player} not found, nothing to remove*"

        self._log_operation("remove_with_audit", mesg)
        return mesg
