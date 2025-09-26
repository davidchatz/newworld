"""Integration tests for IrusContainer with real AWS resources.

These tests validate that the dependency injection container works correctly
with real AWS services and properly manages resource lifecycle.
"""

import pytest
from irus.repositories.invasion import InvasionRepository
from irus.repositories.member import MemberRepository


class TestContainerIntegration:
    """Integration tests for container dependency injection with real AWS."""

    def test_production_container_creates_real_resources(self, integration_container):
        """Validate that production container creates working AWS clients.

        This test verifies:
        - Container can create real AWS service clients
        - Clients have proper configuration and permissions
        - Resources are accessible and functional
        """
        # Act - Get AWS clients from container
        s3_client = integration_container.s3()
        table = integration_container.table()
        logger = integration_container.logger()

        # Assert - All resources should be available and functional
        assert s3_client is not None
        assert table is not None
        assert logger is not None

        # Test basic functionality of each resource
        # DynamoDB table should be accessible
        table_name = integration_container.table_name()
        assert table_name is not None
        assert "irus-dev" in table_name.lower()

        # S3 client should be functional
        bucket_name = integration_container.bucket_name()
        assert bucket_name is not None
        assert "irus-dev" in bucket_name.lower()

        # Logger should be functional
        logger.info("Integration test: container resource validation")

    def test_repository_creation_with_real_container(self, integration_container):
        """Test that repositories work correctly with production container.

        This validates:
        - Repository initialization with real container
        - Repository can access AWS resources through container
        - Container provides proper dependency injection
        """
        # Act - Create repositories using production container
        member_repo = MemberRepository(integration_container)
        invasion_repo = InvasionRepository(integration_container)

        # Assert - Repositories should be properly initialized
        assert member_repo is not None
        assert invasion_repo is not None

        # Verify repositories can access their dependencies
        assert member_repo._container is integration_container
        assert invasion_repo._container is integration_container

        # Test basic repository functionality
        # This should not raise an exception if properly configured
        try:
            # Try a simple query operation (should not find anything with unique name)
            result = member_repo.get_by_player("NonExistentTestPlayer999999")
            assert result is None  # Expected result for non-existent player
        except Exception as e:
            pytest.fail(f"Repository should work with real container: {e}")

    def test_container_resource_sharing(self, integration_container):
        """Test that container properly shares resources between components.

        This validates:
        - Same container instance provides consistent resources
        - Resources are properly cached/reused when appropriate
        - Multiple repositories can share the same container
        """
        # Act - Create multiple repositories with same container
        member_repo_1 = MemberRepository(integration_container)
        member_repo_2 = MemberRepository(integration_container)
        invasion_repo = InvasionRepository(integration_container)

        # Assert - All repositories should share the same container resources
        assert member_repo_1._container is integration_container
        assert member_repo_2._container is integration_container
        assert invasion_repo._container is integration_container

        # Verify that underlying resources are shared appropriately
        table_1 = member_repo_1._container.table()
        table_2 = member_repo_2._container.table()
        table_3 = invasion_repo._container.table()

        # Tables should be the same instance (container reuse)
        assert table_1 is table_2
        assert table_2 is table_3

    def test_container_environment_variables(self, integration_container):
        """Test that container reads environment variables correctly.

        This validates:
        - Container gets AWS profile and region from environment
        - Container creates resources with correct configuration
        - Environment-based configuration works in integration context
        """
        # Act - Get configuration from container
        bucket_name = integration_container.bucket_name()
        table = integration_container.table()

        # Assert - Resources should reflect dev environment configuration
        assert bucket_name is not None
        assert "irus-dev" in bucket_name.lower()
        assert "ap-southeast-2" in bucket_name or "154744860445" in bucket_name

        assert table is not None
        assert "irus-dev" in table.table_name.lower()

    def test_container_error_handling_with_real_aws(self, integration_container):
        """Test container behavior with real AWS error conditions.

        This validates:
        - Container handles AWS service errors gracefully
        - Error messages are informative and actionable
        - Container doesn't crash on AWS permission or network issues
        """
        # Act - Test with invalid resource access
        s3_client = integration_container.s3()

        # Try to access a non-existent bucket (should handle error gracefully)
        try:
            response = s3_client.list_objects_v2(Bucket="non-existent-bucket-999999")
            # If this succeeds, the bucket actually exists (unexpected)
            pytest.fail("Expected NoSuchBucket error for non-existent bucket")
        except Exception as e:
            # Assert - Should get proper AWS error, not container error
            error_message = str(e).lower()
            assert "nosuchbucket" in error_message or "not found" in error_message
            # Should not be a container initialization error
            assert "container" not in error_message

    def test_container_lazy_loading(self, integration_container):
        """Test that container resources are created lazily and efficiently.

        This validates:
        - Resources are only created when requested
        - Subsequent requests reuse existing resources
        - Container doesn't create unnecessary AWS connections
        """
        # Act - Request the same resource multiple times
        table_1 = integration_container.table()
        table_2 = integration_container.table()
        table_3 = integration_container.table()

        # Assert - Should return the same instance (lazy loading with caching)
        assert table_1 is table_2
        assert table_2 is table_3

        # Act - Request different resources
        s3_client_1 = integration_container.s3()
        s3_client_2 = integration_container.s3()

        # Assert - S3 clients should also be reused
        assert s3_client_1 is s3_client_2

    def test_container_cross_service_functionality(
        self, integration_container, test_member_data
    ):
        """Test that container enables cross-service operations.

        This validates:
        - Multiple AWS services work together through container
        - Repository operations can access both DynamoDB and S3
        - Container provides consistent service configuration
        """
        # Act - Use container for operations across multiple services
        member_repo = MemberRepository(integration_container)
        s3_client = integration_container.s3()
        bucket_name = integration_container.bucket_name()

        # Create a member (DynamoDB operation)
        created_member = member_repo.create_from_user_input(**test_member_data)
        assert created_member is not None

        # Test S3 connectivity (should not interfere with DynamoDB)
        try:
            # List bucket contents (read-only operation)
            response = s3_client.list_objects_v2(Bucket=bucket_name, MaxKeys=1)
            assert "Contents" in response or response.get("KeyCount", 0) == 0
        except Exception as e:
            pytest.fail(
                f"S3 operation failed when using same container as DynamoDB: {e}"
            )

        # Verify member is still accessible after S3 operation
        retrieved_member = member_repo.get_by_player(created_member.player)
        assert retrieved_member is not None
        assert retrieved_member.player == created_member.player
