# Project: Tooling Modernization

## Overview
Modernize the development tooling and configuration management for the Discord bot project by migrating to uv for Python environment management, implementing a structured TOML-based configuration system, and adding quality development tools.

## Context
- **Current State**: Using virtualenv + pip, scattered configuration in samconfig.toml, no linting/formatting tools
- **Target State**: Modern Python tooling with uv, centralized config management, dev/prod environments, quality tools
- **Scope**: Tooling and configuration only - no package restructuring or major dependency changes
- **Branch**: All changes to be made on `rework-202509` branch

## Requirements
### Functional Requirements
- [ ] Migrate from virtualenv/pip to uv for environment management
- [ ] Create config.toml with default settings (AWS profile, region, Parameter Store paths)
- [ ] Create config-local.toml for developer overrides (gitignored)
- [ ] Support dev/prod environments in configuration
- [ ] Deploy script accepts environment parameter (defaults to dev)
- [ ] Preserve existing AWS Parameter Store secret paths in config

### Technical Requirements
- [ ] Convert requirements.txt to pyproject.toml with dev/prod dependency groups
- [ ] Update to latest compatible dependency versions
- [ ] Add development tools: ruff, mypy, pytest-cov, pre-commit
- [ ] Config files located in invasions/ directory
- [ ] Deploy script can generate samconfig.toml from config settings

### Quality Requirements
- [ ] All configuration type-safe and validated
- [ ] Clear documentation for setup and usage
- [ ] Backward compatibility with existing deployment process

## Tasks
### Phase 1: Python Environment Migration
- [x] Create pyproject.toml with project metadata
- [x] Migrate dependencies from requirements.txt (update to latest)
- [x] Set up dev dependency group (ruff, mypy, pytest-cov, pre-commit)
- [x] Set up prod dependency group (runtime dependencies)
- [x] Test uv environment creation and dependency installation (NO TEST EXECUTION)
- [x] **REVIEW POINT**: User review and approval of Phase 1 changes
- [ ] **COMMIT**: Add and commit Phase 1 changes

### Phase 2: Configuration System
- [ ] Design config.toml schema (AWS settings, environments, Parameter Store paths)
- [ ] Create default config.toml with dev/prod sections
- [ ] Create config-local.toml template
- [ ] Add config-local.toml to .gitignore
- [ ] Create simple config loading module (no pydantic for now)
- [ ] **REVIEW POINT**: User review and approval of Phase 2 changes
- [ ] **COMMIT**: Add and commit Phase 2 changes

### Phase 3: Development Tools Setup
- [ ] Configure ruff for linting and formatting
- [ ] Configure mypy for type checking
- [ ] Set up pre-commit hooks
- [ ] Configure pytest coverage reporting
- [ ] Update development documentation
- [ ] **REVIEW POINT**: User review and approval of Phase 3 changes
- [ ] **COMMIT**: Add and commit Phase 3 changes

### Phase 4: Deployment Integration
- [ ] Create/update deploy.sh script with environment parameter
- [ ] Implement samconfig.toml generation from config settings
- [ ] Test deployment with dev environment (NO TEST EXECUTION)
- [ ] Document new deployment process
- [ ] **REVIEW POINT**: User review and approval of Phase 4 changes
- [ ] **COMMIT**: Add and commit Phase 4 changes

### Phase 5: New AWS Account Deployment
- [ ] Update config-local.toml with new AWS account profile
- [ ] Test deployment to new account
- [ ] Verify all components work in new environment
- [ ] **REVIEW POINT**: User review and approval of Phase 5 changes
- [ ] **COMMIT**: Add and commit Phase 5 changes

## Files/Areas Involved
- `invasions/pyproject.toml` - New project configuration
- `invasions/config.toml` - Default configuration
- `invasions/config-local.toml` - Local overrides (template)
- `invasions/deploy.sh` - Deployment script
- `.gitignore` - Add config-local.toml
- `invasions/src/` - New config loading module
- `requirements.txt` - Remove after migration
- Development tool configs (ruff.toml, mypy.ini, .pre-commit-config.yaml)

## Success Criteria
- [ ] Can create environment with `uv sync`
- [ ] Linting and formatting work with `uv run ruff`
- [ ] Type checking works with `uv run mypy`
- [ ] Tests run with coverage reporting
- [ ] Deploy script works for both dev and prod
- [ ] Successful deployment to new AWS account
- [ ] All existing functionality preserved

## Dependencies
- uv installed on development machine
- Access to new AWS account with configured profile

## Risks & Considerations
- Dependency version updates might introduce breaking changes
- Configuration changes might affect SAM deployment
- Need to ensure Lambda layer compatibility is maintained
- Must preserve existing Parameter Store integration
- **CRITICAL**: Do not execute tests during this project as they may impact production systems

## Notes
- Keep package structure unchanged for now (future project)
- No pydantic migration in this project (future project)
- Focus on tooling and config management foundations
- Ensure all team members can easily set up development environment

---

## Implementation Log
### [Date] - [Status Update]
- Progress made
- Issues encountered
- Next steps