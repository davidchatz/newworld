"""Tests for MemberRepository."""

from unittest.mock import Mock, patch

import pytest
from irus.container import IrusContainer
from irus.models.member import IrusMember
from irus.repositories.member import MemberRepository


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
    """Create MemberRepository with container-based dependencies."""
    return MemberRepository(container=test_container)


@pytest.fixture
def legacy_repository(mock_table, mock_logger):
    """Create MemberRepository with legacy dependency injection (for compatibility tests)."""
    return MemberRepository(table=mock_table, logger=mock_logger)


@pytest.fixture
def sample_member():
    """Create a sample member for testing."""
    return IrusMember(
        start=20240301,
        player="TestPlayer",
        faction="yellow",
        admin=False,
        salary=True,
        discord="testplayer#1234",
        notes="Test member",
    )


class TestMemberRepository:
    """Test suite for MemberRepository."""

    def test_save(self, repository, mock_table, sample_member):
        """Test saving a member."""
        # Arrange
        mock_table.put_item = Mock()

        # Act
        with patch.object(
            repository, "_create_timestamp", return_value="20240301120000"
        ):
            result = repository.save(sample_member)

        # Assert
        assert result == sample_member
        mock_table.put_item.assert_called_once()

        call_args = mock_table.put_item.call_args[1]
        item = call_args["Item"]

        assert item["invasion"] == "#member"
        assert item["id"] == "TestPlayer"
        assert item["start"] == 20240301
        assert item["faction"] == "yellow"
        assert item["admin"] is False
        assert item["salary"] is True
        assert item["discord"] == "testplayer#1234"
        assert item["notes"] == "Test member"
        assert item["event"] == "20240301120000"

    def test_get_by_player_found(self, repository, mock_table):
        """Test getting a member by player name when member exists."""
        # Arrange
        mock_table.get_item.return_value = {
            "Item": {
                "start": 20240301,
                "id": "TestPlayer",
                "faction": "yellow",
                "admin": False,
                "salary": True,
                "discord": "testplayer#1234",
                "notes": "Test member",
            }
        }

        # Act
        result = repository.get_by_player("TestPlayer")

        # Assert
        assert result is not None
        assert result.player == "TestPlayer"
        assert result.faction == "yellow"
        assert result.start == 20240301

        mock_table.get_item.assert_called_once_with(
            Key={"invasion": "#member", "id": "TestPlayer"}
        )

    def test_get_by_player_not_found(self, repository, mock_table):
        """Test getting a member by player name when member doesn't exist."""
        # Arrange
        mock_table.get_item.return_value = {}  # No 'Item' key

        # Act
        result = repository.get_by_player("NonExistentPlayer")

        # Assert
        assert result is None
        mock_table.get_item.assert_called_once_with(
            Key={"invasion": "#member", "id": "NonExistentPlayer"}
        )

    def test_get_generic(self, repository, mock_table):
        """Test the generic get method."""
        # Arrange
        key = {"invasion": "#member", "id": "TestPlayer"}
        mock_table.get_item.return_value = {
            "Item": {
                "start": 20240301,
                "id": "TestPlayer",
                "faction": "yellow",
                "admin": False,
                "salary": True,
            }
        }

        # Act
        result = repository.get(key)

        # Assert
        assert result is not None
        assert result.player == "TestPlayer"
        mock_table.get_item.assert_called_once_with(Key=key)

    def test_delete_by_player_success(self, repository, mock_table):
        """Test deleting a member that exists."""
        # Arrange
        mock_table.delete_item.return_value = {
            "Attributes": {"id": "TestPlayer"}  # Item was deleted
        }

        # Act
        result = repository.delete_by_player("TestPlayer")

        # Assert
        assert result is True
        mock_table.delete_item.assert_called_once_with(
            Key={"invasion": "#member", "id": "TestPlayer"}, ReturnValues="ALL_OLD"
        )

    def test_delete_by_player_not_found(self, repository, mock_table):
        """Test deleting a member that doesn't exist."""
        # Arrange
        mock_table.delete_item.return_value = {}  # No 'Attributes' key

        # Act
        result = repository.delete_by_player("NonExistentPlayer")

        # Assert
        assert result is False
        mock_table.delete_item.assert_called_once_with(
            Key={"invasion": "#member", "id": "NonExistentPlayer"},
            ReturnValues="ALL_OLD",
        )

    def test_delete_generic(self, repository, mock_table):
        """Test the generic delete method."""
        # Arrange
        key = {"invasion": "#member", "id": "TestPlayer"}
        mock_table.delete_item.return_value = {"Attributes": {"id": "TestPlayer"}}

        # Act
        result = repository.delete(key)

        # Assert
        assert result is True
        mock_table.delete_item.assert_called_once_with(Key=key, ReturnValues="ALL_OLD")

    def test_create_from_user_input_success(self, repository, mock_table):
        """Test creating a new member from user input."""
        # Arrange
        mock_table.get_item.return_value = {}  # Member doesn't exist
        mock_table.put_item = Mock()

        # Act
        with patch.object(
            repository, "_create_timestamp", return_value="20240301120000"
        ):
            result = repository.create_from_user_input(
                player="NewPlayer",
                day=15,
                month=3,
                year=2024,
                faction="yellow",
                admin=False,
                salary=True,
                discord="newplayer#5678",
                notes="New member",
            )

        # Assert
        assert isinstance(result, IrusMember)
        assert result.player == "NewPlayer"
        assert result.start == 20240315
        assert result.faction == "yellow"
        assert result.discord == "newplayer#5678"

        # Check that put_item was called twice (audit event + member)
        assert mock_table.put_item.call_count == 2

        # Check audit event
        audit_call = mock_table.put_item.call_args_list[0]
        audit_item = audit_call[1]["Item"]
        assert audit_item["invasion"] == "#memberevent"
        assert audit_item["event"] == "add"
        assert audit_item["player"] == "NewPlayer"

    def test_create_from_user_input_member_exists(self, repository, mock_table):
        """Test creating a member that already exists."""
        # Arrange
        mock_table.get_item.return_value = {
            "Item": {
                "start": 20240301,
                "id": "ExistingPlayer",
                "faction": "yellow",
                "admin": False,
                "salary": False,
            }
        }

        # Act & Assert
        with pytest.raises(ValueError, match="Member ExistingPlayer already exists"):
            repository.create_from_user_input(
                player="ExistingPlayer",
                day=15,
                month=3,
                year=2024,
                faction="yellow",
                admin=False,
                salary=True,
            )

    def test_create_from_user_input_invalid_date(self, repository, mock_table):
        """Test creating a member with invalid date."""
        # Arrange
        mock_table.get_item.return_value = {}

        # Act & Assert
        with pytest.raises(ValueError):  # Invalid date will raise ValueError
            repository.create_from_user_input(
                player="TestPlayer",
                day=30,
                month=2,  # February 30 doesn't exist
                year=2024,
                faction="yellow",
                admin=False,
                salary=True,
            )

    def test_remove_with_audit_success(self, repository, mock_table):
        """Test removing a member with audit logging."""
        # Arrange
        mock_table.delete_item.return_value = {
            "Attributes": {"id": "TestPlayer"}  # Member existed and was deleted
        }
        mock_table.put_item = Mock()

        # Act
        with patch.object(
            repository, "_create_timestamp", return_value="20240301120000"
        ):
            result = repository.remove_with_audit("TestPlayer")

        # Assert
        assert result == "## Removed member TestPlayer"

        # Check delete was called
        mock_table.delete_item.assert_called_once()

        # Check audit event was created
        mock_table.put_item.assert_called_once()
        audit_call = mock_table.put_item.call_args[1]
        audit_item = audit_call["Item"]
        assert audit_item["invasion"] == "#memberevent"
        assert audit_item["event"] == "delete"
        assert audit_item["player"] == "TestPlayer"

    def test_remove_with_audit_not_found(self, repository, mock_table):
        """Test removing a member that doesn't exist."""
        # Arrange
        mock_table.delete_item.return_value = {}  # Member didn't exist

        # Act
        result = repository.remove_with_audit("NonExistentPlayer")

        # Assert
        assert result == "*Member NonExistentPlayer not found, nothing to remove*"

        # Check delete was attempted
        mock_table.delete_item.assert_called_once()

        # Check no audit event was created for non-existent member
        mock_table.put_item.assert_not_called()

    def test_remove_with_audit_empty_player(self, repository):
        """Test removing with empty player name."""
        with pytest.raises(ValueError, match="Player name cannot be empty"):
            repository.remove_with_audit("")

        with pytest.raises(ValueError, match="Player name cannot be empty"):
            repository.remove_with_audit("   ")

    def test_legacy_compatibility(self, mock_table, mock_logger):
        """Test backward compatibility with legacy dependency injection."""
        repo = MemberRepository(table=mock_table, logger=mock_logger)

        # Should work the same as container-based approach
        assert repo.table == mock_table
        assert repo.logger == mock_logger

    def test_container_context_manager(self, mock_table, mock_logger):
        """Test using container context manager."""
        with IrusContainer.test_context(table=mock_table, logger=mock_logger):
            # Repository created inside context should use test dependencies
            repo = MemberRepository()

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

            repo = MemberRepository()

            # Access properties to trigger lazy loading
            result_table = repo.table
            result_logger = repo.logger

            mock_default.assert_called_once()
            assert result_table == mock_table
            assert result_logger == mock_logger

    def test_logging_methods(self, repository, mock_logger):
        """Test that logging methods are called appropriately."""
        # Test save operation logging
        member = IrusMember(start=20240301, player="TestPlayer", faction="yellow")

        repository.save(member)

        # Check that logger was called
        assert mock_logger.info.called
        assert mock_logger.debug.called
