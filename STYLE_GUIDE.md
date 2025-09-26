# New World Discord Bot - Coding Style Guide

## Overview

This style guide documents the coding patterns, conventions, and best practices established during the Code Quality Foundation project. It serves as the definitive reference for maintaining consistency and quality across the codebase.

## Table of Contents

1. [General Principles](#general-principles)
2. [Code Organization](#code-organization)
3. [Naming Conventions](#naming-conventions)
4. [Model Patterns](#model-patterns)
5. [Service Layer Patterns](#service-layer-patterns)
6. [Repository Patterns](#repository-patterns)
7. [Testing Patterns](tests/STYLE_GUIDE.md)
8. [Error Handling](#error-handling)
9. [Import Conventions](#import-conventions)
10. [Type Hints](#type-hints)
11. [Documentation](#documentation)
12. [Tools & Linting](#tools--linting)

## General Principles

### Clean Architecture
- **Separation of Concerns**: Models handle data validation, repositories handle data access, services handle business logic
- **Dependency Injection**: Use container pattern for testable, mockable dependencies
- **Pure Functions**: Separate data transformation from I/O operations where possible
- **Explicit is Better**: Prefer explicit dependency injection over global state

### Modern Python Practices
- Use Python 3.12+ features and type hints throughout
- Prefer Pydantic for data validation over manual validation
- Use `pathlib` over string path manipulation
- Leverage dataclasses and Pydantic models over dictionaries for structured data

## Code Organization

### Directory Structure
```
src/layer/irus/
├── __init__.py              # Public API exports
├── container.py             # Dependency injection container
├── models/                  # Pure Pydantic models
│   ├── __init__.py
│   ├── member.py
│   ├── invasion.py
│   └── ladder.py
├── repositories/            # Data access layer
│   ├── __init__.py
│   ├── base.py
│   ├── member.py
│   └── invasion.py
├── services/                # Business logic services
│   ├── __init__.py
│   ├── discord_messaging.py
│   └── image_processing.py
└── utilities.py             # Pure utility functions
```

### File Organization Principles
- **Single Responsibility**: Each file should have one clear purpose
- **Logical Grouping**: Related functionality lives together
- **Import Hierarchy**: Lower-level modules don't import from higher levels
- **Clean Exports**: Use `__init__.py` to control public API

### Module Size Guidelines
- **Models**: 50-150 lines per model class
- **Repositories**: 100-300 lines (one entity per file)
- **Services**: 100-500 lines (related operations grouped)
- **Split when**: File exceeds 500 lines or has multiple unrelated responsibilities

## Naming Conventions

### Classes
```python
# Use PascalCase for all classes
class IrusMember:          # Domain models
class MemberRepository:    # Repositories
class DiscordMessagingService:  # Services
class TestMemberRepository:     # Test classes
```

### Functions and Methods
```python
# Use snake_case for functions and methods
def get_by_name(self, name: str) -> Member | None:
def create_from_user_input(self, day: int, month: int) -> Invasion:
def _log_operation(self, operation: str, details: str) -> None:  # Private methods
```

### Variables and Parameters
```python
# Use snake_case for variables
member_count = 10
invasion_date = 20240301
container = IrusContainer.default()

# Use descriptive names over abbreviations
invasion_repository = InvasionRepository()  # Good
inv_repo = InvasionRepository()             # Avoid
```

### Constants
```python
# Use SCREAMING_SNAKE_CASE for constants
DEFAULT_TIMEOUT = 300
MAX_INVASION_NAME_LENGTH = 50
VALID_SETTLEMENTS = {"bw", "ef", "ww", "md", "rw", "ck", "fl", "mb", "es", "wf", "ct"}
```

### Files and Directories
```python
# Use snake_case for files and directories
member_repository.py       # Good
memberRepository.py        # Avoid
member-repository.py       # Avoid

# Test files mirror source structure with test_ prefix
test_member_repository.py
test_discord_messaging_service.py
```

## Model Patterns

### Pydantic Model Structure
```python
from decimal import Decimal
from pydantic import BaseModel, Field, field_validator

class IrusMember(BaseModel):
    """Pure data model for clan members with comprehensive validation.

    This model handles member data validation and serialization without
    any external dependencies or side effects.
    """
    # Required fields first
    player: str = Field(min_length=1, max_length=50)
    faction: str
    start: int

    # Optional fields with defaults
    admin: bool = False
    salary: bool = False
    discord: str | None = None
    notes: str | None = None

    @field_validator("faction")
    @classmethod
    def validate_faction(cls, v: str) -> str:
        """Validate faction is one of the allowed values."""
        valid_factions = {"yellow", "purple", "green"}
        if v.lower() not in valid_factions:
            raise ValueError(f"Faction must be one of: {', '.join(valid_factions)}")
        return v.lower()

    @field_validator("start")
    @classmethod
    def validate_start_date(cls, v: int) -> int:
        """Validate start date is in YYYYMMDD format."""
        if not (20200101 <= v <= 20991231):
            raise ValueError("Start date must be in YYYYMMDD format between 2020-2099")
        return v

    def to_dict(self) -> dict:
        """Convert to DynamoDB-compatible dictionary."""
        return {
            "invasion": "#member",
            "id": self.player,
            **self.model_dump()
        }
```

### Model Design Principles
- **Pure Data Objects**: Models contain no business logic, only validation
- **Comprehensive Validation**: Use Pydantic validators for all constraints
- **Type Safety**: Full type hints for all fields
- **Documentation**: Clear docstrings explaining purpose and usage
- **Serialization**: Provide explicit `to_dict()` methods for external formats

## Service Layer Patterns

### Service Class Structure
```python
from typing import Optional
from .container import IrusContainer
from .repositories.member import MemberRepository

class MemberManagementService:
    """Service for member-related business operations.

    Handles complex member workflows that span multiple repositories
    or require business logic validation.
    """

    def __init__(self, container: Optional[IrusContainer] = None):
        """Initialize service with dependency injection.

        Args:
            container: Dependency container, uses default if None
        """
        self._container = container or IrusContainer.default()
        self._logger = self._container.logger()
        self._member_repo = MemberRepository(self._container)

    @classmethod
    def create_with_defaults(cls) -> "MemberManagementService":
        """Factory method for common service configuration."""
        return cls()

    def update_member_ladder_history(self, member: IrusMember) -> str:
        """Update member flag in all ladder entries since join date.

        Args:
            member: Member to update ladder history for

        Returns:
            Status message describing operation result

        Raises:
            ValueError: If member data is invalid
        """
        self._logger.info(f"Updating ladder history for {member.player}")

        try:
            # Business logic implementation here
            result = self._perform_update_operation(member)
            self._logger.info(f"Successfully updated ladder history for {member.player}")
            return result

        except Exception as e:
            self._logger.error(f"Failed to update ladder history for {member.player}: {e}")
            raise ValueError(f"Ladder history update failed: {e}") from e
```

### Service Design Principles
- **Container Injection**: All services accept optional container for dependency injection
- **Factory Methods**: Provide class methods for common configurations
- **Single Responsibility**: Each service handles one domain area
- **Error Handling**: Convert technical exceptions to domain-appropriate errors
- **Logging**: Comprehensive operation logging through container

### Container Environment Methods
```python
# Use these standardized methods for different environments
container = IrusContainer.create_unit()        # Unit tests with mocked dependencies (alias for create_test)
container = IrusContainer.create_test()        # Unit tests with specific mocks
container = IrusContainer.create_integration(aws_resources, stack_name)  # Integration tests with real AWS
container = IrusContainer.create_production()  # Production with real AWS from env vars
```

## Repository Patterns

### Repository Class Structure
```python
from typing import Any, Optional
from ..models.member import IrusMember
from .base import BaseRepository

class MemberRepository(BaseRepository[IrusMember]):
    """Repository for member CRUD operations and queries.

    Handles all database interactions for member data with proper
    error handling and logging.
    """

    def __init__(self, container: Optional[IrusContainer] = None):
        """Initialize repository with dependency injection."""
        super().__init__(container=container)

    def save(self, member: IrusMember) -> IrusMember:
        """Save member to database.

        Args:
            member: Member instance to save

        Returns:
            The saved member instance

        Raises:
            ValueError: If save operation fails
        """
        self._log_operation("save", f"member {member.player}")

        try:
            item = member.to_dict()
            self.table.put_item(Item=item)
            self._log_debug("save", f"Saved {member.player}")
            return member

        except ClientError as e:
            error_msg = f"Failed to save member {member.player}: {e}"
            self.logger.error(error_msg)
            raise ValueError(error_msg) from e

    def get_by_player(self, player: str) -> Optional[IrusMember]:
        """Get member by player name.

        Args:
            player: Player name to search for

        Returns:
            Member if found, None otherwise
        """
        self._log_operation("get_by_player", player)

        key = {"invasion": "#member", "id": player}
        response = self.table.get_item(Key=key)

        if "Item" not in response:
            self._log_operation("get_by_player", f"Member {player} not found")
            return None

        return IrusMember.model_validate(response["Item"])
```

### Repository Design Principles
- **Generic Base**: Inherit from `BaseRepository[ModelType]` for common functionality
- **Pure CRUD**: Focus on data access operations, no business logic
- **Error Translation**: Convert AWS exceptions to domain exceptions with context
- **Operation Logging**: Log all database operations for debugging
- **Type Safety**: Use generic types for proper IDE support

## Testing Patterns

See [tests/STYLE_GUIDE.md](tests/STYLE_GUIDE.md) for comprehensive testing patterns, including:

- **Unit Testing**: Test individual classes with mocked dependencies
- **Integration Testing**: Test with real AWS resources using year 9999 isolation
- **Container Patterns**: Standardized container methods for different environments
- **Fixture Patterns**: Reusable test setup and cleanup
- **Error Testing**: Exception handling and validation patterns

Key testing principles:
- Use `IrusContainer.create_unit()` for unit tests with mocked dependencies
- Use `IrusContainer.create_integration()` for integration tests with real AWS resources
- Use timestamp-based unique identifiers to avoid test data conflicts
- Skip tests gracefully on rare data conflicts rather than complex workarounds

## Error Handling

### Exception Hierarchy
```python
# Custom exceptions for domain-specific errors
class IrusError(Exception):
    """Base exception for all Irus-related errors."""
    pass

class ValidationError(IrusError):
    """Raised when data validation fails."""
    pass

class RepositoryError(IrusError):
    """Raised when database operations fail."""
    pass

class ServiceError(IrusError):
    """Raised when business logic operations fail."""
    pass
```

### Error Handling Patterns
```python
def save_member(self, member: IrusMember) -> IrusMember:
    """Save member with proper error handling and context."""
    try:
        # Validate input
        if not member.player:
            raise ValidationError("Player name is required")

        # Perform operation
        result = self._perform_save_operation(member)

        # Log success
        self.logger.info(f"Successfully saved member {member.player}")
        return result

    except ClientError as e:
        # Convert AWS errors to domain errors with context
        error_msg = f"Failed to save member {member.player}: {e}"
        self.logger.error(error_msg)
        raise RepositoryError(error_msg) from e

    except Exception as e:
        # Handle unexpected errors
        error_msg = f"Unexpected error saving member {member.player}: {e}"
        self.logger.error(error_msg)
        raise ServiceError(error_msg) from e
```

### Error Handling Principles
- **Exception Chaining**: Use `raise ... from e` to preserve original error context
- **Domain Exceptions**: Convert technical exceptions to domain-appropriate types
- **Comprehensive Logging**: Log errors with sufficient context for debugging
- **Input Validation**: Validate inputs early and provide clear error messages
- **Recovery Information**: Include information about how to fix the error when possible

## Import Conventions

### Import Order
```python
# 1. Standard library imports
from decimal import Decimal
from typing import Optional, Dict, List
from datetime import datetime

# 2. Third-party imports
import boto3
from pydantic import BaseModel, Field
from botocore.exceptions import ClientError

# 3. Local application imports
from .container import IrusContainer
from .models.member import IrusMember
from .repositories.base import BaseRepository
```

### Import Style Guidelines
```python
# Prefer specific imports over wildcard imports
from irus.models.member import IrusMember        # Good
from irus.models import *                        # Avoid

# Use absolute imports for clarity
from irus.repositories.member import MemberRepository   # Good
from ..repositories.member import MemberRepository     # Avoid in non-test code

# Group related imports
from irus.models.member import IrusMember
from irus.models.invasion import IrusInvasion
from irus.models.ladder import IrusLadder

# Use aliases for commonly used long names
from irus.repositories.member import MemberRepository as MemberRepo  # When needed
```

### Import Principles
- **Explicit Imports**: Import exactly what you need
- **Logical Grouping**: Group imports by source (stdlib, third-party, local)
- **Avoid Circular Dependencies**: Structure modules to prevent circular imports
- **Consistent Ordering**: Follow PEP 8 import ordering guidelines

## Type Hints

### Function Signatures
```python
from typing import Optional, List, Dict, Any, Union

# Always include type hints for parameters and return values
def get_members_by_faction(self, faction: str) -> List[IrusMember]:
    """Get all members belonging to specified faction."""
    pass

def process_invasion_data(
    self,
    invasion_name: str,
    member_data: Dict[str, Any],
    include_inactive: bool = False
) -> Optional[IrusInvasion]:
    """Process invasion data with explicit parameter types."""
    pass

# Use Union for multiple possible types (Python 3.10+: use | syntax)
def find_member(self, identifier: Union[str, int]) -> Optional[IrusMember]:
    pass

# Python 3.10+ syntax (preferred when available)
def find_member(self, identifier: str | int) -> IrusMember | None:
    pass
```

### Generic Types
```python
from typing import Generic, TypeVar, List

T = TypeVar('T')

class BaseRepository(Generic[T]):
    """Generic repository base class."""

    def get_all(self) -> List[T]:
        """Return all entities of type T."""
        pass

    def save(self, entity: T) -> T:
        """Save entity and return saved instance."""
        pass
```

### Type Hint Principles
- **Complete Coverage**: Add type hints to all function signatures
- **Specificity**: Use the most specific type possible
- **Consistency**: Use consistent patterns across the codebase
- **Documentation**: Type hints serve as inline documentation
- **Modern Syntax**: Use Python 3.10+ union syntax (`|`) when available

## Documentation

### Docstring Format
```python
def create_invasion_from_input(
    self,
    day: int,
    month: int,
    year: int,
    settlement: str,
    win: bool,
    notes: Optional[str] = None
) -> IrusInvasion:
    """Create a new invasion from user input with validation.

    This method handles the complete workflow of creating an invasion
    including validation, conflict checking, and database persistence.

    Args:
        day: Day of the month (1-31)
        month: Month of the year (1-12)
        year: Year (e.g., 2024)
        settlement: Settlement code (e.g., 'bw', 'ef')
        win: True if invasion was won, False if lost
        notes: Optional additional notes about the invasion

    Returns:
        Newly created and saved IrusInvasion instance

    Raises:
        ValueError: If input validation fails or invasion already exists
        RepositoryError: If database operation fails

    Example:
        >>> invasion = repo.create_invasion_from_input(
        ...     day=15, month=3, year=2024,
        ...     settlement='bw', win=True
        ... )
        >>> invasion.name
        '20240315-bw'
    """
```

### Class Documentation
```python
class MemberRepository(BaseRepository[IrusMember]):
    """Repository for member CRUD operations and business queries.

    This repository handles all database interactions for member data,
    providing a clean abstraction over DynamoDB operations with proper
    error handling and logging.

    The repository follows the established patterns:
    - Uses dependency injection via IrusContainer
    - Converts technical exceptions to domain exceptions
    - Provides comprehensive operation logging
    - Maintains type safety with generic base class

    Examples:
        Basic usage with default container:
        >>> repo = MemberRepository()
        >>> member = repo.get_by_player("PlayerName")

        Usage with custom container (for testing):
        >>> test_container = IrusContainer.create_test()
        >>> repo = MemberRepository(test_container)
    """
```

### Documentation Principles
- **Purpose First**: Start with what the function/class does
- **Comprehensive Args**: Document all parameters with types and constraints
- **Return Values**: Clearly describe what is returned
- **Exceptions**: List all exceptions that may be raised
- **Examples**: Provide usage examples for complex operations
- **Context**: Explain how the component fits into the larger system

## Tools & Linting

### Pre-commit Hooks Configuration
The project uses pre-commit hooks for code quality enforcement:

```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.4.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-toml
      - id: check-json
      - id: check-merge-conflict
      - id: debug-statements
      - id: check-docstring-first

  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.1.6
    hooks:
      - id: ruff
        args: [--fix, --exit-non-zero-on-fix]
      - id: ruff-format

  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.8.0
    hooks:
      - id: mypy
        additional_dependencies: [types-requests]
```

### Ruff Configuration
```toml
# pyproject.toml
[tool.ruff]
target-version = "py312"
line-length = 88
extend-exclude = ["tests/legacy"]

[tool.ruff.lint]
select = [
    "E",    # pycodestyle errors
    "W",    # pycodestyle warnings
    "F",    # pyflakes
    "I",    # isort
    "N",    # pep8-naming
    "UP",   # pyupgrade
    "B",    # flake8-bugbear
    "C4",   # flake8-comprehensions
    "SIM",  # flake8-simplify
]

ignore = [
    "E501",  # line too long (handled by formatter)
    "B008",  # do not perform function calls in argument defaults
]

[tool.ruff.lint.per-file-ignores]
"tests/*" = ["N802", "N803"]  # Allow uppercase in test names

[tool.ruff.format]
quote-style = "double"
indent-style = "space"
```

### MyPy Configuration
```toml
[tool.mypy]
python_version = "3.12"
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true
disallow_incomplete_defs = true
check_untyped_defs = true
disallow_untyped_decorators = true
no_implicit_optional = true
warn_redundant_casts = true
warn_unused_ignores = true
warn_no_return = true

[[tool.mypy.overrides]]
module = "tests.*"
disallow_untyped_defs = false
```

### Testing Configuration
```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
filterwarnings = [
    "ignore::DeprecationWarning",
    "ignore::PendingDeprecationWarning",
]
addopts = [
    "--cov=src",
    "--cov-report=html",
    "--cov-report=term-missing",
    "--cov-fail-under=70",
]
```

### Tool Integration Principles
- **Automation**: Use pre-commit hooks to enforce standards automatically
- **Consistency**: Configure tools to work together harmoniously
- **Flexibility**: Allow overrides for special cases (tests, legacy code)
- **Feedback**: Provide clear error messages and suggestions
- **CI Integration**: Ensure tools run in CI/CD pipeline

---

## Conclusion

This style guide represents the culmination of patterns established during the Code Quality Foundation project. Following these guidelines ensures:

- **Consistency** across the codebase
- **Maintainability** for future development
- **Testability** with proper separation of concerns
- **Type Safety** with comprehensive type hints
- **Documentation** that serves both developers and users

When in doubt, refer to existing modernized code in the `src/layer/irus/models/`, `src/layer/irus/repositories/`, and `src/layer/irus/services/` directories as exemplars of these patterns.

For questions or clarifications about these guidelines, refer to the project documentation in `projects/03-code-quality-foundation.md` or the implementation examples throughout the codebase.
