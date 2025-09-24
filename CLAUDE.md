# New World Discord Bot - Project Overview

## About
Discord bot for New World invasion stats tracking. Extracts statistics from ladder screenshots and generates reports for company management.

## Current Architecture
- **Frontend**: Discord slash commands (`/irus`)
- **Backend**: AWS Lambda functions with API Gateway
- **Database**: DynamoDB for member and invasion data
- **Image Processing**: AWS Textract for ladder screenshot OCR
- **Deployment**: AWS SAM (Serverless Application Model)
- **Language**: Python 3.12

## Directory Structure
- `invasions/` - Main application code
  - `src/layer/irus/` - Core business logic
  - `src/bot/` - Discord bot handlers
  - `tests/` - Test suite
  - `discord/` - Command registration
- `projects/` - Project management and documentation

## Development Commands
- **Tests**: `pytest` (from invasions/ directory)
- **Deploy**: `sam build && sam deploy` (from invasions/ directory)
- **Lint**: [TO BE DETERMINED - needs setup]
- **Format**: [TO BE DETERMINED - needs setup]

## Current Status
- **Active Branch**: rework-202509
- **Recent Work**: Image processing improvements, DynamoDB recovery scripts
- **Known Issues**: Need linting setup, test coverage gaps, inconsistent error handling

## Future Projects

### High Priority
1. **Code Quality Foundation** - Linting, formatting, type hints
2. **Test Coverage Expansion** - Unit tests, integration tests, test automation
3. **Error Handling Standardization** - Consistent error patterns and logging
4. **Documentation Improvement** - API docs, code documentation

### Medium Priority
5. **Performance Optimization** - Image processing, database queries
6. **Security Review** - Input validation, secrets management
7. **Monitoring & Observability** - Better logging, metrics, alerting
8. **Code Refactoring** - Extract utilities, reduce duplication

### Future Enhancements
9. **Feature Extensions** - New Discord commands, reporting features
10. **Infrastructure Improvements** - CI/CD pipeline, automated deployments
11. **Data Analytics** - Enhanced reporting, trend analysis
12. **Multi-server Support** - Support multiple Discord servers

## Project Management
- Each project has detailed documentation in `projects/[project-name].md`
- Start new Claude Code conversations for each project
- Reference relevant project file at conversation start
- Update this file as projects evolve

## Notes for Claude Code
- Always check this file first for context
- Prefer editing existing files over creating new ones
- Follow existing code patterns and conventions
- Test changes before marking tasks complete
- When running `aws` commands always specify the profile and region from the config.
- When running the `aws` cli, always disable the pager so you aren't waiting for me to scroll through output, like this `AWS_PAGER="" aws sts get-caller-identity --profile PROFILE --region REGION`
