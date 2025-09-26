# Project 05: Integration Testing Expansion

## Status: Planning
**Priority**: High
**Est. Effort**: Medium (1-2 weeks)
**Dependencies**: Project 03 (Code Quality Foundation)

## Overview

Develop focused integration tests that validate core functionality against real AWS resources. This project aims to build confidence in the modernized architecture by testing key workflows with actual DynamoDB, S3, and other AWS services in the development environment.

## Objectives

### Primary Goal
Create a solid foundation of integration tests that validate core system functionality with real AWS resources, ensuring the modernized architecture works correctly in practice.

### Secondary Goals
- Establish patterns for integration testing with AWS services
- Validate the container and repository patterns work with real dependencies
- Create test data management strategies for AWS resources
- Build confidence for future modernization efforts (Project 06)

## Scope

### In Scope: Core Functionality Integration Tests
- **DynamoDB Integration**: Repository CRUD operations with real tables
- **S3 Integration**: File operations for ladder images and reports
- **Repository Pattern**: Validate modern repositories work with AWS
- **Container System**: Dependency injection with real AWS clients
- **Service Layer**: Business logic with real AWS dependencies
- **Monthly Reporting**: Statistical calculations with real data

### Out of Scope (for this project)
- **Textract**: Costs money, will use existing processed data
- **Step Functions**: Requires Lambda functions, defer to end-to-end tests
- **Lambda Functions**: Not touching Lambda layer yet
- **Discord Integration**: End-to-end testing project
- **Performance/Load Testing**: Future optimization project

## Test Categories

**Note**: All code follows STYLE_GUIDE.md patterns including container injection, Arrange-Act-Assert structure, and comprehensive documentation.

### 1. Repository Integration Tests
```python
# tests/integration/test_member_repository_integration.py
import pytest
from irus.container import IrusContainer
from irus.repositories.member import MemberRepository

class TestMemberRepositoryIntegration:
    @pytest.fixture
    def repository(self, integration_container):
        return MemberRepository(integration_container)

    def test_create_and_retrieve_member(self, repository, test_member_data):
        """Test full member lifecycle with real DynamoDB."""
        # Arrange - covered by fixtures
        # Act
        created_member = repository.create_from_user_input(**test_member_data)
        retrieved_member = repository.get_by_player(created_member.player)
        # Assert
        assert retrieved_member is not None
        assert retrieved_member.player == created_member.player
        # Cleanup
        repository.delete_by_player(created_member.player)
```

### 2. Service Layer Integration Tests
```python
# tests/integration/test_member_management_service_integration.py
from irus.services.member_management import MemberManagementService

class TestMemberManagementServiceIntegration:
    @pytest.fixture
    def service(self, integration_container):
        return MemberManagementService(integration_container)

    def test_update_invasions_for_new_member(self, service, test_member_data):
        """Test member invasion history updates with real data."""
        # Implementation details provided during development
```

### 3. Container & Dependency Integration
```python
# tests/integration/test_container_integration.py
class TestContainerIntegration:
    def test_production_container_creates_real_resources(self):
        """Validate container creates working AWS clients"""

    def test_repository_with_real_container(self):
        """Test repositories work with production container"""
```

## Test Environment Setup

### AWS Environment
- **Target**: Development environment (`irus-dev-*` resources)
- **Credentials**: Use existing profile (`irus-202509-dev`)
- **Region**: `ap-southeast-2` (as per CLAUDE.md)

### Test Data Strategy - **Use Production Data Copies with 9999 Date Range**
- **Source**: Copy subset of real production data for testing
- **Benefits**: Realistic patterns, edge cases, no Textract costs, existing processed ladder data
- **Isolation**: Use year 9999 (maximum allowed) to avoid conflicts with production queries
- **Date Mapping**: Map production dates to 9999 equivalents (e.g., `20240301` → `99990301`)
- **Cleanup**: Tests clean up all 9999-dated records in teardown
- **Examples**:
  ```python
  # Production: "20240301-bw" → Test: "99990301-bw"
  # Production: "20240315-ef" → Test: "99990315-ef"
  TEST_INVASIONS = ["99990301-bw", "99990315-ef"]     # Maps to real invasion data
  TEST_MEMBERS = ["RealPlayerName1", "RealPlayerName2"]  # Real member names
  TEST_MONTHLY = "999903"  # March 9999 for monthly data
  ```

### Configuration
```python
# tests/integration/conftest.py
import time
import pytest
from irus.container import IrusContainer

@pytest.fixture(scope="session")
def integration_container():
    """Container configured for integration testing with real AWS."""
    return IrusContainer.create_production()

@pytest.fixture
def test_member_data():
    """Generate unique test member data using 9999 date range."""
    timestamp = int(time.time())
    return {
        "player": f"TestPlayer-{timestamp}",
        "faction": "yellow",
        "start": 99990101,  # January 1, 9999
        "admin": False,
        "salary": True,
        "notes": "Integration test member"
    }
```

### Test Execution
```bash
# 1. Setup test data
cd invasions/
AWS_PROFILE=irus-202509-dev uv run python -m tests.utilities.production_data_copier --setup-integration-tests

# 2. Run integration tests
AWS_PROFILE=irus-202509-dev uv run pytest tests/integration/ -v

# 3. Cleanup test data
AWS_PROFILE=irus-202509-dev uv run python -m tests.utilities.production_data_copier --cleanup
```

## Production Data Utility

### Purpose
Copy production data to support integration testing and production issue debugging.

### Implementation
```python
# tests/utilities/production_data_copier.py
from typing import Optional
from irus.container import IrusContainer
from irus.repositories.member import MemberRepository
from irus.repositories.invasion import InvasionRepository

class ProductionDataCopier:
    """Utility to copy production data for testing and debugging."""

    def __init__(self, container: Optional[IrusContainer] = None):
        self._container = container or IrusContainer.default()
        self._logger = self._container.logger()
        self._member_repo = MemberRepository(self._container)
        self._invasion_repo = InvasionRepository(self._container)

    def copy_recent_invasions(self, count: int = 10) -> list[str]:
        """Copy recent invasions mapped to 9999 date range."""
        self._logger.info(f"Copying {count} recent invasions to test data")
        # Implementation: Query production, map dates to 9999 range

    def copy_active_members(self, count: int = 20) -> list[str]:
        """Copy active members with 9999 start dates."""
        self._logger.info(f"Copying {count} active members to test data")
        # Implementation: Copy member data, adjust start dates to 9999

    def cleanup_test_data(self) -> None:
        """Remove all 9999-dated test records safely."""
        # Implementation: Delete only records with 9999 dates
```

### CLI Interface
```bash
# Copy standard test dataset
python -m tests.utilities.production_data_copier --setup-integration-tests

# Copy specific invasion for debugging
python -m tests.utilities.production_data_copier --copy-invasion "99990315-bw" --debug-mode

# Cleanup all test data
python -m tests.utilities.production_data_copier --cleanup
```

### Use Cases
1. **Integration Testing**: Standard dataset for running tests
2. **Issue Debugging**: Copy specific problematic records for investigation
3. **Test Data Refresh**: Update test dataset with recent production patterns
4. **Development Support**: Developers can quickly get realistic data

## Implementation Approach

### Week 1: Foundation & Repositories
- **Production Data Utility**: Build copying tool with 9999 date mapping
- **Repository Tests**: Member and Invasion repositories with real DynamoDB
- **Container Integration**: Validate dependency injection with AWS clients
- **Test Infrastructure**: Fixtures, cleanup, and execution patterns

### Week 2: Services & Documentation
- **Service Integration**: Member management and monthly reporting services
- **Cross-service Workflows**: Multi-repository interactions
- **S3 Integration**: File operations for ladder data and reports
- **Documentation**: Test patterns and execution guidelines

### Priority Order
1. **Member Repository** (foundation for all other tests)
2. **Invasion Repository** (core workflow validation)
3. **Production Data Utility** (enables realistic test data)
4. **Service Layer Tests** (business logic validation)

## Test Data Strategy

### Core Strategy: **Production Data Copies with Year 9999**
- **Source**: Copy subset of real production data
- **Date Isolation**: Map production dates to year 9999 (e.g., `20240301` → `99990301`)
- **Benefits**: Realistic patterns, no Textract costs, existing processed data
- **Compatibility**: Works with all existing `begins_with(date)` queries

### Definitions
- **"Recent Invasions"**: Last 30 days or most recent 10 invasions from production
- **"Active Members"**: Members who participated in at least 1 invasion in the last 60 days

### Examples
```python
# Production → Test mapping
"20240301-bw" → "99990301-bw"
"20240315-ef" → "99990315-ef"
TEST_MONTHLY = "999903"  # March 9999 monthly data
```

## Success Criteria

- [ ] **Production data copying utility** built and documented
- [ ] Repository pattern validated with real DynamoDB operations
- [ ] Service layer works correctly with AWS dependencies
- [ ] Container system properly manages real AWS resources
- [ ] Test data management strategy established with realistic production data
- [ ] Core member and invasion workflows validated
- [ ] Error handling works with real AWS error responses
- [ ] S3 integration tests with ladder images/reports
- [ ] Utility can copy specific records for production issue debugging
- [ ] Documentation and patterns for future integration tests

## Code Standards

### STYLE_GUIDE.md Compliance
All code follows **STYLE_GUIDE.md** patterns: container injection, Arrange-Act-Assert testing, comprehensive documentation, and service layer architecture.

### Single Deviation: Year 9999 Test Data
- **Reason**: Prevents conflicts with production `begins_with(date)` queries
- **Impact**: No code changes required, full query compatibility maintained

## Dependencies

### Prerequisites
- **Project 03**: Code Quality Foundation (linting, formatting, **STYLE_GUIDE.md**)
- **Project 04**: Test Coverage Expansion (comprehensive test suite)

### Follow-up Projects
- **Project 06**: Comprehensive Code Modernization (benefits from integration test safety net)

## Next Steps

Once you clarify the scope and approach, I can:
1. Create the specific test files and structure
2. Set up the integration test configuration
3. Implement the core test cases
4. Document the integration testing patterns

What aspects would you like me to focus on first?
