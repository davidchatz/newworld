"""Tests for LadderRankRepository."""

from unittest.mock import Mock

import pytest
from botocore.exceptions import ClientError
from irus.container import IrusContainer
from irus.models.ladderrank import IrusLadderRank
from irus.repositories.ladderrank import LadderRankRepository


class TestLadderRankRepository:
    """Test suite for LadderRankRepository."""

    @pytest.fixture
    def mock_container(self):
        """Mock container with table and logger."""
        container = Mock(spec=IrusContainer)
        container.table = Mock()
        container.logger = Mock()
        return container

    @pytest.fixture
    def repository(self, mock_container):
        """Create repository with mocked dependencies."""
        return LadderRankRepository(container=mock_container)

    @pytest.fixture
    def sample_rank(self):
        """Sample ladder rank for testing."""
        return IrusLadderRank(
            invasion_name="brightwood-20240301",
            rank="01",
            player="TestPlayer",
            score=1000,
            kills=10,
            deaths=2,
            assists=5,
            heals=20,
            damage=15000,
            member=True,
            ladder=True,
        )

    def test_initialization_with_container(self, mock_container):
        """Test repository initialization with container."""
        repo = LadderRankRepository(container=mock_container)
        assert repo.table == mock_container.table()
        assert repo.logger == mock_container.logger()

    def test_save(self, repository, sample_rank):
        """Test saving a ladder rank."""
        # Setup
        repository.table.put_item = Mock()

        # Execute
        result = repository.save(sample_rank)

        # Verify
        assert result == sample_rank
        repository.table.put_item.assert_called_once()

        call_args = repository.table.put_item.call_args[1]
        item = call_args["Item"]
        assert item["invasion"] == "#ladder#brightwood-20240301"
        assert item["id"] == "01"
        assert item["player"] == "TestPlayer"
        assert "event" in item  # Audit timestamp should be added

    def test_get(self, repository):
        """Test getting a ladder rank by key."""
        # Setup
        key = {"invasion": "#ladder#brightwood-20240301", "id": "01"}
        mock_item = {
            "invasion": "#ladder#brightwood-20240301",
            "id": "01",
            "player": "TestPlayer",
            "score": 1000,
            "kills": 10,
            "deaths": 2,
            "assists": 5,
            "heals": 20,
            "damage": 15000,
            "member": True,
            "ladder": True,
            "adjusted": False,
            "error": False,
        }
        repository.table.get_item = Mock(return_value={"Item": mock_item})

        # Execute
        result = repository.get(key)

        # Verify
        assert result is not None
        assert result.invasion_name == "brightwood-20240301"
        assert result.player == "TestPlayer"
        assert result.rank == "01"
        repository.table.get_item.assert_called_once_with(Key=key)

    def test_get_not_found(self, repository):
        """Test getting rank when it doesn't exist."""
        # Setup
        key = {"invasion": "#ladder#nonexistent", "id": "99"}
        repository.table.get_item = Mock(return_value={})  # No 'Item' key

        # Execute
        result = repository.get(key)

        # Verify
        assert result is None

    def test_delete(self, repository):
        """Test deleting a ladder rank."""
        # Setup
        key = {"invasion": "#ladder#brightwood-20240301", "id": "01"}
        repository.table.delete_item = Mock(return_value={"Attributes": {"id": "01"}})

        # Execute
        result = repository.delete(key)

        # Verify
        assert result is True
        repository.table.delete_item.assert_called_once_with(
            Key=key, ReturnValues="ALL_OLD"
        )

    def test_delete_not_found(self, repository):
        """Test deleting rank when it doesn't exist."""
        # Setup
        key = {"invasion": "#ladder#brightwood-20240301", "id": "99"}
        repository.table.delete_item = Mock(return_value={})  # No 'Attributes' key

        # Execute
        result = repository.delete(key)

        # Verify
        assert result is False

    def test_get_by_invasion_and_rank(self, repository, sample_rank):
        """Test getting rank by invasion and rank position."""
        # Setup
        mock_item = sample_rank.to_dict()
        repository.table.get_item = Mock(return_value={"Item": mock_item})

        # Execute
        result = repository.get_by_invasion_and_rank("brightwood-20240301", "01")

        # Verify
        assert result is not None
        assert result.player == "TestPlayer"
        assert result.rank == "01"

        expected_key = {"invasion": "#ladder#brightwood-20240301", "id": "01"}
        repository.table.get_item.assert_called_once_with(Key=expected_key)

    def test_get_by_player(self, repository):
        """Test getting rank by player name."""
        # Setup
        mock_item = {
            "invasion": "#ladder#brightwood-20240301",
            "id": "01",
            "player": "TestPlayer",
            "score": 1000,
            "member": True,
            "ladder": True,
            "adjusted": False,
            "error": False,
        }
        repository.table.query = Mock(return_value={"Items": [mock_item]})

        # Execute
        result = repository.get_by_player("brightwood-20240301", "TestPlayer")

        # Verify
        assert result is not None
        assert result.player == "TestPlayer"
        assert result.rank == "01"
        repository.table.query.assert_called_once()

    def test_get_by_player_not_found(self, repository):
        """Test getting rank when player not found."""
        # Setup
        repository.table.query = Mock(return_value={"Items": []})

        # Execute
        result = repository.get_by_player("brightwood-20240301", "NonExistent")

        # Verify
        assert result is None

    def test_get_by_player_multiple_matches(self, repository):
        """Test error when player matches multiple times."""
        # Setup - return two items (should never happen in real data)
        mock_items = [
            {"id": "01", "player": "TestPlayer"},
            {"id": "02", "player": "TestPlayer"},
        ]
        repository.table.query = Mock(return_value={"Items": mock_items})

        # Execute & Verify
        with pytest.raises(ValueError, match="matched multiple times"):
            repository.get_by_player("brightwood-20240301", "TestPlayer")

    def test_update_membership(self, repository):
        """Test updating rank membership status."""
        # Setup
        repository.table.update_item = Mock(
            return_value={"Attributes": {"member": True}}
        )

        # Execute
        result = repository.update_membership("brightwood-20240301", "01", True)

        # Verify
        assert result is True
        repository.table.update_item.assert_called_once()

        call_args = repository.table.update_item.call_args[1]
        assert call_args["Key"] == {
            "invasion": "#ladder#brightwood-20240301",
            "id": "01",
        }
        assert call_args["UpdateExpression"] == "SET #m = :m"
        assert call_args["ExpressionAttributeNames"] == {"#m": "member"}
        assert call_args["ExpressionAttributeValues"] == {":m": True}

    def test_update_membership_not_found(self, repository):
        """Test updating membership when rank doesn't exist."""
        # Setup
        repository.table.update_item = Mock(return_value={})  # No 'Attributes' key

        # Execute
        result = repository.update_membership("brightwood-20240301", "99", True)

        # Verify
        assert result is False

    def test_delete_by_invasion_and_rank(self, repository):
        """Test deleting rank by invasion and rank position."""
        # Setup
        repository.table.delete_item = Mock(return_value={"Attributes": {"id": "01"}})

        # Execute
        result = repository.delete_by_invasion_and_rank("brightwood-20240301", "01")

        # Verify
        assert result is True
        expected_key = {"invasion": "#ladder#brightwood-20240301", "id": "01"}
        repository.table.delete_item.assert_called_once_with(
            Key=expected_key, ReturnValues="ALL_OLD"
        )

    def test_list_by_invasion(self, repository):
        """Test getting all ranks for an invasion."""
        # Setup
        mock_items = [
            {
                "invasion": "#ladder#brightwood-20240301",
                "id": "02",
                "player": "Player2",
                "score": 800,
                "member": False,
                "ladder": True,
                "adjusted": False,
                "error": False,
            },
            {
                "invasion": "#ladder#brightwood-20240301",
                "id": "01",
                "player": "Player1",
                "score": 1000,
                "member": True,
                "ladder": True,
                "adjusted": False,
                "error": False,
            },
        ]
        repository.table.query = Mock(return_value={"Items": mock_items})

        # Execute
        result = repository.list_by_invasion("brightwood-20240301")

        # Verify
        assert len(result) == 2
        # Should be sorted by rank position
        assert result[0].rank == "01"
        assert result[0].player == "Player1"
        assert result[1].rank == "02"
        assert result[1].player == "Player2"

    def test_list_by_invasion_empty(self, repository):
        """Test listing ranks when none exist."""
        # Setup
        repository.table.query = Mock(return_value={"Items": []})

        # Execute
        result = repository.list_by_invasion("nonexistent")

        # Verify
        assert result == []

    def test_delete_all_by_invasion(self, repository):
        """Test deleting all ranks for an invasion."""
        # Setup - mock listing ranks first
        mock_ranks = [
            IrusLadderRank(invasion_name="test", rank="01", player="P1"),
            IrusLadderRank(invasion_name="test", rank="02", player="P2"),
        ]

        # Mock the list_by_invasion method
        repository.list_by_invasion = Mock(return_value=mock_ranks)

        mock_batch = Mock()
        repository.table.batch_writer = Mock(return_value=mock_batch)
        mock_batch.__enter__ = Mock(return_value=mock_batch)
        mock_batch.__exit__ = Mock(return_value=None)

        # Execute
        result = repository.delete_all_by_invasion("test")

        # Verify
        assert result == 2
        repository.list_by_invasion.assert_called_once_with("test")
        repository.table.batch_writer.assert_called_once()
        assert mock_batch.delete_item.call_count == 2

    def test_delete_all_by_invasion_empty(self, repository):
        """Test deleting all ranks when none exist."""
        # Setup
        repository.list_by_invasion = Mock(return_value=[])

        # Execute
        result = repository.delete_all_by_invasion("nonexistent")

        # Verify
        assert result == 0

    def test_save_multiple(self, repository):
        """Test saving multiple ranks with batch operations."""
        # Setup
        ranks = [
            IrusLadderRank(invasion_name="test", rank="01", player="P1"),
            IrusLadderRank(invasion_name="test", rank="02", player="P2"),
        ]

        mock_batch = Mock()
        repository.table.batch_writer = Mock(return_value=mock_batch)
        mock_batch.__enter__ = Mock(return_value=mock_batch)
        mock_batch.__exit__ = Mock(return_value=None)

        # Execute
        result = repository.save_multiple(ranks)

        # Verify
        assert result == ranks
        repository.table.batch_writer.assert_called_once()
        assert mock_batch.put_item.call_count == 2

    def test_save_multiple_empty(self, repository):
        """Test saving empty list."""
        # Execute
        result = repository.save_multiple([])

        # Verify
        assert result == []

    def test_save_multiple_client_error(self, repository):
        """Test save_multiple with DynamoDB client error."""
        # Setup
        ranks = [IrusLadderRank(invasion_name="test", rank="01", player="P1")]

        mock_batch = Mock()
        repository.table.batch_writer = Mock(return_value=mock_batch)
        mock_batch.__enter__ = Mock(return_value=mock_batch)
        mock_batch.__exit__ = Mock(
            side_effect=ClientError(
                error_response={
                    "Error": {"Code": "TestError", "Message": "Test error"}
                },
                operation_name="BatchWriteItem",
            )
        )

        # Execute & Verify
        with pytest.raises(ValueError, match="Failed to save multiple ranks"):
            repository.save_multiple(ranks)

    def test_repository_logging(self, repository, sample_rank):
        """Test that repository operations are logged."""
        # Setup
        repository.table.put_item = Mock()

        # Execute
        repository.save(sample_rank)

        # Verify logging calls were made
        assert repository.logger.info.called
        log_calls = [call[0][0] for call in repository.logger.info.call_args_list]
        assert any("save" in call for call in log_calls)

    def test_timestamp_creation(self, repository, sample_rank):
        """Test that timestamps are created for audit trails."""
        # Setup
        repository.table.put_item = Mock()

        # Execute
        repository.save(sample_rank)

        # Verify timestamp was added
        call_args = repository.table.put_item.call_args[1]
        item = call_args["Item"]
        assert "event" in item
        assert isinstance(item["event"], str)
        assert len(item["event"]) > 10  # Should be a timestamp string

    @pytest.mark.parametrize(
        "invasion_name,rank_pos,expected_key",
        [
            (
                "brightwood-20240301",
                "01",
                {"invasion": "#ladder#brightwood-20240301", "id": "01"},
            ),
            ("test", "05", {"invasion": "#ladder#test", "id": "05"}),
            (
                "long-invasion-name",
                "99",
                {"invasion": "#ladder#long-invasion-name", "id": "99"},
            ),
        ],
    )
    def test_key_generation(self, invasion_name, rank_pos, expected_key):
        """Test DynamoDB key generation for different invasions and ranks."""
        rank = IrusLadderRank(
            invasion_name=invasion_name, rank=rank_pos, player="TestPlayer"
        )
        assert rank.key() == expected_key
