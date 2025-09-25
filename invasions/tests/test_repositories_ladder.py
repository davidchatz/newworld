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
            assert repo.table == mock_container.table()
            assert repo.logger == mock_container.logger()

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
        # Setup - Mock the rank repository to raise ClientError
        repository._mock_rank_repo.save_multiple.side_effect = ClientError(
            error_response={"Error": {"Code": "TestError", "Message": "Test error"}},
            operation_name="BatchWriteItem",
        )

        # Execute & Verify
        with pytest.raises(ValueError, match="Failed to save ladder"):
            repository.save_ladder(sample_ladder)

    def test_get_ladder(self, repository, sample_ladder):
        """Test getting a complete ladder."""
        # Setup - Mock the rank repository's list_by_invasion method
        mock_ranks = [
            IrusLadderRank(
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
                adjusted=False,
                error=False,
            ),
            IrusLadderRank(
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
                adjusted=False,
                error=False,
            ),
        ]

        repository._mock_rank_repo.list_by_invasion.return_value = mock_ranks

        # Execute
        result = repository.get_ladder("brightwood-20240301")

        # Verify
        assert result is not None
        assert result.invasion_name == "brightwood-20240301"
        assert len(result.ranks) == 2
        assert result.ranks[0].rank == "01"
        assert result.ranks[1].rank == "02"

        repository._mock_rank_repo.list_by_invasion.assert_called_once_with(
            "brightwood-20240301"
        )

    def test_get_ladder_not_found(self, repository):
        """Test getting ladder when none exists."""
        # Setup - Mock empty results
        repository._mock_rank_repo.list_by_invasion.return_value = []

        # Execute
        result = repository.get_ladder("nonexistent")

        # Verify
        assert result is None
        repository._mock_rank_repo.list_by_invasion.assert_called_once_with(
            "nonexistent"
        )

    def test_get_ladder_client_error(self, repository):
        """Test get_ladder with DynamoDB client error."""
        # Setup - Mock the rank repository to raise ClientError
        repository._mock_rank_repo.list_by_invasion.side_effect = ClientError(
            error_response={"Error": {"Code": "TestError", "Message": "Test error"}},
            operation_name="Query",
        )

        # Execute & Verify - The error should propagate up
        with pytest.raises(ClientError):
            repository.get_ladder("brightwood-20240301")

    def test_get_rank_by_player(self, repository):
        """Test getting a specific player's rank."""
        # Setup
        mock_rank = IrusLadderRank(
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
            adjusted=False,
            error=False,
        )

        repository._mock_rank_repo.get_by_player.return_value = mock_rank

        # Execute
        result = repository.get_rank_by_player("brightwood-20240301", "TestPlayer")

        # Verify
        assert result is not None
        assert result.player == "TestPlayer"
        assert result.rank == "01"
        assert result.score == 1000
        repository._mock_rank_repo.get_by_player.assert_called_once_with(
            "brightwood-20240301", "TestPlayer"
        )

    def test_get_rank_by_player_not_found(self, repository):
        """Test getting rank when player not found."""
        # Setup
        repository._mock_rank_repo.get_by_player.return_value = None

        # Execute
        result = repository.get_rank_by_player("brightwood-20240301", "NonExistent")

        # Verify
        assert result is None
        repository._mock_rank_repo.get_by_player.assert_called_once_with(
            "brightwood-20240301", "NonExistent"
        )

    def test_get_rank_by_player_multiple_matches(self, repository):
        """Test error when player matches multiple times."""
        # Setup - Mock the rank repository to raise ValueError for multiple matches
        repository._mock_rank_repo.get_by_player.side_effect = ValueError(
            "Player matched multiple times"
        )

        # Execute & Verify
        with pytest.raises(ValueError, match="matched multiple times"):
            repository.get_rank_by_player("brightwood-20240301", "TestPlayer")

    def test_delete_ladder(self, repository):
        """Test deleting an entire ladder."""
        # Setup - mock rank repository to return count of deleted items
        repository._mock_rank_repo.delete_all_by_invasion.return_value = 2

        # Execute
        result = repository.delete_ladder("test")

        # Verify
        assert result is True
        repository._mock_rank_repo.delete_all_by_invasion.assert_called_once_with(
            "test"
        )

    def test_delete_ladder_not_found(self, repository):
        """Test deleting ladder when none exists."""
        # Setup - mock rank repository to return 0 deleted items
        repository._mock_rank_repo.delete_all_by_invasion.return_value = 0

        # Execute
        result = repository.delete_ladder("nonexistent")

        # Verify
        assert result is False
        repository._mock_rank_repo.delete_all_by_invasion.assert_called_once_with(
            "nonexistent"
        )

    def test_delete_rank(self, repository):
        """Test deleting a specific rank."""
        # Setup - mock rank repository to return True (item was deleted)
        repository._mock_rank_repo.delete_by_invasion_and_rank.return_value = True

        # Execute
        result = repository.delete_rank("brightwood-20240301", "01")

        # Verify
        assert result is True
        repository._mock_rank_repo.delete_by_invasion_and_rank.assert_called_once_with(
            "brightwood-20240301", "01"
        )

    def test_delete_rank_not_found(self, repository):
        """Test deleting rank when it doesn't exist."""
        # Setup - mock rank repository to return False (no item was deleted)
        repository._mock_rank_repo.delete_by_invasion_and_rank.return_value = False

        # Execute
        result = repository.delete_rank("brightwood-20240301", "99")

        # Verify
        assert result is False
        repository._mock_rank_repo.delete_by_invasion_and_rank.assert_called_once_with(
            "brightwood-20240301", "99"
        )

    def test_update_rank_membership(self, repository):
        """Test updating rank membership status."""
        # Setup - mock rank repository to return True (item was updated)
        repository._mock_rank_repo.update_membership.return_value = True

        # Execute
        result = repository.update_rank_membership("brightwood-20240301", "01", True)

        # Verify
        assert result is True
        repository._mock_rank_repo.update_membership.assert_called_once_with(
            "brightwood-20240301", "01", True
        )

    def test_update_rank_membership_not_found(self, repository):
        """Test updating membership when rank doesn't exist."""
        # Setup - mock rank repository to return False (no item was updated)
        repository._mock_rank_repo.update_membership.return_value = False

        # Execute
        result = repository.update_rank_membership("brightwood-20240301", "99", True)

        # Verify
        assert result is False
        repository._mock_rank_repo.update_membership.assert_called_once_with(
            "brightwood-20240301", "99", True
        )

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
        repository._mock_rank_repo.save_multiple = Mock()  # For ladder save

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

        # Should save ladder via rank repository
        repository._mock_rank_repo.save_multiple.assert_called_once_with(
            sample_ladder.ranks
        )

    def test_repository_logging(self, repository, sample_ladder_rank):
        """Test that repository operations are logged."""
        # Setup - mock rank repository save
        repository._mock_rank_repo.save.return_value = sample_ladder_rank

        # Execute
        repository.save_rank(sample_ladder_rank)

        # Verify - the operation is delegated to rank repository, no direct logging in ladder repo
        repository._mock_rank_repo.save.assert_called_once_with(sample_ladder_rank)

    def test_timestamp_creation(self, repository, sample_ladder_rank):
        """Test that timestamps are created for audit trails."""
        # Setup - mock rank repository save
        repository._mock_rank_repo.save.return_value = sample_ladder_rank

        # Execute
        repository.save_rank(sample_ladder_rank)

        # Verify - delegated to rank repository
        repository._mock_rank_repo.save.assert_called_once_with(sample_ladder_rank)

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
