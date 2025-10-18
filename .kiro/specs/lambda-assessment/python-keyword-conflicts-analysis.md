# Python Keyword Conflicts Analysis & Resolution

## Overview

This document identifies and addresses Python keyword conflicts and import issues in the Lambda function codebase that could interfere with the testing framework's ability to import Lambda modules correctly.

## Identified Conflicts

### 1. Module Name Conflicts (Not Python Keywords, but Built-in Modules)

#### Process Module Conflict
**Issue**: `src/process/process.py` creates a module path conflict
- **File**: `invasions/src/process/process.py`
- **Import Path**: `src.process.process`
- **Conflict**: The name `process` conflicts with Python's built-in `multiprocessing.process` module
- **Impact**: Can cause import confusion and testing issues

**Current Import Pattern in Tests**:
```python
# This works but is confusing due to duplicate 'process'
from src.process.process import lambda_handler
```

### 2. Directory Structure Analysis

**Current Lambda Structure**:
```
src/
├── bot/
│   └── bot.py          # Handler: lambda_handler
├── invasion/
│   └── invasion.py     # Handler: lambda_handler
├── month/
│   └── month.py        # Handler: lambda_handler
└── process/
    └── process.py      # Handler: lambda_handler (CONFLICT)
```

**Analysis**:
- `bot`, `invasion`, `month` - No conflicts with Python keywords or built-ins
- `process` - Potential conflict with multiprocessing.process module

### 3. Testing Import Issues

**Current Test Import Pattern**:
```python
# Tests correctly use delayed imports to avoid environment issues
@patch.dict(os.environ, {"DISCORD_CMD": "irus"})
def test_something(self):
    from src.bot.bot import lambda_handler  # Import inside test method
    # Test logic here
```

**Issues Identified**:
1. **Environment Variable Dependency**: Lambda modules depend on environment variables being set before import
2. **Import Timing**: Tests must import Lambda handlers after setting up environment
3. **Module Path Clarity**: `src.process.process` is confusing and error-prone

## Recommended Solutions

### Solution 1: Rename Process Module (Recommended)

**Change**: Rename `src/process/process.py` to `src/process/handler.py`

**Benefits**:
- Eliminates potential module name conflict
- Follows AWS Lambda best practice of using `handler.py`
- Maintains consistency with Lambda naming conventions
- No impact on deployment (SAM template uses handler function name)

**Implementation**:
```bash
# Rename the file
mv invasions/src/process/process.py invasions/src/process/handler.py
```

**Update SAM Template**:
```yaml
# template.yaml - Update handler reference
ProcessFunction:
  Type: AWS::Serverless::Function
  Properties:
    CodeUri: src/process/
    Handler: handler.lambda_handler  # Changed from process.lambda_handler
```

**Update Test Imports**:
```python
# Before
from src.process.process import lambda_handler

# After
from src.process.handler import lambda_handler
```

### Solution 2: Standardize All Lambda Handlers (Alternative)

**Change**: Rename all Lambda handler files to `handler.py` for consistency

**Files to Rename**:
- `src/bot/bot.py` → `src/bot/handler.py`
- `src/invasion/invasion.py` → `src/invasion/handler.py`
- `src/month/month.py` → `src/month/handler.py`
- `src/process/process.py` → `src/process/handler.py`

**Benefits**:
- Complete consistency across all Lambda functions
- Follows AWS Lambda best practices
- Eliminates any potential naming confusion
- Clear separation between directory name and handler file

**SAM Template Updates**:
```yaml
BotFunction:
  Properties:
    Handler: handler.lambda_handler

InvasionFunction:
  Properties:
    Handler: handler.lambda_handler

MonthFunction:
  Properties:
    Handler: handler.lambda_handler

ProcessFunction:
  Properties:
    Handler: handler.lambda_handler
```

### Solution 3: Environment Variable Management for Testing

**Issue**: Lambda modules require environment variables to be set before import

**Current Pattern** (Correct):
```python
@patch.dict(os.environ, {"DISCORD_CMD": "irus"})
def test_lambda_function(self):
    # Import AFTER environment is patched
    from src.bot.bot import lambda_handler
    # Test logic
```

**Enhanced Pattern** (Recommended):
```python
@pytest.fixture(autouse=True)
def lambda_environment():
    """Set up Lambda environment variables before any imports."""
    env_vars = {
        "AWS_DEFAULT_REGION": "ap-southeast-2",
        "ENVIRONMENT": "test",
        "LOG_LEVEL": "INFO",
        "DISCORD_CMD": "irus"
    }
    with patch.dict(os.environ, env_vars, clear=False):
        yield

class TestBotLambda:
    def test_lambda_function(self, lambda_environment):
        # Environment is already set up
        from src.bot.handler import lambda_handler
        # Test logic
```

## Implementation Plan

### Phase 1: Address Process Module Conflict (Immediate)

1. **Rename Process Handler**:
   ```bash
   cd invasions/
   mv src/process/process.py src/process/handler.py
   ```

2. **Update SAM Template**:
   ```yaml
   ProcessFunction:
     Properties:
       Handler: handler.lambda_handler
   ```

3. **Update Test Imports**:
   ```python
   # In tests/unit/lambdas/test_process_lambda.py
   from src.process.handler import lambda_handler
   ```

4. **Verify No Import Issues**:
   ```bash
   cd invasions/
   uv run python -c "from src.process.handler import lambda_handler; print('Import successful')"
   ```

### Phase 2: Enhance Testing Environment Management (Optional)

1. **Create Lambda Test Fixture**:
   ```python
   # In tests/conftest.py
   @pytest.fixture(autouse=True, scope="session")
   def lambda_test_environment():
       """Global Lambda testing environment setup."""
       env_vars = {
           "AWS_DEFAULT_REGION": "ap-southeast-2",
           "ENVIRONMENT": "test",
           "LOG_LEVEL": "DEBUG",
           "DISCORD_CMD": "irus"
       }
       with patch.dict(os.environ, env_vars, clear=False):
           yield
   ```

2. **Update Test Files**:
   - Remove individual `@patch.dict` decorators
   - Rely on global fixture for environment setup
   - Import Lambda handlers at module level (after fixture setup)

### Phase 3: Standardize All Handlers (Future Enhancement)

If desired for consistency:

1. **Rename All Handler Files**:
   ```bash
   mv src/bot/bot.py src/bot/handler.py
   mv src/invasion/invasion.py src/invasion/handler.py
   mv src/month/month.py src/month/handler.py
   ```

2. **Update All SAM Template References**
3. **Update All Test Imports**
4. **Update Any Documentation References**

## Validation Steps

### 1. Import Testing
```bash
cd invasions/

# Test each Lambda handler import
uv run python -c "
import os
os.environ['AWS_DEFAULT_REGION'] = 'ap-southeast-2'
os.environ['ENVIRONMENT'] = 'test'
os.environ['DISCORD_CMD'] = 'irus'

from src.bot.bot import lambda_handler as bot_handler
from src.invasion.invasion import lambda_handler as invasion_handler
from src.month.month import lambda_handler as month_handler
from src.process.handler import lambda_handler as process_handler

print('All Lambda handlers imported successfully')
"
```

### 2. Test Execution
```bash
# Run Lambda unit tests to verify imports work
uv run pytest tests/unit/lambdas/ -v

# Run specific test to verify process handler
uv run pytest tests/unit/lambdas/test_process_lambda.py -v
```

### 3. Deployment Validation
```bash
# Validate SAM template
sam validate --template template.yaml

# Test local invocation (if needed)
sam local invoke ProcessFunction --event test-event.json
```

## Files Requiring Updates

### Immediate (Process Module Only)

1. **File Rename**:
   - `src/process/process.py` → `src/process/handler.py`

2. **SAM Template** (`template.yaml`):
   ```yaml
   ProcessFunction:
     Properties:
       Handler: handler.lambda_handler  # Update this line
   ```

3. **Test File** (`tests/unit/lambdas/test_process_lambda.py`):
   ```python
   # Update import statements
   from src.process.handler import lambda_handler
   ```

4. **Integration Tests** (if any reference process handler):
   - Update any integration test imports

### Future (All Handlers)

If implementing full standardization:
- All `src/*/handler.py` files
- All SAM template handler references
- All test file imports
- Documentation updates

## Risk Assessment

### Low Risk Changes
- **Process module rename**: Isolated change, no functional impact
- **SAM template update**: Standard configuration change
- **Test import updates**: Localized to test files

### Validation Required
- **Deployment testing**: Ensure SAM deployment works with new handler name
- **Integration testing**: Verify Lambda functions work in AWS environment
- **Test suite execution**: Ensure all tests pass with new imports

### Rollback Plan
- **File rename**: Simple `mv` command to revert
- **SAM template**: Git revert of template changes
- **Test updates**: Git revert of test file changes

## Conclusion

The primary issue is the `src/process/process.py` module name conflict. The recommended solution is to rename this file to `handler.py` to eliminate the conflict and follow AWS Lambda best practices.

The current test import pattern (importing inside test methods after environment setup) is correct and should be maintained. The environment variable dependency is a legitimate requirement that is properly handled by the existing test structure.

This change will ensure the testing framework can import Lambda modules correctly without conflicts or confusion.
