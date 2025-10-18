# New World Discord Bot - Testing Strategy

## 🔴 CRITICAL - Always Follow

### MANDATORY: 99DDHHMM Pattern for Test Dates
- **NEVER use hardcoded dates** like "9999" or static test data
- **ALWAYS use `get_test_date_components()`** from conftest.py for ALL dates
- **ALWAYS use `f"TestPlayer-{timestamp}-{uuid4().hex[:8]}"`** for player names
- **NEVER hardcode** names like "TestPlayer1"

### Test Data Generation Pattern
```python
import time
from uuid import uuid4
from tests.integration.conftest import get_test_date_components

# Get unique test date components
date_components = get_test_date_components()
# Returns: {'year': 9915, 'month': 12, 'day': 28, 'date_string': '99151228', 'date_int': 99151228}

# Generate unique player names with timestamp + uuid
timestamp = int(time.time())
unique_id = uuid4().hex[:8]
player_name = f"TestPlayer-{timestamp}-{unique_id}"

# Create invasion with test date pattern
invasion_name = f"{date_components['date_string']}-bw"  # e.g., "99151228-bw"

# Member start date uses test pattern
member_start = date_components['date_int']  # e.g., 99151228
```

### Container Types
- **Unit Tests**: `IrusContainer.create_unit()` - Mocked dependencies
- **Integration Tests**: `IrusContainer.create_integration(aws_resources, stack_name)` - Real AWS dev resources
- **Production**: `IrusContainer.create_production()` - Real AWS from environment variables

### Critical Safety Requirements
- **Read Before Writing**: Always examine existing interfaces and patterns before implementing tests
- **NEVER Hardcode**: NEVER hardcode test data values - always use helper functions and timestamps
- **Use Helper Functions**: MANDATORY use of `generate_test_date()`, `get_test_date_components()` from conftest.py
- **Unique Identifiers**: ALWAYS use timestamp-based unique identifiers for all test data to prevent collisions
- **Verify Test Results**: MUST run tests and verify actual PASSED output - never assume tests work
- **Environment Safety**: MUST use integration config for AWS profile/region, never hardcode values
- **Incremental Development**: MUST run tests after each change and show actual output

### Critical Development Process
- **Read Existing Code First**: Before writing any test, MUST read existing test files to understand patterns and interfaces
- **Use Todo Lists**: MUST break complex testing tasks into tracked steps
- **Incremental Verification**: MUST run related tests after each significant change
- **Never Assume Success**: MUST verify test results with actual pytest output showing PASSED status
- **Show Actual Output**: MUST include actual command output in responses, not summaries or assumptions
- **Investigate Failures**: When tests fail, MUST investigate and fix the issue, not claim tests work
- **Safe Cleanup Only**: MUST use only cleanup methods that remove only test data

---

## 🟡 IMPORTANT - Usually Follow

### Test Categories
- **Unit Tests**: Test individual classes/methods in isolation with mocked dependencies
- **Integration Tests**: Test with real AWS resources using year 9999 test data
- **Service Tests**: Test business logic orchestration between repositories

### Two Types of Tests

#### Unit Tests
- Fast, isolated, mocked dependencies
- Use `IrusContainer.create_unit()` (alias for `create_test()`)
- Mock all external dependencies (AWS, file I/O, etc.)
- Test business logic in isolation
- Location: `tests/unit/`

#### Integration Tests
- Real AWS resources, end-to-end validation
- Use `IrusContainer.create_integration(aws_resources, stack_name)`
- Real DynamoDB, S3, and other AWS services
- **99DDHHMM date pattern** for test data isolation
- Location: `tests/integration/`

### Core Testing Guidelines
- **Arrange-Act-Assert**: Clear test structure for readability
- **Fixture Usage**: Leverage pytest fixtures for setup and teardown
- **Mock Isolation**: Mock external dependencies, test internal logic
- **Parametrized Tests**: Use `@pytest.mark.parametrize` for multiple inputs
- **Descriptive Names**: Test method names clearly describe what is being tested
- **Error Testing**: Test both success and failure scenarios
- **Avoid colliding test data**: Use timestamps or similar to minimise tests failing due to existing data

### Benefits of 99DDHHMM Pattern
1. **Automatic Cleanup**: All records with `id` starting with "99" are automatically cleaned up
2. **No Conflicts**: Each test run gets unique dates based on execution time
3. **Parallel Safe**: Tests can run concurrently without date conflicts
4. **Production Safe**: Cannot accidentally affect production data (year 2024+)
5. **Query Compatible**: Works with existing `begins_with(date)` queries

### Test Date Pattern: Unique Test Dates
Integration tests use a **unique date pattern** for isolated test data that ensures:
- **Uniqueness**: Each test run gets a different date down to the minute
- **Isolation**: Test dates are clearly distinguishable from production data
- **Cleanup**: Easy to identify and remove all test records
- **Maintainability**: Algorithm can change without breaking tests

### Container Testing Patterns
```python
# Use these standardized methods for different environments
container = IrusContainer.create_unit()        # Unit tests with mocked dependencies (alias for create_test)
container = IrusContainer.create_test()        # Unit tests with specific mocks
container = IrusContainer.create_integration(aws_resources, stack_name)  # Integration tests with real AWS
container = IrusContainer.create_production()  # Production with real AWS from env vars
```

### Integration Testing Guidelines
- **Use Date Helpers**: Always use `get_test_date_components()`, `is_test_date()` helpers - never hardcode test date patterns
- **Encapsulation**: The specific test date format is encapsulated in helper functions
- **Separate Expectations**: Use separate expectation fixtures to avoid parameter conflicts
- **Config-Driven Safety**: Use stack_name from config for environment validation
- **Graceful Conflicts**: Skip tests on rare data conflicts rather than complex workarounds
- **Legacy Dependencies**: Skip services that use legacy classes until modernized
- **No Hardcoding**: Avoid hardcoded dates - let the helper functions generate them dynamically

### Test Assertions Best Practices
```python
# GOOD: Check your specific test data appears
assert unique_player in csv_output
assert retrieved_member.player == unique_player

# BAD: Assume only your test data exists
assert len(member_list.members) == 3  # May have old test data!

# BETTER: Filter to your test data first
exact_test_members = [
    m for m in member_list.members
    if m.player in [unique_player1, unique_player2]
]
assert len(exact_test_members) == 2
```

### Graceful Conflict Handling
```python
@pytest.mark.skip(reason="Rare data conflict - acceptable per style guide")
def test_that_occasionally_conflicts(self):
    """Skip this test if it has unavoidable data conflicts."""
    pass
```

---

## 🟢 REFERENCE - When Relevant

### Test Organization

#### Directory Structure
```
tests/
├── STYLE_GUIDE.md           # Testing patterns and practices
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

#### Test File Naming
```python
# Unit tests mirror source structure with test_ prefix
test_member_repository.py       # Tests for src/layer/irus/repositories/member.py
test_discord_messaging_service.py  # Tests for src/layer/irus/services/discord_messaging.py

# Integration tests use _integration suffix
test_member_repository_integration.py
test_container_integration.py
```

### Unit Testing Patterns

#### Test File Organization
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
        import time
        timestamp = int(time.time())
        date_components = get_test_date_components()
        return IrusMember(
            player=f"TestPlayer-{timestamp}",
            faction="yellow",
            start=date_components["date_int"],
            salary=True
        )
```

#### Test Method Patterns
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

### Integration Testing Patterns

#### Container Setup
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

#### Date Helper Functions
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

### Integration Test Template
```python
import time
from uuid import uuid4
from irus.models.member import IrusMember
from irus.repositories.member import MemberRepository
from tests.integration.conftest import get_test_date_components

class TestMemberWorkflow:
    """Integration test for member workflows."""

    @pytest.fixture
    def repositories(self, integration_container):
        """Create repository instances."""
        return {"member": MemberRepository(integration_container)}

    def test_create_and_retrieve_member(self, integration_container, repositories):
        """Test member creation and retrieval with unique data."""
        # 1. Generate unique test data using 99DDHHMM pattern
        timestamp = int(time.time())
        unique_id = uuid4().hex[:8]
        unique_player = f"TestPlayer-{timestamp}-{unique_id}"

        # 2. Get test date using helper
        date_components = get_test_date_components()

        # 3. Create member with 99DDHHMM date pattern
        member = IrusMember(
            player=unique_player,
            faction="green",
            start=date_components['date_int'],  # e.g., 99151228
            salary=True,
            admin=False
        )

        # 4. Save to DynamoDB
        repositories["member"].save(member)

        # 5. Retrieve and verify
        retrieved = repositories["member"].get_by_player(unique_player)
        assert retrieved.player == unique_player
        assert retrieved.faction == "green"

        # No manual cleanup needed - automatic via fixture
```

### Automatic Cleanup via Fixtures
Integration tests have automatic cleanup via the `cleanup_test_data` fixture in `conftest.py`:

```python
@pytest.fixture(autouse=True)
def cleanup_test_data(integration_container):
    yield  # Test runs here
    # Automatic cleanup of all records with id starting with "99"
    table = integration_container.table()
    response = table.scan(
        FilterExpression="begins_with(id, :test_prefix)",
        ExpressionAttributeValues={":test_prefix": "99"}
    )
    # Deletes all matching records in batches
```

### Manual Cleanup Script
To manually clean up leftover test data (e.g., from failed tests or interrupted runs):

```bash
cd invasions/
uv run python -m tests.utilities.cleanup_test_data
```

### Running Integration Tests
```bash
# Prerequisites - AWS credentials are auto-configured from config.toml
cd invasions/
uv sync

# Run all integration tests
uv run pytest tests/integration/ -v

# Run specific test file
uv run pytest tests/integration/test_member_repository_integration.py -v

# Run with coverage
uv run pytest tests/integration/ -v --cov=src --cov-report=html

# Debug with full output
uv run pytest tests/integration/ -v -s --tb=short
```

### Debugging Failed Tests

#### Common Issues
1. **"Token has expired"** - AWS credentials expired
   - Stop and ask user to reauthenticate
   - Never proceed with expired credentials

2. **AssertionError on data not found** - Test data not using 99DDHHMM pattern
   - Check: Are you using hardcoded dates like "9999" or names like "TestPlayer1"?
   - Fix: Use `get_test_date_components()` and timestamp-based unique identifiers

3. **Data conflicts** - Old test data interfering
   - Check: Are you asserting exact counts?
   - Fix: Filter to your specific test data first or run manual cleanup

4. **Leftover test data** - Cleanup didn't run or tests were interrupted
   - Fix: Run `uv run python -m tests.utilities.cleanup_test_data`

#### Debug Commands
```bash
# Verify AWS access
AWS_PAGER="" aws sts get-caller-identity --profile irus-202509-dev --region ap-southeast-2

# Check DynamoDB table
AWS_PAGER="" aws dynamodb describe-table --table-name irus-dev-table --profile irus-202509-dev --region ap-southeast-2

# Manual cleanup (removes all records with id starting with "99")
uv run python -m tests.utilities.cleanup_test_data
```

### Before Writing Any Integration Test: Checklist
- [ ] Am I using `get_test_date_components()` for dates (99DDHHMM pattern)?
- [ ] Am I using `f"TestPlayer-{timestamp}-{uuid4().hex[:8]}"` for player names?
- [ ] Am I relying on automatic cleanup fixture (not manual)?
- [ ] Are my assertions filtering to my specific test data?
- [ ] Am I using real AWS resources (no mocking)?
- [ ] Have I read the target interface first (not hallucinating)?

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
```

### Error Testing

#### Exception Testing Patterns
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

#### Error Handling Guidelines
- **Exception Chaining**: Verify original error context is preserved
- **Domain Exceptions**: Test that technical exceptions are converted to domain-appropriate types
- **Error Messages**: Assert error messages contain sufficient context
- **Input Validation**: Test early validation with clear error messages

### Fixture Patterns

#### Session-Scoped Fixtures
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

### Skipping Legacy Services
```python
@pytest.mark.skip(reason="MemberManagementService uses legacy dependencies - modernize first")
class TestMemberManagementServiceIntegration:
    """Integration tests for member management service business logic."""
    # Tests skipped until service is modernized
```

### FixtureLoader Pattern
For integration tests, use JSON fixtures with the `FixtureLoader` utility:

```python
import time
from uuid import uuid4
from tests.integration.fixtures import FixtureLoader
from tests.integration.conftest import get_test_date_components
from irus.models.member import IrusMember

# Load fixture and override with unique identifier using 99DDHHMM pattern
member_data = FixtureLoader.load(IrusMember, "test_player1")

# Generate unique identifier
timestamp = int(time.time())
unique_id = uuid4().hex[:8]
member_data.player = f"TestPlayer-{timestamp}-{unique_id}"

# Use 99DDHHMM date pattern
date_components = get_test_date_components()
member_data.start = date_components['date_int']  # e.g., 99151228

repository.save(member_data)
```

**IMPORTANT**: JSON fixtures serve as templates. Always override identifiers and dates with unique values using the 99DDHHMM pattern before saving to database.
