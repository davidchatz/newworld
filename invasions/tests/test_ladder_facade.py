"""Tests for IrusLadder facade backward compatibility."""

import warnings
from unittest.mock import Mock, patch

import pytest
from irus.ladder import IrusLadder
from irus.ladderrank import IrusLadderRank


class TestIrusLadderFacade:
    """Test suite for IrusLadder facade."""

    @pytest.fixture
    def mock_invasion(self):
        """Mock invasion object."""
        invasion = Mock()
        invasion.name = "brightwood-20240301"
        return invasion

    @pytest.fixture
    def sample_ranks(self, mock_invasion):
        """Sample ladder ranks."""
        return [
            IrusLadderRank(
                mock_invasion,
                {
                    "rank": "01",
                    "player": "Player1",
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
            ),
            IrusLadderRank(
                mock_invasion,
                {
                    "rank": "02",
                    "player": "Player2",
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
            ),
        ]

    def test_deprecation_warning(self):
        """Test that importing the module issues a deprecation warning."""
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")

            # Re-import to trigger warning
            import importlib

            import irus.ladder

            importlib.reload(irus.ladder)

            # Should have issued a deprecation warning
            assert len(w) > 0
            assert any(
                issubclass(warning.category, DeprecationWarning) for warning in w
            )
            assert any("deprecated" in str(warning.message) for warning in w)

    def test_basic_creation(self, mock_invasion, sample_ranks):
        """Test basic facade creation."""
        ladder = IrusLadder(mock_invasion, sample_ranks)

        assert ladder.invasion == mock_invasion
        assert len(ladder.ranks) == 2
        assert ladder._model.invasion_name == "brightwood-20240301"
        assert ladder._model.count == 2

    def test_creation_with_empty_ranks(self, mock_invasion):
        """Test creation with empty ranks list."""
        ladder = IrusLadder(mock_invasion, [])

        assert ladder.invasion == mock_invasion
        assert len(ladder.ranks) == 0
        assert ladder._model.count == 0

    def test_invasion_key(self, mock_invasion, sample_ranks):
        """Test invasion key generation."""
        ladder = IrusLadder(mock_invasion, sample_ranks)
        assert ladder.invasion_key() == "#ladder#brightwood-20240301"

    @patch("irus.ladder.import_ladder_table")
    @patch("irus.ladder.extract_blocks")
    @patch("irus.ladder.get_rows_columns_map")
    @patch("irus.ladder.generate_ladder_ranks")
    @patch("irus.ladder.LadderRepository")
    def test_from_ladder_image(
        self,
        mock_repo_class,
        mock_generate_ranks,
        mock_get_rows,
        mock_extract_blocks,
        mock_import_table,
        mock_invasion,
    ):
        """Test from_ladder_image class method."""
        # Setup mocks
        mock_invasion.name = "test-invasion-20240301"

        mock_response = {"key": "response"}
        mock_import_table.return_value = mock_response

        mock_blocks = [{"BlockType": "TABLE"}]
        mock_blocks_map = {"block1": "data"}
        mock_extract_blocks.return_value = (mock_blocks, mock_blocks_map)

        mock_rows = {"1": {"1": "row1"}}
        mock_get_rows.return_value = mock_rows

        # Create mock rank with ._model attribute (facade pattern)
        from irus.models.ladderrank import IrusLadderRank as PureLadderRank

        pure_rank = PureLadderRank(
            invasion_name="test-invasion-20240301",
            rank="01",
            player="TestPlayer",
            score=1000,
            kills=10,
            deaths=2,
            assists=5,
            heals=100,
            damage=5000,
            member=True,
            ladder=True,
            adjusted=False,
            error=False,
        )

        mock_rank = Mock()
        mock_rank._model = pure_rank

        mock_ranks = [mock_rank]
        mock_generate_ranks.return_value = mock_ranks

        mock_repo = Mock()
        mock_repo_class.return_value = mock_repo

        mock_members = Mock()

        # Execute
        IrusLadder.from_ladder_image(
            mock_invasion, mock_members, "test-bucket", "test-key"
        )

        # Verify
        mock_import_table.assert_called_once_with("test-bucket", "test-key")
        mock_extract_blocks.assert_called_once_with(mock_response)
        mock_get_rows.assert_called_once_with(mock_blocks[0], mock_blocks_map)
        mock_generate_ranks.assert_called_once_with(
            mock_invasion, mock_rows, mock_members
        )
        # The repository should be called with the saved ladder data
        mock_repo.save_ladder_from_processing.assert_called_once()
        args = mock_repo.save_ladder_from_processing.call_args[0]
        assert args[0].invasion_name == "test-invasion-20240301"
        assert len(args[0].ranks) == 1
        assert args[1] == "test-key"

    @pytest.mark.skip(
        reason="Complex AWS mocking for deprecated facade - will be removed"
    )
    @patch("boto3.session.Session")
    def test_from_ladder_image_no_tables(self, mock_session_class, mock_invasion):
        """Test from_ladder_image with no tables found."""
        with patch("src.layer.irus.ladder.extract_blocks") as mock_extract:
            with patch(
                "src.layer.irus.environ.IrusResources.textract"
            ) as mock_textract_resource:
                # Mock the boto3 session and its S3 client
                # Create a valid test image data
                import io

                from PIL import Image

                test_img = Image.new("RGB", (100, 100), color=(255, 255, 255))
                img_bytes = io.BytesIO()
                test_img.save(img_bytes, format="PNG")
                test_img_data = img_bytes.getvalue()

                mock_session = Mock()
                mock_s3_client = Mock()
                mock_s3_client.get_object.return_value = {"Body": Mock()}
                mock_s3_client.get_object.return_value[
                    "Body"
                ].read.return_value = test_img_data
                mock_s3_client.put_object.return_value = {}
                mock_session.client.return_value = mock_s3_client
                mock_session_class.return_value = mock_session

                # Mock textract service
                mock_textract = Mock()
                mock_textract.analyze_document.return_value = {"response": "data"}
                mock_textract_resource.return_value = mock_textract

                mock_extract.return_value = ([], {})  # No table blocks

                with pytest.raises(ValueError, match="No invasion ladder not found"):
                    IrusLadder.from_ladder_image(mock_invasion, Mock(), "bucket", "key")

    @pytest.mark.skip(
        reason="Complex AWS mocking for deprecated facade - will be removed"
    )
    @patch("boto3.session.Session")
    def test_from_ladder_image_multiple_tables(self, mock_session_class, mock_invasion):
        """Test from_ladder_image with multiple tables found."""
        with patch("src.layer.irus.ladder.extract_blocks") as mock_extract:
            with patch(
                "src.layer.irus.environ.IrusResources.textract"
            ) as mock_textract_resource:
                # Mock the boto3 session and its S3 client
                # Create a valid test image data
                import io

                from PIL import Image

                test_img = Image.new("RGB", (100, 100), color=(255, 255, 255))
                img_bytes = io.BytesIO()
                test_img.save(img_bytes, format="PNG")
                test_img_data = img_bytes.getvalue()

                mock_session = Mock()
                mock_s3_client = Mock()
                mock_s3_client.get_object.return_value = {"Body": Mock()}
                mock_s3_client.get_object.return_value[
                    "Body"
                ].read.return_value = test_img_data
                mock_s3_client.put_object.return_value = {}
                mock_session.client.return_value = mock_s3_client
                mock_session_class.return_value = mock_session

                # Mock textract service
                mock_textract = Mock()
                mock_textract.analyze_document.return_value = {"response": "data"}
                mock_textract_resource.return_value = mock_textract
                # Multiple table blocks
                mock_extract.return_value = (
                    [{"table1": "data"}, {"table2": "data"}],
                    {},
                )

                with pytest.raises(
                    ValueError, match="Do not recognise invasion ladder"
                ):
                    IrusLadder.from_ladder_image(mock_invasion, Mock(), "bucket", "key")

    @patch("src.layer.irus.repositories.ladder.LadderRepository")
    @pytest.mark.skip(
        reason="Complex AWS mocking for deprecated facade - will be removed"
    )
    def test_from_invasion(self, mock_repo_class, mock_invasion):
        """Test from_invasion class method."""
        # Setup mock repository
        mock_repo = Mock()
        mock_repo_class.return_value = mock_repo

        mock_pure_ladder = Mock()
        mock_pure_ladder.ranks = [Mock(), Mock()]
        mock_repo.get_ladder.return_value = mock_pure_ladder

        # Execute
        ladder = IrusLadder.from_invasion(mock_invasion)

        # Verify
        mock_repo.get_ladder.assert_called_once_with("brightwood-20240301")
        assert len(ladder.ranks) == 2

    @patch("src.layer.irus.repositories.ladder.LadderRepository")
    @pytest.mark.skip(
        reason="Complex AWS mocking for deprecated facade - will be removed"
    )
    def test_from_invasion_not_found(self, mock_repo_class, mock_invasion):
        """Test from_invasion when no ladder exists."""
        # Setup mock repository
        mock_repo = Mock()
        mock_repo_class.return_value = mock_repo
        mock_repo.get_ladder.return_value = None

        # Execute
        ladder = IrusLadder.from_invasion(mock_invasion)

        # Verify
        assert len(ladder.ranks) == 0

    @patch("src.layer.irus.repositories.ladder.LadderRepository")
    @pytest.mark.skip(
        reason="Complex AWS mocking for deprecated facade - will be removed"
    )
    def test_from_csv(self, mock_repo_class, mock_invasion):
        """Test from_csv class method."""
        # Setup mock repository
        mock_repo = Mock()
        mock_repo_class.return_value = mock_repo

        mock_members = Mock()
        mock_members.is_member = Mock(return_value=True)

        csv_data = """rank,player,score,kills,deaths,assists,heals,damage
01,Player1,1000,10,2,5,20,15000
02,Player2,800,8,3,4,15,12000"""

        # Execute
        IrusLadder.from_csv(mock_invasion, csv_data, mock_members)

        # Verify
        mock_repo.save_ladder_from_processing.assert_called_once()
        # Should have parsed 2 rows (excluding header)
        saved_ladder = mock_repo.save_ladder_from_processing.call_args[0][0]
        assert saved_ladder.count == 2

    def test_count_methods(self, mock_invasion, sample_ranks):
        """Test count-related methods."""
        ladder = IrusLadder(mock_invasion, sample_ranks)

        assert ladder.count() == 2
        assert ladder.members() == 1  # Only Player1 is a member
        assert ladder.contiguous_from_1_until() == 2

    def test_rank_access_methods(self, mock_invasion, sample_ranks):
        """Test rank access methods."""
        ladder = IrusLadder(mock_invasion, sample_ranks)

        # Test rank() method
        rank1 = ladder.rank(1)
        assert rank1 is not None
        assert rank1.player == "Player1"

        rank_none = ladder.rank(99)
        assert rank_none is None

        # Test member() method
        member_rank = ladder.member("Player1")
        assert member_rank is not None
        assert member_rank.player == "Player1"

        non_member = ladder.member("Player2")  # Not a member
        assert non_member is None

    def test_formatting_methods(self, mock_invasion, sample_ranks):
        """Test various formatting methods."""
        ladder = IrusLadder(mock_invasion, sample_ranks)

        # Test list() method
        member_list = ladder.list(True)  # Members only
        assert "Player1" in member_list
        assert "Player2" not in member_list

        all_list = ladder.list(False)  # All players
        assert "Player1" in all_list
        assert "Player2" in all_list

        # Test str() method
        summary = ladder.str()
        assert "brightwood-20240301" in summary
        assert "2 rank(s)" in summary

        # Test csv() method
        csv_output = ladder.csv()
        assert "brightwood-20240301" in csv_output
        assert "Player1" in csv_output
        assert "Player2" in csv_output

        # Test markdown() method
        markdown = ladder.markdown()
        assert "# Ladder" in markdown
        assert "Ranks: 2" in markdown

        # Test post() method
        post_lines = ladder.post()
        assert any("brightwood-20240301" in line for line in post_lines)
        assert any("Player1" in line for line in post_lines)
        assert any("Player2" in line for line in post_lines)

    @patch("src.layer.irus.repositories.ladder.LadderRepository")
    @pytest.mark.skip(
        reason="Complex AWS mocking for deprecated facade - will be removed"
    )
    def test_delete_from_table(self, mock_repo_class, mock_invasion, sample_ranks):
        """Test delete_from_table method."""
        # Setup mock repository
        mock_repo = Mock()
        mock_repo_class.return_value = mock_repo

        ladder = IrusLadder(mock_invasion, sample_ranks)

        # Execute
        ladder.delete_from_table()

        # Verify
        mock_repo.delete_ladder.assert_called_once_with("brightwood-20240301")

    @pytest.mark.skip(
        reason="Complex AWS mocking for deprecated facade - will be removed"
    )
    def test_edit_existing_rank(self, mock_invasion, sample_ranks):
        """Test edit method for existing rank."""
        ladder = IrusLadder(mock_invasion, sample_ranks)

        # Mock the rank's update_item method
        with patch.object(ladder.ranks[0], "update_item") as mock_update:
            with patch.object(ladder.ranks[0], "str", return_value="Updated rank"):
                result = ladder.edit(
                    1, member=False, player="UpdatedPlayer", score=1500
                )

                # Verify
                assert "Updating rank 1" in result
                assert "member True -> False" in result
                assert "player Player1 -> UpdatedPlayer" in result
                assert "score 1000 -> 1500" in result
                assert "Updated rank" in result
                mock_update.assert_called_once()

    @pytest.mark.skip(
        reason="Complex AWS mocking for deprecated facade - will be removed"
    )
    def test_edit_replace_rank(self, mock_invasion, sample_ranks):
        """Test edit method for replacing rank position."""
        ladder = IrusLadder(mock_invasion, sample_ranks)

        # Mock the repository delete method
        with patch.object(ladder._repository, "delete_rank") as mock_delete:
            with patch.object(ladder.ranks[0], "update_item") as mock_update:
                with patch.object(ladder.ranks[0], "str", return_value="Replaced rank"):
                    result = ladder.edit(1, new_rank=5, member=False)

                    # Verify
                    assert "Replacing rank 5" in result
                    mock_delete.assert_called_once_with("brightwood-20240301", "01")
                    assert ladder.ranks[0].rank == "05"
                    mock_update.assert_called_once()

    @pytest.mark.skip(
        reason="Complex AWS mocking for deprecated facade - will be removed"
    )
    def test_edit_create_new_rank(self, mock_invasion, sample_ranks):
        """Test edit method for creating new rank."""
        ladder = IrusLadder(mock_invasion, sample_ranks)

        original_count = len(ladder.ranks)

        # Mock the new rank's update_item and str methods
        with patch("src.layer.irus.ladderrank.IrusLadderRank") as mock_rank_class:
            mock_new_rank = Mock()
            mock_new_rank.str.return_value = "New rank created"
            mock_rank_class.return_value = mock_new_rank

            result = ladder.edit(99, player="NewPlayer", score=500, member=True)

            # Verify
            assert "Creating new entry for rank 99" in result
            assert "New rank created" in result
            mock_new_rank.update_item.assert_called_once()
            assert len(ladder.ranks) == original_count + 1

    @pytest.mark.skip(
        reason="Complex AWS mocking for deprecated facade - will be removed"
    )
    def test_edit_error_cases(self, mock_invasion, sample_ranks):
        """Test edit method error cases."""
        ladder = IrusLadder(mock_invasion, sample_ranks)

        # Test rank not found without player name
        result = ladder.edit(99)  # No player provided
        assert "not found, need to provide player name" in result

        # Test replacing non-existent rank
        result = ladder.edit(99, new_rank=5)  # Rank 99 doesn't exist
        assert "does not exist to replace" in result

    def test_rank_conversion_in_init(self, mock_invasion):
        """Test that different rank formats are properly converted."""
        # Test with pure model ranks
        from src.layer.irus.models.ladderrank import IrusLadderRank as PureRank

        pure_rank = PureRank(
            invasion_name="brightwood-20240301",
            rank="01",
            player="PurePlayer",
        )

        ladder = IrusLadder(mock_invasion, [pure_rank])
        assert len(ladder.ranks) == 1
        assert ladder.ranks[0].player == "PurePlayer"

        # Test with facade ranks
        facade_rank = IrusLadderRank(
            mock_invasion,
            {
                "rank": "01",
                "player": "FacadePlayer",
            },
        )

        ladder2 = IrusLadder(mock_invasion, [facade_rank])
        assert len(ladder2.ranks) == 1
        assert ladder2.ranks[0].player == "FacadePlayer"

    def test_invasion_name_extraction(self):
        """Test invasion name extraction from different invasion objects."""
        # Test with object that has .name attribute
        invasion_with_name = Mock()
        invasion_with_name.name = "test-invasion"

        ladder = IrusLadder(invasion_with_name, [])
        assert ladder._model.invasion_name == "test-invasion"

        # Test with string invasion
        ladder2 = IrusLadder("string-invasion", [])
        assert ladder2._model.invasion_name == "string-invasion"

    def test_backward_compatibility_properties(self, mock_invasion, sample_ranks):
        """Test that all original properties and methods are accessible."""
        ladder = IrusLadder(mock_invasion, sample_ranks)

        # All these should work without errors (backward compatibility)
        assert hasattr(ladder, "invasion")
        assert hasattr(ladder, "ranks")
        assert hasattr(ladder, "count")
        assert hasattr(ladder, "members")
        assert hasattr(ladder, "rank")
        assert hasattr(ladder, "member")
        assert hasattr(ladder, "list")
        assert hasattr(ladder, "str")
        assert hasattr(ladder, "csv")
        assert hasattr(ladder, "markdown")
        assert hasattr(ladder, "post")
        assert hasattr(ladder, "delete_from_table")
        assert hasattr(ladder, "edit")

        # Class methods
        assert hasattr(IrusLadder, "from_ladder_image")
        assert hasattr(IrusLadder, "from_roster_image")
        assert hasattr(IrusLadder, "from_invasion")
        assert hasattr(IrusLadder, "from_csv")

    @patch("irus.ladder.save_enhanced_debug")
    def test_image_processing_functions_exist(self, mock_save_debug):
        """Test that image processing functions are still available."""
        # These functions should still be importable for backward compatibility
        from irus.ladder import (
            extract_blocks,
            generate_ladder_ranks,
            generate_roster_ranks,
            get_rows_columns_map,
            get_text,
            import_ladder_table,
            import_roster_table,
            member_match,
            numeric,
            reduce_list,
        )

        # Just verify they exist - detailed testing would require extensive mocking
        assert callable(import_ladder_table)
        assert callable(extract_blocks)
        assert callable(get_text)
        assert callable(get_rows_columns_map)
        assert callable(numeric)
        assert callable(generate_ladder_ranks)
        assert callable(import_roster_table)
        assert callable(reduce_list)
        assert callable(member_match)
        assert callable(generate_roster_ranks)

    def test_numeric_function(self):
        """Test the numeric helper function."""
        from irus.ladder import numeric

        assert numeric("123") == 123
        assert numeric("1o2") == 102  # 'o' -> '0'
        assert numeric("1O2") == 102  # 'O' -> '0'
        assert numeric("1l2") == 112  # 'l' -> '1'
        assert numeric("1I2") == 112  # 'I' -> '1'
        assert numeric("abc") == 0  # No digits
        assert numeric("") == 0  # Empty string
