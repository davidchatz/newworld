# Lambda Modernization Process

## Overview

This document provides step-by-step guides for modernizing each Lambda type and the service layer development requirements. Since this is for a new production environment, the focus is on building modern Lambda functions from the start.

## Service Development Requirements

### Required Services for Lambda Modernization

The following services need to be developed to support modern Lambda functions:

1. **ReportGenerationService** - For Invasion and Month Lambda report generation
2. **FileManagementService** - For Process Lambda file operations
3. **LadderExtractionService** - For Process Lambda OCR processing
4. **DiscordCommandService** - For Bot Lambda command parsing
5. **InvasionWorkflowService** - For Bot Lambda workflow orchestration

### Service Development Standards

Each service should meet these criteria:

#### Development Requirements
- [ ] Clear service interface with method signatures
- [ ] Integration with `IrusContainer` for dependency injection
- [ ] Comprehensive error handling with domain-specific exceptions
- [ ] Structured logging with appropriate log levels
- [ ] Input validation with clear error messages

#### Testing Requirements
- [ ] Unit tests with >90% code coverage using mocked dependencies
- [ ] Integration tests with real AWS resources using 99DDHHMM pattern
- [ ] Performance validation to ensure acceptable response times
- [ ] Error scenario testing for robust error handling

## Lambda Modernization by Type

### Type 1: Month Lambda (Simple)

**Complexity**: LOW
**Service Dependencies**: ReportGenerationService (optional - can use existing IrusMonth/IrusReport)

#### Modernization Steps
1. **Replace IrusResources with IrusContainer**
   ```python
   # Before
   logger = IrusResources.logger()

   # After
   container = IrusContainer.create_production()
   logger = container.logger()
   ```

2. **Add Input Validation**
   ```python
   month_str = event.get("month")
   if not month_str or len(month_str) != 6:
       raise ValueError(f"Invalid month format: {month_str}")
   ```

3. **Implement Structured Error Handling**
   ```python
   try:
       # Business logic
   except ValueError as e:
       logger.warning(f"Validation error: {e}")
       return {"statusCode": 400, "body": {"error": str(e)}}
   except Exception as e:
       logger.error(f"Unexpected error: {e}")
       return {"statusCode": 500, "body": {"error": "Internal server error"}}
   ```

#### Testing
- Unit tests with mocked dependencies
- Integration tests with real AWS resources
- Performance validation (< 30 seconds execution time)

### Type 2: Invasion Lambda (Medium)

**Complexity**: MEDIUM
**Service Dependencies**: ReportGenerationService

#### Modernization Steps
1. **Replace Legacy Facades with Service**
   ```python
   # Before
   invasion = IrusInvasion.from_table(name)
   ladder = IrusLadder.from_invasion(invasion)
   report = IrusReport.from_invasion(ladder)

   # After
   container = IrusContainer.create_production()
   report_service = ReportGenerationService(container)
   report_data = report_service.generate_invasion_report(invasion_name)
   ```

2. **Update Response Format**
   ```python
   response_body = {
       'name': invasion_name,
       'ranks': report_data['total_ranks'],
       'members': report_data['member_count'],
       'memberlist': report_data['member_list'],
       'nonmemberlist': report_data['non_member_list'],
       'contiguous': report_data['contiguous_status'],
       'url': report_data['report_url']
   }
   ```

#### Testing
- Unit tests with mocked ReportGenerationService
- Integration tests with real service
- Step Function compatibility validation

### Type 3: Process Lambda (High)

**Complexity**: HIGH
**Service Dependencies**: LadderExtractionService, FileManagementService

#### Modernization Steps
1. **Replace Direct AWS Operations with Services**
   ```python
   # Before
   s3.upload_fileobj(pool_mgr.request('GET', url, preload_content=False), bucket_name, target)
   ladder = IrusLadder.from_ladder_image(invasion, members, bucket_name, target)

   # After
   container = IrusContainer.create_production()
   file_service = FileManagementService(container)
   extraction_service = LadderExtractionService(container)

   file_data = file_service.download_discord_file(file_url)
   s3_url = file_service.upload_to_s3(file_data, s3_key)

   if process_type == 'Ladder':
       ladder = extraction_service.extract_ladder_from_image(file_data, invasion_name)
   else:  # Roster
       ladder = extraction_service.extract_roster_from_image(file_data, invasion_name)
   ```

2. **Add File Validation**
   ```python
   if not file_service.validate_file_type(filename):
       raise ValueError(f"Invalid file type: {filename}")
   ```

#### Testing
- Unit tests with mocked services
- Integration tests with real Discord files and OCR
- OCR accuracy validation with known images

### Type 4: Bot Lambda (High)

**Complexity**: HIGH
**Service Dependencies**: DiscordCommandService, InvasionWorkflowService, plus all other services

#### Modernization Steps
1. **Replace Monolithic Command Handling with Services**
   ```python
   # Before
   if name == "invasion":
       content = invasion_cmd(app_id, body["token"], subcommand["options"][0], resolved)
   elif name == "member":
       content = member_cmd(subcommand["options"][0], resolved)

   # After
   container = IrusContainer.create_production()
   command_service = DiscordCommandService(container)
   invasion_service = InvasionWorkflowService(container)
   member_service = MemberManagementService(container)

   command_request = command_service.parse_command(event)

   if command_request.command_name == "invasion":
       result = invasion_service.handle_invasion_command(command_request)
   elif command_request.command_name == "member":
       result = member_service.handle_member_command(command_request)
   ```

2. **Add Permission Validation**
   ```python
   if not command_service.validate_permissions(command_request.user_id, command_request.command_name):
       return command_service.format_error_response("Permission denied")
   ```

#### Testing
- Discord integration tests with real events
- Service orchestration validation
- Performance testing (< 3 seconds response time)

## Testing Guidelines

### Service Testing

#### Unit Testing Pattern
```python
class TestReportGenerationService:
    @pytest.fixture
    def container(self):
        return IrusContainer.create_unit()

    @pytest.fixture
    def service(self, container):
        return ReportGenerationService(container)

    def test_generate_invasion_report_success(self, service, container):
        # Mock repository responses
        container.invasion_repository().get_by_name.return_value = mock_invasion

        # Test service method
        result = service.generate_invasion_report("test-invasion")

        # Validate result
        assert result["invasion_name"] == "test-invasion"
        assert "total_ranks" in result
```

#### Integration Testing Pattern
```python
def test_service_integration(integration_container):
    # Create test data using 99DDHHMM pattern
    date_components = get_test_date_components()
    invasion_name = f"{date_components['date_string']}-bw"

    # Test service with real AWS resources
    service = ReportGenerationService(integration_container)
    result = service.generate_invasion_report(invasion_name)

    # Validate real results
    assert result["report_url"].startswith("https://")
```

### Lambda Testing

#### Unit Testing Pattern
```python
def test_lambda_handler_unit():
    container = IrusContainer.create_unit()

    # Mock service responses
    mock_service = Mock()
    mock_service.generate_monthly_report.return_value = test_data

    # Test Lambda handler
    with patch('lambda_module.ReportGenerationService', return_value=mock_service):
        result = lambda_handler(test_event, test_context)

    assert result["statusCode"] == 200
```

#### Integration Testing Pattern
```python
def test_lambda_integration(integration_container):
    # Test with real services and AWS resources
    result = lambda_handler(test_event, test_context)

    assert result["statusCode"] == 200
    assert result["body"]["url"].startswith("https://")
```

### Performance Requirements
- **ReportGenerationService**: < 30 seconds
- **LadderExtractionService**: < 2 minutes per image
- **FileManagementService**: < 30 seconds
- **DiscordCommandService**: < 1 second
- **InvasionWorkflowService**: < 5 seconds

### Lambda Performance Requirements
- **Month Lambda**: < 30 seconds
- **Invasion Lambda**: < 60 seconds
- **Process Lambda**: < 5 minutes
- **Bot Lambda**: < 3 seconds (Discord response time)

## Implementation Checklist

### For Each Service:
- [ ] Design clear interface with method signatures
- [ ] Implement with IrusContainer dependency injection
- [ ] Add comprehensive error handling
- [ ] Create unit tests with >90% coverage
- [ ] Create integration tests with real AWS resources
- [ ] Document usage patterns and examples

### For Each Lambda:
- [ ] Replace IrusResources with IrusContainer
- [ ] Replace legacy facades with modern services
- [ ] Add proper input validation
- [ ] Implement structured error handling
- [ ] Add comprehensive logging
- [ ] Create unit and integration tests
- [ ] Validate performance requirements
