"""Tests for LadderRepository collection manager."""

from unittest.mock import Mock, patch

import pytest
from botocore.exceptions import ClientError
from irus.container import IrusContainer
from irus.models.ladder import IrusLadder
from irus.models.ladderrank import IrusLadderRank
from irus.repositories.ladder import LadderRepository


class TestLadderRepository:
    """Test suite for LadderRepository collection manager."""

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
        # Mock the internal rank repository
        with patch(
            "irus.repositories.ladder.LadderRankRepository"
        ) as mock_rank_repo_class:
            mock_rank_repo = Mock()
            mock_rank_repo_class.return_value = mock_rank_repo

            repo = LadderRepository(container=mock_container)
            repo._mock_rank_repo = mock_rank_repo  # Store reference for tests
            return repo

    @pytest.fixture
    def sample_ladder_rank(self):
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

    @pytest.fixture
    def sample_ladder(self, sample_ladder_rank):
        """Sample ladder for testing."""
        rank2 = IrusLadderRank(
            invasion_name="brightwood-20240301",
            rank="02",
            player="TestPlayer2",
            score=800,
            kills=8,
            deaths=3,
            assists=4,
            heals=15,
            damage=12000,
            member=False,
            ladder=True,
        )
        return IrusLadder(
            invasion_name="brightwood-20240301", ranks=[sample_ladder_rank, rank2]
        )

    def test_initialization_with_container(self, mock_container):
        """Test repository initialization with container."""
        with patch("irus.repositories.ladder.LadderRankRepository"):
            repo = LadderRepository(container=mock_container)
            assert repo.container == mock_container
            assert repo.table == mock_container.table
            assert repo.logger == mock_container.logger

    def test_initialization_legacy_compatibility(self):
        """Test legacy initialization with table and logger."""
        mock_table = Mock()
        mock_logger = Mock()

        with patch("irus.repositories.ladder.LadderRankRepository"):
            repo = LadderRepository(table=mock_table, logger=mock_logger)
            # Should create container internally
            assert repo.table == mock_table
            assert repo.logger == mock_logger

    def test_save_rank(self, repository, sample_ladder_rank):
        """Test saving a single ladder rank."""
        # Setup
        repository._mock_rank_repo.save.return_value = sample_ladder_rank

        # Execute
        result = repository.save_rank(sample_ladder_rank)

        # Verify
        assert result == sample_ladder_rank
        repository._mock_rank_repo.save.assert_called_once_with(sample_ladder_rank)

    def test_save_ladder(self, repository, sample_ladder):
        """Test saving a complete ladder."""
        # Setup
        repository._mock_rank_repo.save_multiple.return_value = sample_ladder.ranks

        # Execute
        result = repository.save_ladder(sample_ladder)

        # Verify
        assert result == sample_ladder
        repository._mock_rank_repo.save_multiple.assert_called_once_with(
            sample_ladder.ranks
        )

    def test_save_ladder_client_error(self, repository, sample_ladder):
        """Test save_ladder with DynamoDB client error."""
        # Setup
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
        with pytest.raises(ValueError, match="Failed to save ladder"):
            repository.save_ladder(sample_ladder)

    def test_get_ladder(self, repository, sample_ladder):
        """Test getting a complete ladder."""
        # Setup
        mock_items = [
            {
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
            },
            {
                "invasion": "#ladder#brightwood-20240301",
                "id": "02",
                "player": "TestPlayer2",
                "score": 800,
                "kills": 8,
                "deaths": 3,
                "assists": 4,
                "heals": 15,
                "damage": 12000,
                "member": False,
                "ladder": True,
                "adjusted": False,
                "error": False,
            },
        ]

        repository.table.query = Mock(return_value={"Items": mock_items})

        # Execute
        result = repository.get_ladder("brightwood-20240301")

        # Verify
        assert result is not None
        assert result.invasion_name == "brightwood-20240301"
        assert len(result.ranks) == 2
        assert result.ranks[0].rank == "01"
        assert result.ranks[1].rank == "02"

        repository.table.query.assert_called_once()

    def test_get_ladder_not_found(self, repository):
        """Test getting ladder when none exists."""
        # Setup
        repository.table.query = Mock(return_value={"Items": []})

        # Execute
        result = repository.get_ladder("nonexistent")

        # Verify
        assert result is None

    def test_get_ladder_client_error(self, repository):
        """Test get_ladder with DynamoDB client error."""
        # Setup
        repository.table.query = Mock(
            side_effect=ClientError(
                error_response={
                    "Error": {"Code": "TestError", "Message": "Test error"}
                },
                operation_name="Query",
            )
        )

        # Execute & Verify
        with pytest.raises(ValueError, match="Failed to get ladder"):
            repository.get_ladder("brightwood-20240301")

    def test_get_rank_by_player(self, repository):
        """Test getting a specific player's rank."""
        # Setup
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

        repository.table.query = Mock(return_value={"Items": [mock_item]})

        # Execute
        result = repository.get_rank_by_player("brightwood-20240301", "TestPlayer")

        # Verify
        assert result is not None
        assert result.player == "TestPlayer"
        assert result.rank == "01"
        assert result.score == 1000

    def test_get_rank_by_player_not_found(self, repository):
        """Test getting rank when player not found."""
        # Setup
        repository.table.query = Mock(return_value={"Items": []})

        # Execute
        result = repository.get_rank_by_player("brightwood-20240301", "NonExistent")

        # Verify
        assert result is None

    def test_get_rank_by_player_multiple_matches(self, repository):
        """Test error when player matches multiple times."""
        # Setup - return two items (should never happen in real data)
        mock_items = [
            {"id": "01", "player": "TestPlayer"},
            {"id": "02", "player": "TestPlayer"},
        ]
        repository.table.query = Mock(return_value={"Items": mock_items})

        # Execute & Verify
        with pytest.raises(ValueError, match="matched multiple times"):
            repository.get_rank_by_player("brightwood-20240301", "TestPlayer")

    def test_delete_ladder(self, repository):
        """Test deleting an entire ladder."""
        # Setup - mock getting ladder first
        mock_items = [
            {"invasion": "#ladder#test", "id": "01", "player": "P1"},
            {"invasion": "#ladder#test", "id": "02", "player": "P2"},
        ]
        repository.table.query = Mock(return_value={"Items": mock_items})

        mock_batch = Mock()
        repository.table.batch_writer = Mock(return_value=mock_batch)
        mock_batch.__enter__ = Mock(return_value=mock_batch)
        mock_batch.__exit__ = Mock(return_value=None)

        # Execute
        result = repository.delete_ladder("test")

        # Verify
        assert result is True
        assert mock_batch.delete_item.call_count == 2

    def test_delete_ladder_not_found(self, repository):
        """Test deleting ladder when none exists."""
        # Setup
        repository.table.query = Mock(return_value={"Items": []})

        # Execute
        result = repository.delete_ladder("nonexistent")

        # Verify
        assert result is False

    def test_delete_rank(self, repository):
        """Test deleting a specific rank."""
        # Setup
        repository.table.delete_item = Mock(return_value={"Attributes": {"id": "01"}})

        # Execute
        result = repository.delete_rank("brightwood-20240301", "01")

        # Verify
        assert result is True
        repository.table.delete_item.assert_called_once_with(
            Key={"invasion": "#ladder#brightwood-20240301", "id": "01"},
            ReturnValues="ALL_OLD",
        )

    def test_delete_rank_not_found(self, repository):
        """Test deleting rank when it doesn't exist."""
        # Setup
        repository.table.delete_item = Mock(return_value={})  # No 'Attributes' key

        # Execute
        result = repository.delete_rank("brightwood-20240301", "99")

        # Verify
        assert result is False

    def test_update_rank_membership(self, repository):
        """Test updating rank membership status."""
        # Setup
        repository.table.update_item = Mock(
            return_value={"Attributes": {"member": True}}
        )

        # Execute
        result = repository.update_rank_membership("brightwood-20240301", "01", True)

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

    def test_update_rank_membership_not_found(self, repository):
        """Test updating membership when rank doesn't exist."""
        # Setup
        repository.table.update_item = Mock(return_value={})  # No 'Attributes' key

        # Execute
        result = repository.update_rank_membership("brightwood-20240301", "99", True)

        # Verify
        assert result is False

    def test_create_upload_record(self, repository):
        """Test creating upload audit record."""
        # Setup
        repository.table.put_item = Mock()

        # Execute
        repository.create_upload_record("brightwood-20240301", "test.png")

        # Verify
        repository.table.put_item.assert_called_once()
        call_args = repository.table.put_item.call_args[1]
        item = call_args["Item"]

        assert item["invasion"] == "#upload#brightwood-20240301"
        assert item["id"] == "test.png"
        assert "event" in item  # Should have timestamp

    def test_create_upload_record_client_error(self, repository):
        """Test upload record creation with client error (should not fail)."""
        # Setup
        repository.table.put_item = Mock(
            side_effect=ClientError(
                error_response={
                    "Error": {"Code": "TestError", "Message": "Test error"}
                },
                operation_name="PutItem",
            )
        )

        # Execute - should not raise exception
        repository.create_upload_record("brightwood-20240301", "test.png")

        # Verify - error should be logged but not raised
        repository.logger.info.assert_called()

    def test_save_ladder_from_processing(self, repository, sample_ladder):
        """Test saving ladder from image/CSV processing."""
        # Setup mocks for both upload record and ladder save
        repository.table.put_item = Mock()  # For upload record
        mock_batch = Mock()
        repository.table.batch_writer = Mock(return_value=mock_batch)
        mock_batch.__enter__ = Mock(return_value=mock_batch)
        mock_batch.__exit__ = Mock(return_value=None)

        # Execute
        result = repository.save_ladder_from_processing(sample_ladder, "test.png")

        # Verify
        assert result == sample_ladder

        # Should create upload record
        repository.table.put_item.assert_called_once()
        upload_call_args = repository.table.put_item.call_args[1]
        upload_item = upload_call_args["Item"]
        assert upload_item["invasion"] == "#upload#brightwood-20240301"
        assert upload_item["id"] == "test.png"

        # Should save ladder
        repository.table.batch_writer.assert_called_once()
        assert mock_batch.put_item.call_count == 2

    def test_repository_logging(self, repository, sample_ladder_rank):
        """Test that repository operations are logged."""
        # Setup
        repository.table.put_item = Mock()

        # Execute
        repository.save_rank(sample_ladder_rank)

        # Verify logging calls were made
        assert repository.logger.info.called
        # Should log the operation
        log_calls = [call[0][0] for call in repository.logger.info.call_args_list]
        assert any("save_rank" in call for call in log_calls)

    def test_timestamp_creation(self, repository, sample_ladder_rank):
        """Test that timestamps are created for audit trails."""
        # Setup
        repository.table.put_item = Mock()

        # Execute
        repository.save_rank(sample_ladder_rank)

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
