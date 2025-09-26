"""Integration tests for InvasionRepository with real DynamoDB.

These tests validate that the InvasionRepository works correctly with
real AWS DynamoDB resources using the year 9999 test data strategy.
"""

import pytest
from irus.repositories.invasion import InvasionRepository

from tests.integration.conftest import is_test_date


class TestInvasionRepositoryIntegration:
    """Integration tests for invasion repository CRUD operations."""

    @pytest.fixture
    def repository(self, integration_container):
        """Create InvasionRepository with real AWS container."""
        return InvasionRepository(integration_container)

    def test_create_and_retrieve_invasion(self, repository, test_invasion_data):
        """Test full invasion lifecycle with real DynamoDB.

        This test validates:
        - Invasion creation with real DynamoDB table
        - Invasion retrieval by invasion ID
        - Data integrity and type conversion
        """
        # Arrange - test_invasion_data fixture provides unique test data

        try:
            # Act - Create invasion
            created_invasion = repository.create_from_user_input(**test_invasion_data)

            # Act - Retrieve invasion
            retrieved_invasion = repository.get_by_name(created_invasion.name)

            # Assert - Verify invasion was created and retrieved correctly
            assert retrieved_invasion is not None
            assert retrieved_invasion.name == created_invasion.name
            assert retrieved_invasion.settlement == test_invasion_data["settlement"]
            assert retrieved_invasion.win == test_invasion_data["win"]
            assert retrieved_invasion.notes == test_invasion_data["notes"]

        except ValueError as e:
            if "already exists" in str(e):
                pytest.skip(f"Test data conflict (rare): {e}")
            else:
                raise

        # Note: cleanup happens automatically via cleanup_test_data fixture

    def test_get_invasions_by_date_range(self, repository, test_invasion_data):
        """Test date range queries with real DynamoDB."""
        # Arrange - Create multiple test invasions with different dates
        invasion_data_1 = test_invasion_data.copy()
        invasion_data_1["day"] = 1
        invasion_data_1["month"] = 3
        invasion_data_1["settlement"] = "ef"

        invasion_data_2 = test_invasion_data.copy()
        invasion_data_2["day"] = 2
        invasion_data_2["month"] = 3
        invasion_data_2["settlement"] = "bw"

        invasion_data_3 = test_invasion_data.copy()
        invasion_data_3["day"] = 3
        invasion_data_3["month"] = 3
        invasion_data_3["settlement"] = "ww"

        # Act - Create invasions
        inv1 = repository.create_from_user_input(**invasion_data_1)
        inv2 = repository.create_from_user_input(**invasion_data_2)
        inv3 = repository.create_from_user_input(**invasion_data_3)

        # Act - Query invasions for March (using the test year from the created invasion)
        march_invasions = repository.get_by_month(inv1.year, 3)

        # Assert - Should find all three test invasions
        invasion_names = [inv.name for inv in march_invasions]
        assert inv1.name in invasion_names
        assert inv2.name in invasion_names
        assert inv3.name in invasion_names

    def test_invasion_not_found(self, repository):
        """Test handling of non-existent invasion with real DynamoDB."""
        # Arrange
        non_existent_invasion_name = "99999999-nonexistent"

        # Act
        result = repository.get_by_name(non_existent_invasion_name)

        # Assert
        assert result is None

    def test_test_data_isolation_from_production(self, repository, test_invasion_data):
        """Test that test data (99DDHHMM pattern) is isolated from production queries."""
        # Arrange - Create test invasion
        created_invasion = repository.create_from_user_input(**test_invasion_data)

        # Act - Try to get invasions with production date patterns (2024)
        production_invasions = repository.get_by_month(2024, 3)  # March 2024

        # Assert - Test invasion should not appear in production queries
        test_invasion_in_results = any(
            inv.name == created_invasion.name for inv in production_invasions
        )
        assert not test_invasion_in_results, (
            "Test invasion should not appear in production date queries"
        )

        # Act - Query with the test year should find the test invasion
        test_invasions = repository.get_by_month(
            created_invasion.year, created_invasion.month
        )

        # Assert - Test invasion should appear in test date queries
        test_invasion_in_test_results = any(
            inv.name == created_invasion.name for inv in test_invasions
        )
        assert test_invasion_in_test_results, (
            "Test invasion should appear in test date queries"
        )

    def test_invasion_with_notes(self, repository, test_invasion_data):
        """Test invasion creation and retrieval with notes."""
        # Arrange - Add notes to invasion
        test_invasion_data["notes"] = "Test invasion with detailed notes"

        # Act - Create invasion with notes
        created_invasion = repository.create_from_user_input(**test_invasion_data)

        # Act - Retrieve invasion
        retrieved_invasion = repository.get_by_name(created_invasion.name)

        # Assert - Verify notes are preserved
        assert retrieved_invasion is not None
        assert retrieved_invasion.notes == "Test invasion with detailed notes"

    def test_invasion_key_generation(self, repository, test_invasion_data):
        """Test that invasions generate correct DynamoDB keys."""
        # Arrange - Create invasion
        created_invasion = repository.create_from_user_input(**test_invasion_data)

        # Act - Get DynamoDB key
        key = created_invasion.key()

        # Assert - Verify key format
        assert key == {"invasion": "#invasion", "id": created_invasion.name}
        # Assert - Invasion name should use test data format (starts with 99)
        assert is_test_date(created_invasion.year), (
            "Test invasion should use 99DDHHMM year pattern"
        )

    def test_bulk_invasion_operations(self, repository):
        """Test bulk operations with real DynamoDB performance characteristics."""
        # Arrange - Create multiple test invasions with proper data format
        invasion_data_list = []
        settlements = ["bw", "ef", "ww", "md", "rw", "ck", "wf", "mb", "eg", "rs"]
        for i in range(10):
            invasion_data = {
                "day": i + 1,
                "month": 3,
                "year": 9999,
                "settlement": settlements[i % len(settlements)],
                "win": i % 2 == 0,
                "notes": f"Bulk test invasion {i}",
            }
            invasion_data_list.append(invasion_data)

        # Act - Create invasions in bulk
        created_invasions = []
        for data in invasion_data_list:
            invasion = repository.create_from_user_input(**data)
            created_invasions.append(invasion)

        # Act - Retrieve all created invasions
        retrieved_invasions = []
        for invasion in created_invasions:
            retrieved = repository.get_by_name(invasion.name)
            retrieved_invasions.append(retrieved)

        # Assert - All invasions should be created and retrievable
        assert len(retrieved_invasions) == 10
        assert all(inv is not None for inv in retrieved_invasions)

        # Verify names match
        created_names = {inv.name for inv in created_invasions}
        retrieved_names = {inv.name for inv in retrieved_invasions}
        assert created_names == retrieved_names

    def test_invasion_date_parsing_and_queries(self, repository, test_invasion_data):
        """Test that invasion date parsing works correctly with real DynamoDB."""
        # Arrange - Create invasions with different settlements but same date pattern
        # Each will get the same 99DDHHMM pattern but different settlement

        invasion_data_1 = test_invasion_data.copy()
        invasion_data_1["settlement"] = "bw"
        invasion_data_1["win"] = True

        invasion_data_2 = test_invasion_data.copy()
        invasion_data_2["settlement"] = "ef"
        invasion_data_2["win"] = False

        invasion_data_3 = test_invasion_data.copy()
        invasion_data_3["settlement"] = "ww"
        invasion_data_3["win"] = True

        # Act - Create invasions
        inv1 = repository.create_from_user_input(**invasion_data_1)
        inv2 = repository.create_from_user_input(**invasion_data_2)
        inv3 = repository.create_from_user_input(**invasion_data_3)

        # Act - Query by the test month
        test_month_invasions = repository.get_by_month(inv1.year, inv1.month)

        # Assert - All invasions should be found in the same month query
        invasion_names = [inv.name for inv in test_month_invasions]
        assert inv1.name in invasion_names
        assert inv2.name in invasion_names
        assert inv3.name in invasion_names

        # Assert - Each invasion should have unique settlement
        settlements_found = {
            inv.settlement
            for inv in test_month_invasions
            if inv.name in [inv1.name, inv2.name, inv3.name]
        }
        assert "bw" in settlements_found
        assert "ef" in settlements_found
        assert "ww" in settlements_found
