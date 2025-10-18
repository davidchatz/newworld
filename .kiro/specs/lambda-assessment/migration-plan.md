# Lambda Migration Plan & Service Dependencies

## Overview

This document outlines the detailed migration order for Lambda functions and the service layer development required to support modernization. The plan prioritizes service development first, followed by incremental Lambda migration based on complexity and risk assessment.

## Migration Strategy

### Service-First Approach
1. **Build Required Services First**: Develop all necessary services before migrating Lambda functions
2. **Establish Patterns**: Use low-risk migrations to establish and validate patterns
3. **Incremental Deployment**: Deploy services and Lambda functions incrementally with rollback capability
4. **Validation at Each Step**: Comprehensive testing and validation before proceeding

### Complexity-Based Grouping

#### Low Complexity Group
- **Month Lambda**: 60 lines, already uses modern patterns
- **Invasion Lambda**: 70 lines, focused report generation

#### Medium Complexity Group
- **Process Lambda**: 80 lines, image processing workflow

#### High Complexity Group
- **Bot Lambda**: 650 lines, complex command routing and orchestration

## Service Development Plan

### Phase 1: Foundation Services (Weeks 1-3)

#### 1.1 ReportGenerationService (Week 1)
**Purpose**: Consolidate report generation logic across multiple Lambda functions
**Priority**: HIGH - Required by Invasion Lambda (first migration target)
**Complexity**: MEDIUM

**Service Interface:**
```python
class ReportGenerationService:
    def generate_invasion_report(self, invasion_name: str) -> dict
    def generate_monthly_report(self, year: int, month: int) -> dict
    def generate_member_report(self, player: str) -> dict
    def store_report_to_s3(self, report_data: dict, report_type: str) -> str
```

**Dependencies:**
- `InvasionRepository` (existing)
- `LadderRepository` (existing)
- `MemberRepository` (existing)
- `IrusContainer` for S3 and logging

**Development Tasks:**
- [ ] Design service interface and contracts
- [ ] Implement invasion report generation logic
- [ ] Implement monthly report aggregation
- [ ] Add S3 report storage functionality
- [ ] Create comprehensive unit tests
- [ ] Create integration tests with real AWS resources
- [ ] Document service usage patterns

**Success Criteria:**
- [ ] All existing report formats are supported
- [ ] Performance matches or exceeds legacy implementation
- [ ] Comprehensive test coverage (>90%)
- [ ] Clear error handling and logging

---

### Phase 2: Processing Services (Weeks 2-4)

#### 2.1 LadderExtractionService (Week 2-3)
**Purpose**: OCR and ladder data extraction from invasion screenshots
**Priority**: HIGH - Required by Process Lambda
**Complexity**: HIGH

**Service Interface:**
```python
class LadderExtractionService:
    def extract_ladder_from_image(self, image_data: bytes, invasion_name: str) -> IrusLadder
    def extract_roster_from_image(self, image_data: bytes, invasion_name: str) -> IrusLadder
    def validate_extracted_data(self, ladder: IrusLadder, member_list: IrusMemberList) -> bool
    def handle_extraction_errors(self, error: Exception, image_data: bytes) -> dict
```

**Dependencies:**
- `ImageProcessingService` (existing) - for image preprocessing
- `LadderRepository` (existing) - for data persistence
- `MemberRepository` (existing) - for validation
- AWS Textract - for OCR processing
- `IrusContainer` for AWS services

**Development Tasks:**
- [ ] Design service interface for OCR operations
- [ ] Implement AWS Textract integration
- [ ] Create ladder data parsing and validation logic
- [ ] Add error handling for OCR failures
- [ ] Implement retry mechanisms for transient failures
- [ ] Create unit tests with mocked Textract responses
- [ ] Create integration tests with real images
- [ ] Document OCR accuracy and limitations

**Success Criteria:**
- [ ] OCR accuracy matches or exceeds legacy implementation
- [ ] Robust error handling for image processing failures
- [ ] Comprehensive validation of extracted data
- [ ] Performance suitable for real-time processing

#### 2.2 FileManagementService (Week 3-4)
**Purpose**: Discord file downloads and S3 operations
**Priority**: HIGH - Required by Process Lambda
**Complexity**: MEDIUM

**Service Interface:**
```python
class FileManagementService:
    def download_discord_file(self, url: str) -> bytes
    def upload_to_s3(self, file_data: bytes, key: str) -> str
    def validate_file_type(self, file_data: bytes) -> bool
    def handle_download_errors(self, url: str, error: Exception) -> dict
```

**Dependencies:**
- `IrusContainer` for S3 and logging
- HTTP client for Discord file downloads
- File validation utilities

**Development Tasks:**
- [ ] Design service interface for file operations
- [ ] Implement Discord file download with proper error handling
- [ ] Add file type validation and security checks
- [ ] Implement S3 upload with retry mechanisms
- [ ] Create timeout and rate limiting for downloads
- [ ] Create unit tests with mocked HTTP responses
- [ ] Create integration tests with real Discord files
- [ ] Document file size limits and supported formats

**Success Criteria:**
- [ ] Reliable file downloads from Discord CDN
- [ ] Proper error handling for network failures
- [ ] Security validation of downloaded files
- [ ] Performance suitable for real-time processing

---

### Phase 3: Orchestration Services (Weeks 4-6)

#### 3.1 DiscordCommandService (Week 4-5)
**Purpose**: Discord command parsing and routing
**Priority**: MEDIUM - Required by Bot Lambda (last migration)
**Complexity**: HIGH

**Service Interface:**
```python
class DiscordCommandService:
    def parse_command(self, discord_event: dict) -> CommandRequest
    def route_command(self, command: CommandRequest) -> CommandResponse
    def validate_permissions(self, user_id: str, command: str) -> bool
    def format_response(self, result: dict) -> dict
```

**Dependencies:**
- All existing services (for command execution)
- Discord API integration
- `IrusContainer` for dependency injection

**Development Tasks:**
- [ ] Design command parsing and routing architecture
- [ ] Implement Discord event parsing logic
- [ ] Create command validation and permission checking
- [ ] Add response formatting for Discord API
- [ ] Implement error handling for invalid commands
- [ ] Create unit tests for command parsing
- [ ] Create integration tests with Discord events
- [ ] Document supported commands and parameters

**Success Criteria:**
- [ ] All existing Discord commands are supported
- [ ] Clear error messages for invalid commands
- [ ] Proper permission checking and validation
- [ ] Maintainable command routing architecture

#### 3.2 InvasionWorkflowService (Week 5-6)
**Purpose**: Coordinate invasion creation and processing workflows
**Priority**: MEDIUM - Required by Bot Lambda
**Complexity**: HIGH

**Service Interface:**
```python
class InvasionWorkflowService:
    def create_invasion_workflow(self, invasion_data: dict) -> WorkflowResult
    def process_invasion_files(self, invasion_name: str, file_urls: list) -> ProcessingResult
    def coordinate_step_functions(self, workflow_data: dict) -> dict
    def handle_workflow_errors(self, error: Exception, context: dict) -> dict
```

**Dependencies:**
- `InvasionRepository` (existing)
- `LadderExtractionService` (Phase 2)
- `FileManagementService` (Phase 2)
- `ReportGenerationService` (Phase 1)
- AWS Step Functions
- `IrusContainer` for orchestration

**Development Tasks:**
- [ ] Design workflow orchestration architecture
- [ ] Implement invasion creation workflow
- [ ] Add file processing coordination logic
- [ ] Implement Step Functions integration
- [ ] Create workflow state management
- [ ] Add comprehensive error handling and recovery
- [ ] Create unit tests for workflow logic
- [ ] Create integration tests with Step Functions
- [ ] Document workflow states and error recovery

**Success Criteria:**
- [ ] Reliable workflow orchestration
- [ ] Proper error handling and recovery mechanisms
- [ ] Clear workflow state tracking
- [ ] Performance suitable for real-time operations

## Lambda Migration Plan

### Phase 4: Low-Risk Lambda Migrations (Week 7)

#### 4.1 Month Lambda Migration (Day 1-2)
**Complexity**: LOW
**Service Dependencies**: None (already uses modern patterns)
**Migration Effort**: 2-3 days

**Migration Steps:**
1. **Container Integration** (Day 1)
   - Replace `IrusResources` with `IrusContainer.create_production()`
   - Update resource access patterns
   - Add proper error handling

2. **Testing and Validation** (Day 2)
   - Create unit tests with mocked dependencies
   - Create integration tests with real AWS resources
   - Validate report output matches legacy implementation

3. **Deployment** (Day 2)
   - Deploy to staging environment
   - Run parallel testing with legacy implementation
   - Deploy to production with monitoring

**Rollback Strategy:**
- Simple Lambda code rollback via AWS Console
- No data structure changes required
- Feature flag for switching implementations

#### 4.2 Invasion Lambda Migration (Day 3-5)
**Complexity**: LOW
**Service Dependencies**: `ReportGenerationService` (completed in Phase 1)
**Migration Effort**: 3-4 days

**Migration Steps:**
1. **Service Integration** (Day 3)
   - Replace legacy facades with `ReportGenerationService`
   - Update container pattern usage
   - Implement proper error handling

2. **Testing and Validation** (Day 4)
   - Create comprehensive unit tests
   - Create integration tests with real data
   - Validate report formats and content

3. **Deployment** (Day 5)
   - Deploy to staging with parallel testing
   - Validate report generation performance
   - Deploy to production with monitoring

**Rollback Strategy:**
- Gradual migration of report types
- Parallel execution for validation
- Circuit breaker for automatic fallback

---

### Phase 5: High-Risk Lambda Migrations (Weeks 8-10)

#### 5.1 Process Lambda Migration (Week 8)
**Complexity**: HIGH
**Service Dependencies**: `LadderExtractionService`, `FileManagementService`
**Migration Effort**: 5-7 days

**Migration Steps:**
1. **Service Integration** (Days 1-2)
   - Replace legacy facades with modern services
   - Implement `LadderExtractionService` integration
   - Add `FileManagementService` for file operations

2. **Workflow Testing** (Days 3-4)
   - Create comprehensive integration tests
   - Test with real Discord files and images
   - Validate OCR accuracy and performance

3. **Staged Deployment** (Days 5-7)
   - Deploy to staging with extensive testing
   - Test with non-critical invasions first
   - Monitor OCR accuracy and error rates
   - Deploy to production with careful monitoring

**Rollback Strategy:**
- Staged rollout with non-critical invasions
- Manual override capability for processing failures
- Legacy fallback for emergency situations
- Data recovery procedures for failed extractions

#### 5.2 Bot Lambda Migration (Weeks 9-10)
**Complexity**: HIGH
**Service Dependencies**: All services (5 total)
**Migration Effort**: 10-14 days

**Migration Steps:**
1. **Command-by-Command Migration** (Days 1-5)
   - Migrate individual Discord commands incrementally
   - Start with low-risk commands (display, help)
   - Progress to high-risk commands (invasion creation)

2. **Service Integration** (Days 6-8)
   - Integrate `DiscordCommandService` for routing
   - Add `InvasionWorkflowService` for orchestration
   - Connect all existing services

3. **Comprehensive Testing** (Days 9-12)
   - Extensive Discord integration testing
   - Test all command combinations and edge cases
   - Performance testing under load
   - Error handling and recovery testing

4. **Production Deployment** (Days 13-14)
   - Blue/green deployment with traffic switching
   - Gradual rollout with monitoring
   - Full monitoring and alerting setup

**Rollback Strategy:**
- Blue/green deployment for immediate rollback
- Command-by-command rollback capability
- Circuit breaker for automatic fallback
- Emergency rollback procedures
- Comprehensive monitoring and alerting

## Service Dependency Matrix

| Lambda Function | Required Services | Development Weeks | Migration Week |
|----------------|-------------------|-------------------|----------------|
| Month          | None              | 0                 | 7              |
| Invasion       | ReportGeneration  | 1                 | 7              |
| Process        | LadderExtraction, FileManagement | 3 | 8              |
| Bot            | All 5 services    | 6                 | 9-10           |

## Critical Path Analysis

### Service Development Critical Path (6 weeks)
1. **Week 1**: ReportGenerationService
2. **Week 2-3**: LadderExtractionService (parallel with FileManagement)
3. **Week 3-4**: FileManagementService (parallel with LadderExtraction)
4. **Week 4-5**: DiscordCommandService
5. **Week 5-6**: InvasionWorkflowService

### Lambda Migration Critical Path (4 weeks)
1. **Week 7**: Month + Invasion Lambda migrations
2. **Week 8**: Process Lambda migration
3. **Week 9-10**: Bot Lambda migration

### Total Project Timeline: 10 weeks

## Risk Mitigation Timeline

### Weeks 1-3: Foundation Phase
- **Risk**: Service development delays
- **Mitigation**: Start with simplest service (ReportGeneration)
- **Validation**: Each service fully tested before proceeding

### Weeks 4-6: Complex Services Phase
- **Risk**: OCR and workflow complexity
- **Mitigation**: Extensive testing with real data
- **Validation**: Performance benchmarking against legacy

### Weeks 7-8: Initial Migrations Phase
- **Risk**: Migration pattern failures
- **Mitigation**: Start with lowest-risk Lambda functions
- **Validation**: Parallel execution and comparison

### Weeks 9-10: Critical Migration Phase
- **Risk**: Bot functionality disruption
- **Mitigation**: Command-by-command migration, extensive monitoring
- **Validation**: Blue/green deployment with immediate rollback capability

## Success Metrics

### Service Development Success
- [ ] All 5 required services implemented and tested
- [ ] Performance matches or exceeds legacy implementation
- [ ] Comprehensive test coverage (>90% for all services)
- [ ] Clear documentation and usage patterns

### Lambda Migration Success
- [ ] All 4 Lambda functions successfully migrated
- [ ] Zero downtime during migration process
- [ ] No degradation in Discord bot functionality
- [ ] Improved error handling and monitoring

### Overall Project Success
- [ ] Modern architecture fully implemented
- [ ] Established patterns for future development
- [ ] Comprehensive documentation and runbooks
- [ ] Team knowledge transfer completed

## Deployment Strategy

### Environment Progression
1. **Development**: Individual service and Lambda testing
2. **Staging**: Full integration testing with real AWS resources
3. **Production**: Gradual rollout with monitoring and rollback capability

### Monitoring and Validation
- **Service Metrics**: Performance, error rates, resource usage
- **Lambda Metrics**: Execution time, error rates, Discord response times
- **Business Metrics**: Command success rates, user satisfaction, system reliability

### Communication Plan
- **Weekly Updates**: Progress reports to stakeholders
- **Migration Notifications**: Advance notice of production deployments
- **Incident Response**: Clear escalation procedures for migration issues
