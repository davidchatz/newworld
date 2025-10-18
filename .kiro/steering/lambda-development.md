# New World Discord Bot - Lambda Development Guide

## 🔴 CRITICAL - Always Follow

### Modern Lambda Handler Pattern
- **NEVER use legacy facades** (`IrusMember`, `IrusInvasion`, `IrusLadder`) in Lambda handlers
- **ALWAYS use dependency injection** with `IrusContainer.create_production()` for production Lambda functions
- **ALWAYS separate business logic** into services - Lambda handlers should only orchestrate
- **NEVER include complex business logic** directly in Lambda handler functions

### Lambda Handler Structure
```python
from aws_lambda_powertools import Logger
from aws_lambda_powertools.utilities.typing import LambdaContext

from irus.container import IrusContainer
from irus.services.discord_command_service import DiscordCommandService

logger = Logger()

def lambda_handler(event: dict, context: LambdaContext) -> dict:
    """Modern Lambda handler with proper dependency injection."""
    try:
        # Initialize container for production environment
        container = IrusContainer.create_production()

        # Initialize service with container
        command_service = DiscordCommandService(container)

        # Delegate to service layer
        result = command_service.handle_discord_event(event)

        logger.info("Successfully processed Discord event", extra={"result": result})
        return result

    except Exception as e:
        logger.error("Failed to process Discord event", extra={"error": str(e), "event": event})
        raise
```

### Environment Variable Management for Lambda Testing
- **MUST patch environment variables BEFORE importing Lambda modules** to avoid import-time errors
- **ALWAYS use pytest fixtures** to manage environment setup for Lambda tests
- **NEVER hardcode AWS credentials** or region information in Lambda code

### Lambda Testing Environment Setup
```python
import pytest
import os
from unittest.mock import patch

@pytest.fixture(autouse=True)
def lambda_environment():
    """Set up environment variables before Lambda handler imports."""
    env_vars = {
        "AWS_DEFAULT_REGION": "ap-southeast-2",
        "ENVIRONMENT": "test",
        "LOG_LEVEL": "INFO"
    }

    with patch.dict(os.environ, env_vars, clear=False):
        yield
```

### Container Integration in Lambda Functions
```python
# CORRECT: Use container for all AWS resource access
container = IrusContainer.create_production()
logger = container.logger()
table = container.table()

# WRONG: Direct resource access
import boto3
table = boto3.resource('dynamodb').Table('some-table')
```

---

## 🟡 IMPORTANT - Usually Follow

### Lambda Function Organization

#### Handler Responsibilities
- **Event Parsing**: Extract and validate input from Lambda event
- **Service Orchestration**: Initialize and coordinate service calls
- **Response Formatting**: Format output for the calling service (Discord, Step Functions)
- **Error Handling**: Catch and log errors, return appropriate error responses

#### Service Layer Integration
```python
class DiscordCommandService:
    """Service for handling Discord command processing."""

    def __init__(self, container: IrusContainer):
        self._container = container
        self._logger = container.logger()
        self._member_repo = MemberRepository(container)
        self._invasion_repo = InvasionRepository(container)

    def handle_discord_event(self, event: dict) -> dict:
        """Process Discord event and return formatted response."""
        # Business logic implementation
        pass
```

### Lambda Testing Patterns

#### Unit Testing Lambda Handlers
```python
import pytest
from unittest.mock import Mock, patch
from src.bot.bot import lambda_handler

class TestBotLambdaHandler:
    """Unit tests for Bot Lambda handler."""

    @pytest.fixture
    def mock_container(self):
        """Create mocked container for unit testing."""
        container = Mock()
        container.logger.return_value = Mock()
        return container

    @pytest.fixture
    def discord_event(self):
        """Sample Discord event for testing."""
        return {
            "type": 1,  # PING
            "data": {"name": "irus", "options": []}
        }

    @patch('src.bot.bot.IrusContainer.create_production')
    def test_lambda_handler_ping(self, mock_container_factory, mock_container, discord_event):
        """Test Lambda handler with Discord ping event."""
        # Arrange
        mock_container_factory.return_value = mock_container

        # Act
        result = lambda_handler(discord_event, Mock())

        # Assert
        assert result["type"] == 1  # PONG response
        mock_container_factory.assert_called_once()
```

#### Integration Testing Lambda Handlers
```python
import time
from uuid import uuid4
from tests.integration.conftest import get_test_date_components

class TestBotLambdaIntegration:
    """Integration tests for Bot Lambda with real AWS resources."""

    def test_member_command_integration(self, integration_container):
        """Test member command with real DynamoDB operations."""
        # Generate unique test data
        timestamp = int(time.time())
        unique_id = uuid4().hex[:8]
        test_player = f"TestPlayer-{timestamp}-{unique_id}"

        # Create Discord event for member command
        discord_event = {
            "type": 2,  # APPLICATION_COMMAND
            "data": {
                "name": "irus",
                "options": [
                    {
                        "name": "member",
                        "options": [
                            {"name": "player", "value": test_player},
                            {"name": "faction", "value": "yellow"}
                        ]
                    }
                ]
            }
        }

        # Test Lambda handler with real AWS resources
        with patch('src.bot.bot.IrusContainer.create_production') as mock_factory:
            mock_factory.return_value = integration_container
            result = lambda_handler(discord_event, Mock())

        # Verify response format
        assert "type" in result
        assert "data" in result
```

### Error Handling in Lambda Functions

#### Structured Error Responses
```python
def lambda_handler(event: dict, context: LambdaContext) -> dict:
    """Lambda handler with proper error handling."""
    try:
        # Main processing logic
        return process_event(event)

    except ValidationError as e:
        logger.warning("Invalid input received", extra={"error": str(e), "event": event})
        return {
            "statusCode": 400,
            "body": {"error": "Invalid input", "details": str(e)}
        }

    except ServiceError as e:
        logger.error("Service error occurred", extra={"error": str(e), "event": event})
        return {
            "statusCode": 500,
            "body": {"error": "Internal service error"}
        }

    except Exception as e:
        logger.error("Unexpected error occurred", extra={"error": str(e), "event": event})
        return {
            "statusCode": 500,
            "body": {"error": "Internal server error"}
        }
```

### Lambda Performance Patterns

#### Container Reuse
```python
# Initialize container outside handler for reuse across invocations
container = None

def lambda_handler(event: dict, context: LambdaContext) -> dict:
    """Lambda handler with container reuse for performance."""
    global container

    # Initialize container once per Lambda container lifecycle
    if container is None:
        container = IrusContainer.create_production()

    # Use container for this invocation
    service = SomeService(container)
    return service.process(event)
```

#### Resource Connection Management
```python
class OptimizedService:
    """Service optimized for Lambda execution."""

    def __init__(self, container: IrusContainer):
        self._container = container
        self._logger = container.logger()
        # Lazy initialization of expensive resources
        self._table = None
        self._s3 = None

    @property
    def table(self):
        """Lazy-loaded DynamoDB table resource."""
        if self._table is None:
            self._table = self._container.table()
        return self._table
```

---

## 🟢 REFERENCE - When Relevant

### Lambda Function Migration Patterns

#### Before: Legacy Facade Pattern
```python
# OLD: Legacy facade usage in Lambda handler
from irus import IrusMember, IrusInvasion, IrusResources

def lambda_handler(event: dict, context: LambdaContext):
    # Direct facade usage with business logic in handler
    member = IrusMember.from_table(player_name)
    invasion = IrusInvasion.from_user(day, month, year, settlement, win)

    # Business logic mixed with handler logic
    if member.faction == "yellow":
        # Complex business logic here
        pass

    return {"statusCode": 200}
```

#### After: Modern Service Pattern
```python
# NEW: Modern service pattern with dependency injection
from irus.container import IrusContainer
from irus.services.member_management_service import MemberManagementService
from irus.services.invasion_workflow_service import InvasionWorkflowService

def lambda_handler(event: dict, context: LambdaContext):
    # Initialize container and services
    container = IrusContainer.create_production()
    member_service = MemberManagementService(container)
    invasion_service = InvasionWorkflowService(container)

    # Delegate to service layer
    member = member_service.get_member(player_name)
    invasion = invasion_service.create_invasion(day, month, year, settlement, win)

    return {"statusCode": 200, "data": {"invasion": invasion.name}}
```

### Discord Event Processing Patterns

#### Discord Event Structure
```python
# Discord PING event
ping_event = {
    "type": 1,
    "id": "interaction_id",
    "token": "interaction_token"
}

# Discord APPLICATION_COMMAND event
command_event = {
    "type": 2,
    "data": {
        "name": "irus",
        "options": [
            {
                "name": "member",
                "type": 1,
                "options": [
                    {"name": "player", "type": 3, "value": "PlayerName"},
                    {"name": "faction", "type": 3, "value": "yellow"}
                ]
            }
        ]
    },
    "member": {"user": {"id": "user_id", "username": "username"}},
    "token": "interaction_token"
}
```

#### Discord Response Patterns
```python
# PONG response for PING
pong_response = {"type": 1}

# Deferred response for long-running operations
deferred_response = {
    "type": 5,  # DEFERRED_CHANNEL_MESSAGE_WITH_SOURCE
    "data": {"flags": 64}  # EPHEMERAL flag
}

# Message response with content
message_response = {
    "type": 4,  # CHANNEL_MESSAGE_WITH_SOURCE
    "data": {
        "content": "Command executed successfully",
        "flags": 64  # EPHEMERAL flag
    }
}
```

### Step Functions Integration Patterns

#### Step Function Input/Output
```python
# Step Function input format
step_function_input = {
    "invasion_name": "20241215-bw",
    "file_urls": ["https://discord.com/file1.png"],
    "user_id": "discord_user_id"
}

# Step Function output format
step_function_output = {
    "statusCode": 200,
    "invasion_name": "20241215-bw",
    "processed_files": 1,
    "ladder_extracted": True,
    "report_generated": True
}
```

#### Lambda Handler for Step Functions
```python
def lambda_handler(event: dict, context: LambdaContext) -> dict:
    """Lambda handler for Step Function integration."""
    container = IrusContainer.create_production()
    logger = container.logger()

    try:
        # Extract Step Function parameters
        invasion_name = event["invasion_name"]
        file_urls = event.get("file_urls", [])

        # Process via service layer
        service = InvasionWorkflowService(container)
        result = service.process_invasion_files(invasion_name, file_urls)

        # Return Step Function compatible response
        return {
            "statusCode": 200,
            "invasion_name": invasion_name,
            "processed_files": len(file_urls),
            "success": True,
            "result": result
        }

    except Exception as e:
        logger.error("Step Function processing failed", extra={"error": str(e), "event": event})
        return {
            "statusCode": 500,
            "error": str(e),
            "success": False
        }
```

### Lambda Testing Best Practices

#### Test File Organization
```
tests/
├── unit/
│   └── lambdas/
│       ├── test_bot_lambda.py
│       ├── test_process_lambda.py
│       ├── test_invasion_lambda.py
│       └── test_month_lambda.py
├── integration/
│   └── lambdas/
│       ├── test_bot_lambda_integration.py
│       ├── test_process_lambda_integration.py
│       ├── test_invasion_lambda_integration.py
│       └── test_month_lambda_integration.py
└── fixtures/
    └── discord_events.py
```

#### Discord Event Fixtures
```python
# tests/fixtures/discord_events.py
"""Fixtures for Discord event testing."""

def create_ping_event():
    """Create Discord PING event for testing."""
    return {"type": 1, "id": "test_id", "token": "test_token"}

def create_member_command_event(player: str, faction: str):
    """Create Discord member command event for testing."""
    return {
        "type": 2,
        "data": {
            "name": "irus",
            "options": [
                {
                    "name": "member",
                    "options": [
                        {"name": "player", "value": player},
                        {"name": "faction", "value": faction}
                    ]
                }
            ]
        },
        "token": "test_token"
    }
```

#### Environment Variable Testing
```python
@pytest.fixture
def lambda_test_environment():
    """Set up Lambda testing environment variables."""
    test_env = {
        "AWS_DEFAULT_REGION": "ap-southeast-2",
        "ENVIRONMENT": "test",
        "LOG_LEVEL": "DEBUG",
        "STACK_NAME": "irus-test-stack"
    }

    with patch.dict(os.environ, test_env, clear=False):
        yield test_env
```

### Lambda Deployment Patterns

#### SAM Template Configuration
```yaml
# template.yaml - Lambda function configuration
BotFunction:
  Type: AWS::Serverless::Function
  Properties:
    CodeUri: src/bot/
    Handler: bot.lambda_handler
    Runtime: python3.12
    Timeout: 30
    MemorySize: 512
    Environment:
      Variables:
        ENVIRONMENT: !Ref Environment
        LOG_LEVEL: INFO
    Events:
      DiscordWebhook:
        Type: Api
        Properties:
          Path: /discord
          Method: post
```

#### Lambda Layer Dependencies
```yaml
# Dependencies layer for shared code
IrusLayer:
  Type: AWS::Serverless::LayerVersion
  Properties:
    LayerName: !Sub "${AWS::StackName}-irus-layer"
    ContentUri: src/layer/
    CompatibleRuntimes:
      - python3.12
    RetentionPolicy: Delete
```

### Performance Optimization

#### Cold Start Optimization
```python
# Initialize expensive resources outside handler
import boto3
from irus.container import IrusContainer

# Global initialization for container reuse
_container = None

def get_container() -> IrusContainer:
    """Get or create container instance for reuse."""
    global _container
    if _container is None:
        _container = IrusContainer.create_production()
    return _container

def lambda_handler(event: dict, context: LambdaContext) -> dict:
    """Optimized Lambda handler with container reuse."""
    container = get_container()
    # Use container for processing
```

#### Memory and Timeout Configuration
```python
# Lambda function sizing guidelines based on complexity
LAMBDA_CONFIGURATIONS = {
    "month": {"memory": 256, "timeout": 30},      # Simple aggregation
    "invasion": {"memory": 512, "timeout": 60},   # Report generation
    "process": {"memory": 1024, "timeout": 300},  # Image processing
    "bot": {"memory": 512, "timeout": 30}         # Discord commands
}
```

### Monitoring and Observability

#### Structured Logging
```python
from aws_lambda_powertools import Logger, Tracer, Metrics
from aws_lambda_powertools.metrics import MetricUnit

logger = Logger()
tracer = Tracer()
metrics = Metrics()

@tracer.capture_lambda_handler
@logger.inject_lambda_context
@metrics.log_metrics
def lambda_handler(event: dict, context: LambdaContext) -> dict:
    """Lambda handler with full observability."""

    # Add custom metrics
    metrics.add_metric(name="InvocationCount", unit=MetricUnit.Count, value=1)

    # Structured logging
    logger.info("Processing event", extra={"event_type": event.get("type")})

    try:
        result = process_event(event)
        metrics.add_metric(name="SuccessCount", unit=MetricUnit.Count, value=1)
        return result

    except Exception as e:
        logger.error("Processing failed", extra={"error": str(e)})
        metrics.add_metric(name="ErrorCount", unit=MetricUnit.Count, value=1)
        raise
```

#### CloudWatch Alarms
```yaml
# CloudWatch alarm for Lambda errors
LambdaErrorAlarm:
  Type: AWS::CloudWatch::Alarm
  Properties:
    AlarmName: !Sub "${AWS::StackName}-lambda-errors"
    AlarmDescription: "Lambda function error rate"
    MetricName: Errors
    Namespace: AWS/Lambda
    Statistic: Sum
    Period: 300
    EvaluationPeriods: 2
    Threshold: 5
    ComparisonOperator: GreaterThanThreshold
    Dimensions:
      - Name: FunctionName
        Value: !Ref BotFunction
```

### Migration Checklist

#### Pre-Migration Checklist
- [ ] All required services are implemented and tested
- [ ] Lambda handler follows modern container pattern
- [ ] Business logic is extracted to service layer
- [ ] Comprehensive unit and integration tests exist
- [ ] Environment variables are properly configured
- [ ] Error handling follows established patterns

#### Post-Migration Validation
- [ ] Lambda function deploys successfully
- [ ] All existing functionality works as expected
- [ ] Performance meets or exceeds legacy implementation
- [ ] Error handling and logging work correctly
- [ ] Monitoring and alerting are configured
- [ ] Rollback procedure is tested and documented
