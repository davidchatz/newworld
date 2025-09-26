# Testing Style Guide

## Overview

This guide documents testing patterns, conventions, and best practices for the New World Discord Bot project. It covers unit testing, integration testing, and test infrastructure patterns established during the Code Quality Foundation project.

## Table of Contents

1. [Testing Principles](#testing-principles)
2. [Unit Testing Patterns](#unit-testing-patterns)
3. [Integration Testing Patterns](#integration-testing-patterns)
4. [Test Organization](#test-organization)
5. [Container Testing Patterns](#container-testing-patterns)
6. [Fixture Patterns](#fixture-patterns)
7. [Error Testing](#error-testing)

## Testing Principles

### Core Testing Guidelines
- **Arrange-Act-Assert**: Clear test structure for readability
- **Fixture Usage**: Leverage pytest fixtures for setup and teardown
- **Mock Isolation**: Mock external dependencies, test internal logic
- **Parametrized Tests**: Use `@pytest.mark.parametrize` for multiple inputs
- **Descriptive Names**: Test method names clearly describe what is being tested
- **Error Testing**: Test both success and failure scenarios

### Test Categories
- **Unit Tests**: Test individual classes/methods in isolation with mocked dependencies
- **Integration Tests**: Test with real AWS resources using year 9999 test data
- **Service Tests**: Test business logic orchestration between repositories

## Unit Testing Patterns

### Test File Organization
```python
# tests/test_repositories_member.py
"""Tests for MemberRepository class."""

import pytest
from unittest.mock import Mock, patch
from botocore.exceptions import ClientError

from irus.container import IrusContainer
from irus.models.member import IrusMember
from irus.repositories.member import MemberRepository

class TestMemberRepository:
    """Test suite for MemberRepository class."""

    @pytest.fixture
    def container(self):
        """Create test container with mocked dependencies."""
        return IrusContainer.create_unit()

    @pytest.fixture
    def repository(self, container):
        """Create repository instance with test container."""
        return MemberRepository(container)

    @pytest.fixture
    def sample_member(self):
        """Create sample member for testing."""
        return IrusMember(
            player="TestPlayer",
            faction="yellow",
            start=20240101,
            salary=True
        )
```

### Test Method Patterns
```python
def test_save_success(self, repository, sample_member, container):
    """Test successful member save operation."""
    # Arrange
    mock_table = container.table()
    mock_table.put_item.return_value = {}

    # Act
    result = repository.save(sample_member)

    # Assert
    assert result == sample_member
    mock_table.put_item.assert_called_once()
    call_args = mock_table.put_item.call_args[1]['Item']
    assert call_args['id'] == 'TestPlayer'
    assert call_args['invasion'] == '#member'

def test_save_client_error(self, repository, sample_member, container):
    """Test save operation with DynamoDB client error."""
    # Arrange
    mock_table = container.table()
    error = ClientError(
        error_response={'Error': {'Code': 'ValidationException', 'Message': 'Test error'}},
        operation_name='PutItem'
    )
    mock_table.put_item.side_effect = error

    # Act & Assert
    with pytest.raises(ValueError, match="Failed to save member TestPlayer"):
        repository.save(sample_member)

@pytest.mark.parametrize("player,faction,expected_valid", [
    ("ValidPlayer", "yellow", True),
    ("ValidPlayer", "purple", True),
    ("ValidPlayer", "green", True),
    ("ValidPlayer", "invalid", False),
    ("", "yellow", False),
])
def test_member_validation(self, player, faction, expected_valid):
    """Test member validation with various inputs."""
    if expected_valid:
        member = IrusMember(player=player, faction=faction, start=20240101)
        assert member.player == player
        assert member.faction == faction
    else:
        with pytest.raises(ValueError):
            IrusMember(player=player, faction=faction, start=20240101)
```

### Service Testing with Repository Mocks
```python
@patch('irus.services.member_management.MemberRepository')
def test_service_with_repository_mock(self, mock_repo_class, container):
    """Test service that uses repository with proper mocking."""
    # Arrange
    mock_repo = Mock()
    mock_repo.get_by_player.return_value = sample_member
    mock_repo_class.return_value = mock_repo

    service = MemberManagementService(container)

    # Act
    result = service.some_operation("TestPlayer")

    # Assert
    mock_repo.get_by_player.assert_called_once_with("TestPlayer")
    assert result is not None
```

## Integration Testing Patterns

### Container Setup
```python
# Use config-driven container setup
@pytest.fixture(scope="session")
def integration_container(integration_config, aws_resources):
    """Container configured for integration testing with real AWS resources."""
    container = IrusContainer.create_integration(aws_resources, integration_config["stack_name"])

    # Configure session with discovered profile and region
    container._session = boto3.session.Session(
        profile_name=integration_config["aws_profile"],
        region_name=integration_config["aws_region"],
    )

    return container
```

### Test Date Pattern: Unique Test Dates

Integration tests use a **unique date pattern** for isolated test data that ensures:
- **Uniqueness**: Each test run gets a different date down to the minute
- **Isolation**: Test dates are clearly distinguishable from production data
- **Cleanup**: Easy to identify and remove all test records
- **Maintainability**: Algorithm can change without breaking tests

The specific date format is encapsulated in the helper functions - tests should not depend on the exact pattern.

### Date Helper Functions

```python
# Use these helper functions from conftest.py for consistent date handling

def generate_test_date():
    """Generate unique test date using configurable test pattern."""
    # Returns tuple: (year, month, day)

def get_test_date_components():
    """Get test date components for consistent use across tests."""
    # Returns dict with 'year', 'month', 'day', 'date_string', 'date_int'

def is_test_date(date_value):
    """Check if a date value uses our test date pattern."""
    # Returns True if date matches the configured test pattern
```

### Test Data Fixtures

```python
@pytest.fixture
def test_member_data():
    """Generate unique test member data using 99DDHHMM pattern."""
    timestamp = int(time.time())
    date_components = get_test_date_components()

    return {
        "player": f"TestPlayer-{timestamp}",
        "day": date_components["day"],
        "month": date_components["month"],
        "year": date_components["year"],
        "faction": "yellow",
        "admin": False,
        "salary": True,
        "discord": None,
        "notes": "Integration test member"
    }

@pytest.fixture
def test_member_expectations(test_member_data):
    """Helper fixture providing expected values for member tests."""
    date_components = get_test_date_components()
    return {
        "expected_start_date": date_components["date_int"]
    }

@pytest.fixture
def test_invasion_data():
    """Generate unique test invasion data using 99DDHHMM pattern."""
    timestamp = int(time.time())
    date_components = get_test_date_components()

    return {
        "day": date_components["day"],
        "month": date_components["month"],
        "year": date_components["year"],
        "settlement": "ef",
        "win": True,
        "notes": f"Integration test invasion {timestamp}"
    }
```

### Using Test Date Helpers

```python
def test_member_date_validation(self, repository, test_member_data, test_member_expectations):
    """Test member creation with proper date validation."""
    # Act - Create member
    created_member = repository.create_from_user_input(**test_member_data)

    # Assert - Verify date was constructed correctly using helper
    assert created_member.start == test_member_expectations["expected_start_date"]

    # Assert - Verify it uses our test date pattern
    assert is_test_date(created_member.start)

def test_invasion_isolation(self, repository, test_invasion_data):
    """Test that test invasions are isolated from production queries."""
    # Act - Create test invasion
    invasion = repository.create_from_user_input(**test_invasion_data)

    # Assert - Should not appear in production date ranges
    production_invasions = repository.get_by_date_range(20240101, 20241231)
    production_names = [inv.name for inv in production_invasions]
    assert invasion.name not in production_names

    # Assert - Uses test date pattern (helper encapsulates the actual pattern)
    assert is_test_date(invasion.year)
```

### Graceful Conflict Handling
```python
# Handle rare data conflicts gracefully
def test_create_member(self, repository, test_member_data):
    """Test member creation with graceful conflict handling."""
    try:
        # Act - Create member
        member = repository.create_from_user_input(**test_member_data)

        # Assert - Test member properties
        assert member.player == test_member_data["player"]
        assert member.faction == test_member_data["faction"]

    except ValueError as e:
        if "already exists" in str(e):
            pytest.skip(f"Test data conflict (rare): {e}")
        else:
            raise
```

### Integration Testing Guidelines
- **Use Date Helpers**: Always use `get_test_date_components()`, `is_test_date()` helpers - never hardcode test date patterns
- **Encapsulation**: The specific test date format is encapsulated in helper functions
- **Separate Expectations**: Use separate expectation fixtures to avoid parameter conflicts
- **Config-Driven Safety**: Use stack_name from config for environment validation
- **Graceful Conflicts**: Skip tests on rare data conflicts rather than complex workarounds
- **Legacy Dependencies**: Skip services that use legacy classes until modernized
- **No Hardcoding**: Avoid hardcoded dates - let the helper functions generate them dynamically

### Skipping Legacy Services
```python
@pytest.mark.skip(reason="MemberManagementService uses legacy dependencies - modernize first")
class TestMemberManagementServiceIntegration:
    """Integration tests for member management service business logic."""
    # Tests skipped until service is modernized
```

## Test Organization

### Directory Structure
```
tests/
├── STYLE_GUIDE.md           # This file - testing patterns and practices
├── conftest.py              # Global test configuration and fixtures
├── unit/                    # Unit tests with mocked dependencies
│   ├── test_models/
│   ├── test_repositories/
│   └── test_services/
├── integration/             # Integration tests with real AWS resources
│   ├── conftest.py         # Integration-specific fixtures
│   ├── test_*_integration.py
│   └── README.md
├── legacy/                  # Legacy tests being modernized
└── utilities/               # Test utilities and helpers
```

### Test File Naming
```python
# Unit tests mirror source structure with test_ prefix
test_member_repository.py       # Tests for src/layer/irus/repositories/member.py
test_discord_messaging_service.py  # Tests for src/layer/irus/services/discord_messaging.py

# Integration tests use _integration suffix
test_member_repository_integration.py
test_container_integration.py
```

## Container Testing Patterns

### Container Environment Methods
```python
# Use these standardized methods for different environments
container = IrusContainer.create_unit()        # Unit tests with mocked dependencies (alias for create_test)
container = IrusContainer.create_test()        # Unit tests with specific mocks
container = IrusContainer.create_integration(aws_resources, stack_name)  # Integration tests with real AWS
container = IrusContainer.create_production()  # Production with real AWS from env vars
```

### Container Test Patterns
```python
class TestContainerIntegration:
    """Test container integration with real AWS resources."""

    def test_production_container_creates_real_resources(self, integration_container):
        """Validate container creates working AWS clients."""
        # Test that real AWS resources are accessible
        table = integration_container.table()
        logger = integration_container.logger()

        assert table is not None
        assert logger is not None

    def test_repository_with_real_container(self, integration_container):
        """Test repositories work with production container."""
        repo = MemberRepository(integration_container)

        # Test basic functionality works
        assert repo is not None
        assert repo._container == integration_container
```

## Fixture Patterns

### Session-Scoped Fixtures
```python
@pytest.fixture(scope="session")
def integration_config():
    """Load integration test configuration and set AWS environment."""
    config = load_config()
    env = os.environ.get("TEST_ENV", "dev")

    # Set environment variables from config
    env_config = config["environments"][env]
    os.environ["AWS_PROFILE"] = env_config["aws_profile"]
    os.environ["AWS_DEFAULT_REGION"] = env_config["aws_region"]

    return env_config
```

### Auto-Use Cleanup Fixtures
```python
@pytest.fixture(autouse=True)
def cleanup_test_data(integration_container):
    """Automatically cleanup test data after each test."""
    yield  # Run the test

    # Cleanup happens here after the test
    from tests.utilities.production_data_copier import ProductionDataCopier

    copier = ProductionDataCopier(integration_container)
    copier.cleanup_test_data()
```

## Error Testing

### Exception Testing Patterns
```python
def test_save_client_error(self, repository, sample_member, container):
    """Test save operation with DynamoDB client error."""
    # Arrange
    mock_table = container.table()
    error = ClientError(
        error_response={'Error': {'Code': 'ValidationException', 'Message': 'Test error'}},
        operation_name='PutItem'
    )
    mock_table.put_item.side_effect = error

    # Act & Assert
    with pytest.raises(ValueError, match="Failed to save member TestPlayer"):
        repository.save(sample_member)
```

### Error Handling Guidelines
- **Exception Chaining**: Verify original error context is preserved
- **Domain Exceptions**: Test that technical exceptions are converted to domain-appropriate types
- **Error Messages**: Assert error messages contain sufficient context
- **Input Validation**: Test early validation with clear error messages

---

## Conclusion

Following these testing patterns ensures:

- **Consistency** across all test types
- **Reliability** with proper isolation and cleanup
- **Maintainability** with clear organization and naming
- **Safety** with config-driven environment validation
- **Efficiency** with appropriate use of fixtures and mocking

For questions about these testing guidelines, refer to the main project documentation or the implementation examples throughout the test suite.
