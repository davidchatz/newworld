"""Integration tests for MemberManagementService with real AWS resources.

These tests are SKIPPED because MemberManagementService uses legacy dependencies
(IrusInvasionList, IrusLadderRank) that need modernization before integration testing.
"""

import pytest
from irus.repositories.invasion import InvasionRepository
from irus.repositories.member import MemberRepository
from irus.services.member_management import MemberManagementService


# @pytest.mark.skip(
#     reason="MemberManagementService uses legacy dependencies - modernize first"
# )
class TestMemberManagementServiceIntegration:
    """Integration tests for member management service business logic."""

    @pytest.fixture
    def service(self, integration_container):
        """Create MemberManagementService with real AWS container."""
        return MemberManagementService(integration_container)

    @pytest.fixture
    def member_repo(self, integration_container):
        """Create MemberRepository for test setup."""
        return MemberRepository(integration_container)

    @pytest.fixture
    def invasion_repo(self, integration_container):
        """Create InvasionRepository for test setup."""
        return InvasionRepository(integration_container)

    def test_service_with_real_member(self, service, member_repo, test_member_data):
        """Test service with properly created member from repository."""
        # Arrange - Create member through repository (which handles the proper data conversion)
        test_member = member_repo.create_from_user_input(**test_member_data)

        # Act - Call service with the actual member object
        result = service.update_invasions_for_new_member(test_member)

        # Assert - Service should return a result string
        assert result is not None
        assert isinstance(result, str)

    def test_service_initialization(self, integration_container):
        """Test service can be initialized with integration container."""
        # Arrange & Act
        service = MemberManagementService(integration_container)

        # Assert - Service should be properly initialized
        assert service is not None
        assert service._container == integration_container

    def test_service_with_invasions_and_member(
        self, service, member_repo, invasion_repo, test_member_data, test_invasion_data
    ):
        """Test service with both invasions and members created through proper repositories."""
        # Arrange - Create test invasion first
        _invasion = invasion_repo.create_from_user_input(**test_invasion_data)

        # Create member with test data
        test_member = member_repo.create_from_user_input(**test_member_data)

        # Act - Process member
        result = service.update_invasions_for_new_member(test_member)

        # Assert - Service should complete successfully
        assert result is not None
        assert isinstance(result, str)

    def test_service_error_handling(self, service, member_repo, test_member_data):
        """Test service error handling with proper member object."""
        # Arrange - Create member with valid data
        test_member_data["day"] = 1
        test_member_data["month"] = 1
        test_member = member_repo.create_from_user_input(**test_member_data)

        # Act - Try to process member (should handle gracefully even with no invasions)
        try:
            result = service.update_invasions_for_new_member(test_member)
            # Should succeed and return a result
            assert result is not None
            assert isinstance(result, str)
        except Exception as e:
            # If it fails, should be a reasonable business logic error
            error_message = str(e).lower()
            assert "member" in error_message or "invasion" in error_message

    def test_service_dependency_injection(self, integration_container):
        """Test service uses container for dependency injection."""
        # Arrange & Act
        service = MemberManagementService(integration_container)

        # Assert - Service should use the provided container
        assert service._container == integration_container
        assert service._logger is not None  # Logger should be accessible

    def test_service_logging_integration(self, service, member_repo, test_member_data):
        """Test that service logging works with real AWS integration."""
        # Arrange - Create member
        test_member = member_repo.create_from_user_input(**test_member_data)

        # Act - Call service (should log operations)
        result = service.update_invasions_for_new_member(test_member)

        # Assert - Service should complete without logging errors
        assert result is not None
        # The actual logging verification would require log capture,
        # but this tests that logging doesn't break the service
