"""Tests for the pure IrusMember model."""

import pytest
from irus.models.member import IrusMember
from pydantic import ValidationError


class TestIrusMember:
    """Test suite for IrusMember model."""

    def test_create_valid_member(self):
        """Test creating a valid member."""
        member = IrusMember(
            start=20240301,
            player="TestPlayer",
            faction="covenant",
            admin=False,
            salary=True,
            discord="testplayer#1234",
            notes="Test member",
        )

        assert member.start == 20240301
        assert member.player == "TestPlayer"
        assert member.faction == "covenant"
        assert member.admin is False
        assert member.salary is True
        assert member.discord == "testplayer#1234"
        assert member.notes == "Test member"

    def test_create_minimal_member(self):
        """Test creating member with only required fields."""
        member = IrusMember(start=20240301, player="MinimalPlayer", faction="marauders")

        assert member.start == 20240301
        assert member.player == "MinimalPlayer"
        assert member.faction == "marauders"
        assert member.admin is False  # Default
        assert member.salary is False  # Default
        assert member.discord is None
        assert member.notes is None

    def test_faction_validation_valid(self):
        """Test valid faction values."""
        valid_factions = ["covenant", "marauders", "syndicate"]

        for faction in valid_factions:
            member = IrusMember(
                start=20240301, player=f"Player_{faction}", faction=faction
            )
            assert member.faction == faction.lower()

    def test_faction_validation_case_insensitive(self):
        """Test faction validation is case insensitive."""
        member = IrusMember(start=20240301, player="TestPlayer", faction="COVENANT")
        assert member.faction == "covenant"

    def test_faction_validation_invalid(self):
        """Test invalid faction raises ValueError."""
        with pytest.raises(ValidationError) as exc_info:
            IrusMember(start=20240301, player="TestPlayer", faction="invalid_faction")

        error = exc_info.value.errors()[0]
        assert error["type"] == "value_error"
        error_str = str(error["ctx"])
        # Check that all valid factions are mentioned (order may vary)
        assert "covenant" in error_str
        assert "syndicate" in error_str
        assert "marauders" in error_str

    def test_player_name_validation_empty(self):
        """Test empty player name raises ValueError."""
        with pytest.raises(ValidationError) as exc_info:
            IrusMember(start=20240301, player="   ", faction="covenant")

        error = exc_info.value.errors()[0]
        assert error["type"] == "value_error"
        assert "empty or whitespace" in str(error["ctx"])

    def test_player_name_validation_strips_whitespace(self):
        """Test player name strips whitespace."""
        member = IrusMember(start=20240301, player="  TestPlayer  ", faction="covenant")
        assert member.player == "TestPlayer"

    def test_start_date_validation_valid(self):
        """Test valid start date formats."""
        valid_dates = [
            20240301,  # March 1, 2024
            20231225,  # December 25, 2023
            20240229,  # Leap year Feb 29
        ]

        for date in valid_dates:
            member = IrusMember(start=date, player="TestPlayer", faction="covenant")
            assert member.start == date

    def test_start_date_validation_invalid_format(self):
        """Test invalid date format raises ValueError."""
        invalid_dates = [
            2024301,  # 7 digits
            202403011,  # 9 digits
            20240232,  # Invalid day
            20241301,  # Invalid month
        ]

        for invalid_date in invalid_dates:
            with pytest.raises(ValidationError):
                IrusMember(start=invalid_date, player="TestPlayer", faction="covenant")

    def test_start_date_validation_invalid_date(self):
        """Test invalid calendar date raises ValueError."""
        with pytest.raises(ValidationError):
            IrusMember(
                start=20240230,  # February 30th doesn't exist
                player="TestPlayer",
                faction="covenant",
            )

    def test_field_length_validation(self):
        """Test field length validation."""
        # Player name too long
        with pytest.raises(ValidationError):
            IrusMember(
                start=20240301,
                player="a" * 51,  # Max is 50
                faction="covenant",
            )

        # Discord too long
        with pytest.raises(ValidationError):
            IrusMember(
                start=20240301,
                player="TestPlayer",
                faction="covenant",
                discord="a" * 101,  # Max is 100
            )

        # Notes too long
        with pytest.raises(ValidationError):
            IrusMember(
                start=20240301,
                player="TestPlayer",
                faction="covenant",
                notes="a" * 501,  # Max is 500
            )

    def test_key_method(self):
        """Test key method returns correct DynamoDB key."""
        member = IrusMember(start=20240301, player="TestPlayer", faction="covenant")

        key = member.key()
        assert key == {"invasion": "#member", "id": "TestPlayer"}

    def test_to_dict_complete(self):
        """Test to_dict method with all fields."""
        member = IrusMember(
            start=20240301,
            player="TestPlayer",
            faction="covenant",
            admin=True,
            salary=False,
            discord="testplayer#1234",
            notes="Test notes",
        )

        result = member.to_dict()
        expected = {
            "invasion": "#member",
            "id": "TestPlayer",
            "start": 20240301,
            "faction": "covenant",
            "admin": True,
            "salary": False,
            "discord": "testplayer#1234",
            "notes": "Test notes",
        }
        assert result == expected

    def test_to_dict_minimal(self):
        """Test to_dict method with only required fields."""
        member = IrusMember(start=20240301, player="TestPlayer", faction="covenant")

        result = member.to_dict()
        expected = {
            "invasion": "#member",
            "id": "TestPlayer",
            "start": 20240301,
            "faction": "covenant",
            "admin": False,
            "salary": False,
        }
        assert result == expected

    def test_from_dict_complete(self):
        """Test from_dict method with all fields."""
        item = {
            "start": "20240301",  # String as from DynamoDB
            "id": "TestPlayer",
            "faction": "covenant",
            "admin": True,
            "salary": False,
            "discord": "testplayer#1234",
            "notes": "Test notes",
        }

        member = IrusMember.from_dict(item)
        assert member.start == 20240301  # Converted to int
        assert member.player == "TestPlayer"
        assert member.faction == "covenant"
        assert member.admin is True
        assert member.salary is False
        assert member.discord == "testplayer#1234"
        assert member.notes == "Test notes"

    def test_from_dict_minimal(self):
        """Test from_dict method with only required fields."""
        item = {
            "start": "20240301",
            "id": "TestPlayer",
            "faction": "covenant",
            "admin": False,
            "salary": True,
        }

        member = IrusMember.from_dict(item)
        assert member.start == 20240301
        assert member.player == "TestPlayer"
        assert member.faction == "covenant"
        assert member.admin is False
        assert member.salary is True
        assert member.discord is None
        assert member.notes is None

    def test_create_start_date(self):
        """Test create_start_date static method."""
        result = IrusMember.create_start_date(15, 3, 2024)
        assert result == 20240315

        result = IrusMember.create_start_date(1, 12, 2023)
        assert result == 20231201

    def test_create_start_date_invalid(self):
        """Test create_start_date with invalid date."""
        with pytest.raises(ValueError):
            IrusMember.create_start_date(30, 2, 2024)  # Feb 30 doesn't exist

    def test_str_method(self):
        """Test str method formatting."""
        member = IrusMember(
            start=20240301, player="TestPlayer", faction="covenant", admin=True
        )

        result = member.str()
        expected = (
            "## Member TestPlayer\nFaction: covenant\nStarting 20240301\nAdmin True\n"
        )
        assert result == expected

    def test_post_method_complete(self):
        """Test post method with all fields."""
        member = IrusMember(
            start=20240301,
            player="TestPlayer",
            faction="covenant",
            admin=True,
            salary=False,
            notes="Test notes",
        )

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
        member = IrusMember(start=20240301, player="TestPlayer", faction="covenant")

        result = member.post()
        expected = [
            "Faction: covenant",
            "Starting: 20240301",
            "Admin: False",
            "Earns salary: False",
        ]
        assert result == expected

    def test_model_configuration(self):
        """Test Pydantic model configuration."""
        # Test extra fields are forbidden
        with pytest.raises(ValidationError):
            IrusMember(
                start=20240301,
                player="TestPlayer",
                faction="covenant",
                extra_field="not_allowed",
            )

    def test_validate_assignment(self):
        """Test that assignment validation works."""
        member = IrusMember(start=20240301, player="TestPlayer", faction="covenant")

        # This should work
        member.faction = "marauders"
        assert member.faction == "marauders"

        # This should fail
        with pytest.raises(ValidationError):
            member.faction = "invalid_faction"
