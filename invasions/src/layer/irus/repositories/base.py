"""Base repository class with common DynamoDB patterns."""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, TypeVar

# Type variable for model types
ModelType = TypeVar("ModelType")


class BaseRepository[ModelType](ABC):
    """Abstract base repository for DynamoDB operations.

    Provides common patterns and dependency injection support for testing.
    """

    def __init__(self, container=None):
        """Initialize repository with optional dependency container.

        Args:
            container: IrusContainer instance (None = use default)
        """
        self._container = container

    @property
    def container(self):
        """Get dependency container."""
        if self._container is None:
            from ..container import IrusContainer

            self._container = IrusContainer.default()
        return self._container

    @property
    def table(self):
        """Get DynamoDB table."""
        return self.container.table()

    @property
    def logger(self):
        """Get logger."""
        return self.container.logger()

    @abstractmethod
    def save(self, model: ModelType) -> ModelType:
        """Save a model to the database.

        Args:
            model: Model instance to save

        Returns:
            The saved model instance
        """
        pass

    @abstractmethod
    def get(self, key: dict[str, Any]) -> ModelType | None:
        """Get a model by its key.

        Args:
            key: DynamoDB key dictionary

        Returns:
            Model instance if found, None otherwise
        """
        pass

    @abstractmethod
    def delete(self, key: dict[str, Any]) -> bool:
        """Delete a model by its key.

        Args:
            key: DynamoDB key dictionary

        Returns:
            True if item was deleted, False if not found
        """
        pass

    def _log_operation(self, operation: str, details: str):
        """Log repository operation."""
        self.logger.info(f"{self.__class__.__name__}.{operation}: {details}")

    def _log_debug(self, operation: str, details: Any):
        """Log debug information for repository operation."""
        self.logger.debug(f"{self.__class__.__name__}.{operation}: {details}")

    @staticmethod
    def _create_timestamp() -> str:
        """Create timestamp for audit operations."""
        return datetime.today().strftime("%Y%m%d%H%M%S")
