# Development Rules

## 🔴 CRITICAL - Always Follow

### Behavioral Guidelines
- **Show approach/plan first, then implement after approval**
- **Present options when there are multiple ways to solve something**
- **Ask "Should I proceed with this approach?" before major changes**
- **Never declare tasks "done" - say "I've completed X, please review"**
- **Let the human review and confirm when tasks are actually complete**

### Communication Style
- "Here's what I'm thinking..." before acting
- "I've completed X, please review" instead of "task is done"
- Present 2-3 options when there are different approaches
- Ask questions and propose options for decisions

### Core Technical Rules
- **Use `uv` for all Python environment management and commands**
- **Disable AWS_PAGER with `aws` cli: `AWS_PAGER="" aws command`**
- **Specify AWS profile and region from [config.toml] and [config.local.toml]**
- **Never modify files in URL-Shortener/ directory (reference only)**
- **If you see "security token invalid" - stop and ask for reauthentication**

---

## 🟡 IMPORTANT - Usually Follow

### Development Workflow
- Add and commit files at end of each task (confirm commit message first)
- Deploy and test changes before committing to git
- Keep commit messages under 6 lines and must only describe what changed in those files
- Build and maintain a bash demo script with each function showing good use cases for product owner demos
- Show errors/logs and suggest next steps when things fail
- If you have attempted to fix an issue twice without success, stop and ask for help

### Core Principles
- **Simplicity over complexity** - Choose the simpler solution

### Testing Requirements
- Run pytest directly with uv: `uv run pytest tests/`
- Unit tests for all Lambda functions
- Integration tests against real AWS services
- Ask if I need you to run regression tests before completing each task

---

## 🟢 REFERENCE - When Relevant

### Demo Script Guidelines
- Demo scripts should show the happy path working end-to-end
- Create test users with authentication like integration tests do
- Focus on successful workflows, not error cases (leave that to unit/integration tests)
- Clean up test users and data after demo completes

### Testing Commands
- Run pytest with specific options: `uv run pytest tests/integration/ -v --tb=short`
- Run `sam remote` to invoke lambdas in integration tests

### Deployment Commands
- Encapsulate build, deployment and cleanup in `./scripts/deploy.sh`
- Deploy backend only with `./scripts/deploy.sh dev backend`
- Do not use `sam build` or `sam deploy` outside of the deploy script

### Things to Avoid
- Use custom test wrapper scripts
- Create Lambda layers for shared code

### Steering Documentation Standards
When creating or updating steering files, organize content by criticality:

**Structure Pattern:**
```markdown
# File Title

## 🔴 CRITICAL - Always Follow
### Section Name
- Critical rules that must always be followed

## 🟡 IMPORTANT - Usually Follow
### Section Name
- Important practices and standards

## 🟢 REFERENCE - When Relevant
### Section Name
- Detailed examples, commands, and reference material
```

**Benefits:**
- **Quick scanning** - Most important rules are at the top
- **Clear hierarchy** - Easy to see what matters most
- **Better navigation** - Can jump to appropriate priority level
- **Consistent structure** - All steering files follow same pattern
