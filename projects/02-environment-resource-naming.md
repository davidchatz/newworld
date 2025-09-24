# Project: Environment-Aware Resource Naming

## Overview
Embed environment identifiers (dev/prod) into all AWS resource names to enable multi-environment deployments within the same AWS account while maintaining best practices of separate accounts. This ensures complete resource isolation and enables flexible deployment strategies.

## Context
- **Current State**: Stack name includes environment (irus-dev/irus-prod) but individual resources don't consistently embed environment
- **Target State**: All AWS resources explicitly include environment in their names, enabling same-account multi-env deployments
- **Scope**: CloudFormation template, SSM parameter paths, deploy script, and configuration system updates
- **Branch**: All changes to be made on branch `rework-202509`

## Requirements
### Functional Requirements
- [ ] All CloudFormation resources include environment in their logical and physical names
- [ ] S3 bucket naming pattern: `{stack-name}-{account-id}-{region}` (already includes env via stack-name)
- [ ] DynamoDB table naming pattern: `{stack-name}-Table-{suffix}` (already includes env via stack-name)
- [ ] Lambda function naming: `{stack-name}-{function-name}-{suffix}` (already includes env via stack-name)
- [ ] Step Functions naming: `{stack-name}-{state-machine-name}-{suffix}` (already includes env via stack-name)
- [ ] Log Groups naming: `/aws/lambda/{stack-name}-{function-name}` and `/stepfunctions/{stack-name}/{state-machine}`
- [ ] SSM Parameter paths include environment: `/irus-{env}/{parameter-name}`
- [ ] API Gateway naming includes environment identifier

### Technical Requirements
- [ ] Add Environment parameter to CloudFormation template with dev/prod allowed values
- [ ] Update template.yaml to use Environment parameter consistently in resource naming
- [ ] Modify deploy script to pass environment parameter to SAM deploy
- [ ] Update config system to support environment-specific SSM prefixes
- [ ] Ensure backward compatibility with existing deployments
- [ ] Update parameter store path references throughout the application

### Quality Requirements
- [ ] All resource names follow consistent naming convention
- [ ] No hard-coded environment values in templates
- [ ] Clear documentation of new naming patterns
- [ ] Validation that same-account multi-environment deployment works

## Tasks
### Phase 1: CloudFormation Template Updates
- [ ] Add Environment parameter to template.yaml with validation
- [ ] Update all resource logical names to include environment context where beneficial
- [ ] Update log group naming patterns to include environment consistently
- [ ] Update API Gateway naming to include environment
- [ ] Review and update resource descriptions to include environment context
- [ ] **REVIEW POINT**: User review and approval of Phase 1 changes

### Phase 2: SSM Parameter Path Updates
- [ ] Update template.yaml parameter references to use environment-specific SSM paths
- [ ] Modify SsmPrefix parameter to be environment-aware
- [ ] Update all SSMParameterReadPolicy references to new path structure
- [ ] Review Lambda function environment variables for SSM path usage
- [ ] **REVIEW POINT**: User review and approval of Phase 2 changes

### Phase 3: Deploy Script Integration
- [ ] Modify deploy.sh to pass Environment parameter to SAM deploy
- [ ] Update samconfig.toml generation to include environment parameter
- [ ] Ensure environment parameter flows from config system to CloudFormation
- [ ] Update environment variable generation in deploy script
- [ ] **REVIEW POINT**: User review and approval of Phase 3 changes

### Phase 4: Configuration System Updates
- [ ] Update config.toml to reflect new SSM path patterns
- [ ] Ensure config-local.toml examples use new path structure
- [ ] Update config loading module if needed for new patterns
- [ ] Verify environment-specific configuration loading
- [ ] **REVIEW POINT**: User review and approval of Phase 4 changes

### Phase 5: Testing and Validation
- [ ] Cleanup existing dev deployment
- [ ] Deploy dev environment and verify all resources have correct names
- [ ] Test that same-account deployment would work (different resource names)
- [ ] Verify SSM parameter paths are correctly referenced
- [ ] Test environment switching between dev and prod
- [ ] Validate backward compatibility with existing deployments
- [ ] **REVIEW POINT**: User review and approval of Phase 5 changes
- [ ] **COMMIT**: Add and commit all changes

## Files/Areas Involved
- `invasions/template.yaml` - CloudFormation resource naming updates
- `invasions/deploy.sh` - Environment parameter passing
- `invasions/config.toml` - SSM path patterns
- `invasions/config-local.toml` - Example configurations
- `invasions/src/deploy_config.py` - Configuration loading (if changes needed)
- Lambda function code - SSM parameter path references (review only)

## Success Criteria
- [ ] All AWS resources include environment identifier in names
- [ ] SSM parameter paths are environment-specific
- [ ] Deploy script correctly passes environment to CloudFormation
- [ ] Same-account multi-environment deployment is theoretically possible
- [ ] Existing single-account-per-environment deployment continues to work
- [ ] No hard-coded environment values in templates
- [ ] Clear and consistent naming conventions across all resources

## Dependencies
- Completed tooling modernization project (Project 01)
- Access to both dev and prod AWS accounts for testing
- Understanding of current SSM parameter usage in Lambda functions

## Risks & Considerations
- Resource naming changes might affect existing integrations
- SSM parameter path changes require coordination with parameter store setup
- Need to ensure CloudFormation stack updates don't cause resource replacement
- Must maintain backward compatibility during transition
- **CRITICAL**: Verify changes don't break existing deployments

## Notes
- Focus on template-level changes first, application code changes come later
- Environment parameter should be passed from config system, not hard-coded
- Consider future expansion to additional environments (staging, test)
- Ensure naming patterns are consistent with AWS best practices

---

## Implementation Log
### [Date] - [Status Update]
- Progress made
- Issues encountered
- Next steps
