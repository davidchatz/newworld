"""Tests for the pure IrusInvasion model."""

import pytest
from irus.models.invasion import IrusInvasion
from pydantic import ValidationError


class TestIrusInvasion:
    """Test suite for IrusInvasion model."""

    def test_create_valid_invasion(self):
        """Test creating a valid invasion."""
        invasion = IrusInvasion(
            name="20240301-bw",
            settlement="bw",
            win=True,
            date=20240301,
            year=2024,
            month=3,
            day=1,
            notes="Great coordination!",
        )

        assert invasion.name == "20240301-bw"
        assert invasion.settlement == "bw"
        assert invasion.win is True
        assert invasion.date == 20240301
        assert invasion.year == 2024
        assert invasion.month == 3
        assert invasion.day == 1
        assert invasion.notes == "Great coordination!"

    def test_create_minimal_invasion(self):
        """Test creating invasion with only required fields."""
        invasion = IrusInvasion(
            name="20240301-ef",
            settlement="ef",
            win=False,
            date=20240301,
            year=2024,
            month=3,
            day=1,
        )

        assert invasion.name == "20240301-ef"
        assert invasion.settlement == "ef"
        assert invasion.win is False
        assert invasion.notes is None

    def test_settlement_map(self):
        """Test settlement mapping constants."""
        expected_settlements = {
            "bw": "Brightwood",
            "bs": "Brimstone Sands",
            "ck": "Cutlass Keys",
            "er": "Ebonscale Reach",
            "eg": "Edengrove",
            "ef": "Everfall",
            "mb": "Monarchs Bluff",
            "md": "Mourningdale",
            "rw": "Reekwater",
            "rs": "Restless Shore",
            "wf": "Weavers Fen",
            "ww": "Windsward",
        }

        assert IrusInvasion.SETTLEMENT_MAP == expected_settlements

    def test_settlement_validation_valid(self):
        """Test valid settlement codes."""
        valid_settlements = [
            "bw",
            "bs",
            "ck",
            "er",
            "eg",
            "ef",
            "mb",
            "md",
            "rw",
            "rs",
            "wf",
            "ww",
        ]

        for settlement in valid_settlements:
            invasion = IrusInvasion(
                name=f"20240301-{settlement}",
                settlement=settlement,
                win=True,
                date=20240301,
                year=2024,
                month=3,
                day=1,
            )
            assert invasion.settlement == settlement.lower()

    def test_settlement_validation_case_insensitive(self):
        """Test settlement validation is case insensitive."""
        invasion = IrusInvasion(
            name="20240301-BW",
            settlement="BW",
            win=True,
            date=20240301,
            year=2024,
            month=3,
            day=1,
        )
        assert invasion.settlement == "bw"

    def test_settlement_validation_invalid(self):
        """Test invalid settlement raises ValueError."""
        with pytest.raises(ValidationError) as exc_info:
            IrusInvasion(
                name="20240301-invalid",
                settlement="invalid",
                win=True,
                date=20240301,
                year=2024,
                month=3,
                day=1,
            )

        # Check for the validation error - could be value_error or string constraint
        errors = exc_info.value.errors()
        error_messages = [str(e.get("ctx", e)) for e in errors]
        assert any("Unknown settlement" in msg for msg in error_messages)

    def test_date_validation_valid(self):
        """Test valid date formats."""
        valid_dates = [
            (20240301, 2024, 3, 1),  # March 1, 2024
            (20231225, 2023, 12, 25),  # December 25, 2023
            (20240229, 2024, 2, 29),  # Leap year Feb 29
        ]

        for date, year, month, day in valid_dates:
            invasion = IrusInvasion(
                name=f"{date}-bw",
                settlement="bw",
                win=True,
                date=date,
                year=year,
                month=month,
                day=day,
            )
            assert invasion.date == date

    def test_date_validation_invalid_format(self):
        """Test invalid date format raises ValueError."""
        invalid_dates = [
            2024301,  # 7 digits
            202403011,  # 9 digits
        ]

        for invalid_date in invalid_dates:
            with pytest.raises(ValidationError):
                IrusInvasion(
                    name=f"{invalid_date}-bw",
                    settlement="bw",
                    win=True,
                    date=invalid_date,
                    year=2024,
                    month=3,
                    day=1,
                )

    def test_date_validation_invalid_date(self):
        """Test invalid calendar date raises ValueError."""
        with pytest.raises(ValidationError):
            IrusInvasion(
                name="20240230-bw",
                settlement="bw",
                win=True,
                date=20240230,  # February 30th doesn't exist
                year=2024,
                month=2,
                day=30,
            )

    def test_name_validation_valid(self):
        """Test valid name formats."""
        valid_names = ["20240301-bw", "20231225-ef", "20240229-ww"]

        for name in valid_names:
            invasion = IrusInvasion(
                name=name,
                settlement=name.split("-")[1],
                win=True,
                date=int(name.split("-")[0]),
                year=int(name[:4]),
                month=int(name[4:6]),
                day=int(name[6:8]),
            )
            assert invasion.name == name

    def test_name_validation_invalid(self):
        """Test invalid name formats raise ValueError."""
        invalid_names = [
            "20240301_bw",  # underscore instead of dash
            "20240301",  # no settlement
            "2024-03-01-bw",  # wrong date format
            "20240301-bw-extra",  # too many parts
        ]

        for invalid_name in invalid_names:
            with pytest.raises(ValidationError):
                IrusInvasion(
                    name=invalid_name,
                    settlement="bw",
                    win=True,
                    date=20240301,
                    year=2024,
                    month=3,
                    day=1,
                )

    def test_field_constraints(self):
        """Test field constraint validation."""
        # Date range constraints
        with pytest.raises(ValidationError):
            IrusInvasion(
                name="19991231-bw",
                settlement="bw",
                win=True,
                date=19991231,  # Too early
                year=1999,
                month=12,
                day=31,
            )

        # Month constraints
        with pytest.raises(ValidationError):
            IrusInvasion(
                name="20240301-bw",
                settlement="bw",
                win=True,
                date=20240301,
                year=2024,
                month=13,  # Invalid month
                day=1,
            )

        # Day constraints
        with pytest.raises(ValidationError):
            IrusInvasion(
                name="20240301-bw",
                settlement="bw",
                win=True,
                date=20240301,
                year=2024,
                month=3,
                day=32,  # Invalid day
            )

        # Notes length
        with pytest.raises(ValidationError):
            IrusInvasion(
                name="20240301-bw",
                settlement="bw",
                win=True,
                date=20240301,
                year=2024,
                month=3,
                day=1,
                notes="x" * 1001,  # Too long
            )

    def test_computed_field_settlement_name(self):
        """Test computed field for settlement name."""
        invasion = IrusInvasion(
            name="20240301-bw",
            settlement="bw",
            win=True,
            date=20240301,
            year=2024,
            month=3,
            day=1,
        )

        assert invasion.settlement_name == "Brightwood"

    def test_key_method(self):
        """Test key method returns correct DynamoDB key."""
        invasion = IrusInvasion(
            name="20240301-ef",
            settlement="ef",
            win=True,
            date=20240301,
            year=2024,
            month=3,
            day=1,
        )

        key = invasion.key()
        assert key == {"invasion": "#invasion", "id": "20240301-ef"}

    def test_to_dict_complete(self):
        """Test to_dict method with all fields."""
        invasion = IrusInvasion(
            name="20240301-bw",
            settlement="bw",
            win=True,
            date=20240301,
            year=2024,
            month=3,
            day=1,
            notes="Test invasion",
        )

        result = invasion.to_dict()
        expected = {
            "invasion": "#invasion",
            "id": "20240301-bw",
            "settlement": "bw",
            "win": True,
            "date": 20240301,
            "year": 2024,
            "month": 3,
            "day": 1,
            "notes": "Test invasion",
        }
        assert result == expected

    def test_to_dict_minimal(self):
        """Test to_dict method with only required fields."""
        invasion = IrusInvasion(
            name="20240301-ef",
            settlement="ef",
            win=False,
            date=20240301,
            year=2024,
            month=3,
            day=1,
        )

        result = invasion.to_dict()
        expected = {
            "invasion": "#invasion",
            "id": "20240301-ef",
            "settlement": "ef",
            "win": False,
            "date": 20240301,
            "year": 2024,
            "month": 3,
            "day": 1,
        }
        assert result == expected

    def test_from_dict_complete(self):
        """Test from_dict method with all fields."""
        item = {
            "id": "20240301-ww",
            "settlement": "ww",
            "win": True,
            "date": 20240301,
            "year": 2024,
            "month": 3,
            "day": 1,
            "notes": "Test invasion",
        }

        invasion = IrusInvasion.from_dict(item)
        assert invasion.name == "20240301-ww"
        assert invasion.settlement == "ww"
        assert invasion.win is True
        assert invasion.date == 20240301
        assert invasion.year == 2024
        assert invasion.month == 3
        assert invasion.day == 1
        assert invasion.notes == "Test invasion"

    def test_from_dict_minimal(self):
        """Test from_dict method with only required fields."""
        item = {
            "id": "20240301-rs",
            "settlement": "rs",
            "win": False,
            "date": 20240301,
            "year": 2024,
            "month": 3,
            "day": 1,
        }

        invasion = IrusInvasion.from_dict(item)
        assert invasion.name == "20240301-rs"
        assert invasion.settlement == "rs"
        assert invasion.win is False
        assert invasion.notes is None

    def test_create_from_user_input(self):
        """Test create_from_user_input class method."""
        invasion = IrusInvasion.create_from_user_input(
            day=15,
            month=6,
            year=2024,
            settlement="bw",
            win=True,
            notes="User created invasion",
        )

        assert invasion.name == "20240615-bw"
        assert invasion.settlement == "bw"
        assert invasion.win is True
        assert invasion.date == 20240615
        assert invasion.year == 2024
        assert invasion.month == 6
        assert invasion.day == 15
        assert invasion.notes == "User created invasion"

    def test_create_from_user_input_invalid_date(self):
        """Test create_from_user_input with invalid date."""
        with pytest.raises(ValueError):  # datetime validation error
            IrusInvasion.create_from_user_input(
                day=30,
                month=2,  # February 30 doesn't exist
                year=2024,
                settlement="ef",
                win=True,
            )

    def test_str_method(self):
        """Test __str__ method formatting."""
        invasion = IrusInvasion(
            name="20240301-bw",
            settlement="bw",
            win=True,
            date=20240301,
            year=2024,
            month=3,
            day=1,
            notes="Test notes",
        )

        result = str(invasion)
        expected = "20240301-bw, bw, 20240301, True, Test notes"
        assert result == expected

    def test_str_method_no_notes(self):
        """Test __str__ method without notes."""
        invasion = IrusInvasion(
            name="20240301-ef",
            settlement="ef",
            win=False,
            date=20240301,
            year=2024,
            month=3,
            day=1,
        )

        result = str(invasion)
        expected = "20240301-ef, ef, 20240301, False"
        assert result == expected

    def test_markdown_method(self):
        """Test markdown method formatting."""
        invasion = IrusInvasion(
            name="20240301-bw",
            settlement="bw",
            win=True,
            date=20240301,
            year=2024,
            month=3,
            day=1,
            notes="Great teamwork",
        )

        result = invasion.markdown()
        expected = (
            "## Invasion 20240301-bw\n"
            "Settlement: Brightwood\n"
            "Date: 20240301\n"
            "Win: True\n"
            "Notes: Great teamwork\n"
        )
        assert result == expected

    def test_post_method_complete(self):
        """Test post method with all fields."""
        invasion = IrusInvasion(
            name="20240301-ef",
            settlement="ef",
            win=False,
            date=20240301,
            year=2024,
            month=3,
            day=1,
            notes="Close fight",
        )

        result = invasion.post()
        expected = [
            "Invasion: 20240301-ef",
            "Settlement: Everfall",
            "Date: 20240301",
            "Win: False",
            "Notes: Close fight",
        ]
        assert result == expected

    def test_post_method_no_notes(self):
        """Test post method without notes."""
        invasion = IrusInvasion(
            name="20240301-ww",
            settlement="ww",
            win=True,
            date=20240301,
            year=2024,
            month=3,
            day=1,
        )

        result = invasion.post()
        expected = [
            "Invasion: 20240301-ww",
            "Settlement: Windsward",
            "Date: 20240301",
            "Win: True",
        ]
        assert result == expected

    def test_month_prefix(self):
        """Test month_prefix method."""
        invasion = IrusInvasion(
            name="20240301-bw",
            settlement="bw",
            win=True,
            date=20240301,
            year=2024,
            month=3,
            day=1,
        )

        assert invasion.month_prefix() == "202403"

    def test_path_methods(self):
        """Test S3 path methods."""
        invasion = IrusInvasion(
            name="20240301-bw",
            settlement="bw",
            win=True,
            date=20240301,
            year=2024,
            month=3,
            day=1,
        )

        assert invasion.path_ladders() == "ladders/20240301-bw/"
        assert invasion.path_roster() == "roster/20240301-bw/"

    def test_model_configuration(self):
        """Test Pydantic model configuration."""
        # Test extra fields are forbidden
        with pytest.raises(ValidationError):
            IrusInvasion(
                name="20240301-bw",
                settlement="bw",
                win=True,
                date=20240301,
                year=2024,
                month=3,
                day=1,
                extra_field="not_allowed",
            )

    def test_validate_assignment(self):
        """Test that assignment validation works."""
        invasion = IrusInvasion(
            name="20240301-bw",
            settlement="bw",
            win=True,
            date=20240301,
            year=2024,
            month=3,
            day=1,
        )

        # This should work
        invasion.settlement = "ef"
        assert invasion.settlement == "ef"

        # This should fail
        with pytest.raises(ValidationError):
            invasion.settlement = "invalid_settlement"
