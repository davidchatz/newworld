# Lambda Function Inventory

## Overview

This document provides a comprehensive inventory of all Lambda functions in the Discord bot application, documenting their purposes, dependencies, and migration complexity.

**Total Lambda Functions:** 4

## Lambda Function Details

### 1. Bot Lambda (`src/bot/bot.py`)

**Handler:** `bot.lambda_handler`
**Purpose:** Main Discord bot handler that processes Discord slash commands and coordinates bot functionality
**Lines of Code:** ~650 lines
**Complexity:** HIGH

#### Current Imports from `src/layer/irus/`
```python
import irus
from irus import (
    IrusFiles,
    IrusInvasion,
    IrusInvasionList,
    IrusLadder,
    IrusMember,
    IrusMemberList,
    IrusMonth,
    IrusPostTable,
    IrusProcess,
    IrusReport,
    IrusResources,
    IrusSecrets,
)
```

#### Legacy Dependencies
- **Legacy Facades:** Uses all major legacy facades (`IrusInvasion`, `IrusMember`, `IrusLadder`)
- **Direct Model Usage:** Extensive direct usage of model classes
- **Business Logic:** Contains significant business logic that should be in services
- **AWS SDK Calls:** Direct calls through `IrusResources` and `IrusSecrets`

#### External Dependencies
- Discord API integration via webhooks
- Step Functions execution
- SSM Parameter Store access
- DynamoDB operations
- S3 operations

#### Migration Notes
- Most complex Lambda function with extensive business logic
- Heavy reliance on legacy facade pattern
- Contains Discord command parsing and routing logic
- Requires careful extraction of business logic to services

---

### 2. Process Lambda (`src/process/process.py`)

**Handler:** `process.lambda_handler`
**Purpose:** Downloads Discord attachments and processes invasion screenshots using AWS Textract
**Lines of Code:** ~80 lines
**Complexity:** MEDIUM

#### Current Imports from `src/layer/irus/`
```python
from irus import IrusResources, IrusMemberList, IrusLadder, IrusInvasion
```

#### Legacy Dependencies
- **Legacy Facades:** Uses `IrusLadder`, `IrusInvasion`
- **Direct Model Usage:** Uses `IrusMemberList`
- **AWS SDK Calls:** Direct S3 operations through `IrusResources`

#### External Dependencies
- S3 for file storage
- AWS Textract for OCR processing
- HTTP requests for file downloads

#### Migration Notes
- Focused on file processing workflow
- Uses legacy facades for ladder creation
- Relatively straightforward migration to modern services

---

### 3. Invasion Lambda (`src/invasion/invasion.py`)

**Handler:** `invasion.lambda_handler`
**Purpose:** Generates invasion reports and statistics from processed ladder data
**Lines of Code:** ~70 lines
**Complexity:** LOW

#### Current Imports from `src/layer/irus/`
```python
from irus import IrusResources, IrusLadder, IrusInvasion, IrusReport
```

#### Legacy Dependencies
- **Legacy Facades:** Uses `IrusLadder`, `IrusInvasion`, `IrusReport`
- **AWS SDK Calls:** Minimal, through `IrusResources` for logging

#### External Dependencies
- DynamoDB for data retrieval
- S3 for report generation

#### Migration Notes
- Simple report generation logic
- Straightforward mapping to modern repository/service pattern
- Good candidate for early migration

---

### 4. Month Lambda (`src/month/month.py`)

**Handler:** `month.lambda_handler`
**Purpose:** Generates monthly statistics and reports from invasion data
**Lines of Code:** ~60 lines
**Complexity:** LOW

#### Current Imports from `src/layer/irus/`
```python
from irus import IrusResources, IrusReport, IrusMonth
```

#### Legacy Dependencies
- **Legacy Facades:** Uses `IrusMonth`, `IrusReport`
- **AWS SDK Calls:** Minimal, through `IrusResources` for logging

#### External Dependencies
- DynamoDB for data aggregation
- S3 for report generation

#### Migration Notes
- Simple monthly aggregation logic
- Minimal dependencies make it ideal for early migration
- Good template for other report-generating Lambda functions

## Summary Statistics

| Function | Complexity | Legacy Dependencies | Lines of Code | Migration Priority |
|----------|------------|-------------------|---------------|-------------------|
| Bot      | HIGH       | 9 imports         | ~650          | 4 (Last)         |
| Process  | MEDIUM     | 4 imports         | ~80           | 3 (Third)        |
| Invasion | LOW        | 4 imports         | ~70           | 1 (First)        |
| Month    | LOW        | 3 imports         | ~60           | 2 (Second)       |

## Common Dependencies

All Lambda functions share these common dependencies:
- **aws_lambda_powertools** - For logging and observability
- **Pillow** - For image processing capabilities
- **IrusResources** - Legacy resource management facade

## Migration Complexity Assessment

### Low Risk (Invasion, Month)
- Simple, focused functionality
- Minimal business logic
- Clear input/output patterns
- Limited legacy dependencies

### Medium Risk (Process)
- File processing workflow
- External HTTP dependencies
- Image processing logic
- Moderate legacy dependencies

### High Risk (Bot)
- Complex Discord command routing
- Extensive business logic
- Multiple external integrations
- Heavy legacy dependency usage
- Critical to bot functionality

## Next Steps

1. **Start with low-risk Lambda functions** (Invasion, Month) to establish migration patterns
2. **Create modern service equivalents** for report generation and monthly statistics
3. **Develop testing framework** for Lambda functions with modern architecture
4. **Gradually migrate Process Lambda** once patterns are established
5. **Bot Lambda migration last** due to complexity and criticality
