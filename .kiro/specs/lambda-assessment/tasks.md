# Implementation Plan

- [x] 1. Manual Lambda function inventory
  - Read and document each Lambda function in `src/bot/`
  - Identify handler names, purposes, and current imports
  - Create simple inventory document with basic metadata
  - _Requirements: 1.1, 1.2_

- [x] 2. Dependency analysis and mapping
- [x] 2.1 Analyze current Lambda dependencies
  - List all imports from `src/layer/irus/` used by each Lambda
  - Identify legacy facade usage (`member.py`, `invasion.py`, `ladder.py`)
  - Document direct model usage and AWS SDK calls
  - _Requirements: 2.1, 2.3, 2.4_

- [x] 2.2 Map to modern equivalents
  - Map legacy facade usage to modern repositories and services
  - Document which modern services should replace current business logic
  - Identify AWS calls that should move to repositories
  - _Requirements: 2.2, 2.5_

- [x] 3. Risk assessment and migration planning
- [x] 3.1 Assess migration complexity
  - Evaluate each Lambda's complexity and migration effort based on dependency analysis
  - Identify high-risk migrations (Bot and Process Lambdas require 5 new services)
  - Document service layer prerequisites for each Lambda migration
  - Document rollback strategies for each Lambda
  - _Requirements: 3.1, 3.5_

- [x] 3.2 Create migration order and service dependencies
  - Determine logical order for Lambda modernization based on service dependencies
  - Group Lambda functions by complexity (Month=Low, Invasion=Medium, Bot/Process=High)
  - Plan incremental deployment approach with service layer development first
  - Document which services must be built before each Lambda can be modernized
  - _Requirements: 4.2, 4.5_

- [x] 4. Create Lambda testing framework design
- [x] 4.1 Design Lambda testing patterns
  - Create templates for unit testing Lambda functions with `IrusContainer`
  - Design integration testing approach with real AWS resources
  - Create Discord event fixtures for common scenarios
  - _Requirements: 5.1, 5.3_

- [x] 4.2 Create testing examples
  - Write example tests for each type of Lambda function
  - Show how to mock dependencies using modern container pattern
  - Document testing best practices for Lambda functions
  - _Requirements: 5.2, 5.4, 5.5_

- [x] 5. Create migration templates and documentation
- [x] 5.1 Build migration templates
  - Create before/after code examples for common Lambda patterns
  - Show how to modernize Lambda handlers to use repositories/services
  - Include templates for the 5 missing services identified in analysis
  - Include error handling and logging patterns with IrusContainer
  - _Requirements: 4.1, 4.3_

- [x] 5.2 Document migration process and service prerequisites
  - Write step-by-step migration guide for each Lambda type
  - Document service layer development requirements before Lambda migration
  - Include testing and validation procedures for both services and Lambdas
  - Document deployment and rollback procedures
  - _Requirements: 7.2, 7.3_

- [x] 6. Service layer gap analysis
- [x] 6.1 Design missing service interfaces
  - Create interface designs for the 5 missing services identified
  - Define service contracts and dependencies for each missing service
  - Document integration points with existing repositories and services
  - _Requirements: 4.4, 6.1_

- [x] 6.2 Estimate service development effort
  - Assess complexity and development time for each missing service
  - Identify shared patterns and reusable components across services
  - Document testing requirements for each new service
  - _Requirements: 6.2, 6.3_

- [x] 7. Update project documentation
- [x] 7.1 Create Lambda inventory report
  - Compile assessment findings into comprehensive report
  - Include migration recommendations and timeline estimates
  - Document service layer prerequisites and development effort
  - Document risks and mitigation strategies
  - _Requirements: 7.1_

- [x] 7.2 Update steering documentation
  - Add Lambda-specific patterns to steering docs
  - Include testing guidelines for Lambda functions
  - Document modern Lambda development practices
  - Document service layer development patterns
  - Include environment variable management patterns for Lambda testing
  - _Requirements: 7.4_

- [x] 7.3 Address Python keyword conflicts
  - Identify and resolve directory/file naming conflicts with Python keywords
  - Update import statements and references throughout codebase
  - Ensure testing framework can import Lambda modules correctly
  - _Requirements: 5.1, 5.2_

- [x] 7.4 Prepare next project specifications
  - Create detailed specifications for Lambda modernization projects
  - Include timeline estimates and resource requirements (service development + Lambda migration)
  - Document success criteria and validation approaches
  - Create separate project specs for service layer development vs Lambda migration
  - _Requirements: 7.5_
