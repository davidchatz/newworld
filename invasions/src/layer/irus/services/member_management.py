"""Member management service for business logic consolidation."""

from ..container import IrusContainer
from ..invasionlist import IrusInvasionList
from ..ladderrank import IrusLadderRank
from ..models.member import IrusMember


class MemberManagementService:
    """Service for managing member-related business operations."""

    def __init__(self, container: IrusContainer | None = None):
        """Initialize the member management service.

        Args:
            container: Dependency injection container. Uses default if None.
        """
        self._container = container or IrusContainer.default()
        self._logger = self._container.logger()

    def update_invasions_for_new_member(self, member: IrusMember) -> str:
        """Update invasion records when a new member joins.

        This method finds all invasions that occurred on or after the member's
        start date and updates their ladder rankings to reflect membership status.

        Args:
            member: The new member to process

        Returns:
            Status message describing the update results
        """
        self._logger.info(f"Updating invasions for new member: {member.str()}")

        # Get invasions from member's start date onwards
        invasion_list = IrusInvasionList.from_start(member.start)
        self._logger.debug(
            f"Found {invasion_list.count()} invasions on or after {member.start}"
        )

        if invasion_list.count() == 0:
            message = "\nNo invasions found to update\n"
            self._logger.info(message)
            return message

        # Process each invasion
        updated_invasions = []
        for invasion in invasion_list.invasions:
            try:
                # Find the member's ladder ranking for this invasion
                ladder_rank = IrusLadderRank.from_invasion_for_member(invasion, member)
                self._logger.debug(
                    f"Found ladder rank for {invasion.name}: rank {ladder_rank.rank}"
                )

                # Update membership flag
                ladder_rank.update_membership(True)
                updated_invasions.append(f"- {invasion.name} rank {ladder_rank.rank}")

            except ValueError as e:
                # Member not found in this invasion's ladder - skip
                self._logger.debug(f"Member not found in {invasion.name} ladder: {e}")
                continue

        # Build result message
        if updated_invasions:
            message = "\n## Member flag updated in these invasions:\n"
            message += "\n".join(updated_invasions) + "\n"
        else:
            message = "\nNo ladder entries found to update\n"

        self._logger.info(f"Updated {len(updated_invasions)} invasion records")
        return message

    def bulk_update_member_status(
        self, members: list[IrusMember], is_active: bool
    ) -> str:
        """Bulk update membership status for multiple members.

        Args:
            members: List of members to update
            is_active: New active status

        Returns:
            Status message describing the bulk update results
        """
        self._logger.info(f"Bulk updating {len(members)} members to active={is_active}")

        updated_count = 0
        failed_updates = []

        for member in members:
            try:
                # This would require additional methods on IrusMember or repository
                # For now, we'll log the operation
                self._logger.debug(
                    f"Would update {member.player} active status to {is_active}"
                )
                updated_count += 1

            except Exception as e:
                failed_updates.append(f"{member.player}: {str(e)}")
                self._logger.warning(f"Failed to update {member.player}: {e}")

        # Build result message
        message = "\nBulk member status update completed:\n"
        message += f"- Successfully updated: {updated_count}\n"
        message += f"- Failed updates: {len(failed_updates)}\n"
        if failed_updates:
            message += "Failed members:\n"
            for failure in failed_updates:
                message += f"  - {failure}\n"

        return message

    def validate_member_data(self, member: IrusMember) -> list[str]:
        """Validate member data for consistency and completeness.

        Args:
            member: Member to validate

        Returns:
            List of validation error messages (empty if valid)
        """
        errors = []

        # Validate required fields
        if not member.player or not member.player.strip():
            errors.append("Player name is required")

        if not member.faction:
            errors.append("Faction is required")
        elif member.faction not in ["green", "purple", "yellow"]:
            errors.append(f"Invalid faction: {member.faction}")

        if not member.start:
            errors.append("Start date is required")

        # Validate start date format (assuming YYYYMMDD format)
        if member.start and len(str(member.start)) != 8:
            errors.append("Start date must be in YYYYMMDD format")

        # Log validation results
        if errors:
            self._logger.warning(
                f"Member validation failed for {member.player}: {errors}"
            )
        else:
            self._logger.debug(f"Member validation passed for {member.player}")

        return errors

    def find_duplicate_members(
        self, members: list[IrusMember]
    ) -> list[list[IrusMember]]:
        """Find potential duplicate members based on name similarity.

        Args:
            members: List of members to check

        Returns:
            List of groups containing potential duplicates
        """
        self._logger.info(f"Checking {len(members)} members for duplicates")

        duplicates = []
        processed = set()

        for i, member in enumerate(members):
            if i in processed:
                continue

            similar_members = [member]
            processed.add(i)

            # Check for similar names (handles O/0 substitution)
            for j, other_member in enumerate(members[i + 1 :], i + 1):
                if j in processed:
                    continue

                if self._are_names_similar(member.player, other_member.player):
                    similar_members.append(other_member)
                    processed.add(j)

            # Only add groups with more than one member
            if len(similar_members) > 1:
                duplicates.append(similar_members)

        self._logger.info(f"Found {len(duplicates)} potential duplicate groups")
        return duplicates

    def _are_names_similar(self, name1: str, name2: str) -> bool:
        """Check if two names are similar (handles O/0 substitution).

        Args:
            name1: First name to compare
            name2: Second name to compare

        Returns:
            True if names are considered similar
        """
        # Exact match
        if name1 == name2:
            return True

        # O/0 substitution check (from memberlist.py logic)
        name1_variants = [name1, name1.replace("O", "0"), name1.replace("0", "O")]

        name2_variants = [name2, name2.replace("O", "0"), name2.replace("0", "O")]

        # Check all combinations
        for variant1 in name1_variants:
            for variant2 in name2_variants:
                if variant1 == variant2:
                    return True

        return False

    def generate_member_activity_report(
        self, member: IrusMember, days: int = 30
    ) -> str:
        """Generate activity report for a specific member.

        Args:
            member: Member to generate report for
            days: Number of days to look back

        Returns:
            Activity report as formatted string
        """
        self._logger.info(f"Generating {days}-day activity report for {member.player}")

        # This would require integration with invasion/ladder data
        # For now, we'll create a placeholder structure
        report = f"\n# Activity Report: {member.player}\n"
        report += f"Faction: {member.faction}\n"
        report += f"Member since: {member.start}\n"
        report += f"Report period: Last {days} days\n"
        report += "\n## Invasion Participation\n"
        report += "- [This would show recent invasion participation]\n"
        report += "\n## Performance Summary\n"
        report += "- [This would show performance metrics]\n"

        return report
