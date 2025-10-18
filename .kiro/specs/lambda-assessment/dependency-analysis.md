# Lambda Dependency Analysis

## Current Lambda Dependencies

### 1. Bot Lambda (`src/bot/bot.py`)

**Direct imports from `src/layer/irus/`:**
- `irus` (main module)
- `IrusFiles`
- `IrusInvasion` (legacy facade)
- `IrusInvasionList`
- `IrusLadder` (legacy facade)
- `IrusMember` (legacy facade)
- `IrusMemberList`
- `IrusMonth`
- `IrusPostTable`
- `IrusProcess`
- `IrusReport`
- `IrusResources`
- `IrusSecrets`

**Legacy facade usage:**
- `IrusInvasion.from_table()` - Loading invasions from database
- `IrusInvasion.from_user()` - Creating new invasions
- `IrusMember.from_table()` - Loading members from database
- `IrusMember.from_user()` - Creating new members
- `IrusLadder.from_invasion()` - Loading ladder data

**Direct model usage:**
- Uses legacy facades which wrap modern models internally

**AWS SDK calls:**
- None direct - all through `IrusResources` and other classes

**Business logic complexity:**
- High - Contains all Discord command parsing and routing
- Complex command handling for invasion, member, report, and display operations
- File upload processing coordination

### 2. Invasion Lambda (`src/invasion/invasion.py`)

**Direct imports from `src/layer/irus/`:**
- `IrusResources`
- `IrusLadder` (legacy facade)
- `IrusInvasion` (legacy facade)
- `IrusReport`

**Legacy facade usage:**
- `IrusInvasion.from_table()` - Loading invasion data
- `IrusLadder.from_invasion()` - Loading ladder data

**Direct model usage:**
- None - uses legacy facades

**AWS SDK calls:**
- None direct - all through `IrusResources`

**Business logic complexity:**
- Medium - Generates invasion reports and statistics
- Calculates member counts, contiguous ranks
- Formats response data for Step Functions

### 3. Month Lambda (`src/month/month.py`)

**Direct imports from `src/layer/irus/`:**
- `IrusResources`
- `IrusReport`
- `IrusMonth`

**Legacy facade usage:**
- None - uses modern classes

**Direct model usage:**
- `IrusMonth.from_invasion_stats()` - Aggregating monthly statistics

**AWS SDK calls:**
- None direct - all through `IrusResources`

**Business logic complexity:**
- Low - Simple monthly report generation
- Aggregates invasion statistics for a month
- Formats response for Step Functions

### 4. Process Lambda (`src/process/process.py`)

**Direct imports from `src/layer/irus/`:**
- `IrusResources`
- `IrusMemberList`
- `IrusLadder` (legacy facade)
- `IrusInvasion` (legacy facade)

**Legacy facade usage:**
- `IrusInvasion.from_table()` - Loading invasion data
- `IrusLadder.from_ladder_image()` - Processing ladder screenshots
- `IrusLadder.from_roster_image()` - Processing roster screenshots

**Direct model usage:**
- `IrusMemberList` - Member data for image processing

**AWS SDK calls:**
- Direct S3 operations via `s3.upload_fileobj()`
- Uses `IrusResources.s3()` and `IrusResources.bucket_name()`

**Business logic complexity:**
- High - File download and image processing
- Coordinates between Discord file URLs and S3 storage
- Handles both ladder and roster image processing workflows

## Summary by Complexity

### High Complexity (Significant Migration Effort)
1. **Bot Lambda** - Complex command routing, multiple legacy facade dependencies
2. **Process Lambda** - Image processing workflows, direct S3 operations

### Medium Complexity (Moderate Migration Effort)
3. **Invasion Lambda** - Report generation, legacy facade usage

### Low Complexity (Simple Migration)
4. **Month Lambda** - Already uses modern patterns, minimal changes needed

## Legacy Dependencies Summary

### Legacy Facades Used
- `IrusInvasion` (used by: bot, invasion, process)
- `IrusLadder` (used by: bot, invasion, process)
- `IrusMember` (used by: bot)

### Modern Classes Already Used
- `IrusMonth` (used by: month)
- `IrusReport` (used by: invasion, month)
- `IrusMemberList` (used by: process)
- `IrusResources` (used by: all)

### Direct AWS Operations
- S3 file operations in Process Lambda
- All other AWS operations go through `IrusResources`
## Mo
dern Architecture Mapping

### Legacy Facade to Modern Repository Mapping

#### IrusMember (Legacy Facade) → Modern Equivalents
- **Repository**: `MemberRepository` (`src/layer/irus/repositories/member.py`)
- **Model**: `IrusMember` (`src/layer/irus/models/member.py`)
- **Service**: `MemberManagementService` (`src/layer/irus/services/member_management.py`)

**Migration mapping:**
- `IrusMember.from_table(player)` → `MemberRepository.get_by_player(player)`
- `IrusMember.from_user(...)` → `MemberRepository.create_from_user_input(...)`
- `member.remove()` → `MemberRepository.remove_with_audit(player)`
- `member.str()` → `member_model.str()` (method on pure model)

#### IrusInvasion (Legacy Facade) → Modern Equivalents
- **Repository**: `InvasionRepository` (`src/layer/irus/repositories/invasion.py`)
- **Model**: `IrusInvasion` (`src/layer/irus/models/invasion.py`)
- **Service**: No dedicated service yet (business logic in repository)

**Migration mapping:**
- `IrusInvasion.from_table(name)` → `InvasionRepository.get_by_name(name)`
- `IrusInvasion.from_user(...)` → `InvasionRepository.create_from_user_input(...)`
- `invasion.markdown()` → `invasion_model.markdown()` (method on pure model)
- `invasion.delete_from_table()` → `InvasionRepository.delete_by_name(name)`

#### IrusLadder (Legacy Facade) → Modern Equivalents
- **Repository**: `LadderRepository` (`src/layer/irus/repositories/ladder.py`)
- **Model**: `IrusLadder` (`src/layer/irus/models/ladder.py`)
- **Service**: `ImageProcessingService` (for image processing workflows)

**Migration mapping:**
- `IrusLadder.from_invasion(invasion)` → `LadderRepository.get_ladder(invasion_name)`
- `IrusLadder.from_ladder_image(...)` → Move to service layer with `ImageProcessingService`
- `IrusLadder.from_roster_image(...)` → Move to service layer with `ImageProcessingService`
- `ladder.edit(...)` → `LadderRepository.update_rank_membership(...)` + other update methods
- `ladder.delete_from_table()` → `LadderRepository.delete_ladder(invasion_name)`

### AWS SDK Operations to Repository Mapping

#### Direct S3 Operations (Process Lambda)
**Current:**
```python
s3.upload_fileobj(pool_mgr.request('GET', url, preload_content=False), bucket_name, target)
```

**Modern equivalent:**
- Move to `ImageProcessingService` or new `FileManagementService`
- Use `IrusContainer.s3()` for dependency injection
- Wrap in proper error handling and logging

#### Resource Access Pattern
**Current:**
```python
s3 = IrusResources.s3()
bucket_name = IrusResources.bucket_name()
```

**Modern equivalent:**
```python
container = IrusContainer.create_production()
s3 = container.s3()
bucket_name = container.bucket_name()
```

### Business Logic Migration Recommendations

#### Bot Lambda Business Logic
**Current complex command routing should be extracted to:**
- `DiscordCommandService` - Handle command parsing and routing
- `InvasionWorkflowService` - Coordinate invasion creation and file processing
- `ReportGenerationService` - Handle report generation workflows
- `MemberManagementService` - Already exists, use for member operations

#### Process Lambda Image Processing
**Current image processing should be moved to:**
- `ImageProcessingService` - Already exists for preprocessing
- `LadderExtractionService` - New service for OCR and ladder data extraction
- `FileManagementService` - New service for Discord file downloads and S3 uploads

#### Invasion Lambda Report Generation
**Current report logic should use:**
- `ReportGenerationService` - New service to consolidate report logic
- Keep using existing `IrusReport` class for formatting
- Use modern repositories for data access

#### Month Lambda (Already Modern)
**No major changes needed:**
- Already uses modern `IrusMonth` class
- Uses `IrusReport` for output formatting
- Minimal migration effort required

### Service Layer Gaps

#### Missing Services Needed for Lambda Modernization
1. **DiscordCommandService** - Command parsing and routing logic
2. **InvasionWorkflowService** - Coordinate invasion creation and processing
3. **ReportGenerationService** - Consolidate report generation logic
4. **LadderExtractionService** - OCR and ladder data extraction from images
5. **FileManagementService** - Discord file downloads and S3 operations

#### Existing Services to Leverage
1. **ImageProcessingService** - Image preprocessing for OCR
2. **DiscordMessagingService** - Discord webhook posting
3. **MemberManagementService** - Member-related business logic

### Container Integration

#### Current Resource Access
**Legacy pattern:**
```python
logger = IrusResources.logger()
table = IrusResources.table()
```

**Modern pattern:**
```python
container = IrusContainer.create_production()
logger = container.logger()
table = container.table()
```

#### Lambda Handler Modernization Pattern
**Current:**
```python
def lambda_handler(event: dict, context: LambdaContext):
    # Direct resource access and business logic mixed
```

**Modern:**
```python
def lambda_handler(event: dict, context: LambdaContext):
    container = IrusContainer.create_production()
    service = SomeService(container)
    return service.handle_request(event)
```
