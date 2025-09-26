# Integration Testing Guide

This directory contains integration tests that validate core system functionality against real AWS resources in the development environment.

## Overview

Integration tests verify that:
- Repository pattern works with real DynamoDB
- Service layer coordinates multiple AWS operations correctly
- Container dependency injection provides working AWS clients
- S3 file operations function with real buckets
- Year 9999 test data isolation prevents production conflicts

## Test Strategy: SAM-Discovered Resources + Year 9999 Data Isolation

Integration tests use two key strategies for safe testing:

### 1. SAM Resource Discovery
- **Container Method**: `IrusContainer.create_integration(aws_resources)`
- **Resource Discovery**: Uses SAM CLI to discover dev environment resources
- **Safety Checks**: Validates resources contain "irus-dev" to prevent production access
- **Environment Variables**: Sets env vars from discovered resources, then calls `create_production`

### 2. Year 9999 Data Isolation
- **Test invasions**: `99990301-test` instead of `20240301-bw`
- **Test members**: Start dates like `99990101` (January 1, 9999)
- **Monthly data**: `999903` for March 9999
- **Benefit**: Compatible with all existing `begins_with(date)` queries
- **Cleanup**: All 9999-dated records are automatically removed after tests

## Running Integration Tests

### Prerequisites

1. **AWS Credentials**: Configure the development profile
   ```bash
   export AWS_PROFILE=irus-202509-dev
   export AWS_REGION=ap-southeast-2
   ```

2. **Dependencies**: Install test dependencies
   ```bash
   cd invasions/
   uv sync
   ```

### Execution Commands

```bash
# Run all integration tests
cd invasions/
AWS_PROFILE=irus-202509-dev uv run pytest tests/integration/ -v

# Run specific test category
AWS_PROFILE=irus-202509-dev uv run pytest tests/integration/test_member_repository_integration.py -v

# Run with detailed output
AWS_PROFILE=irus-202509-dev uv run pytest tests/integration/ -v -s --tb=short

# Setup test data (if needed manually)
AWS_PROFILE=irus-202509-dev uv run python -m tests.utilities.production_data_copier --setup-integration-tests

# Cleanup test data (automatic via fixtures)
AWS_PROFILE=irus-202509-dev uv run python -m tests.utilities.production_data_copier --cleanup
```

## Test Categories

### 1. Repository Integration (`test_*_repository_integration.py`)

Tests repository CRUD operations with real DynamoDB:

- **Member Repository**: Player management, queries, updates
- **Invasion Repository**: Invasion lifecycle, date-based queries
- **Data Validation**: Real DynamoDB constraints and error handling

**Example:**
```python
def test_create_and_retrieve_member(self, repository, test_member_data):
    created_member = repository.create_from_user_input(**test_member_data)
    retrieved_member = repository.get_by_player(created_member.player)
    assert retrieved_member.player == created_member.player
```

### 2. Container Integration (`test_container_integration.py`)

Tests dependency injection with real AWS clients:

- **Resource Creation**: Validates container creates working AWS services
- **Resource Sharing**: Multiple repositories share container resources
- **Error Handling**: AWS service errors are handled gracefully

**Example:**
```python
def test_production_container_creates_real_resources(self, integration_container):
    dynamodb = integration_container.dynamodb()
    s3_client = integration_container.s3()
    assert dynamodb is not None and s3_client is not None
```

### 3. Service Integration (`test_*_service_integration.py`)

Tests business logic coordination across AWS services:

- **Member Management**: Cross-repository operations
- **Performance**: Real AWS latency characteristics
- **Business Logic**: End-to-end workflows with real dependencies

**Example:**
```python
def test_update_invasions_for_new_member(self, service, test_member_data):
    result = service.update_invasions_for_new_member(test_member)
    assert "success" in result.lower()
```

### 4. S3 Integration (`test_s3_integration.py`)

Tests file operations with real S3 bucket:

- **File Operations**: Upload, download, delete with real latency
- **Metadata**: S3 object metadata and tagging
- **Large Files**: Performance with realistic file sizes
- **Error Handling**: Real S3 error responses

**Example:**
```python
def test_s3_put_and_get_object(self, s3_client, bucket_name, test_file_key):
    s3_client.put_object(Bucket=bucket_name, Key=test_file_key, Body=test_data)
    response = s3_client.get_object(Bucket=bucket_name, Key=test_file_key)
    assert response['Body'].read() == test_data
```

## Test Fixtures and Utilities

### Core Fixtures

- **`integration_container`**: Integration container with SAM-discovered dev resources
- **`test_member_data`**: Unique member data with 9999 dates
- **`test_invasion_data`**: Unique invasion data with 9999 dates
- **`cleanup_test_data`**: Automatic cleanup after each test

### Production Data Utility

The `ProductionDataCopier` utility supports:

```python
# Copy standard test dataset
copier.setup_integration_test_dataset()

# Copy specific invasion for debugging
copier.copy_specific_invasion("20240315-bw", debug_mode=True)

# Clean up all test data
copier.cleanup_test_data()
```

**CLI Usage:**
```bash
# Setup integration test data
python -m tests.utilities.production_data_copier --setup-integration-tests

# Copy specific invasion for debugging
python -m tests.utilities.production_data_copier --copy-invasion "20240315-bw" --debug-mode

# Cleanup all test data
python -m tests.utilities.production_data_copier --cleanup
```

## Test Data Management

### Automatic Cleanup

Every test automatically cleans up its 9999-dated records via the `cleanup_test_data` fixture:

```python
@pytest.fixture(autouse=True)
def cleanup_test_data(integration_container):
    yield  # Run the test
    # Cleanup happens here automatically
    copier = ProductionDataCopier(integration_container)
    copier.cleanup_test_data()
```

### Test Isolation

- **Unique IDs**: Each test uses timestamp-based unique identifiers
- **Date Isolation**: Year 9999 prevents conflicts with production queries
- **Parallel Safe**: Tests can run in parallel without data conflicts

### Production Data Copying

For realistic test scenarios, copy production patterns to year 9999:

```python
# Production: "20240301-bw" → Test: "99990301-bw"
# Production: "20240315-ef" → Test: "99990315-ef"
# Monthly: "202403" → Test: "999903"
```

## Debugging Integration Tests

### Common Issues

1. **AWS Credentials**: Ensure `AWS_PROFILE` is set correctly
2. **Permissions**: Verify access to dev DynamoDB table and S3 bucket
3. **Test Data**: Use `--cleanup` if tests fail due to leftover data
4. **Timeouts**: Integration tests are slower than unit tests

### Debug Commands

```bash
# Verify AWS access
AWS_PROFILE=irus-202509-dev aws sts get-caller-identity

# Check DynamoDB table
AWS_PAGER="" AWS_PROFILE=irus-202509-dev aws dynamodb describe-table --table-name irus-dev-table

# Check S3 bucket
AWS_PAGER="" AWS_PROFILE=irus-202509-dev aws s3 ls s3://irus-dev-154744860445-ap-southeast-2/

# Manual cleanup if needed
AWS_PROFILE=irus-202509-dev uv run python -m tests.utilities.production_data_copier --cleanup
```

### Test-Specific Debugging

```bash
# Run single test with full output
AWS_PROFILE=irus-202509-dev uv run pytest tests/integration/test_member_repository_integration.py::TestMemberRepositoryIntegration::test_create_and_retrieve_member -v -s

# Debug with pdb
AWS_PROFILE=irus-202509-dev uv run pytest tests/integration/ --pdb

# Capture logs
AWS_PROFILE=irus-202509-dev uv run pytest tests/integration/ -v -s --log-cli-level=INFO
```

## Best Practices

### Writing Integration Tests

1. **Use Fixtures**: Leverage provided fixtures for consistency
2. **Unique Data**: Generate unique test data to avoid conflicts
3. **Error Testing**: Test both success and failure scenarios
4. **Cleanup**: Rely on automatic cleanup, don't implement manual cleanup
5. **Performance**: Accept that integration tests are slower than unit tests

### Test Organization

```python
class TestRepositoryIntegration:
    @pytest.fixture
    def repository(self, integration_container):
        return SomeRepository(integration_container)

    def test_basic_crud_operations(self, repository, test_data):
        # Arrange - use fixture data
        # Act - perform repository operation
        # Assert - verify results with real AWS
```

### Avoiding Common Pitfalls

- **Don't mock AWS**: These are integration tests, use real services
- **Don't hardcode dates**: Use 9999 date fixtures for isolation
- **Don't skip cleanup**: Let automatic cleanup handle test data removal
- **Don't assume fast execution**: Integration tests have network latency

## CI/CD Integration

Integration tests are designed to run in CI/CD environments:

```yaml
# Example CI configuration
- name: Run Integration Tests
  env:
    AWS_PROFILE: irus-202509-dev
    AWS_REGION: ap-southeast-2
  run: |
    cd invasions/
    uv run pytest tests/integration/ -v --tb=short
```

## Container Usage Patterns

Understanding when to use each container creation method:

### `IrusContainer.create_test()`
- **Purpose**: Unit tests with mocked dependencies
- **When**: Testing business logic in isolation
- **Resources**: Mock objects (no real AWS calls)
- **Example**: Repository pattern tests, service logic validation

### `IrusContainer.create_production()`
- **Purpose**: Production Lambda functions
- **When**: Running in AWS Lambda environment
- **Resources**: Real AWS clients from environment variables
- **Example**: Lambda handlers, deployed application code

### `IrusContainer.create_integration(aws_resources)`
- **Purpose**: Integration tests with real AWS resources
- **When**: Validating end-to-end functionality in dev environment
- **Resources**: Real AWS clients from SAM-discovered resources
- **Example**: Repository integration, service coordination, cross-AWS operations

## Future Enhancements

This integration test foundation supports future extensions:

- **End-to-end tests** with Lambda functions
- **Performance testing** with realistic data volumes
- **Multi-environment testing** (dev, staging)
- **Monitoring integration** with test metrics collection

The year 9999 isolation strategy and container-based architecture provide a solid foundation for expanding integration test coverage as the system evolves.
