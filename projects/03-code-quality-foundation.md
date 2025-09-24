# Project: Code Quality Foundation

## Overview
Modernize the `irus` package with type safety, comprehensive testing, and improved architecture to establish a solid foundation for future development. Convert core models to Pydantic, implement modern testing patterns, and improve code organization while maintaining Lambda layer compatibility.

## Context
- **Current State**: Mixed dataclasses/plain classes, limited type hints, sparse test coverage
- **Target State**: Pydantic models with full type safety, comprehensive test suite with mocking, clean architecture
- **Scope**: Focus on `src/layer/irus` package - Lambda functions addressed later
- **Branch**: All changes to be made on branch `rework-202509`

## Requirements
### Functional Requirements
- [ ] All core models use Pydantic with full type annotations
- [ ] Comprehensive test suite with >90% coverage for models and services
- [ ] Modern testing patterns: fixtures, parametrize, mocking for AWS services
- [ ] Clean separation of concerns: models, services, adapters
- [ ] Maintain Lambda layer deployment compatibility
- [ ] All existing functionality preserved during refactor

### Technical Requirements
- [ ] Add Pydantic as project dependency
- [ ] Add modern testing dependencies (pytest-mock, moto, factory-boy)
- [ ] Move existing tests to `tests/legacy/` for reference
- [ ] Implement proper mocking for DynamoDB, S3, and Textract
- [ ] Type checking with mypy integration
- [ ] Maintain current import patterns in `__init__.py` for backward compatibility

### Quality Requirements
- [ ] All models have comprehensive docstrings and examples
- [ ] Test coverage reports generated and tracked
- [ ] Type safety verified with mypy
- [ ] Performance regression tests for critical paths
- [ ] Clear migration path documented for future Lambda function updates

## Tasks
### Phase 1: Foundation Setup
- [ ] Move existing tests to `tests/legacy/` directory
- [ ] Add Pydantic and modern testing dependencies to project
- [ ] Configure pytest with modern patterns and fixtures
- [ ] Set up test coverage reporting and CI integration
- [ ] **REVIEW POINT**: User review and approval of Phase 1 changes

### Phase 2: Package Restructure (Optional - Defer if Complex)
- [ ] Evaluate current vs proposed structure (models/services/adapters)
- [ ] Create new directory structure if beneficial
- [ ] Move files and update imports systematically
- [ ] Update `__init__.py` to maintain API compatibility
- [ ] **REVIEW POINT**: User review and approval of Phase 2 changes

### Phase 3: Core Models Modernization with Repository Pattern
**Architecture Decision**: Implement Repository Pattern to separate data models from AWS resource access, enabling proper unit testing and clean architecture.

#### Phase 3A: Pure Pydantic Models
- [ ] Convert `IrusMember` to pure Pydantic model (no AWS calls)
- [ ] Convert `IrusInvasion` to pure Pydantic model with validation
- [ ] Convert remaining model classes (`IrusLadderRank`, `IrusLadder`, etc.) to pure models
- [ ] Ensure all models are pure data objects with validation only

#### Phase 3B: Repository Layer Implementation
- [ ] Create `repositories/` directory structure
- [ ] Implement `MemberRepository` with all CRUD operations
- [ ] Implement `InvasionRepository` with query methods
- [ ] Implement `LadderRepository` for ranking data
- [ ] Create base `Repository` class for common patterns

#### Phase 3C: Service Layer Refactoring
- [ ] Update service classes to use repositories instead of direct model calls
- [ ] Refactor `process.py` to use repository pattern
- [ ] Refactor `report.py` and `month.py` for repository access
- [ ] Maintain backward compatibility in public APIs

#### Phase 3D: Comprehensive Testing
- [ ] Write unit tests for pure models (validation, serialization)
- [ ] Write unit tests for repositories with mocked DynamoDB
- [ ] Write integration tests for service layer with mocked repositories
- [ ] Achieve >90% test coverage for models and repositories
- [ ] **REVIEW POINT**: User review and approval of Phase 3 changes

### Phase 4: Service Layer & Adapters
- [ ] Create DynamoDB adapter layer with proper mocking support
- [ ] Create S3 and Textract adapter abstractions
- [ ] Refactor service classes to use new models and adapters
- [ ] Write integration tests for service layer with mocked dependencies
- [ ] **REVIEW POINT**: User review and approval of Phase 4 changes

### Phase 5: Testing & Validation
- [ ] Achieve >90% test coverage for all models and core services
- [ ] Run full regression testing against existing functionality
- [ ] Performance testing to ensure no degradation
- [ ] Documentation updates for new patterns and architecture
- [ ] **REVIEW POINT**: User review and approval of Phase 5 changes
- [ ] **COMMIT**: Add and commit all changes

## Files/Areas Involved
### Pure Models (Phase 3A)
- `src/layer/irus/models/member.py` - Pure Member data model
- `src/layer/irus/models/invasion.py` - Pure Invasion data model
- `src/layer/irus/models/ladderrank.py` - Pure Ladder ranking model
- `src/layer/irus/models/ladder.py` - Pure Ladder data model
- `src/layer/irus/models/__init__.py` - Model exports

### Repository Layer (Phase 3B)
- `src/layer/irus/repositories/base.py` - Base repository class
- `src/layer/irus/repositories/member.py` - Member data access
- `src/layer/irus/repositories/invasion.py` - Invasion data access
- `src/layer/irus/repositories/ladder.py` - Ladder data access
- `src/layer/irus/repositories/__init__.py` - Repository exports

### Service Classes (Phase 3C - Updated)
- `src/layer/irus/process.py` - File processing logic (updated for repositories)
- `src/layer/irus/report.py` - Report generation (updated for repositories)
- `src/layer/irus/month.py` - Monthly reporting (updated for repositories)
- `src/layer/irus/posttable.py` - Table posting (updated for repositories)

### Legacy Models (Deprecated but maintained for compatibility)
- `src/layer/irus/member.py` - Legacy member model (facade to new structure)
- `src/layer/irus/invasion.py` - Legacy invasion model (facade to new structure)
- `src/layer/irus/ladderrank.py` - Legacy ladder model (facade to new structure)

### Infrastructure
- `src/layer/irus/environ.py` - Environment and resources
- `src/layer/irus/utilities.py` - Shared utilities
- `src/layer/irus/__init__.py` - Package exports

### Testing
- `tests/` - New comprehensive test suite
- `tests/legacy/` - Moved existing tests
- `pytest.ini` - Test configuration
- `pyproject.toml` - Dependencies and tool configuration

## Success Criteria
- [ ] All core models are Pydantic-based with full type safety
- [ ] Test coverage >90% for models and services
- [ ] Zero regression in existing functionality
- [ ] Clean separation between models, services, and external dependencies
- [ ] Comprehensive mocking for all AWS service interactions
- [ ] Type checking passes with mypy
- [ ] Lambda layer deployment remains functional
- [ ] Clear patterns established for future development

## Dependencies
- Completed environment-aware resource naming (Project 02)
- Modern tooling foundation established (Project 01)
- Access to AWS services for integration testing
- Understanding of current model usage patterns

## Architecture Decision: Repository Pattern

### Problem
The current architecture has models tightly coupled to AWS resources:
- Models import `environ.py` → AWS resource initialization at import time
- Direct AWS calls in model methods (`table.put_item()`, `table.get_item()`)
- Impossible to unit test without AWS credentials and resources
- Violates Dependency Inversion Principle

### Solution: Repository Pattern
- **Pure Models**: Pydantic models with only data validation, no AWS calls
- **Repository Layer**: Separate classes handle all database operations
- **Dependency Injection**: Repositories can be mocked for testing
- **Clean Architecture**: Clear separation of concerns

### Benefits
- **Testable**: Models become pure data objects, easily unit tested
- **Maintainable**: Clear separation between data and persistence logic
- **Future-proof**: Easy to swap DynamoDB for other storage solutions
- **AWS SDK v2 Ready**: Isolated changes when AWS APIs evolve

## Risks & Considerations
- Large refactor could introduce subtle bugs - comprehensive testing essential
- Pydantic may change serialization behavior - validate carefully
- Performance impact of Pydantic validation in Lambda environment
- Breaking changes to internal APIs require careful coordination
- **CRITICAL**: Maintain backward compatibility for Lambda functions during transition
- **NEW**: Repository pattern adds indirection - ensure performance testing
- **NEW**: More complex dependency management - document injection patterns

## Notes
- Focus on `irus` package only - Lambda functions updated in future project
- Prioritize models over services - establish patterns then apply consistently
- Use modern Python patterns (3.11+ features where beneficial)
- Consider async patterns for future AWS SDK v2 migration
- Document architectural decisions for future team members

---

## Implementation Log
### [Date] - [Status Update]
- Progress made
- Issues encountered
- Next steps
