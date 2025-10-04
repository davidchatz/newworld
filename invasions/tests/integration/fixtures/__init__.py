"""Test fixture loader utility for integration tests.

This module provides utilities for loading test data from JSON fixtures,
enabling consistent test data management and regression testing.

Example:
    >>> from tests.integration.fixtures import FixtureLoader
    >>> member = FixtureLoader.load(IrusMember, "test_player1")
    >>> ladder = FixtureLoader.load(IrusLadder, "99990301-bw")
"""

import json
from pathlib import Path
from typing import TypeVar

from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)


class FixtureLoader:
    """Utility for loading and saving test fixtures from JSON files.

    This class provides a centralized way to manage test fixtures, supporting
    both loading fixtures for tests and saving production data for regression
    testing.

    Directory Structure:
        tests/integration/fixtures/
        ├── member/          # IrusMember fixtures
        ├── ladder/          # IrusLadder fixtures
        ├── invasion/        # IrusInvasion fixtures
        └── month/           # IrusMonth fixtures

    The loader automatically maps model classes to subdirectories based on
    the class name (e.g., IrusMember -> member/).
    """

    FIXTURES_DIR = Path(__file__).parent

    @classmethod
    def load(cls, model_class: type[T], fixture_name: str) -> T:
        """Load a Pydantic model from a JSON fixture file.

        Args:
            model_class: The Pydantic model class to instantiate
            fixture_name: Name of the fixture file (without .json extension)

        Returns:
            Instance of model_class populated from the fixture

        Raises:
            FileNotFoundError: If the fixture file doesn't exist
            ValidationError: If the JSON doesn't match the model schema

        Example:
            >>> member = FixtureLoader.load(IrusMember, "test_player1")
            >>> assert member.player == "TestPlayer1"
        """
        subdir = cls._get_subdir(model_class)
        filepath = cls.FIXTURES_DIR / subdir / f"{fixture_name}.json"

        if not filepath.exists():
            raise FileNotFoundError(
                f"Fixture not found: {filepath}\n"
                f"Expected location: {filepath.relative_to(cls.FIXTURES_DIR.parent)}"
            )

        return model_class.model_validate_json(filepath.read_text())

    @classmethod
    def load_list(cls, model_class: type[T], fixture_name: str) -> list[T]:
        """Load a list of models from a JSON array fixture.

        Useful for loading multiple items like a ladder ranks list.

        Args:
            model_class: The Pydantic model class for list items
            fixture_name: Name of the fixture file (without .json extension)

        Returns:
            List of model instances

        Example:
            >>> ranks = FixtureLoader.load_list(IrusLadderRank, "99990301-bw-ranks")
            >>> assert len(ranks) == 50
        """
        subdir = cls._get_subdir(model_class)
        filepath = cls.FIXTURES_DIR / subdir / f"{fixture_name}.json"

        if not filepath.exists():
            raise FileNotFoundError(f"Fixture not found: {filepath}")

        data = json.loads(filepath.read_text())
        if not isinstance(data, list):
            raise ValueError(f"Expected JSON array in {filepath}, got {type(data)}")

        return [model_class.model_validate(item) for item in data]

    @classmethod
    def save(cls, model: BaseModel, fixture_name: str) -> Path:
        """Save a model instance to a JSON fixture file.

        Useful for creating regression test fixtures from production data.

        Args:
            model: The Pydantic model instance to save
            fixture_name: Name for the fixture file (without .json extension)

        Returns:
            Path to the saved fixture file

        Example:
            >>> # Capture production state for regression testing
            >>> month = IrusMonth.from_invasion_stats(3, 2024)
            >>> path = FixtureLoader.save(month, "202403-regression")
        """
        subdir = cls._get_subdir(model.__class__)
        filepath = cls.FIXTURES_DIR / subdir / f"{fixture_name}.json"
        filepath.parent.mkdir(parents=True, exist_ok=True)

        # Use Pydantic's JSON export with pretty printing
        filepath.write_text(model.model_dump_json(indent=2))
        return filepath

    @classmethod
    def save_list(cls, models: list[BaseModel], fixture_name: str, subdir: str) -> Path:
        """Save a list of models to a JSON array fixture.

        Args:
            models: List of Pydantic model instances
            fixture_name: Name for the fixture file (without .json extension)
            subdir: Subdirectory name (since we can't infer from list)

        Returns:
            Path to the saved fixture file

        Example:
            >>> ranks = ladder.ranks
            >>> path = FixtureLoader.save_list(ranks, "99990301-bw-ranks", "ladderrank")
        """
        filepath = cls.FIXTURES_DIR / subdir / f"{fixture_name}.json"
        filepath.parent.mkdir(parents=True, exist_ok=True)

        # Export list as JSON array
        data = [model.model_dump() for model in models]
        filepath.write_text(json.dumps(data, indent=2, default=str))
        return filepath

    @classmethod
    def _get_subdir(cls, model_class: type[BaseModel]) -> str:
        """Map model class name to fixture subdirectory.

        Args:
            model_class: The model class

        Returns:
            Subdirectory name for this model type

        Example:
            IrusMember -> "member"
            IrusLadder -> "ladder"
            IrusInvasion -> "invasion"
        """
        class_name = model_class.__name__
        # Remove "Irus" prefix and convert to lowercase
        subdir = class_name.replace("Irus", "").lower()
        return subdir

    @classmethod
    def list_fixtures(cls, subdir: str) -> list[str]:
        """List all available fixtures in a subdirectory.

        Args:
            subdir: Subdirectory name (e.g., "member", "ladder")

        Returns:
            List of fixture names (without .json extension)

        Example:
            >>> fixtures = FixtureLoader.list_fixtures("member")
            >>> print(fixtures)
            ['test_player1', 'test_player2', 'new_mid_month']
        """
        fixture_dir = cls.FIXTURES_DIR / subdir
        if not fixture_dir.exists():
            return []

        return [f.stem for f in fixture_dir.glob("*.json")]
