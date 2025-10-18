# Lambda Modernization Roadmap

## Overview

This document outlines the planned modernization of Lambda functions to use the modern architecture (models, repositories, services) established in Projects 03-06. The goal is to migrate Lambda handlers from legacy facades to modern services while maintaining reliability and performance.

## Context

### Current State
- **Modern Foundation**: Complete with Pydantic models, repository pattern, service layer, and IoC container
- **Legacy Facades**: Backward-compatible facades in `member.py`, `invasion.py`, `ladder.py`
- **Lambda Functions**: Still using legacy facades and direct model imports
- **Test Coverage**: 468 tests (453 passing) with 69.89% coverage for modern architecture

### Target State
- Lambda functions use modern repositories and services via dependency injection
- Comprehensive Lambda integration testing
- End-to-end testing covering Discord → Lambda → Database workflows
- Legacy facades removed once migration is complete
- Performance maintained or improved

## Project Series

### **Project 07: Lambda Function Assessment & Planning**
**Status**: Planned
**Priority**: High
**Effort**: Small (1 week)
**Dependencies**: Project 06 (Comprehensive Modernization)

#### Objectives
- Audit all Lambda functions and identify current dependencies
- Map Lambda functions to modern services and repositories
- Create migration strategy with minimal risk
- Establish Lambda testing patterns

#### Key Tasks
- **Lambda Inventory**: Document all handlers in `src/bot/` and their imports
- **Dependency Mapping**: Map current facade usage to modern services
  - `member.py` usage → `MemberRepository` + `MemberManagementService`
  - `invasion.py` usage → `InvasionRepository` + related services
  - `ladder.py` usage → `LadderRepository` + image processing services
- **Risk Assessment**: Identify high-risk migrations and mitigation strategies
- **Testing Strategy**: Design Lambda integration testing approach
- **Migration Templates**: Create standardized patterns for Lambda modernization

#### Deliverables
- Lambda function inventory with dependency analysis
- Migration roadmap with risk assessment
- Lambda testing framework design
- Modernization templates and patterns

---

### **Project 08: Lambda Integration Testing Infrastructure**
**Status**: Planned
**Priority**: High
**Effort**: Medium (2 weeks)
**Dependencies**: Project 07

#### Objectives
- Establish testing patterns for Lambda functions with modern architecture
- Create test fixtures for Lambda event simulation
- Build integration test suite for Lambda + modern services
- Enable safe Lambda modernization through comprehensive testing

#### Key Tasks
- **Testing Framework**: Set up Lambda testing using `moto` and modern container patterns
- **Event Fixtures**: Create Discord event fixtures and test data generators
- **Integration Tests**: Implement Lambda integration tests with real AWS services
- **CI/CD Integration**: Ensure Lambda tests run in deployment pipeline
- **Documentation**: Update steering docs with Lambda testing patterns

#### Technical Approach
```python
# Lambda integration test pattern
def test_member_registration_lambda():
    # Arrange - Use integration container with real AWS
    container = IrusContainer.create_integration(aws_resources, stack_name)

    # Act - Invoke Lambda with Discord event
    response = lambda_handler(discord_member_event, context)

    # Assert - Verify database changes and Discord response
    member_repo = MemberRepository(container)
    assert member_repo.get_by_player("TestPlayer") is not None
```

#### Deliverables
- Lambda testing framework with modern container integration
- Comprehensive test fixtures for Discord events
- Integration test suite covering key Lambda workflows
- Updated testing documentation and patterns

---

### **Project 09: Core Lambda Function Modernization**
**Status**: Planned
**Priority**: High
**Effort**: Large (3-4 weeks)
**Dependencies**: Project 08

#### Objectives
- Modernize Lambda handlers to use repositories and services
- Maintain backward compatibility during transition
- Achieve comprehensive test coverage for Lambda layer
- Improve Lambda performance and maintainability

#### Implementation Phases

##### Phase 9A: Member Management Lambdas (Week 1)
- Update member registration/update handlers
- Migrate to `MemberRepository` + `MemberManagementService`
- Implement comprehensive Lambda tests
- Performance validation

##### Phase 9B: Invasion Tracking Lambdas (Week 1-2)
- Modernize invasion creation/update handlers
- Use `InvasionRepository` + related services
- Test invasion workflow end-to-end
- Validate reporting functionality

##### Phase 9C: Ladder Processing Lambdas (Week 2-3)
- Update image processing and ladder ranking handlers
- Integrate `LadderRepository` + image processing services
- Test Textract integration with modern services
- Performance optimization for image processing

##### Phase 9D: Reporting Lambdas (Week 3-4)
- Modernize monthly and custom report handlers
- Use `MonthlyReportService` and report generation services
- Test report generation workflows
- Validate Discord message formatting

#### Modern Lambda Pattern
```python
def lambda_handler(event, context):
    """Modern Lambda handler using dependency injection."""
    try:
        # Use production container with real AWS resources
        container = IrusContainer.create_production()
        service = MemberManagementService(container)

        # Parse Discord event
        discord_data = parse_discord_event(event)

        # Use service layer for business logic
        result = service.register_member(
            player=discord_data['player'],
            faction=discord_data['faction']
        )

        # Return Discord-formatted response
        return format_discord_response(result)

    except Exception as e:
        logger.error(f"Lambda execution failed: {e}")
        return format_error_response(str(e))
```

#### Deliverables
- All Lambda functions modernized to use repositories/services
- Comprehensive Lambda test coverage (>90%)
- Performance benchmarks showing no regression
- Updated Lambda deployment and monitoring

---

### **Project 10: End-to-End Testing & Discord Integration**
**Status**: Planned
**Priority**: Medium
**Effort**: Medium (2-3 weeks)
**Dependencies**: Project 09

#### Objectives
- Create comprehensive end-to-end tests simulating real Discord workflows
- Test complete user journeys from Discord command to database
- Validate Step Functions and Lambda orchestration
- Ensure system reliability under realistic conditions

#### Key Tasks
- **Discord Bot Testing**: Build framework for testing Discord interactions
- **User Journey Tests**: Complete workflows (registration, invasion reporting, ladder updates)
- **Step Function Testing**: Validate orchestration and error handling
- **Performance Testing**: Load testing for realistic Discord usage
- **Monitoring Integration**: Ensure proper logging and alerting

#### Test Scenarios
1. **Member Registration Flow**: Discord command → Lambda → DynamoDB → Discord response
2. **Invasion Reporting**: Screenshot upload → Textract → Data processing → Database update
3. **Monthly Reports**: Scheduled trigger → Data aggregation → Report generation → Discord delivery
4. **Error Handling**: Invalid inputs, AWS service failures, timeout scenarios

#### Deliverables
- End-to-end test suite covering major user workflows
- Performance benchmarks and load testing results
- Step Function integration tests
- Monitoring and alerting validation

---

### **Project 11: Legacy Facade Removal & API Cleanup**
**Status**: Planned
**Priority**: Low
**Effort**: Medium (2 weeks)
**Dependencies**: Project 10

#### Objectives
- Remove legacy facades once Lambda functions are modernized
- Clean up deprecated imports and code paths
- Finalize modern API surface
- Optimize performance of modern architecture

#### Key Tasks
- **Facade Removal**: Delete `member.py`, `invasion.py`, `ladder.py` facades
- **Import Cleanup**: Update all imports to use modern services directly
- **Code Path Cleanup**: Remove deprecated methods and compatibility layers
- **Documentation Updates**: Reflect final modern architecture
- **Performance Optimization**: Fine-tune modern code paths

#### Risk Mitigation
- Comprehensive testing before facade removal
- Gradual deprecation with clear migration timeline
- Rollback plan if issues discovered
- Performance monitoring during cleanup

#### Deliverables
- Clean modern codebase with no legacy facades
- Updated documentation reflecting final architecture
- Performance optimization results
- Migration completion report

---

## Implementation Strategy

### **Phase 1: Foundation (Projects 07-08)**
Focus on understanding current state and building robust testing infrastructure. This enables safe modernization.

### **Phase 2: Incremental Migration (Project 09)**
Modernize Lambda functions incrementally using the facade pattern for safety. Each phase can be deployed independently.

### **Phase 3: Integration & Cleanup (Projects 10-11)**
Complete end-to-end validation and remove legacy code once modernization is proven stable.

## Success Criteria

### Technical Metrics
- [ ] All Lambda functions use modern repositories/services
- [ ] Lambda test coverage >90%
- [ ] End-to-end test coverage for major workflows
- [ ] No performance regression in Lambda execution
- [ ] Zero legacy facade dependencies

### Quality Metrics
- [ ] All Lambda functions follow modern patterns from steering docs
- [ ] Comprehensive error handling and logging
- [ ] Clean separation of concerns in Lambda handlers
- [ ] Modern dependency injection throughout

### Operational Metrics
- [ ] Successful deployment of modernized Lambda functions
- [ ] Monitoring and alerting working correctly
- [ ] Discord bot functionality fully preserved
- [ ] User experience maintained or improved

## Risks & Mitigation

### High Risks
1. **Lambda Performance Regression**: Modern architecture adds layers
   - *Mitigation*: Comprehensive performance testing, optimization focus
2. **Discord Integration Breakage**: Complex event handling
   - *Mitigation*: Extensive integration testing, gradual rollout
3. **AWS Service Dependencies**: Real AWS resources in testing
   - *Mitigation*: Robust test isolation, cleanup procedures

### Medium Risks
1. **Step Function Complexity**: Orchestration may be complex to test
   - *Mitigation*: Focus on unit testing individual Lambda functions first
2. **Test Infrastructure Complexity**: Lambda testing can be challenging
   - *Mitigation*: Start simple, build complexity gradually

## Notes

This roadmap builds on the excellent modern foundation established in Projects 03-06. The facade pattern provides a safe migration path, allowing incremental modernization without breaking existing functionality.

The projects are designed to be flexible - they can be executed in order, combined, or adapted based on discoveries during implementation. The key is maintaining the modern architecture principles while ensuring system reliability.

Each project includes comprehensive testing and validation to ensure the modernization improves rather than degrades the system's reliability and performance.
