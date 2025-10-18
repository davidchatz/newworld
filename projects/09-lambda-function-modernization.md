# Project 09: Lambda Function Modernization

## Overview
Modernize all 4 Lambda functions to use the modern repository and service architecture, migrating from legacy facade patterns to dependency injection with comprehensive testing and validation.

## Context
- **Current State**: Lambda functions use legacy facades with business logic mixed into handlers
- **Target State**: Lambda functions use modern services via dependency injection, following established patterns
- **Scope**: Migration of Bot, Process, Invasion, and Month Lambda functions with comprehensive testing

## Requirements

### Functional Requirements
- [ ] Month Lambda modernized to use container pattern (lowest risk)
- [ ] Invasion Lambda modernized to use ReportGenerationService
- [ ] Process Lambda modernized to use LadderExtractionService and FileManagementService
- [ ] Bot Lambda modernized to use all 5 services (highest complexity)

### Technical Requirements
- [ ] All Lambda functions use `IrusContainer.create_production()` for dependency injection
- [ ] Business logic extracted to service layer - handlers only orchestrate
- [ ] Comprehensive Lambda testing with both unit and integration tests
- [ ] Environment variable management for Lambda testing
- [ ] Performance maintained or improved compared to legacy implementations
- [ ] Proper error handling and logging throughout

### Quality Requirements
- [ ] Lambda test coverage >90% for all functions
- [ ] Integration tests with real AWS resources and Discord events
- [ ] Performance benchmarks showing no regression
- [ ] Code follows Lambda development patterns from steering documentation
- [ ] Comprehensive rollback procedures for each Lambda function

## Tasks

### Phase 1: Low-Risk Lambda Migrations (Week 1)
- [ ] **Month Lambda Modernization** (2-3 days)
  - Replace `IrusResources` with `IrusContainer.create_production()`
  - Update resource access patterns to use container
  - Create comprehensive unit tests with mocked container
  - Create integration tests with real AWS resources
  - Deploy and validate in staging environment
  - _Risk: LOW - Already uses modern patterns, minimal changes needed_

- [ ] **Invasion Lambda Modernization** (3-4 days)
  - Replace legacy facades with ReportGenerationService
  - Update handler to use dependency injection pattern
  - Extract report generation logic to service calls
  - Create comprehensive unit and integration tests
  - Validate report formats match legacy implementation
  - Deploy with parallel testing and monitoring
  - _Risk: LOW - Simple report generation, well-defined service interface_

### Phase 2: Medium-Risk Lambda Migration (Week 2)
- [ ] **Process Lambda Modernization** (5-7 days)
  - Replace legacy facades with LadderExtractionService and FileManagementService
  - Update handler to coordinate between services
  - Implement proper error handling for OCR and file operations
  - Create comprehensive testing with real Discord files and images
  - Performance testing with various image sizes and qualities
  - Staged rollout with non-critical invasions first
  - _Risk: MEDIUM - Complex image processing, external dependencies_

### Phase 3: High-Risk Lambda Migration (Week 3-4)
- [ ] **Bot Lambda Modernization** (10-14 days)
  - Command-by-command migration approach for safety
  - Replace legacy facades with all 5 modern services
  - Implement DiscordCommandService for command routing
  - Use InvasionWorkflowService for complex workflows
  - Extract all business logic to appropriate services
  - Comprehensive Discord integration testing
  - Blue/green deployment with traffic switching
  - _Risk: HIGH - Most complex, critical to Discord bot functionality_

### Phase 4: Validation & Monitoring (Week 4-5)
- [ ] **End-to-End Testing** (3-4 days)
  - Complete user journey testing from Discord to database
  - Step Functions integration validation
  - Performance testing under realistic load
  - Error handling and recovery testing

- [ ] **Production Validation** (2-3 days)
  - Monitor Lambda performance and error rates
  - Validate Discord bot functionality
  - Confirm all existing features work correctly
  - Document any performance improvements

## Files/Areas Involved

### Lambda Handler Files
- `src/month/month.py` - Container integration, minimal changes
- `src/invasion/invasion.py` - Service integration for report generation
- `src/process/handler.py` - Service integration for file processing and OCR
- `src/bot/bot.py` - Complete modernization with all services

### Test Files
- `tests/unit/lambdas/test_*_lambda.py` - Unit tests for each Lambda
- `tests/integration/lambdas/test_*_lambda_integration.py` - Integration tests
- `tests/fixtures/discord_events.py` - Discord event fixtures for testing

### Infrastructure Files
- `template.yaml` - SAM template (already updated for Process Lambda)
- `step/process.json` - Step Functions definition (if changes needed)

### Documentation Updates
- `.kiro/steering/lambda-development.md` - Lambda development patterns (already created)
- Migration runbooks and rollback procedures

## Success Criteria
- [ ] All 4 Lambda functions successfully modernized
- [ ] Zero downtime during migration process
- [ ] No degradation in Discord bot functionality
- [ ] Lambda test coverage >90% for all functions
- [ ] Performance meets or exceeds legacy implementations
- [ ] Comprehensive monitoring and alerting working
- [ ] Rollback procedures tested and documented

## Dependencies
- **Project 08**: Service Layer Development (must be completed first)
- **AWS Development Environment**: Real AWS resources for testing
- **Discord Test Environment**: Ability to test Discord interactions
- **Monitoring Infrastructure**: CloudWatch, alerting setup

## Risks & Considerations

### High Risks
1. **Bot Lambda Complexity**: 650 lines of complex Discord command logic
   - *Mitigation*: Command-by-command migration, extensive testing, blue/green deployment
   - *Timeline Impact*: May require additional week for comprehensive testing

2. **Discord Integration Breakage**: Complex event handling and response formatting
   - *Mitigation*: Comprehensive Discord event fixtures, parallel testing
   - *Timeline Impact*: Additional testing time for Discord scenarios

3. **Process Lambda OCR Accuracy**: Image processing must maintain accuracy
   - *Mitigation*: Extensive testing with real images, accuracy validation
   - *Timeline Impact*: May require OCR tuning and optimization

### Medium Risks
1. **Performance Regression**: Modern architecture adds service layers
   - *Mitigation*: Performance benchmarking, optimization focus
   - *Timeline Impact*: May require performance tuning iterations

2. **Step Functions Integration**: Complex orchestration between Lambda functions
   - *Mitigation*: Thorough Step Functions testing, state management validation
   - *Timeline Impact*: Additional integration testing time

3. **Environment Variable Dependencies**: Lambda modules require specific environment setup
   - *Mitigation*: Proper test environment management, documented procedures
   - *Timeline Impact*: Additional setup and validation time

### Rollback Plan
- **Blue/Green Deployment**: Maintain old Lambda versions for immediate rollback
- **Feature Flags**: Environment variables to switch between old/new implementations
- **Command-Level Rollback**: For Bot Lambda, ability to rollback individual commands
- **Monitoring Triggers**: Automatic rollback on error rate thresholds
- **Manual Procedures**: Clear steps for emergency rollback

## Migration Strategy

### Risk-Based Ordering
1. **Month Lambda** - Lowest risk, establishes patterns
2. **Invasion Lambda** - Low risk, validates service integration
3. **Process Lambda** - Medium risk, tests complex service coordination
4. **Bot Lambda** - Highest risk, most critical functionality

### Deployment Approach
- **Staging First**: All migrations tested in staging environment
- **Gradual Rollout**: Start with low-traffic periods
- **Monitoring**: Extensive monitoring during and after migration
- **Validation**: Functional testing after each deployment
- **Rollback Ready**: Immediate rollback capability at each step

### Testing Strategy
- **Unit Tests**: Mock all dependencies, test handler logic
- **Integration Tests**: Real AWS resources, real Discord events
- **Performance Tests**: Validate response times and resource usage
- **End-to-End Tests**: Complete user workflows
- **Load Tests**: Realistic Discord usage patterns

## Notes

### Lambda Handler Pattern
```python
def lambda_handler(event: dict, context: LambdaContext) -> dict:
    """Modern Lambda handler with dependency injection."""
    try:
        # Initialize container for production
        container = IrusContainer.create_production()

        # Initialize required services
        command_service = DiscordCommandService(container)
        workflow_service = InvasionWorkflowService(container)

        # Parse and route command
        command = command_service.parse_discord_event(event)
        result = workflow_service.execute_command(command)

        # Format response
        return command_service.format_discord_response(result)

    except Exception as e:
        logger.error(f"Lambda execution failed: {e}")
        return format_error_response(str(e))
```

### Testing Pattern
```python
class TestBotLambda:
    @pytest.fixture(autouse=True)
    def lambda_environment(self):
        """Set up Lambda environment variables."""
        env_vars = {
            "AWS_DEFAULT_REGION": "ap-southeast-2",
            "ENVIRONMENT": "test",
            "DISCORD_CMD": "irus"
        }
        with patch.dict(os.environ, env_vars, clear=False):
            yield

    def test_member_command(self, integration_container):
        """Test member command with real AWS resources."""
        # Import after environment setup
        from src.bot.bot import lambda_handler

        # Test with real container
        with patch('src.bot.bot.IrusContainer.create_production') as mock_factory:
            mock_factory.return_value = integration_container
            response = lambda_handler(discord_event, context)

        # Validate response and database changes
        assert response["statusCode"] == 200
```

### Performance Targets
- **Month Lambda**: <30 seconds (monthly aggregation)
- **Invasion Lambda**: <60 seconds (report generation)
- **Process Lambda**: <300 seconds (image processing with OCR)
- **Bot Lambda**: <30 seconds (Discord command response)

### Monitoring Metrics
- Lambda execution duration and memory usage
- Error rates and retry counts
- Discord response times
- Database operation performance
- Step Functions execution success rates

---

## Implementation Log

### [To be filled during implementation]
Track migration progress, issues encountered, and lessons learned for each Lambda function.
