# New World Discord Bot - Project Context

## 🔴 CRITICAL - Always Follow

### Project Architecture
- **Discord bot for New World invasion stats tracking** - Extracts statistics from ladder screenshots and generates reports for company management
- **Frontend**: Discord slash commands (`/irus`)
- **Backend**: AWS Lambda functions with API Gateway
- **Database**: DynamoDB for member and invasion data
- **Image Processing**: AWS Textract for ladder screenshot OCR
- **Deployment**: AWS SAM (Serverless Application Model)
- **Language**: Python 3.12

### AWS Commands
- **Always specify profile and region from config** - Never use hardcoded values
- **Always disable AWS pager**: `AWS_PAGER="" aws sts get-caller-identity --profile PROFILE --region REGION`
- **If AWS credentials expired** ("Token has expired") - Stop and ask user to reauthenticate

### Python Environment
- **Always use `uv`** for all Python environment management and commands
- **Tests**: `uv run pytest` (from invasions/ directory)
- **All Python commands**: Use `uv run` prefix

### Critical Safety
- **Read existing code patterns first** - Always examine existing interfaces before implementing, never assume
- **Show actual command output** - Never just claim success, show actual results
- **When tests fail** - Investigate and fix rather than claiming they work

---

## 🟡 IMPORTANT - Usually Follow

### Current Status
- **Active Branch**: rework-202509
- **Recent Work**: Image processing improvements, DynamoDB recovery scripts
- **Known Issues**: Need linting setup, test coverage gaps, inconsistent error handling

### Directory Structure
- `invasions/` - Main application code
  - `src/layer/irus/` - Core business logic
  - `src/bot/` - Discord bot handlers
  - `tests/` - Test suite
  - `discord/` - Command registration
- `projects/` - Project management and documentation

### Development Workflow
- **Prefer editing existing files** over creating new ones
- **Follow existing code patterns** and conventions
- **Test changes** before marking tasks complete
- **Limit commit messages** to 6 lines

### Communication Patterns
- "Here's what I'm thinking..." before acting
- "I've completed X, please review" instead of "task is done"
- Present 2-3 options when there are different approaches
- Ask questions and propose options for decisions

---

## 🟢 REFERENCE - When Relevant

### Future Projects

#### High Priority
1. **Code Quality Foundation** - Linting, formatting, type hints
2. **Test Coverage Expansion** - Unit tests, integration tests, test automation
3. **Error Handling Standardization** - Consistent error patterns and logging
4. **Documentation Improvement** - API docs, code documentation

#### Medium Priority
5. **Performance Optimization** - Image processing, database queries
6. **Security Review** - Input validation, secrets management
7. **Monitoring & Observability** - Better logging, metrics, alerting
8. **Code Refactoring** - Extract utilities, reduce duplication

#### Future Enhancements
9. **Feature Extensions** - New Discord commands, reporting features
10. **Infrastructure Improvements** - CI/CD pipeline, automated deployments
11. **Data Analytics** - Enhanced reporting, trend analysis
12. **Multi-server Support** - Support multiple Discord servers

### Project Management
- Each project has detailed documentation in `projects/[project-name].md`
- Start new conversations for each project
- Reference relevant project file at conversation start
- Update project files as work evolves

### Development Commands
```bash
# Tests
cd invasions/
uv run pytest tests/

# Deploy (use scripts, not direct SAM commands)
./scripts/deploy.sh dev backend

# AWS CLI examples
AWS_PAGER="" aws sts get-caller-identity --profile irus-202509-dev --region ap-southeast-2
AWS_PAGER="" aws dynamodb describe-table --table-name irus-dev-table --profile irus-202509-dev --region ap-southeast-2
```

### Test Development Safety
- **Unique Test Data**: Use helper functions from conftest.py (generate_test_date, get_test_date_components) and timestamp-based identifiers
- **Environment Consistency**: Check integration config and use discovered AWS profile/region, not hardcoded values
- **Verify Success**: Actually run tests and show PASSED output, never assume tests work
- **Safe Cleanup**: Only use cleanup methods that remove test data, never copy or modify production data

### Process Requirements
- **Explicit Verification**: Show actual command output, not just claims of success
- **Pattern Following**: Read existing files to understand current patterns before writing new code
- **Error Investigation**: When tests fail, investigate and fix rather than claiming they work
- **Todo Lists**: Create todo lists for multi-step tasks to track progress methodically
- **Incremental Testing**: Run tests after each significant change, show actual output
