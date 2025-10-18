# Lambda Testing Framework Design

## Overview

This document provides a comprehensive testing framework for modernizing Lambda functions in the Invasions R Us Discord bot. The framework supports both unit testing (with mocked dependencies) and integration testing (with real AWS resources) using the existing `IrusContainer` dependency injection pattern.

## Testing Architecture

### Container-Based Testing Pattern

All Lambda tests use the `IrusContainer` pattern for consistent dependency injection:

```python
# Unit tests - mocked dependencies
container = IrusContainer.create_unit()

# Integration tests - real AWS resources
container = IrusContainer.create_integration(aws_resources, stack_name)
```

### Test Categories

#### Unit Tests
- **Purpose**: Test Lambda handler logic in isolation
- **Dependencies**: All external services mocked
- **Speed**: Fast execution (< 1 second per test)
- **Location**: `tests/unit/lambda/`

#### Integration Tests
- **Purpose**: Test Lambda handlers with real AWS services
- **Dependencies**: Real DynamoDB, S3, Textract, Step Functions
- **Speed**: Slower execution (5-30 seconds per test)
- **Location**: `tests/integration/lambda/`

## Lambda Function Testing Patterns

### 1. Bot Lambda Testing Pattern

The Bot Lambda handles Discord slash commands and has complex routing logic.

#### Unit Test Template

```python
"""Unit tests for Bot Lambda function."""

import json
import pytest
from unittest.mock import Mock, patch
from aws_lambda_powertools.utilities.typing import LambdaContext

from irus.container import IrusContainer
from src.bot.bot import lambda_handler


class TestBotLambda:
    """Test suite for Bot Lambda function."""

    @pytest.fixture
    def container(self):
        """Create test container with mocked dependencies."""
        return IrusContainer.create_unit()

    @pytest.fixture
    def lambda_context(self):
        """Create mock Lambda context."""
        context = Mock(spec=LambdaContext)
        context.function_name = "test-bot-function"
        context.function_version = "1"
        context.invoked_function_arn = "arn:aws:lambda:us-east-1:123456789012:function:test-bot-function"
        context.memory_limit_in_mb = 128
        context.remaining_time_in_millis = 30000
        context.aws_request_id = "test-request-id"
        return context

    @pytest.fixture
    def discord_event_base(self):
        """Base Discord interaction event structure."""
        return {
            "body": json.dumps({
                "type": 2,  # APPLICATION_COMMAND
                "data": {
                    "name": "irus",
                    "options": []
                },
                "member": {
                    "roles": ["admin_role_id"]
                },
                "token": "test_interaction_token"
            }),
            "headers": {
                "x-signature-ed25519": "test_signature",
                "x-signature-timestamp": "1234567890"
            }
        }

    @patch('src.bot.bot.verify_signature')
    @patch('src.bot.bot.IrusContainer.default')
    def test_member_add_command(self, mock_container, mock_verify, container, lambda_context, discord_event_base):
        """Test member add command processing."""
        # Arrange
        mock_container.return_value = container
        mock_verify.return_value = None  # Signature verification passes

        # Configure Discord event for member add
        event_body = json.loads(discord_event_base["body"])
        event_body["data"]["options"] = [{
            "name": "member",
            "options": [{
                "name": "add",
                "options": [
                    {"name": "player", "value": "TestPlayer"},
                    {"name": "faction", "value": "yellow"}
                ]
            }]
        }]
        discord_event_base["body"] = json.dumps(event_body)

        # Mock member creation
        mock_member = Mock()
        mock_member.str.return_value = "Member TestPlayer added successfully"

        with patch('src.bot.bot.IrusMember.from_user', return_value=mock_member):
            with patch('src.bot.bot.irus.update_invasions_for_new_member', return_value=""):
                # Act
                response = lambda_handler(discord_event_base, lambda_context)

        # Assert
        assert response["statusCode"] == 200
        response_data = json.loads(response["body"])
        assert response_data["type"] == 4  # CHANNEL_MESSAGE_WITH_SOURCE
        assert "TestPlayer added successfully" in response_data["data"]["content"]

    @patch('src.bot.bot.verify_signature')
    def test_signature_verification_failure(self, mock_verify, lambda_context, discord_event_base):
        """Test handling of signature verification failure."""
        # Arrange
        from nacl.exceptions import BadSignatureError
        mock_verify.side_effect = BadSignatureError("Invalid signature")

        # Act
        response = lambda_handler(discord_event_base, lambda_context)

        # Assert
        assert response["statusCode"] == 401
        response_data = json.loads(response["body"])
        assert "Bad Signature" in response_data["data"]["content"]

    @patch('src.bot.bot.verify_signature')
    def test_unauthorized_user_admin_command(self, mock_verify, lambda_context, discord_event_base):
        """Test unauthorized user attempting admin command."""
        # Arrange
        mock_verify.return_value = None

        # Remove admin role from user
        event_body = json.loads(discord_event_base["body"])
        event_body["member"]["roles"] = ["regular_user_role"]
        event_body["data"]["options"] = [{
            "name": "member",
            "options": [{"name": "add", "options": []}]
        }]
        discord_event_base["body"] = json.dumps(event_body)

        # Act
        response = lambda_handler(discord_event_base, lambda_context)

        # Assert
        assert response["statusCode"] == 200
        response_data = json.loads(response["body"])
        assert "do not have permissions" in response_data["data"]["content"]
```

#### Integration Test Template

```python
"""Integration tests for Bot Lambda function."""

import json
import time
from uuid import uuid4
import pytest
from aws_lambda_powertools.utilities.typing import LambdaContext

from tests.integration.conftest import get_test_date_components
from src.bot.bot import lambda_handler


class TestBotLambdaIntegration:
    """Integration test suite for Bot Lambda function."""

    @pytest.fixture
    def lambda_context(self):
        """Create mock Lambda context."""
        from unittest.mock import Mock
        context = Mock(spec=LambdaContext)
        context.function_name = "irus-dev-bot"
        context.aws_request_id = f"test-{uuid4().hex}"
        return context

    @pytest.fixture
    def discord_member_add_event(self):
        """Discord event for member add command with unique test data."""
        timestamp = int(time.time())
        unique_id = uuid4().hex[:8]
        date_components = get_test_date_components()

        return {
            "body": json.dumps({
                "type": 2,
                "data": {
                    "name": "irus",
                    "options": [{
                        "name": "member",
                        "options": [{
                            "name": "add",
                            "options": [
                                {"name": "player", "value": f"TestPlayer-{timestamp}-{unique_id}"},
                                {"name": "faction", "value": "yellow"},
                                {"name": "day", "value": date_components["day"]},
                                {"name": "month", "value": date_components["month"]},
                                {"name": "year", "value": date_components["year"]}
                            ]
                        }]
                    }]
                },
                "member": {"roles": [os.environ.get("DISCORD_ADMIN_ROLE_ID", "admin_role")]},
                "token": "test_interaction_token"
            }),
            "headers": {
                "x-signature-ed25519": "test_signature",
                "x-signature-timestamp": str(int(time.time()))
            }
        }

    def test_member_add_end_to_end(self, integration_container, lambda_context, discord_member_add_event):
        """Test complete member add workflow with real AWS resources."""
        # Arrange - Set container as default for Lambda
        from irus.container import IrusContainer
        IrusContainer.set_default(integration_container)

        # Mock signature verification for testing
        with patch('src.bot.bot.verify_signature'):
            # Act
            response = lambda_handler(discord_member_add_event, lambda_context)

        # Assert
        assert response["statusCode"] == 200
        response_data = json.loads(response["body"])
        assert response_data["type"] == 4

        # Verify member was actually created in DynamoDB
        event_body = json.loads(discord_member_add_event["body"])
        player_name = None
        for option in event_body["data"]["options"][0]["options"][0]["options"]:
            if option["name"] == "player":
                player_name = option["value"]
                break

        # Check member exists in database
        from irus.repositories.member import MemberRepository
        member_repo = MemberRepository(integration_container)
        created_member = member_repo.get_by_player(player_name)

        assert created_member is not None
        assert created_member.player == player_name
        assert created_member.faction == "yellow"
```

### 2. Process Lambda Testing Pattern

The Process Lambda handles file downloads and OCR processing.

#### Unit Test Template

```python
"""Unit tests for Process Lambda function."""

import json
import pytest
from unittest.mock import Mock, patch
from aws_lambda_powertools.utilities.typing import LambdaContext

from irus.container import IrusContainer
from src.process.process import lambda_handler


class TestProcessLambda:
    """Test suite for Process Lambda function."""

    @pytest.fixture
    def container(self):
        """Create test container with mocked dependencies."""
        return IrusContainer.create_unit()

    @pytest.fixture
    def lambda_context(self):
        """Create mock Lambda context."""
        context = Mock(spec=LambdaContext)
        context.function_name = "test-process-function"
        context.aws_request_id = "test-request-id"
        return context

    @pytest.fixture
    def process_event(self):
        """Process Lambda event structure."""
        return {
            "invasion": "99151228-ef",
            "filename": "ladder.png",
            "url": "https://cdn.discordapp.com/attachments/123/456/ladder.png",
            "folder": "invasions/99151228-ef/",
            "process": "Ladder"
        }

    @patch('src.process.process.IrusContainer.default')
    @patch('src.process.process.pool_mgr')
    def test_successful_ladder_processing(self, mock_pool, mock_container, container, lambda_context, process_event):
        """Test successful ladder image processing."""
        # Arrange
        mock_container.return_value = container

        # Mock S3 upload
        mock_s3 = container.s3()
        mock_s3.upload_fileobj.return_value = None

        # Mock HTTP download
        mock_response = Mock()
        mock_pool.request.return_value = mock_response

        # Mock invasion and ladder processing
        mock_invasion = Mock()
        mock_invasion.name = "99151228-ef"

        mock_ladder = Mock()
        mock_ladder.str.return_value = "Processed 50 ranks, 25 members"

        with patch('src.process.process.IrusInvasion.from_table', return_value=mock_invasion):
            with patch('src.process.process.IrusMemberList') as mock_member_list:
                with patch('src.process.process.IrusLadder.from_ladder_image', return_value=mock_ladder):
                    # Act
                    response = lambda_handler(process_event, lambda_context)

        # Assert
        assert response["statusCode"] == 200
        response_body = json.loads(response["body"])
        assert "Successful download of ladder.png" in response_body
        assert "Processed 50 ranks, 25 members" in response_body

        # Verify S3 upload was called
        mock_s3.upload_fileobj.assert_called_once()

    def test_invalid_file_type(self, container, lambda_context, process_event):
        """Test handling of invalid file types."""
        # Arrange
        process_event["filename"] = "document.pdf"

        with patch('src.process.process.IrusContainer.default', return_value=container):
            # Act
            response = lambda_handler(process_event, lambda_context)

        # Assert
        assert response["statusCode"] == 400
        response_body = json.loads(response["body"])
        assert "not a PNG file" in response_body

    @patch('src.process.process.IrusContainer.default')
    def test_download_failure(self, mock_container, container, lambda_context, process_event):
        """Test handling of download failures."""
        # Arrange
        mock_container.return_value = container
        mock_s3 = container.s3()
        mock_s3.upload_fileobj.side_effect = Exception("Network error")

        with patch('src.process.process.pool_mgr'):
            # Act
            response = lambda_handler(process_event, lambda_context)

        # Assert
        assert response["statusCode"] == 400
        response_body = json.loads(response["body"])
        assert "Error downloading" in response_body
```

### 3. Invasion Lambda Testing Pattern

The Invasion Lambda generates reports for specific invasions.

#### Unit Test Template

```python
"""Unit tests for Invasion Lambda function."""

import json
import pytest
from unittest.mock import Mock, patch
from aws_lambda_powertools.utilities.typing import LambdaContext

from irus.container import IrusContainer
from src.invasion.invasion import lambda_handler


class TestInvasionLambda:
    """Test suite for Invasion Lambda function."""

    @pytest.fixture
    def container(self):
        """Create test container with mocked dependencies."""
        return IrusContainer.create_unit()

    @pytest.fixture
    def lambda_context(self):
        """Create mock Lambda context."""
        context = Mock(spec=LambdaContext)
        context.function_name = "test-invasion-function"
        return context

    @pytest.fixture
    def invasion_event(self):
        """Invasion Lambda event structure."""
        return {"invasion": "99151228-ef"}

    @patch('src.invasion.invasion.IrusContainer.default')
    def test_successful_invasion_report(self, mock_container, container, lambda_context, invasion_event):
        """Test successful invasion report generation."""
        # Arrange
        mock_container.return_value = container

        mock_invasion = Mock()
        mock_invasion.name = "99151228-ef"

        mock_ladder = Mock()
        mock_ladder.count.return_value = 50
        mock_ladder.members.return_value = 25
        mock_ladder.list.side_effect = lambda member: "Member list" if member else "Non-member list"
        mock_ladder.contiguous_from_1_until.return_value = 50

        mock_report = Mock()
        mock_report.msg = "https://s3.amazonaws.com/bucket/report.csv"

        with patch('src.invasion.invasion.IrusInvasion.from_table', return_value=mock_invasion):
            with patch('src.invasion.invasion.IrusLadder.from_invasion', return_value=mock_ladder):
                with patch('src.invasion.invasion.IrusReport.from_invasion', return_value=mock_report):
                    # Act
                    response = lambda_handler(invasion_event, lambda_context)

        # Assert
        assert response["statusCode"] == 200
        body = response["body"]
        assert body["name"] == "99151228-ef"
        assert body["ranks"] == 50
        assert body["members"] == 25
        assert body["contiguous"] == "Yes"
        assert "s3.amazonaws.com" in body["url"]

    @patch('src.invasion.invasion.IrusInvasion.from_table')
    def test_invasion_not_found(self, mock_from_table, container, lambda_context, invasion_event):
        """Test handling when invasion is not found."""
        # Arrange
        mock_from_table.side_effect = ValueError("Invasion not found")

        with patch('src.invasion.invasion.IrusContainer.default', return_value=container):
            # Act
            response = lambda_handler(invasion_event, lambda_context)

        # Assert
        assert response["statusCode"] == 500
        assert "Error generating report" in response["body"]["url"]
```

### 4. Month Lambda Testing Pattern

The Month Lambda generates monthly statistics reports.

#### Unit Test Template

```python
"""Unit tests for Month Lambda function."""

import json
import pytest
from unittest.mock import Mock, patch
from aws_lambda_powertools.utilities.typing import LambdaContext

from irus.container import IrusContainer
from src.month.month import lambda_handler


class TestMonthLambda:
    """Test suite for Month Lambda function."""

    @pytest.fixture
    def container(self):
        """Create test container with mocked dependencies."""
        return IrusContainer.create_unit()

    @pytest.fixture
    def lambda_context(self):
        """Create mock Lambda context."""
        context = Mock(spec=LambdaContext)
        context.function_name = "test-month-function"
        return context

    @pytest.fixture
    def month_event(self):
        """Month Lambda event structure."""
        return {"month": "202403"}

    @patch('src.month.month.IrusContainer.default')
    def test_successful_month_report(self, mock_container, container, lambda_context, month_event):
        """Test successful monthly report generation."""
        # Arrange
        mock_container.return_value = container

        mock_month_stats = Mock()
        mock_month_stats.invasions = 15
        mock_month_stats.active = 20
        mock_month_stats.participation = 300
        mock_month_stats.report = ["member1", "member2", "member3"]

        mock_report = Mock()
        mock_report.msg = "https://s3.amazonaws.com/bucket/monthly-report.csv"

        with patch('src.month.month.IrusMonth.from_invasion_stats', return_value=mock_month_stats):
            with patch('src.month.month.IrusReport.from_month', return_value=mock_report):
                # Act
                response = lambda_handler(month_event, lambda_context)

        # Assert
        assert response["statusCode"] == 200
        body = response["body"]
        assert body["month"] == "202403"
        assert body["invasions"] == 15
        assert body["active"] == 20
        assert body["members"] == 3
        assert body["participation"] == 300
        assert "s3.amazonaws.com" in body["url"]
```

## Discord Event Fixtures

### Common Discord Event Structures

```python
"""Discord event fixtures for Lambda testing."""

import json
import time
from uuid import uuid4
import pytest


@pytest.fixture
def discord_ping_event():
    """Discord ping event (type 1)."""
    return {
        "body": json.dumps({"type": 1}),
        "headers": {
            "x-signature-ed25519": "test_signature",
            "x-signature-timestamp": str(int(time.time()))
        }
    }


@pytest.fixture
def discord_command_base():
    """Base Discord slash command event."""
    return {
        "body": json.dumps({
            "type": 2,
            "data": {"name": "irus", "options": []},
            "member": {"roles": ["admin_role_id"]},
            "token": f"test_token_{uuid4().hex[:8]}"
        }),
        "headers": {
            "x-signature-ed25519": "test_signature",
            "x-signature-timestamp": str(int(time.time()))
        }
    }


@pytest.fixture
def discord_help_command(discord_command_base):
    """Discord help command event."""
    body = json.loads(discord_command_base["body"])
    body["data"]["options"] = [{"name": "help"}]
    discord_command_base["body"] = json.dumps(body)
    return discord_command_base


@pytest.fixture
def discord_member_add_command(discord_command_base):
    """Discord member add command with test data."""
    timestamp = int(time.time())
    unique_id = uuid4().hex[:8]

    body = json.loads(discord_command_base["body"])
    body["data"]["options"] = [{
        "name": "member",
        "options": [{
            "name": "add",
            "options": [
                {"name": "player", "value": f"TestPlayer-{timestamp}-{unique_id}"},
                {"name": "faction", "value": "yellow"}
            ]
        }]
    }]
    discord_command_base["body"] = json.dumps(body)
    return discord_command_base


@pytest.fixture
def discord_ladder_command(discord_command_base):
    """Discord ladder upload command with test data."""
    from tests.integration.conftest import get_test_date_components

    date_components = get_test_date_components()

    body = json.loads(discord_command_base["body"])
    body["data"]["options"] = [{
        "name": "ladder",
        "options": [
            {"name": "settlement", "value": "ef"},
            {"name": "win", "value": True},
            {"name": "file1", "value": "attachment_id_123"},
            {"name": "day", "value": date_components["day"]},
            {"name": "month", "value": date_components["month"]},
            {"name": "year", "value": date_components["year"]}
        ]
    }]
    body["data"]["resolved"] = {
        "attachments": {
            "attachment_id_123": {
                "filename": "ladder.png",
                "url": "https://cdn.discordapp.com/attachments/123/456/ladder.png"
            }
        }
    }
    discord_command_base["body"] = json.dumps(body)
    return discord_command_base


@pytest.fixture
def discord_unauthorized_user(discord_command_base):
    """Discord command from unauthorized user."""
    body = json.loads(discord_command_base["body"])
    body["member"]["roles"] = ["regular_user_role"]  # Remove admin role
    body["data"]["options"] = [{"name": "member", "options": [{"name": "add", "options": []}]}]
    discord_command_base["body"] = json.dumps(body)
    return discord_command_base
```

## Testing Best Practices

### 1. Test Data Management

```python
# Always use unique identifiers for test data
timestamp = int(time.time())
unique_id = uuid4().hex[:8]
player_name = f"TestPlayer-{timestamp}-{unique_id}"

# Use 99DDHHMM pattern for dates in integration tests
date_components = get_test_date_components()
invasion_name = f"{date_components['date_string']}-ef"  # e.g., "99151228-ef"
```

### 2. Container Management

```python
# Unit tests - always use mocked container
@pytest.fixture
def container():
    return IrusContainer.create_unit()

# Integration tests - use real AWS resources
@pytest.fixture
def container(integration_container):
    return integration_container

# Set container as default for Lambda functions
IrusContainer.set_default(container)
```

### 3. Error Testing

```python
def test_lambda_error_handling(container, lambda_context, event):
    """Test Lambda error handling and logging."""
    # Arrange - cause an error condition
    container.table().get_item.side_effect = Exception("Database error")

    # Act
    response = lambda_handler(event, lambda_context)

    # Assert
    assert response["statusCode"] == 500
    assert "error" in response["body"].lower()
```

### 4. Signature Verification Testing

```python
@patch('src.bot.bot.verify_signature')
def test_signature_verification(mock_verify, lambda_context, discord_event):
    """Test Discord signature verification."""
    # Test valid signature
    mock_verify.return_value = None
    response = lambda_handler(discord_event, lambda_context)
    assert response["statusCode"] == 200

    # Test invalid signature
    from nacl.exceptions import BadSignatureError
    mock_verify.side_effect = BadSignatureError("Invalid")
    response = lambda_handler(discord_event, lambda_context)
    assert response["statusCode"] == 401
```

## Integration Testing Guidelines

### 1. AWS Resource Setup

```python
def test_lambda_with_real_aws(integration_container, lambda_context):
    """Test Lambda with real AWS resources."""
    # Container already configured with real AWS resources
    # from integration_container fixture

    # Set as default for Lambda function
    IrusContainer.set_default(integration_container)

    # Test will use real DynamoDB, S3, etc.
    response = lambda_handler(event, lambda_context)

    # Verify results in actual AWS resources
    table = integration_container.table()
    # ... verify data was written to DynamoDB
```

### 2. Cleanup Strategy

```python
# Automatic cleanup via fixture (recommended)
@pytest.fixture(autouse=True)
def cleanup_test_data(integration_container):
    yield  # Test runs here
    # Cleanup happens automatically via conftest.py

# Manual cleanup (if needed)
def cleanup_test_invasion(container, invasion_name):
    """Manually clean up test invasion data."""
    if invasion_name.startswith("99"):  # Only clean test data
        table = container.table()
        # Delete invasion and related records
```

### 3. Performance Testing

```python
def test_lambda_performance(integration_container, lambda_context, event):
    """Test Lambda performance with real resources."""
    import time

    start_time = time.time()
    response = lambda_handler(event, lambda_context)
    execution_time = time.time() - start_time

    assert response["statusCode"] == 200
    assert execution_time < 30.0  # Should complete within 30 seconds
```

## Test Organization

### Directory Structure

```
tests/
├── unit/
│   └── lambdas/
│       ├── test_bot_lambda.py
│       ├── test_invasion_lambda.py
│       ├── test_month_lambda.py
│       └── test_process_lambda.py
├── integration/
│   └── lambdas/
│       ├── test_bot_lambda_integration.py
│       ├── test_invasion_lambda_integration.py
│       ├── test_month_lambda_integration.py
│       └── test_process_lambda_integration.py
└── fixtures/
    └── discord_events.py
```

### Test Naming Conventions

```python
# Unit tests
def test_member_add_command_success()
def test_member_add_command_invalid_faction()
def test_signature_verification_failure()

# Integration tests
def test_member_add_end_to_end()
def test_ladder_upload_complete_workflow()
def test_report_generation_with_real_data()
```

This framework provides comprehensive testing coverage for all Lambda functions while maintaining consistency with the existing `IrusContainer` pattern and testing infrastructure.
