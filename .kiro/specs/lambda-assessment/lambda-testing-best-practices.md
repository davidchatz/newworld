# Lambda Testing Best Practices

## Overview

This document outlines best practices for testing Lambda functions in the Invasions R Us Discord bot, focusing on practical patterns that ensure reliable, maintainable tests while leveraging the existing `IrusContainer` dependency injection system.

## Core Testing Principles

### 1. Container-Based Dependency Injection

**Always use `IrusContainer` for dependency management:**

```python
# Unit tests - mocked dependencies
@pytest.fixture
def container():
    return IrusContainer.create_unit()

# Integration tests - real AWS resources
@pytest.fixture
def container(integration_container):
    return integration_container

# Set container as default for Lambda functions
IrusContainer.set_default(container)
```

**Why this matters:**
- Consistent dependency management across all tests
- Easy switching between mocked and real dependencies
- Matches production Lambda behavior
- Enables proper isolation and cleanup

### 2. Test Data Isolation

**Use unique identifiers for all test data:**

```python
import time
from uuid import uuid4
from tests.integration.conftest import get_test_date_components

# Generate unique test identifiers
timestamp = int(time.time())
unique_id = uuid4().hex[:8]
player_name = f"TestPlayer-{timestamp}-{unique_id}"

# Use 99DDHHMM pattern for dates in integration tests
date_components = get_test_date_components()
invasion_name = f"{date_components['date_string']}-ef"  # e.g., "99151228-ef"
```

**Why this matters:**
- Prevents test conflicts when running in parallel
- Enables automatic cleanup via test date patterns
- Avoids flaky tests due to data collisions
- Safe for production environments (test data clearly marked)

### 3. Proper Mocking Strategy

**Mock external dependencies, test internal logic:**

```python
# Mock signature verification (external Discord API dependency)
@patch('src.bot.bot.verify_signature')
def test_command_processing(mock_verify, container, lambda_context, event):
    mock_verify.return_value = None  # Signature passes

    # Test the actual command processing logic
    response = lambda_handler(event, lambda_context)
    assert response["statusCode"] == 200

# Mock HTTP downloads (external network dependency)
@patch('src.process.process.pool_mgr')
def test_file_processing(mock_pool, container, lambda_context, event):
    mock_response = Mock()
    mock_response.read.return_value = b'fake_image_data'
    mock_pool.request.return_value = mock_response

    # Test the file processing logic
    response = lambda_handler(event, lambda_context)
```

**What to mock:**
- External API calls (Discord, HTTP requests)
- Complex image processing (OCR, Textract)
- Time-dependent operations
- Network operations

**What NOT to mock:**
- Your own business logic
- Container dependencies (use real or test containers)
- Database operations in integration tests

### 4. Environment Variable Management

**Patch environment variables consistently:**

```python
@patch.dict(os.environ, {"DISCORD_CMD": "irus"})
@patch('src.bot.bot.verify_signature')
def test_bot_command(mock_verify, container, lambda_context, event):
    # Import AFTER patching environment variables
    from src.bot.bot import lambda_handler

    mock_verify.return_value = None
    response = lambda_handler(event, lambda_context)
```

**Why this pattern:**
- Ensures Lambda functions get correct configuration
- Prevents environment variable leakage between tests
- Matches production environment setup
- Avoids import-time errors

### 5. Error Testing Patterns

**Test both success and failure scenarios:**

```python
def test_successful_processing(container, lambda_context, valid_event):
    """Test the happy path."""
    response = lambda_handler(valid_event, lambda_context)
    assert response["statusCode"] == 200

def test_invalid_input_handling(container, lambda_context):
    """Test error handling for invalid input."""
    invalid_event = {"invalid": "data"}
    response = lambda_handler(invalid_event, lambda_context)
    assert response["statusCode"] == 400
    assert "error" in response["body"].lower()

def test_external_service_failure(container, lambda_context, event):
    """Test handling of external service failures."""
    with patch('src.process.process.pool_mgr') as mock_pool:
        mock_pool.request.side_effect = Exception("Network error")
        response = lambda_handler(event, lambda_context)
        assert response["statusCode"] == 400
```

## Unit Testing Best Practices

### Test Structure

**Follow Arrange-Act-Assert pattern:**

```python
def test_member_add_command(self, container, lambda_context, discord_event_base):
    """Test member add command processing."""
    # Arrange - Set up test data and mocks
    mock_container.return_value = container
    mock_verify.return_value = None

    event_body = json.loads(discord_event_base["body"])
    event_body["data"]["options"] = [/* command options */]
    discord_event_base["body"] = json.dumps(event_body)

    # Act - Execute the function under test
    response = lambda_handler(discord_event_base, lambda_context)

    # Assert - Verify the results
    assert response["statusCode"] == 200
    response_data = json.loads(response["body"])
    assert "success" in response_data["data"]["content"]
```

### Fixture Organization

**Create focused, reusable fixtures:**

```python
@pytest.fixture
def container():
    """Test container with mocked dependencies."""
    return IrusContainer.create_unit()

@pytest.fixture
def lambda_context():
    """Mock Lambda context with realistic values."""
    context = Mock(spec=LambdaContext)
    context.function_name = "test-function"
    context.aws_request_id = "test-request-id"
    context.remaining_time_in_millis = 30000
    return context

@pytest.fixture
def discord_member_add_event():
    """Discord event for member add command."""
    # Use helper functions to generate unique test data
    return create_discord_command_event(
        command_name="member",
        subcommand_name="add",
        options=[
            {"name": "player", "value": f"TestPlayer-{int(time.time())}"},
            {"name": "faction", "value": "yellow"}
        ]
    )
```

### Mock Verification

**Verify mocks are called correctly:**

```python
def test_s3_upload_called(self, container, lambda_context, process_event):
    """Test that S3 upload is called with correct parameters."""
    # Arrange
    mock_s3 = container.s3()

    # Act
    response = lambda_handler(process_event, lambda_context)

    # Assert
    assert response["statusCode"] == 200
    mock_s3.upload_fileobj.assert_called_once()

    # Verify call arguments
    call_args = mock_s3.upload_fileobj.call_args
    assert call_args[1] == "test-bucket"  # bucket name
    assert "invasions/" in call_args[2]   # S3 key
```

## Integration Testing Best Practices

### Real AWS Resource Usage

**Use real AWS services for integration tests:**

```python
def test_member_add_end_to_end(self, integration_container, lambda_context, event):
    """Test complete member add workflow with real DynamoDB."""
    # Arrange - Use real container with AWS resources
    IrusContainer.set_default(integration_container)

    # Act - Execute Lambda with real dependencies
    response = lambda_handler(event, lambda_context)

    # Assert - Verify in real database
    assert response["statusCode"] == 200

    # Check data was actually written to DynamoDB
    from irus.repositories.member import MemberRepository
    member_repo = MemberRepository(integration_container)
    created_member = member_repo.get_by_player(player_name)
    assert created_member is not None
```

### Performance Testing

**Include performance assertions:**

```python
def test_lambda_performance(self, integration_container, lambda_context, event):
    """Test Lambda performance with real resources."""
    import time

    start_time = time.time()
    response = lambda_handler(event, lambda_context)
    execution_time = time.time() - start_time

    assert response["statusCode"] == 200
    assert execution_time < 30.0  # Should complete within 30 seconds

    # Log performance for monitoring
    print(f"Lambda execution time: {execution_time:.2f}s")
```

### Data Verification

**Verify data integrity across services:**

```python
def test_invasion_creation_with_s3_upload(self, integration_container, lambda_context, event):
    """Test invasion creation includes S3 file upload."""
    # Act
    response = lambda_handler(event, lambda_context)

    # Assert database record
    invasion_repo = InvasionRepository(integration_container)
    invasion = invasion_repo.get_by_name(invasion_name)
    assert invasion is not None

    # Assert S3 file exists
    s3_resource = integration_container.s3_resource()
    bucket_name = integration_container.bucket_name()

    try:
        s3_resource.Object(bucket_name, expected_s3_key).load()
        file_exists = True
    except s3_resource.meta.client.exceptions.NoSuchKey:
        file_exists = False

    assert file_exists, "File should have been uploaded to S3"
```

## Discord Event Testing

### Event Structure Validation

**Validate Discord event structure:**

```python
def test_discord_event_structure(self, discord_event):
    """Validate Discord event has required structure."""
    body = json.loads(discord_event["body"])

    # Validate required fields
    assert "type" in body
    assert "data" in body
    assert "member" in body
    assert "token" in body

    # Validate headers
    assert "x-signature-ed25519" in discord_event["headers"]
    assert "x-signature-timestamp" in discord_event["headers"]
```

### Command Option Testing

**Test various command option combinations:**

```python
@pytest.mark.parametrize("faction,expected_valid", [
    ("yellow", True),
    ("purple", True),
    ("green", True),
    ("invalid", False),
])
def test_member_add_faction_validation(self, faction, expected_valid, container, lambda_context):
    """Test member add with various faction values."""
    event = create_discord_command_event(
        command_name="member",
        subcommand_name="add",
        options=[
            {"name": "player", "value": "TestPlayer"},
            {"name": "faction", "value": faction}
        ]
    )

    response = lambda_handler(event, lambda_context)

    if expected_valid:
        assert response["statusCode"] == 200
    else:
        assert response["statusCode"] == 200  # Discord always returns 200
        response_data = json.loads(response["body"])
        assert "error" in response_data["data"]["content"].lower()
```

## Error Handling Testing

### Exception Scenarios

**Test comprehensive error scenarios:**

```python
def test_database_connection_failure(self, container, lambda_context, event):
    """Test handling of database connection failures."""
    # Arrange - Mock database failure
    container.table().get_item.side_effect = Exception("Connection timeout")

    # Act
    response = lambda_handler(event, lambda_context)

    # Assert - Should handle gracefully
    assert response["statusCode"] == 500
    response_data = json.loads(response["body"])
    assert "error" in response_data["data"]["content"].lower()
    assert "timeout" in response_data["data"]["content"].lower()

def test_invalid_json_body(self, container, lambda_context):
    """Test handling of malformed JSON in request body."""
    invalid_event = {
        "body": "invalid json{",
        "headers": {
            "x-signature-ed25519": "test_signature",
            "x-signature-timestamp": "1234567890"
        }
    }

    response = lambda_handler(invalid_event, lambda_context)
    assert response["statusCode"] == 401  # Should fail gracefully
```

### Logging Verification

**Verify proper error logging:**

```python
def test_error_logging(self, container, lambda_context, event, caplog):
    """Test that errors are properly logged."""
    # Arrange - Cause an error
    container.table().put_item.side_effect = Exception("Test error")

    # Act
    response = lambda_handler(event, lambda_context)

    # Assert - Error should be logged
    assert "Test error" in caplog.text
    assert "ERROR" in caplog.text
```

## Test Organization

### File Structure

```
tests/
├── unit/
│   └── lambdas/
│       ├── test_bot_lambda.py           # Bot Lambda unit tests
│       ├── test_process_lambda.py       # Process Lambda unit tests
│       ├── test_invasion_lambda.py      # Invasion Lambda unit tests
│       └── test_month_lambda.py         # Month Lambda unit tests
├── integration/
│   └── lambdas/
│       ├── test_bot_lambda_integration.py
│       ├── test_process_lambda_integration.py
│       ├── test_invasion_lambda_integration.py
│       └── test_month_lambda_integration.py
└── fixtures/
    └── discord_events.py               # Reusable Discord event fixtures
```

### Test Naming

**Use descriptive test names:**

```python
# Good - describes what is being tested
def test_member_add_command_creates_database_record()
def test_signature_verification_failure_returns_401()
def test_ladder_processing_uploads_file_to_s3()

# Bad - too generic
def test_member_add()
def test_error_case()
def test_lambda_function()
```

### Test Categories

**Organize tests by functionality:**

```python
class TestBotLambdaCommands:
    """Test Discord command processing."""

    def test_member_add_command(self):
        """Test member add command processing."""
        pass

    def test_invasion_add_command(self):
        """Test invasion add command processing."""
        pass

class TestBotLambdaAuthentication:
    """Test Discord authentication and authorization."""

    def test_signature_verification(self):
        """Test Discord signature verification."""
        pass

    def test_admin_role_required(self):
        """Test admin role requirement for admin commands."""
        pass

class TestBotLambdaErrorHandling:
    """Test error handling scenarios."""

    def test_invalid_command_handling(self):
        """Test handling of invalid commands."""
        pass

    def test_database_error_handling(self):
        """Test handling of database errors."""
        pass
```

## Running Tests

### Test Execution Commands

```bash
# Run all Lambda unit tests
uv run pytest tests/unit/lambdas/ -v

# Run specific Lambda function tests
uv run pytest tests/unit/lambdas/test_bot_lambda.py -v

# Run integration tests (requires AWS credentials)
uv run pytest tests/integration/lambdas/ -v

# Run with coverage
uv run pytest tests/unit/lambdas/ -v --cov=src --cov-report=html

# Run performance tests only
uv run pytest tests/integration/lambdas/ -v -k "performance"
```

### Test Configuration

**Use pytest configuration for consistent behavior:**

```ini
# pytest.ini
[tool:pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts =
    -v
    --tb=short
    --strict-markers
    --disable-warnings
markers =
    unit: Unit tests with mocked dependencies
    integration: Integration tests with real AWS resources
    performance: Performance-focused tests
    slow: Tests that take longer than 30 seconds
```

## Common Pitfalls and Solutions

### 1. Import Timing Issues

**Problem:** Lambda functions fail when environment variables aren't set at import time.

**Solution:** Import Lambda handlers after patching environment variables.

```python
# Wrong - imports before environment is set
from src.bot.bot import lambda_handler

@patch.dict(os.environ, {"DISCORD_CMD": "irus"})
def test_command():
    response = lambda_handler(event, context)

# Right - imports after environment is patched
@patch.dict(os.environ, {"DISCORD_CMD": "irus"})
def test_command():
    from src.bot.bot import lambda_handler
    response = lambda_handler(event, context)
```

### 2. Container State Leakage

**Problem:** Container state persists between tests causing failures.

**Solution:** Always set fresh container as default.

```python
def test_lambda_function(self, container, lambda_context, event):
    # Always set container as default for each test
    IrusContainer.set_default(container)

    response = lambda_handler(event, lambda_context)
    assert response["statusCode"] == 200
```

### 3. Async Operation Testing

**Problem:** Lambda functions trigger async operations (Step Functions) that complete after Lambda returns.

**Solution:** Mock async operations or test their initiation, not completion.

```python
@patch('src.bot.bot.process.start')
def test_ladder_upload_triggers_processing(self, mock_process, container, lambda_context, event):
    """Test that ladder upload triggers async processing."""
    mock_process.return_value = "Process started"

    response = lambda_handler(event, lambda_context)

    # Assert process was triggered
    mock_process.assert_called_once()
    assert response["statusCode"] == 200
    assert "In Progress" in response["body"]
```

### 4. Test Data Cleanup

**Problem:** Test data accumulates in integration environments.

**Solution:** Use automatic cleanup fixtures and test date patterns.

```python
# Automatic cleanup via fixture (preferred)
@pytest.fixture(autouse=True)
def cleanup_test_data(integration_container):
    yield  # Test runs here
    # Cleanup handled automatically by conftest.py

# Manual cleanup script when needed
# uv run python -m tests.utilities.cleanup_test_data
```

This comprehensive testing framework ensures Lambda functions are thoroughly tested while maintaining consistency with the existing architecture and testing patterns.
