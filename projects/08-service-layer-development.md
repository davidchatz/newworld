# Project 08: Service Layer Development for Lambda Modernization

## Overview
Develop the 5 missing services required for Lambda function modernization, establishing the service layer foundation that will enable safe migration of Lambda handlers from legacy facade patterns to modern architecture.

## Context
- **Current State**: Lambda functions use legacy facades (`IrusMember`, `IrusInvasion`, `IrusLadder`) with business logic mixed into handlers
- **Target State**: Complete service layer with 5 new services enabling Lambda functions to use modern repository/service patterns
- **Scope**: Service development only - Lambda migration will be handled in subsequent projects

## Requirements

### Functional Requirements
- [ ] ReportGenerationService - Consolidate report generation logic across Lambda functions
- [ ] FileManagementService - Handle Discord file downloads and S3 operations
- [ ] LadderExtractionService - OCR and ladder data extraction from invasion screenshots
- [ ] DiscordCommandService - Discord command parsing and routing logic
- [ ] InvasionWorkflowService - Coordinate invasion creation and processing workflows

### Technical Requirements
- [ ] All services follow established container dependency injection pattern
- [ ] Services integrate with existing repositories (`MemberRepository`, `InvasionRepository`, `LadderRepository`)
- [ ] Comprehensive unit testing with >90% coverage for all services
- [ ] Integration testing with real AWS resources using 99DDHHMM test pattern
- [ ] Error handling follows established patterns with proper exception chaining
- [ ] Performance meets or exceeds legacy facade implementations

### Quality Requirements
- [ ] Services follow code style guidelines from steering documentation
- [ ] Comprehensive documentation with clear service contracts
- [ ] Proper logging and observability throughout
- [ ] Retry mechanisms and circuit breakers for external dependencies
- [ ] Security validation for file operations and user inputs

## Tasks

### Phase 1: Foundation Services (Week 1-2)
- [ ] **ReportGenerationService Development** (5-7 days)
  - Design service interface for invasion, monthly, and member reports
  - Implement report generation logic extracted from Lambda functions
  - Add S3 report storage and retrieval functionality
  - Create comprehensive unit and integration tests
  - _Priority: HIGH - Required by Invasion Lambda (first migration target)_

- [ ] **FileManagementService Development** (4-6 days)
  - Design service interface for Discord file downloads and S3 operations
  - Implement secure file download with validation and rate limiting
  - Add S3 upload operations with retry mechanisms
  - Create comprehensive error handling for network operations
  - _Priority: HIGH - Required by Process Lambda_

### Phase 2: Processing Services (Week 2-3)
- [ ] **LadderExtractionService Development** (8-10 days)
  - Design service interface for OCR and ladder data extraction
  - Implement AWS Textract integration with error handling
  - Create ladder data parsing and validation logic
  - Add retry mechanisms for transient OCR failures
  - Implement comprehensive testing with real images
  - _Priority: HIGH - Required by Process Lambda (complex image processing)_

### Phase 3: Orchestration Services (Week 3-4)
- [ ] **DiscordCommandService Development** (6-8 days)
  - Design service interface for Discord command parsing and routing
  - Implement Discord event parsing logic
  - Add command validation and permission checking
  - Create response formatting for Discord API
  - _Priority: MEDIUM - Required by Bot Lambda (last migration)_

- [ ] **InvasionWorkflowService Development** (8-12 days)
  - Design service interface for workflow orchestration
  - Implement invasion creation and file processing coordination
  - Add Step Functions integration for workflow management
  - Create workflow state management and error recovery
  - _Priority: MEDIUM - Required by Bot Lambda (most complex)_

### Phase 4: Integration & Validation (Week 4-5)
- [ ] **Cross-Service Integration Testing** (3-4 days)
  - Test service interactions and dependencies
  - Validate performance with realistic data loads
  - Ensure proper error propagation between services
  - Test container lifecycle and resource management

- [ ] **Documentation & Patterns** (2-3 days)
  - Update steering documentation with service patterns
  - Create service usage examples and templates
  - Document service contracts and integration points
  - Prepare Lambda migration templates using new services

## Files/Areas Involved

### New Service Files
- `src/layer/irus/services/report_generation_service.py` - Report generation logic
- `src/layer/irus/services/file_management_service.py` - File download and S3 operations
- `src/layer/irus/services/ladder_extraction_service.py` - OCR and data extraction
- `src/layer/irus/services/discord_command_service.py` - Command parsing and routing
- `src/layer/irus/services/invasion_workflow_service.py` - Workflow orchestration

### Test Files
- `tests/unit/test_*_service.py` - Unit tests for each service
- `tests/integration/test_*_service_integration.py` - Integration tests with AWS
- `tests/fixtures/` - Service test fixtures and data

### Documentation Updates
- `.kiro/steering/service-development.md` - Service development patterns
- `src/layer/irus/services/__init__.py` - Service exports and documentation

## Success Criteria
- [ ] All 5 services implemented with comprehensive interfaces
- [ ] Unit test coverage >90% for all services
- [ ] Integration tests passing with real AWS resources
- [ ] Performance benchmarks meet or exceed legacy implementations
- [ ] Services integrate cleanly with existing repositories
- [ ] Documentation complete with usage examples
- [ ] Code review completed and steering docs updated

## Dependencies
- **Project 06**: Comprehensive Modernization (completed)
- **Project 07**: Lambda Assessment & Planning (completed)
- **AWS Development Environment**: Real AWS resources for integration testing
- **Test Infrastructure**: 99DDHHMM pattern and cleanup automation

## Risks & Considerations

### High Risks
1. **LadderExtractionService Complexity**: OCR processing is complex and error-prone
   - *Mitigation*: Extensive testing with diverse image samples, fallback mechanisms
   - *Timeline Impact*: May require additional 2-3 days for robust error handling

2. **InvasionWorkflowService Dependencies**: Requires coordination of multiple services
   - *Mitigation*: Develop other services first, use mocking for early testing
   - *Timeline Impact*: Must be developed last in sequence

3. **Performance Requirements**: Services must not degrade Lambda performance
   - *Mitigation*: Performance benchmarking throughout development
   - *Timeline Impact*: May require optimization iterations

### Medium Risks
1. **AWS Service Integration**: Real AWS dependencies for Textract, S3, Step Functions
   - *Mitigation*: Robust error handling, retry mechanisms, circuit breakers
   - *Timeline Impact*: Additional testing time for AWS integration scenarios

2. **Service Interface Design**: Getting abstractions right is critical for Lambda migration
   - *Mitigation*: Review service contracts with Lambda usage patterns in mind
   - *Timeline Impact*: May require interface refinements during development

### Rollback Plan
- Services are additive - no existing functionality is modified
- Each service can be developed and tested independently
- Lambda functions continue using legacy facades until migration project
- Services can be disabled or removed without impact on existing system

## Notes

### Development Order Rationale
1. **ReportGenerationService** first - needed by Invasion Lambda (lowest risk migration)
2. **FileManagementService** parallel - needed by Process Lambda, relatively straightforward
3. **LadderExtractionService** - most complex, needs FileManagementService complete
4. **DiscordCommandService** - needed by Bot Lambda, can develop in parallel with LadderExtraction
5. **InvasionWorkflowService** last - depends on all other services

### Service Design Principles
- Follow established container dependency injection pattern
- Use existing repositories for data access
- Implement comprehensive error handling with proper exception types
- Include retry mechanisms for external service calls
- Design for testability with clear interfaces
- Follow established logging and observability patterns

### Testing Strategy
- Unit tests with mocked dependencies using `IrusContainer.create_unit()`
- Integration tests with real AWS using `IrusContainer.create_integration()`
- Use 99DDHHMM test data pattern for isolation
- Performance testing with realistic data volumes
- Error scenario testing for robustness

### Performance Targets
- Report generation: <5 seconds for typical invasion reports
- File downloads: <30 seconds for typical Discord image files
- OCR processing: <60 seconds for typical ladder screenshots
- Command parsing: <100ms for typical Discord commands
- Workflow coordination: <10 seconds for typical invasion workflows

---

## Implementation Log

### [To be filled during implementation]
Track progress, issues, and decisions made during service development.
