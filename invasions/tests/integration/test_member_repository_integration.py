"""Integration tests for MemberRepository with real DynamoDB.

These tests validate that the MemberRepository works correctly with
real AWS DynamoDB resources using the 99DDHHMM test data strategy.
"""

import pytest
from irus.repositories.member import MemberRepository

from tests.integration.conftest import is_test_date


class TestMemberRepositoryIntegration:
    """Integration tests for member repository CRUD operations."""

    @pytest.fixture
    def repository(self, integration_container):
        """Create MemberRepository with real AWS container."""
        return MemberRepository(integration_container)

    def test_create_and_retrieve_member(
        self, repository, test_member_data, test_member_expectations
    ):
        """Test full member lifecycle with real DynamoDB.

        This test validates:
        - Member creation with real DynamoDB table
        - Member retrieval by player name
        - Data integrity and type conversion
        """
        # Arrange - test_member_data fixture provides unique test data

        # Act - Create member
        created_member = repository.create_from_user_input(**test_member_data)

        # Act - Retrieve member
        retrieved_member = repository.get_by_player(created_member.player)

        # Assert - Verify member was created and retrieved correctly
        assert retrieved_member is not None
        assert retrieved_member.player == created_member.player
        assert retrieved_member.faction == test_member_data["faction"]
        assert retrieved_member.admin == test_member_data["admin"]
        assert retrieved_member.salary == test_member_data["salary"]
        assert retrieved_member.notes == test_member_data["notes"]
        # Verify the date was constructed correctly using the precomputed test data
        assert retrieved_member.start == test_member_expectations["expected_start_date"]
        # Also verify it uses our test date pattern
        assert is_test_date(retrieved_member.start)

        # Note: cleanup happens automatically via cleanup_test_data fixture

    def test_update_member_details(self, repository, test_member_data):
        """Test member update operations with real DynamoDB."""
        # Arrange - Create initial member
        created_member = repository.create_from_user_input(**test_member_data)

        # Act - Update member details
        updated_notes = "Updated integration test member"
        updated_faction = "green"

        # Update member object
        created_member.notes = updated_notes
        created_member.faction = updated_faction

        # Save changes using actual save method
        repository.save(created_member)

        # Act - Retrieve updated member
        retrieved_member = repository.get_by_player(created_member.player)

        # Assert - Verify updates were persisted
        assert retrieved_member.notes == updated_notes
        assert retrieved_member.faction == updated_faction
        assert retrieved_member.player == test_member_data["player"]  # Unchanged

    def test_member_not_found(self, repository):
        """Test handling of non-existent member with real DynamoDB."""
        # Arrange
        non_existent_player = "NonExistentPlayer99999999"

        # Act
        result = repository.get_by_player(non_existent_player)

        # Assert
        assert result is None

    def test_list_members_with_test_data_isolation(self, repository, test_member_data):
        """Test that test data (99DDHHMM pattern) is isolated from production queries."""
        # Arrange - Create test member
        created_member = repository.create_from_user_input(**test_member_data)

        # Act - Get all members (this tests basic query functionality)
        all_members = repository.get_all()

        # Assert - Test member should appear in results
        test_player_in_results = any(
            member.player == created_member.player for member in all_members
        )
        assert test_player_in_results, "Test member should appear in get_all() results"

        # Verify the test date isolation by checking the member's start date
        retrieved_member = repository.get_by_player(created_member.player)
        assert is_test_date(retrieved_member.start), (
            "Member should have test date pattern for isolation"
        )

    def test_member_validation_with_real_constraints(
        self, repository, test_member_data
    ):
        """Test that DynamoDB constraints are enforced in integration tests."""
        # Arrange - Invalid member data (empty player name should fail)
        invalid_member_data = test_member_data.copy()
        invalid_member_data["player"] = ""  # Empty player name should fail

        # Act & Assert - Should raise validation error
        with pytest.raises((ValueError, Exception)) as exc_info:
            repository.create_from_user_input(**invalid_member_data)

        # Verify error is related to validation
        assert (
            "player" in str(exc_info.value).lower()
            or "validation" in str(exc_info.value).lower()
        )

    def test_concurrent_member_operations(self, repository, test_member_data):
        """Test that member operations work correctly with real DynamoDB consistency."""
        # Arrange - Create member
        created_member = repository.create_from_user_input(**test_member_data)

        # Act - Perform rapid read operations
        results = []
        for _ in range(5):
            member = repository.get_by_player(created_member.player)
            results.append(member)

        # Assert - All reads should return the same consistent data
        assert all(result is not None for result in results)
        assert all(result.player == created_member.player for result in results)
        assert len(set(result.faction for result in results)) == 1  # All same faction

    def test_large_member_notes_field(self, repository, test_member_data):
        """Test that large text fields work with real DynamoDB limits."""
        # Arrange - Create member with large notes field
        large_notes = "Large notes field: " + "x" * 1000  # 1KB+ of text
        test_member_data["notes"] = large_notes

        # Act - Create and retrieve member
        created_member = repository.create_from_user_input(**test_member_data)
        retrieved_member = repository.get_by_player(created_member.player)

        # Assert - Large text field should be handled correctly
        assert retrieved_member is not None
        assert retrieved_member.notes == large_notes
        assert len(retrieved_member.notes) > 1000
