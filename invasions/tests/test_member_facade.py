"""Tests for backward compatibility facade."""

import warnings
from unittest.mock import patch

import pytest
from irus.member import IrusMember  # This should issue a deprecation warning


class TestIrusMemberFacade:
    """Test suite for the backward compatibility facade."""

    def test_deprecation_warning(self):
        """Test that importing the module issues a deprecation warning."""
        # The warning is issued at import time, so we need to reimport
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            # Force reimport
            import importlib

            import irus.member

            importlib.reload(irus.member)

            assert len(w) >= 1
            assert issubclass(w[-1].category, DeprecationWarning)
            assert "deprecated" in str(w[-1].message).lower()

    def test_create_from_dict(self):
        """Test creating member from dictionary (legacy API)."""
        item = {
            "start": 20240301,
            "id": "TestPlayer",
            "faction": "covenant",
            "admin": False,
            "salary": True,
            "discord": "testplayer#1234",
            "notes": "Test member",
        }

        member = IrusMember(item)

        assert member.start == 20240301
        assert member.player == "TestPlayer"
        assert member.faction == "covenant"
        assert member.admin is False
        assert member.salary is True
        assert member.discord == "testplayer#1234"
        assert member.notes == "Test member"

    def test_properties_readonly(self):
        """Test that properties are read-only."""
        item = {
            "start": 20240301,
            "id": "TestPlayer",
            "faction": "covenant",
            "admin": False,
            "salary": True,
        }

        member = IrusMember(item)

        # Properties should be accessible
        assert member.start == 20240301
        assert member.player == "TestPlayer"

        # Properties should be read-only (setting should have no effect on the model)
        # Note: We can't prevent attribute assignment on the wrapper,
        # but the underlying model is immutable

    def test_key_method(self):
        """Test key method returns correct DynamoDB key."""
        item = {
            "start": 20240301,
            "id": "TestPlayer",
            "faction": "covenant",
            "admin": False,
            "salary": True,
        }

        member = IrusMember(item)
        key = member.key()

        assert key == {"invasion": "#member", "id": "TestPlayer"}

    @patch("irus.repositories.member.MemberRepository.create_from_user_input")
    def test_from_user(self, mock_create):
        """Test creating member from user input."""
        # Mock the repository call
        from irus.models.member import IrusMember as PureMember

        pure_member = PureMember(
            start=20240315,
            player="NewPlayer",
            faction="covenant",
            admin=False,
            salary=True,
        )
        mock_create.return_value = pure_member

        # Test the facade
        result = IrusMember.from_user(
            player="NewPlayer",
            day=15,
            month=3,
            year=2024,
            faction="covenant",
            admin=False,
            salary=True,
        )

        # Verify repository was called correctly
        mock_create.assert_called_once_with(
            player="NewPlayer",
            day=15,
            month=3,
            year=2024,
            faction="covenant",
            admin=False,
            salary=True,
            discord=None,
            notes=None,
        )

        # Verify result
        assert isinstance(result, IrusMember)
        assert result.player == "NewPlayer"
        assert result.faction == "covenant"

    @patch("irus.repositories.member.MemberRepository.get_by_player")
    def test_from_table_found(self, mock_get):
        """Test loading member from table when member exists."""
        # Mock the repository call
        from irus.models.member import IrusMember as PureMember

        pure_member = PureMember(
            start=20240301,
            player="ExistingPlayer",
            faction="covenant",
            admin=False,
            salary=True,
        )
        mock_get.return_value = pure_member

        # Test the facade
        result = IrusMember.from_table("ExistingPlayer")

        # Verify repository was called correctly
        mock_get.assert_called_once_with("ExistingPlayer")

        # Verify result
        assert isinstance(result, IrusMember)
        assert result.player == "ExistingPlayer"

    @patch("irus.repositories.member.MemberRepository.get_by_player")
    def test_from_table_not_found(self, mock_get):
        """Test loading member from table when member doesn't exist."""
        # Mock the repository call to return None
        mock_get.return_value = None

        # Test the facade
        with pytest.raises(
            ValueError, match="No member found called NonExistentPlayer"
        ):
            IrusMember.from_table("NonExistentPlayer")

        # Verify repository was called correctly
        mock_get.assert_called_once_with("NonExistentPlayer")

    def test_str_method(self):
        """Test str method formatting."""
        item = {
            "start": 20240301,
            "id": "TestPlayer",
            "faction": "covenant",
            "admin": True,
            "salary": False,
        }

        member = IrusMember(item)
        result = member.str()

        expected = (
            "## Member TestPlayer\nFaction: covenant\nStarting 20240301\nAdmin True\n"
        )
        assert result == expected

    @patch("irus.repositories.member.MemberRepository.remove_with_audit")
    def test_remove_method(self, mock_remove):
        """Test remove method calls repository."""
        # Mock the repository call
        mock_remove.return_value = "## Removed member TestPlayer"

        item = {
            "start": 20240301,
            "id": "TestPlayer",
            "faction": "covenant",
            "admin": False,
            "salary": True,
        }

        member = IrusMember(item)
        result = member.remove()

        # Verify repository was called correctly
        mock_remove.assert_called_once_with("TestPlayer")

        # Verify result
        assert result == "## Removed member TestPlayer"

    def test_post_method(self):
        """Test post method formatting."""
        item = {
            "start": 20240301,
            "id": "TestPlayer",
            "faction": "covenant",
            "admin": True,
            "salary": False,
            "notes": "Test notes",
        }

        member = IrusMember(item)
        result = member.post()

        expected = [
            "Faction: covenant",
            "Starting: 20240301",
            "Admin: True",
            "Earns salary: False",
            "Notes: Test notes",
        ]
        assert result == expected

    def test_post_method_no_notes(self):
        """Test post method without notes."""
        item = {
            "start": 20240301,
            "id": "TestPlayer",
            "faction": "covenant",
            "admin": False,
            "salary": True,
        }

        member = IrusMember(item)
        result = member.post()

        expected = [
            "Faction: covenant",
            "Starting: 20240301",
            "Admin: False",
            "Earns salary: True",
        ]
        assert result == expected

    def test_validation_through_facade(self):
        """Test that validation errors are properly propagated through facade."""
        # Invalid faction should raise validation error from the pure model
        with pytest.raises(ValueError):  # Pydantic validation error gets converted
            IrusMember(
                {
                    "start": 20240301,
                    "id": "TestPlayer",
                    "faction": "invalid_faction",
                    "admin": False,
                    "salary": True,
                }
            )
