"""Tests for IrusLadderRank facade backward compatibility."""

import warnings
from unittest.mock import Mock, patch

import pytest
from irus.ladderrank import IrusLadderRank
from pydantic import ValidationError


class TestIrusLadderRankFacade:
    """Test suite for IrusLadderRank facade."""

    @pytest.fixture
    def mock_invasion(self):
        """Mock invasion object."""
        invasion = Mock()
        invasion.name = "brightwood-20240301"
        return invasion

    @pytest.fixture
    def sample_item(self):
        """Sample item dictionary."""
        return {
            "rank": "01",
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

    def test_deprecation_warning(self):
        """Test that importing the module issues a deprecation warning."""
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")

            # Re-import to trigger warning
            import importlib

            import irus.ladderrank

            importlib.reload(irus.ladderrank)

            # Should have issued a deprecation warning
            assert len(w) > 0
            assert any(
                issubclass(warning.category, DeprecationWarning) for warning in w
            )
            assert any("deprecated" in str(warning.message) for warning in w)

    def test_basic_creation(self, mock_invasion, sample_item):
        """Test basic facade creation."""
        rank = IrusLadderRank(mock_invasion, sample_item)

        assert rank.rank == "01"
        assert rank.player == "TestPlayer"
        assert rank.score == 1000
        assert rank.kills == 10
        assert rank.deaths == 2
        assert rank.assists == 5
        assert rank.heals == 20
        assert rank.damage == 15000
        assert rank.member is True
        assert rank.ladder is True
        assert rank.adjusted is False
        assert rank.error is False
        assert rank.invasion == mock_invasion

    def test_property_setters(self, mock_invasion, sample_item):
        """Test that properties can be set."""
        rank = IrusLadderRank(mock_invasion, sample_item)

        # Test setting various properties
        rank.rank = "05"
        assert rank.rank == "05"

        rank.player = "NewPlayer"
        assert rank.player == "NewPlayer"

        rank.score = 2000
        assert rank.score == 2000

        rank.member = False
        assert rank.member is False

        rank.adjusted = True
        assert rank.adjusted is True

    def test_rank_formatting(self, mock_invasion, sample_item):
        """Test rank formatting in setter."""
        rank = IrusLadderRank(mock_invasion, sample_item)

        # Setting numeric string should format to 2 digits
        rank.rank = "5"
        assert rank.rank == "05"

        # Setting non-numeric should raise validation error due to strict model validation
        with pytest.raises(ValidationError):
            rank.rank = "XX"

    def test_invasion_key(self, mock_invasion, sample_item):
        """Test invasion key generation."""
        rank = IrusLadderRank(mock_invasion, sample_item)
        assert rank.invasion_key() == "#ladder#brightwood-20240301"

    def test_item_method(self, mock_invasion, sample_item):
        """Test item() method returns proper DynamoDB format."""
        rank = IrusLadderRank(mock_invasion, sample_item)
        item = rank.item()

        expected_keys = {
            "invasion",
            "id",
            "member",
            "player",
            "score",
            "kills",
            "deaths",
            "assists",
            "heals",
            "damage",
            "ladder",
            "adjusted",
            "error",
        }
        assert set(item.keys()) == expected_keys
        assert item["invasion"] == "#ladder#brightwood-20240301"
        assert item["id"] == "01"
        assert item["player"] == "TestPlayer"

    def test_dict_method(self, mock_invasion, sample_item):
        """Test __dict__() method."""
        rank = IrusLadderRank(mock_invasion, sample_item)
        dict_result = rank.__dict__()

        # Should be the same as item()
        assert dict_result == rank.item()

    def test_from_roster_classmethod(self, mock_invasion):
        """Test from_roster class method."""
        rank = IrusLadderRank.from_roster(mock_invasion, 5, "TestPlayer")

        assert rank.rank == "05"
        assert rank.player == "TestPlayer"
        assert rank.score == 0
        assert rank.member is True  # Roster entries are members
        assert rank.ladder is False  # Not from ladder screenshot
        assert rank.adjusted is False
        assert rank.error is False

    @patch("irus.repositories.ladder.LadderRepository")
    @pytest.mark.skip(
        reason="Complex AWS mocking for deprecated facade - will be removed"
    )
    def test_from_invasion_for_member(self, mock_repo_class, mock_invasion):
        """Test from_invasion_for_member class method."""
        # Setup mock repository
        mock_repo = Mock()
        mock_repo_class.return_value = mock_repo

        mock_rank = Mock()
        mock_rank.to_dict.return_value = {
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
        mock_repo.get_rank_by_player.return_value = mock_rank

        # Create mock member
        mock_member = Mock()
        mock_member.player = "TestPlayer"

        # Execute
        rank = IrusLadderRank.from_invasion_for_member(mock_invasion, mock_member)

        # Verify
        mock_repo.get_rank_by_player.assert_called_once_with(
            "brightwood-20240301", "TestPlayer"
        )
        assert rank.player == "TestPlayer"
        assert rank.rank == "01"

    @patch("irus.repositories.ladder.LadderRepository")
    @pytest.mark.skip(
        reason="Complex AWS mocking for deprecated facade - will be removed"
    )
    def test_from_invasion_for_member_not_found(self, mock_repo_class, mock_invasion):
        """Test from_invasion_for_member when player not found."""
        # Setup mock repository
        mock_repo = Mock()
        mock_repo_class.return_value = mock_repo
        mock_repo.get_rank_by_player.return_value = None

        mock_member = Mock()
        mock_member.player = "NonExistent"

        # Execute & Verify
        with pytest.raises(ValueError, match="not found in invasion"):
            IrusLadderRank.from_invasion_for_member(mock_invasion, mock_member)

    def test_string_methods(self, mock_invasion, sample_item):
        """Test string formatting methods."""
        rank = IrusLadderRank(mock_invasion, sample_item)

        # Test __str__
        str_output = str(rank)
        assert "01" in str_output
        assert "TestPlayer" in str_output
        assert "1000" in str_output

        # Test post method
        post_output = rank.post()
        assert "01" in post_output
        assert "TestPlayer" in post_output
        assert "1000" in post_output

        # Test str method (markdown format)
        markdown_output = rank.str()
        assert "**`" in markdown_output
        assert "TestPlayer" in markdown_output
        assert "*Member*:" in markdown_output

    def test_static_methods(self):
        """Test static header and footer methods."""
        header = IrusLadderRank.header()
        footer = IrusLadderRank.footer()

        assert "Rank" in header
        assert "Player" in header
        assert "*Member*:" in footer
        assert "*Ladder*:" in footer

    @patch("irus.repositories.ladder.LadderRepository")
    @pytest.mark.skip(
        reason="Complex AWS mocking for deprecated facade - will be removed"
    )
    def test_update_membership(self, mock_repo_class, mock_invasion, sample_item):
        """Test update_membership method."""
        # Setup mock repository
        mock_repo = Mock()
        mock_repo_class.return_value = mock_repo

        rank = IrusLadderRank(mock_invasion, sample_item)

        # Execute
        rank.update_membership(False)

        # Verify
        assert rank.member is False
        mock_repo.update_rank_membership.assert_called_once_with(
            "brightwood-20240301", "01", False
        )

    @patch("irus.repositories.ladder.LadderRepository")
    @pytest.mark.skip(
        reason="Complex AWS mocking for deprecated facade - will be removed"
    )
    def test_update_item(self, mock_repo_class, mock_invasion, sample_item):
        """Test update_item method."""
        # Setup mock repository
        mock_repo = Mock()
        mock_repo_class.return_value = mock_repo

        rank = IrusLadderRank(mock_invasion, sample_item)

        # Execute
        rank.update_item()

        # Verify
        mock_repo.save_rank.assert_called_once()

    @patch("irus.repositories.ladder.LadderRepository")
    @pytest.mark.skip(
        reason="Complex AWS mocking for deprecated facade - will be removed"
    )
    def test_delete_item(self, mock_repo_class, mock_invasion, sample_item):
        """Test delete_item method."""
        # Setup mock repository
        mock_repo = Mock()
        mock_repo_class.return_value = mock_repo

        rank = IrusLadderRank(mock_invasion, sample_item)

        # Execute
        rank.delete_item()

        # Verify
        mock_repo.delete_rank.assert_called_once_with("brightwood-20240301", "01")

    def test_creation_with_missing_fields(self, mock_invasion):
        """Test creation with minimal item data."""
        minimal_item = {
            "rank": "05",
            "player": "MinimalPlayer",
        }

        rank = IrusLadderRank(mock_invasion, minimal_item)

        assert rank.rank == "05"
        assert rank.player == "MinimalPlayer"
        assert rank.score == 0  # Should use defaults
        assert rank.kills == 0
        assert rank.member is False

    def test_invasion_name_extraction(self):
        """Test invasion name extraction from different invasion objects."""
        # Test with object that has .name attribute
        invasion_with_name = Mock()
        invasion_with_name.name = "test-invasion"

        rank = IrusLadderRank(invasion_with_name, {"rank": "01", "player": "Test"})
        assert rank._model.invasion_name == "test-invasion"

        # Test with string invasion
        rank2 = IrusLadderRank("string-invasion", {"rank": "01", "player": "Test"})
        assert rank2._model.invasion_name == "string-invasion"

    def test_backward_compatibility_properties(self, mock_invasion, sample_item):
        """Test that all original properties are accessible."""
        rank = IrusLadderRank(mock_invasion, sample_item)

        # All these should work without errors (backward compatibility)
        assert hasattr(rank, "rank")
        assert hasattr(rank, "player")
        assert hasattr(rank, "score")
        assert hasattr(rank, "kills")
        assert hasattr(rank, "deaths")
        assert hasattr(rank, "assists")
        assert hasattr(rank, "heals")
        assert hasattr(rank, "damage")
        assert hasattr(rank, "member")
        assert hasattr(rank, "ladder")
        assert hasattr(rank, "adjusted")
        assert hasattr(rank, "error")
        assert hasattr(rank, "invasion")

    def test_numeric_field_conversion(self, mock_invasion):
        """Test that numeric fields are properly converted."""
        item = {
            "rank": "01",
            "player": "TestPlayer",
            "score": "1000",  # String instead of int
            "kills": "10",
            "deaths": "2",
        }

        rank = IrusLadderRank(mock_invasion, item)

        # Should convert to integers
        assert rank.score == 1000
        assert rank.kills == 10
        assert rank.deaths == 2
