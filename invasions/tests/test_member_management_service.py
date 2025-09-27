"""Tests for Member management service."""

from unittest.mock import Mock, patch

import pytest
from irus.container import IrusContainer
from irus.models.member import IrusMember
from irus.services.member_management import MemberManagementService


class TestMemberManagementService:
    """Test suite for MemberManagementService class."""

    @pytest.fixture
    def container(self):
        """Create test container with mocked dependencies."""
        return IrusContainer.create_test()

    @pytest.fixture
    def service(self, container):
        """Create MemberManagementService instance with test container."""
        # Mock the invasion list and ladder repository dependencies
        mock_invasion_list = Mock()
        mock_ladder_repository = Mock()
        return MemberManagementService(
            container=container,
            invasion_list=mock_invasion_list,
            ladder_repository=mock_ladder_repository,
        )

    @pytest.fixture
    def sample_member(self):
        """Create sample member for testing."""
        return IrusMember(player="TestPlayer", faction="green", start=20240301)

    @pytest.fixture
    def sample_members(self):
        """Create list of sample members for testing."""
        return [
            IrusMember(player="Player1", faction="green", start=20240301),
            IrusMember(player="Player2", faction="purple", start=20240315),
            IrusMember(player="Player3", faction="yellow", start=20240401),
            IrusMember(
                player="Player0", faction="green", start=20240301
            ),  # Similar to Player1 (O/0)
        ]

    def test_init(self, container):
        """Test MemberManagementService initialization."""
        service = MemberManagementService(container)

        assert service._container is container
        assert service._logger is not None

    def test_init_default_container(self):
        """Test MemberManagementService initialization with default container."""
        with patch.object(IrusContainer, "default") as mock_default:
            mock_container = Mock(spec=IrusContainer)
            mock_container.logger.return_value = Mock()
            mock_default.return_value = mock_container

            service = MemberManagementService()

            assert service._container is mock_container
            mock_default.assert_called_once()

    def test_update_invasions_for_new_member_no_invasions(self, service, sample_member):
        """Test updating invasions when no invasions are found."""
        # Mock empty invasion list
        service._invasion_list.count.return_value = 0

        result = service.update_invasions_for_new_member(sample_member)

        assert "No invasions found to update" in result
        service._invasion_list.load_from_start.assert_called_once_with(20240301)

    def test_update_invasions_for_new_member_success(self, service, sample_member):
        """Test successfully updating invasions for new member."""
        # Mock invasion list with sample invasions
        mock_invasion1 = Mock()
        mock_invasion1.name = "20240301-bw"
        mock_invasion2 = Mock()
        mock_invasion2.name = "20240315-ef"

        service._invasion_list.count.return_value = 2
        service._invasion_list.invasions = [mock_invasion1, mock_invasion2]

        # Mock ladder ranks
        mock_ladder_rank1 = Mock()
        mock_ladder_rank1.rank = "05"

        mock_ladder_rank2 = Mock()
        mock_ladder_rank2.rank = "12"

        # Mock repository returns
        service._ladder_repository.get_rank_by_player.side_effect = [
            mock_ladder_rank1,
            mock_ladder_rank2,
        ]
        service._ladder_repository.update_rank_membership.return_value = True

        result = service.update_invasions_for_new_member(sample_member)

        # Check result message
        assert "Member flag updated in these invasions:" in result
        assert "20240301-bw rank 05" in result
        assert "20240315-ef rank 12" in result

        # Verify repository method calls
        assert service._ladder_repository.get_rank_by_player.call_count == 2
        service._ladder_repository.get_rank_by_player.assert_any_call(
            "20240301-bw", "TestPlayer"
        )
        service._ladder_repository.get_rank_by_player.assert_any_call(
            "20240315-ef", "TestPlayer"
        )

        assert service._ladder_repository.update_rank_membership.call_count == 2
        service._ladder_repository.update_rank_membership.assert_any_call(
            "20240301-bw", "05", True
        )
        service._ladder_repository.update_rank_membership.assert_any_call(
            "20240315-ef", "12", True
        )

    def test_update_invasions_for_new_member_partial_success(
        self, service, sample_member
    ):
        """Test updating invasions with some failures."""
        # Mock invasion list
        mock_invasion1 = Mock()
        mock_invasion1.name = "20240301-bw"
        mock_invasion2 = Mock()
        mock_invasion2.name = "20240315-ef"

        service._invasion_list.count.return_value = 2
        service._invasion_list.invasions = [mock_invasion1, mock_invasion2]

        # Mock one successful, one failed ladder rank lookup
        mock_ladder_rank = Mock()
        mock_ladder_rank.rank = "05"

        # Return ladder rank for first invasion, None for second (member not found)
        service._ladder_repository.get_rank_by_player.side_effect = [
            mock_ladder_rank,
            None,
        ]
        service._ladder_repository.update_rank_membership.return_value = True

        result = service.update_invasions_for_new_member(sample_member)

        # Should only show the successful update
        assert "Member flag updated in these invasions:" in result
        assert "20240301-bw rank 05" in result
        assert "20240315-ef" not in result

        # Only one update should have been called
        service._ladder_repository.update_rank_membership.assert_called_once_with(
            "20240301-bw", "05", True
        )

    def test_bulk_update_member_status(self, service, sample_members):
        """Test bulk updating member status."""
        result = service.bulk_update_member_status(sample_members, True)

        assert "Bulk member status update completed:" in result
        assert "Successfully updated: 4" in result
        assert "Failed updates: 0" in result

    def test_validate_member_data_valid(self, service, sample_member):
        """Test validating valid member data."""
        errors = service.validate_member_data(sample_member)

        assert errors == []

    def test_validate_member_data_invalid(self, service):
        """Test validating invalid member data using mock object."""
        # Since IrusMember has Pydantic validation that prevents creation of invalid objects,
        # we'll use a mock to simulate invalid data that somehow got through
        from unittest.mock import Mock

        invalid_member = Mock(spec=IrusMember)
        invalid_member.player = ""
        invalid_member.faction = "invalid"
        invalid_member.start = 123

        errors = service.validate_member_data(invalid_member)

        assert len(errors) > 0
        assert any("Player name is required" in error for error in errors)
        assert any("Invalid faction" in error for error in errors)
        assert any("Start date must be in YYYYMMDD format" in error for error in errors)

    def test_validate_member_data_missing_fields(self, service):
        """Test validating member with missing fields using mock object."""
        from unittest.mock import Mock

        invalid_member = Mock(spec=IrusMember)
        invalid_member.player = "TestPlayer"
        invalid_member.faction = None
        invalid_member.start = None

        errors = service.validate_member_data(invalid_member)

        assert any("Faction is required" in error for error in errors)
        assert any("Start date is required" in error for error in errors)

    def test_validate_member_data_whitespace_player_name(self, service):
        """Test validating member with whitespace-only player name using mock."""
        from unittest.mock import Mock

        invalid_member = Mock(spec=IrusMember)
        invalid_member.player = "   "  # Whitespace-only name
        invalid_member.faction = "green"
        invalid_member.start = 20240301

        errors = service.validate_member_data(invalid_member)

        assert any("Player name is required" in error for error in errors)

    def test_find_duplicate_members_no_duplicates(self, service):
        """Test finding duplicates when there are none."""
        members = [
            IrusMember(player="UniquePlayer1", faction="green", start=20240301),
            IrusMember(player="UniquePlayer2", faction="purple", start=20240315),
        ]

        duplicates = service.find_duplicate_members(members)

        assert len(duplicates) == 0

    def test_find_duplicate_members_exact_match(self, service):
        """Test finding exact duplicate names."""
        members = [
            IrusMember(player="DuplicatePlayer", faction="green", start=20240301),
            IrusMember(player="DuplicatePlayer", faction="purple", start=20240315),
            IrusMember(player="UniquePlayer", faction="yellow", start=20240401),
        ]

        duplicates = service.find_duplicate_members(members)

        assert len(duplicates) == 1
        assert len(duplicates[0]) == 2
        assert all(member.player == "DuplicatePlayer" for member in duplicates[0])

    def test_find_duplicate_members_o_zero_substitution(self, service):
        """Test finding duplicates with O/0 substitution."""
        members = [
            IrusMember(player="PlayerO", faction="green", start=20240301),
            IrusMember(player="Player0", faction="purple", start=20240315),
            IrusMember(player="UniquePlayer", faction="yellow", start=20240401),
        ]

        duplicates = service.find_duplicate_members(members)

        assert len(duplicates) == 1
        assert len(duplicates[0]) == 2
        assert {member.player for member in duplicates[0]} == {"PlayerO", "Player0"}

    def test_are_names_similar_exact_match(self, service):
        """Test name similarity with exact match."""
        assert service._are_names_similar("Player1", "Player1") is True

    def test_are_names_similar_o_zero_substitution(self, service):
        """Test name similarity with O/0 substitution."""
        assert service._are_names_similar("PlayerO", "Player0") is True
        assert service._are_names_similar("Player0", "PlayerO") is True
        assert service._are_names_similar("Pl0yer", "PlOyer") is True

    def test_are_names_similar_different_names(self, service):
        """Test name similarity with different names."""
        assert service._are_names_similar("Player1", "Player2") is False
        assert service._are_names_similar("Alice", "Bob") is False

    def test_generate_member_activity_report(self, service, sample_member):
        """Test generating member activity report."""
        report = service.generate_member_activity_report(sample_member, 30)

        assert "Activity Report: TestPlayer" in report
        assert "Faction: green" in report
        assert "Member since: 20240301" in report
        assert "Report period: Last 30 days" in report
        assert "Invasion Participation" in report
        assert "Performance Summary" in report

    def test_generate_member_activity_report_custom_days(self, service, sample_member):
        """Test generating member activity report with custom days."""
        report = service.generate_member_activity_report(sample_member, 60)

        assert "Report period: Last 60 days" in report

    def test_logging_operations(self, service, sample_member):
        """Test that operations are logged correctly."""
        # Mock the invasion list to return no invasions
        service._invasion_list.count.return_value = 0

        service.update_invasions_for_new_member(sample_member)

        # Verify logging calls were made
        assert service._logger.info.call_count >= 2

        service.validate_member_data(sample_member)
        service.find_duplicate_members([sample_member])
        service.generate_member_activity_report(sample_member)

        # Additional logging for various operations
        assert service._logger.info.call_count >= 4

    def test_bulk_update_with_exceptions(self, service, sample_members):
        """Test bulk update handling exceptions."""
        # This test would require implementing actual update logic
        # For now, we test the current placeholder behavior
        result = service.bulk_update_member_status(sample_members, False)

        assert "Successfully updated: 4" in result
        assert "Failed updates: 0" in result

    def test_find_duplicate_members_multiple_groups(self, service):
        """Test finding multiple duplicate groups."""
        members = [
            IrusMember(player="Group1A", faction="green", start=20240301),
            IrusMember(player="Group1A", faction="purple", start=20240315),
            IrusMember(player="Group2O", faction="yellow", start=20240401),
            IrusMember(player="Group20", faction="green", start=20240501),
            IrusMember(player="Unique", faction="purple", start=20240601),
        ]

        duplicates = service.find_duplicate_members(members)

        assert len(duplicates) == 2

        # Check first duplicate group (exact match)
        group1 = next(group for group in duplicates if group[0].player == "Group1A")
        assert len(group1) == 2

        # Check second duplicate group (O/0 substitution)
        group2 = next(
            group for group in duplicates if group[0].player in ["Group2O", "Group20"]
        )
        assert len(group2) == 2
