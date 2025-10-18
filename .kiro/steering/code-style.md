# New World Discord Bot - Code Style Guide

## 🔴 CRITICAL - Always Follow

### Architecture Patterns
- **Separation of Concerns**: Models handle data validation, repositories handle data access, services handle business logic
- **Dependency Injection**: Use IrusContainer pattern for testable, mockable dependencies
- **Pure Functions**: Separate data transformation from I/O operations where possible
- **Explicit is Better**: Prefer explicit dependency injection over global state

### Pydantic Model Structure
```python
from pydantic import BaseModel, Field, field_validator

class IrusMember(BaseModel):
    """Pure data model for clan members with comprehensive validation."""
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

    def to_dict(self) -> dict:
        """Convert to DynamoDB-compatible dictionary."""
        return {
            "invasion": "#member",
            "id": self.player,
            **self.model_dump()
        }
```

### Repository Pattern
```python
from .base import BaseRepository

class MemberRepository(BaseRepository[IrusMember]):
    """Repository for member CRUD operations and queries."""

    def __init__(self, container: Optional[IrusContainer] = None):
        """Initialize repository with dependency injection."""
        super().__init__(container=container)

    def save(self, member: IrusMember) -> IrusMember:
        """Save member to database with proper error handling."""
        self._log_operation("save", f"member {member.player}")

        try:
            item = member.to_dict()
            self.table.put_item(Item=item)
            return member
        except ClientError as e:
            error_msg = f"Failed to save member {member.player}: {e}"
            self.logger.error(error_msg)
            raise ValueError(error_msg) from e
```

### Container Environment Methods
```python
# Use these standardized methods for different environments
container = IrusContainer.create_unit()        # Unit tests with mocked dependencies
container = IrusContainer.create_integration(aws_resources, stack_name)  # Integration tests with real AWS
container = IrusContainer.create_production()  # Production with real AWS from env vars
```

---

## 🟡 IMPORTANT - Usually Follow

### Naming Conventions

#### Classes
```python
class IrusMember:          # Domain models
class MemberRepository:    # Repositories
class DiscordMessagingService:  # Services
class TestMemberRepository:     # Test classes
```

#### Functions and Methods
```python
def get_by_name(self, name: str) -> Member | None:
def create_from_user_input(self, day: int, month: int) -> Invasion:
def _log_operation(self, operation: str, details: str) -> None:  # Private methods
```

#### Variables and Constants
```python
# Variables - snake_case
member_count = 10
invasion_date = 20240301
container = IrusContainer.default()

# Constants - SCREAMING_SNAKE_CASE
DEFAULT_TIMEOUT = 300
MAX_INVASION_NAME_LENGTH = 50
VALID_SETTLEMENTS = {"bw", "ef", "ww", "md", "rw", "ck", "fl", "mb", "es", "wf", "ct"}
```

### Service Layer Pattern
```python
class MemberManagementService:
    """Service for member-related business operations."""

    def __init__(self, container: Optional[IrusContainer] = None):
        """Initialize service with dependency injection."""
        self._container = container or IrusContainer.default()
        self._logger = self._container.logger()
        self._member_repo = MemberRepository(self._container)

    @classmethod
    def create_with_defaults(cls) -> "MemberManagementService":
        """Factory method for common service configuration."""
        return cls()
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
        self.logger.info(f"Successfully saved member {member.player}")
        return result

    except ClientError as e:
        # Convert AWS errors to domain errors with context
        error_msg = f"Failed to save member {member.player}: {e}"
        self.logger.error(error_msg)
        raise RepositoryError(error_msg) from e
```

### Type Hints
```python
# Always include type hints for parameters and return values
def get_members_by_faction(self, faction: str) -> List[IrusMember]:
    """Get all members belonging to specified faction."""
    pass

# Python 3.10+ syntax (preferred when available)
def find_member(self, identifier: str | int) -> IrusMember | None:
    pass
```

### Import Conventions
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

---

## 🟢 REFERENCE - When Relevant

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

### Module Size Guidelines
- **Models**: 50-150 lines per model class
- **Repositories**: 100-300 lines (one entity per file)
- **Services**: 100-500 lines (related operations grouped)
- **Split when**: File exceeds 500 lines or has multiple unrelated responsibilities

### Model Design Principles
- **Pure Data Objects**: Models contain no business logic, only validation
- **Comprehensive Validation**: Use Pydantic validators for all constraints
- **Type Safety**: Full type hints for all fields
- **Documentation**: Clear docstrings explaining purpose and usage
- **Serialization**: Provide explicit `to_dict()` methods for external formats

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

### Tools & Linting Configuration

#### Ruff Configuration
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
```

#### MyPy Configuration
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
```

### Modern Python Practices
- Use Python 3.12+ features and type hints throughout
- Prefer Pydantic for data validation over manual validation
- Use `pathlib` over string path manipulation
- Leverage dataclasses and Pydantic models over dictionaries for structured data

### File Organization Principles
- **Single Responsibility**: Each file should have one clear purpose
- **Logical Grouping**: Related functionality lives together
- **Import Hierarchy**: Lower-level modules don't import from higher levels
- **Clean Exports**: Use `__init__.py` to control public API
