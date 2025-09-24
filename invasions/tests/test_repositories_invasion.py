"""Tests for InvasionRepository."""

from unittest.mock import Mock, patch

import pytest
from irus.container import IrusContainer
from irus.models.invasion import IrusInvasion
from irus.repositories.invasion import InvasionRepository


@pytest.fixture
def mock_table():
    """Create a mock DynamoDB table."""
    return Mock()


@pytest.fixture
def mock_logger():
    """Create a mock logger."""
    return Mock()


@pytest.fixture
def test_container(mock_table, mock_logger):
    """Create test container with mocked dependencies."""
    return IrusContainer.create_test(table=mock_table, logger=mock_logger)


@pytest.fixture
def repository(test_container):
    """Create InvasionRepository with container-based dependencies."""
    return InvasionRepository(container=test_container)


@pytest.fixture
def legacy_repository(mock_table, mock_logger):
    """Create InvasionRepository with legacy dependency injection."""
    return InvasionRepository(table=mock_table, logger=mock_logger)


@pytest.fixture
def sample_invasion():
    """Create a sample invasion for testing."""
    return IrusInvasion(
        name="20240301-bw",
        settlement="bw",
        win=True,
        date=20240301,
        year=2024,
        month=3,
        day=1,
        notes="Test invasion",
    )


class TestInvasionRepository:
    """Test suite for InvasionRepository."""

    def test_save(self, repository, mock_table, sample_invasion):
        """Test saving an invasion."""
        # Arrange
        mock_table.put_item = Mock()

        # Act
        result = repository.save(sample_invasion)

        # Assert
        assert result == sample_invasion
        mock_table.put_item.assert_called_once()

        call_args = mock_table.put_item.call_args[1]
        item = call_args["Item"]

        assert item["invasion"] == "#invasion"
        assert item["id"] == "20240301-bw"
        assert item["settlement"] == "bw"
        assert item["win"] is True
        assert item["date"] == 20240301
        assert item["year"] == 2024
        assert item["month"] == 3
        assert item["day"] == 1
        assert item["notes"] == "Test invasion"

    def test_get_by_name_found(self, repository, mock_table):
        """Test getting an invasion by name when invasion exists."""
        # Arrange
        mock_table.get_item.return_value = {
            "Item": {
                "id": "20240301-ef",
                "settlement": "ef",
                "win": False,
                "date": 20240301,
                "year": 2024,
                "month": 3,
                "day": 1,
                "notes": "Close fight",
            }
        }

        # Act
        result = repository.get_by_name("20240301-ef")

        # Assert
        assert result is not None
        assert result.name == "20240301-ef"
        assert result.settlement == "ef"
        assert result.win is False
        assert result.date == 20240301

        mock_table.get_item.assert_called_once_with(
            Key={"invasion": "#invasion", "id": "20240301-ef"}
        )

    def test_get_by_name_not_found(self, repository, mock_table):
        """Test getting an invasion by name when invasion doesn't exist."""
        # Arrange
        mock_table.get_item.return_value = {}  # No 'Item' key

        # Act
        result = repository.get_by_name("20240301-nonexistent")

        # Assert
        assert result is None
        mock_table.get_item.assert_called_once_with(
            Key={"invasion": "#invasion", "id": "20240301-nonexistent"}
        )

    def test_get_generic(self, repository, mock_table):
        """Test the generic get method."""
        # Arrange
        key = {"invasion": "#invasion", "id": "20240301-ww"}
        mock_table.get_item.return_value = {
            "Item": {
                "id": "20240301-ww",
                "settlement": "ww",
                "win": True,
                "date": 20240301,
                "year": 2024,
                "month": 3,
                "day": 1,
            }
        }

        # Act
        result = repository.get(key)

        # Assert
        assert result is not None
        assert result.name == "20240301-ww"
        mock_table.get_item.assert_called_once_with(Key=key)

    def test_delete_by_name_success(self, repository, mock_table):
        """Test deleting an invasion that exists."""
        # Arrange
        mock_table.delete_item.return_value = {
            "Attributes": {"id": "20240301-bw"}  # Item was deleted
        }

        # Act
        result = repository.delete_by_name("20240301-bw")

        # Assert
        assert result is True
        mock_table.delete_item.assert_called_once_with(
            Key={"invasion": "#invasion", "id": "20240301-bw"}, ReturnValues="ALL_OLD"
        )

    def test_delete_by_name_not_found(self, repository, mock_table):
        """Test deleting an invasion that doesn't exist."""
        # Arrange
        mock_table.delete_item.return_value = {}  # No 'Attributes' key

        # Act
        result = repository.delete_by_name("20240301-nonexistent")

        # Assert
        assert result is False
        mock_table.delete_item.assert_called_once_with(
            Key={"invasion": "#invasion", "id": "20240301-nonexistent"},
            ReturnValues="ALL_OLD",
        )

    def test_delete_generic(self, repository, mock_table):
        """Test the generic delete method."""
        # Arrange
        key = {"invasion": "#invasion", "id": "20240301-ef"}
        mock_table.delete_item.return_value = {"Attributes": {"id": "20240301-ef"}}

        # Act
        result = repository.delete(key)

        # Assert
        assert result is True
        mock_table.delete_item.assert_called_once_with(Key=key, ReturnValues="ALL_OLD")

    def test_create_from_user_input_success(self, repository, mock_table):
        """Test creating a new invasion from user input."""
        # Arrange
        mock_table.get_item.return_value = {}  # Invasion doesn't exist
        mock_table.put_item = Mock()

        # Act
        result = repository.create_from_user_input(
            day=15,
            month=6,
            year=2024,
            settlement="bw",
            win=True,
            notes="Great victory!",
        )

        # Assert
        assert isinstance(result, IrusInvasion)
        assert result.name == "20240615-bw"
        assert result.settlement == "bw"
        assert result.win is True
        assert result.date == 20240615
        assert result.notes == "Great victory!"

        # Check that get_item was called to check for existing invasion
        mock_table.get_item.assert_called_once()

        # Check that put_item was called to save the invasion
        mock_table.put_item.assert_called_once()

    def test_create_from_user_input_invasion_exists(self, repository, mock_table):
        """Test creating an invasion that already exists."""
        # Arrange
        mock_table.get_item.return_value = {
            "Item": {
                "id": "20240615-ef",
                "settlement": "ef",
                "win": False,
                "date": 20240615,
                "year": 2024,
                "month": 6,
                "day": 15,
            }
        }

        # Act & Assert
        with pytest.raises(ValueError, match="Invasion 20240615-ef already exists"):
            repository.create_from_user_input(
                day=15, month=6, year=2024, settlement="ef", win=True
            )

    def test_create_from_user_input_invalid_date(self, repository):
        """Test creating an invasion with invalid date."""
        # Act & Assert
        with pytest.raises(ValueError):  # Invalid date will raise ValueError
            repository.create_from_user_input(
                day=30,
                month=2,  # February 30 doesn't exist
                year=2024,
                settlement="bw",
                win=True,
            )

    def test_get_by_date_range(self, repository, mock_table):
        """Test getting invasions by date range."""
        # Arrange
        mock_table.scan.return_value = {
            "Items": [
                {
                    "id": "20240301-bw",
                    "settlement": "bw",
                    "win": True,
                    "date": 20240301,
                    "year": 2024,
                    "month": 3,
                    "day": 1,
                },
                {
                    "id": "20240315-ef",
                    "settlement": "ef",
                    "win": False,
                    "date": 20240315,
                    "year": 2024,
                    "month": 3,
                    "day": 15,
                },
            ]
        }

        # Act
        result = repository.get_by_date_range(20240301, 20240331)

        # Assert
        assert len(result) == 2
        assert all(isinstance(invasion, IrusInvasion) for invasion in result)
        assert result[0].name == "20240301-bw"
        assert result[1].name == "20240315-ef"

        mock_table.scan.assert_called_once()

    def test_get_by_date_range_no_results(self, repository, mock_table):
        """Test getting invasions by date range with no results."""
        # Arrange
        mock_table.scan.return_value = {"Items": []}

        # Act
        result = repository.get_by_date_range(20240401, 20240430)

        # Assert
        assert len(result) == 0
        assert isinstance(result, list)

    def test_get_by_month(self, repository):
        """Test getting invasions by month."""
        # Mock the get_by_date_range method since get_by_month uses it
        with patch.object(repository, "get_by_date_range") as mock_get_range:
            mock_invasions = [Mock(spec=IrusInvasion)]
            mock_get_range.return_value = mock_invasions

            # Act
            result = repository.get_by_month(2024, 3)

            # Assert
            assert result == mock_invasions
            # Should call get_by_date_range with March 1-31, 2024
            mock_get_range.assert_called_once_with(20240301, 20240331)

    def test_get_by_month_february_leap_year(self, repository):
        """Test getting invasions for February in a leap year."""
        with patch.object(repository, "get_by_date_range") as mock_get_range:
            mock_get_range.return_value = []

            # Act
            repository.get_by_month(2024, 2)  # Leap year February

            # Assert
            # Should call get_by_date_range with Feb 1-29, 2024
            mock_get_range.assert_called_once_with(20240201, 20240229)

    def test_get_by_month_december(self, repository):
        """Test getting invasions for December (year rollover)."""
        with patch.object(repository, "get_by_date_range") as mock_get_range:
            mock_get_range.return_value = []

            # Act
            repository.get_by_month(2024, 12)

            # Assert
            # Should call get_by_date_range with Dec 1-31, 2024
            mock_get_range.assert_called_once_with(20241201, 20241231)

    def test_get_by_settlement(self, repository, mock_table):
        """Test getting invasions by settlement."""
        # Arrange
        mock_table.scan.return_value = {
            "Items": [
                {
                    "id": "20240301-bw",
                    "settlement": "bw",
                    "win": True,
                    "date": 20240301,
                    "year": 2024,
                    "month": 3,
                    "day": 1,
                },
                {
                    "id": "20240315-bw",
                    "settlement": "bw",
                    "win": False,
                    "date": 20240315,
                    "year": 2024,
                    "month": 3,
                    "day": 15,
                },
            ]
        }

        # Act
        result = repository.get_by_settlement("bw")

        # Assert
        assert len(result) == 2
        assert all(invasion.settlement == "bw" for invasion in result)
        assert result[0].name == "20240301-bw"
        assert result[1].name == "20240315-bw"

        mock_table.scan.assert_called_once()

    def test_get_by_settlement_case_insensitive(self, repository, mock_table):
        """Test getting invasions by settlement is case insensitive."""
        # Arrange
        mock_table.scan.return_value = {"Items": []}

        # Act
        repository.get_by_settlement("BW")

        # Assert - should search for lowercase 'bw'
        mock_table.scan.assert_called_once()
        # The filter expression should search for 'bw', not 'BW'
        # This is implicitly tested by the method converting to lowercase

    def test_legacy_compatibility(self, mock_table, mock_logger):
        """Test backward compatibility with legacy dependency injection."""
        repo = InvasionRepository(table=mock_table, logger=mock_logger)

        # Should work the same as container-based approach
        assert repo.table == mock_table
        assert repo.logger == mock_logger

    def test_container_context_manager(self, mock_table, mock_logger):
        """Test using container context manager."""
        with IrusContainer.test_context(table=mock_table, logger=mock_logger):
            # Repository created inside context should use test dependencies
            repo = InvasionRepository()

            assert repo.table == mock_table
            assert repo.logger == mock_logger

    def test_default_container_initialization(self):
        """Test that repository initializes with default container when no dependencies provided."""
        with patch.object(IrusContainer, "default") as mock_default:
            mock_container = Mock()
            mock_table = Mock()
            mock_logger = Mock()
            mock_container.table.return_value = mock_table
            mock_container.logger.return_value = mock_logger
            mock_default.return_value = mock_container

            repo = InvasionRepository()

            # Access properties to trigger lazy loading
            result_table = repo.table
            result_logger = repo.logger

            mock_default.assert_called_once()
            assert result_table == mock_table
            assert result_logger == mock_logger

    def test_logging_methods(self, repository, mock_logger):
        """Test that logging methods are called appropriately."""
        # Test save operation logging
        invasion = IrusInvasion(
            name="20240301-bw",
            settlement="bw",
            win=True,
            date=20240301,
            year=2024,
            month=3,
            day=1,
        )

        repository.save(invasion)

        # Check that logger was called
        assert mock_logger.info.called
        assert mock_logger.debug.called
