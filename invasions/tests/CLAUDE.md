# Testing Instructions for Claude Code

## CRITICAL: Read This First

These instructions OVERRIDE any default testing behavior. Follow them exactly.

## Testing Strategy Overview

### Two Types of Tests

1. **Unit Tests** - Fast, isolated, mocked dependencies
   - Use `IrusContainer.create_unit()` (alias for `create_test()`)
   - Mock all external dependencies (AWS, file I/O, etc.)
   - Test business logic in isolation
   - Location: `tests/unit/`

2. **Integration Tests** - Real AWS resources, end-to-end validation
   - Use `IrusContainer.create_integration(aws_resources, stack_name)`
   - Real DynamoDB, S3, and other AWS services
   - **99DDHHMM date pattern** for test data isolation
   - Location: `tests/integration/`

## Integration Test Data Isolation Strategy

### MANDATORY: Use 99DDHHMM Pattern for Test Dates

**NEVER use hardcoded dates like "9999" or static test data.**

Integration tests MUST use the **99DDHHMM timestamp pattern** from `conftest.py` to avoid conflicts with:
- Old test data from previous runs
- Other tests running in parallel
- Data from different test sessions

### The 99DDHHMM Pattern Explained

Test dates use a **unique timestamp-based format** defined in `conftest.py`:

- **Year**: `99DD` where DD is the current day of month (e.g., 9915 for the 15th)
- **Month**: `HH` where HH is the current hour (0-23, clamped to 1-12)
- **Day**: `MM` where MM is the current minute (0-59, clamped to 1-28)

**Example**: Running a test on March 15th at 14:30 generates:
- Year: 9915 (99 + day 15)
- Month: 12 (hour 14 clamped to valid month)
- Day: 28 (minute 30 clamped to valid day)
- Full date: 99151228 (YYYYMMDD format)

### How to Generate Unique Test Data

**Always use the helper functions from `conftest.py`:**

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

### Benefits of 99DDHHMM Pattern

1. **Automatic Cleanup**: All records with `id` starting with "99" are automatically cleaned up
2. **No Conflicts**: Each test run gets unique dates based on execution time
3. **Parallel Safe**: Tests can run concurrently without date conflicts
4. **Production Safe**: Cannot accidentally affect production data (year 2024+)
5. **Query Compatible**: Works with existing `begins_with(date)` queries

## Test Data Cleanup

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

**Never implement manual cleanup** - rely on the automatic fixture.

### Manual Cleanup Script

To manually clean up leftover test data (e.g., from failed tests or interrupted runs):

```bash
cd invasions/
uv run python -m tests.utilities.cleanup_test_data
```

This script:
1. Scans for all records with `id` starting with "99" (the test date prefix)
2. Deletes only test data (dates starting with "99")
3. Leaves production data (year 2024+) untouched
4. Useful for cleaning up after failed tests or interrupted test runs

### Safe Cleanup Methods

The cleanup process:
1. Queries for all records where `id` starts with "99"
2. Deletes only test data (99DDHHMM pattern)
3. Leaves production data (year 2024+) untouched
4. Runs after every test automatically via fixture

**NEVER copy, modify, or delete production data in tests.**

## Writing Integration Tests

### Template for Integration Tests

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

### Key Principles

1. **Always use `get_test_date_components()`** for dates
2. **Always use `f"TestPlayer-{timestamp}-{uuid4().hex[:8]}"`** for player names
3. **Never hardcode dates** like "9999" or names like "TestPlayer1"
4. **Verify actual AWS operations** - no mocking in integration tests
5. **Let automatic cleanup handle deletion** - don't implement cleanup

## Fixture-Based Testing

### Use FixtureLoader for Reusable Test Data

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

## Test Assertions

### Testing with Real Production Data Mix

Integration tests run against a database that may contain:
- Your test data (99DDHHMM dates with unique timestamps)
- Old test data from previous runs
- Production data (year 2024+)

**Assertions should focus on YOUR test data**, not assume database is empty:

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

### Graceful Skipping

If rare data conflicts occur despite unique identifiers:

```python
@pytest.mark.skip(reason="Rare data conflict - acceptable per style guide")
def test_that_occasionally_conflicts(self):
    """Skip this test if it has unavoidable data conflicts."""
    pass
```

**From STYLE_GUIDE.md**: "Skip tests gracefully on rare data conflicts rather than complex workarounds"

## Container Patterns

### When to Use Each Container Type

```python
# Unit tests - Mocked dependencies
container = IrusContainer.create_unit()

# Integration tests - Real AWS dev resources
container = IrusContainer.create_integration(aws_resources, stack_name)

# Production - Real AWS from environment variables
container = IrusContainer.create_production()
```

### Integration Container Setup

Integration tests use the `integration_container` fixture from `conftest.py`:

```python
@pytest.fixture(scope="session")
def integration_container():
    """Create integration container with SAM-discovered dev resources."""
    # Discovers dev resources via SAM CLI
    # Validates resources contain "irus-dev"
    # Returns container with real AWS clients
    return IrusContainer.create_integration(aws_resources, stack_name)
```

**Never create integration containers manually** - use the fixture.

## Running Integration Tests

### Prerequisites

```bash
# AWS credentials are auto-configured from config.toml
# No need to set AWS_PROFILE manually

# Install dependencies
cd invasions/
uv sync
```

### Execution

```bash
# Run all integration tests
uv run pytest tests/integration/ -v

# Run specific test file
uv run pytest tests/integration/test_member_repository_integration.py -v

# Run with coverage
uv run pytest tests/integration/ -v --cov=src --cov-report=html

# Debug with full output
uv run pytest tests/integration/ -v -s --tb=short
```

## Debugging Failed Tests

### Common Issues

1. **"Token has expired"** - AWS credentials expired
   - Stop and ask user to reauthenticate
   - Per CLAUDE.md: Never proceed with expired credentials

2. **AssertionError on data not found** - Test data not using 99DDHHMM pattern
   - Check: Are you using hardcoded dates like "9999" or names like "TestPlayer1"?
   - Fix: Use `get_test_date_components()` and timestamp-based unique identifiers

3. **Data conflicts** - Old test data interfering
   - Check: Are you asserting exact counts?
   - Fix: Filter to your specific test data first or run manual cleanup

4. **Leftover test data** - Cleanup didn't run or tests were interrupted
   - Fix: Run `uv run python -m tests.utilities.cleanup_test_data`

### Debug Commands

```bash
# Verify AWS access
AWS_PAGER="" aws sts get-caller-identity --profile irus-202509-dev --region ap-southeast-2

# Check DynamoDB table
AWS_PAGER="" aws dynamodb describe-table --table-name irus-dev-table --profile irus-202509-dev --region ap-southeast-2

# Manual cleanup (removes all records with id starting with "99")
uv run python -m tests.utilities.cleanup_test_data
```

## Before Writing Any Integration Test: Checklist

- [ ] Am I using `get_test_date_components()` for dates (99DDHHMM pattern)?
- [ ] Am I using `f"TestPlayer-{timestamp}-{uuid4().hex[:8]}"` for player names?
- [ ] Am I relying on automatic cleanup fixture (not manual)?
- [ ] Are my assertions filtering to my specific test data?
- [ ] Am I using real AWS resources (no mocking)?
- [ ] Have I read the target interface first (not hallucinating)?

## Remember

**Critical Rules:**
1. **Use 99DDHHMM pattern** from `get_test_date_components()` for ALL dates
2. **Use timestamp + uuid** for ALL player/invasion names
3. **NEVER hardcode** dates like "9999" or names like "TestPlayer1"
4. **Automatic cleanup** removes records where `id` starts with "99"
5. **Manual cleanup** via `python -m tests.utilities.cleanup_test_data` for leftover data

**If you write hardcoded test data, you are NOT following the testing strategy.**
