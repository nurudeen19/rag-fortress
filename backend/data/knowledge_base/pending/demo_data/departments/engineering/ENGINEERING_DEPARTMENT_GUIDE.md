# ENGINEERING DEPARTMENT GUIDE

**Department:** Engineering and Product Development  
**Last Updated:** November 2025  
**Document ID:** ENG-DEPT-001

## Engineering Department Overview

The Engineering department is responsible for developing, maintaining, and improving RAG Fortress's core platform and products. We follow best practices in software development, emphasizing code quality, security, scalability, and maintainability.

### Department Mission
To build world-class software solutions that solve real customer problems through innovation, collaboration, and a commitment to technical excellence.

### Department Contact Information
- **Engineering Email:** engineering@ragfortress.com
- **Engineering Phone:** (415) 555-0100 ext. 4100
- **VP Engineering:** David Rodriguez - david.rodriguez@ragfortress.com ext. 4101
- **Engineering Leads:** Available by team
- **DevOps/Infrastructure:** devops@ragfortress.com ext. 4150

### Department Structure

**VP of Engineering**
- Overall engineering strategy and execution
- Technology decisions and architecture
- Team leadership and hiring
- Roadmap prioritization with product

**Engineering Leads (2)**
- Platform Lead: Core RAG engine and APIs
- Infrastructure Lead: DevOps, deployment, monitoring

**Senior Software Engineers (4)**
- 10+ years experience
- Technical mentors and architects
- Solve complex technical problems

**Software Engineers (6)**
- 2-10 years experience
- Feature development and improvements
- Code quality and testing

**Junior Software Engineers (3)**
- 0-2 years experience
- Learning and development focused
- Support from senior engineers

**QA/Test Engineers (2)**
- Automated testing framework
- Test case design
- Quality assurance and bug identification

**DevOps Engineers (2)**
- Infrastructure and deployment
- Monitoring and alerting
- Database administration

---

## TECHNOLOGY STACK AND STANDARDS

### Primary Technologies

**Backend:**
- **Language:** Python 3.11+
- **Framework:** FastAPI for REST APIs
- **Async:** asyncio and aiohttp
- **ORM:** SQLAlchemy
- **Testing:** pytest and pytest-asyncio

**Database:**
- **Primary:** PostgreSQL 14+
- **Search:** Elasticsearch 8.0+
- **Cache:** Redis 7.0+
- **Vector Store:** Qdrant (vector database)

**Infrastructure:**
- **Containerization:** Docker
- **Orchestration:** Kubernetes
- **Cloud:** AWS (EC2, S3, RDS, Lambda)
- **IaC:** Terraform for infrastructure management

**Frontend (if applicable):**
- **Framework:** Vue.js 3
- **Package Manager:** npm
- **Build Tool:** Vite
- **UI Components:** Tailwind CSS

### Code Standards and Best Practices

**Python Code Style:**
- Follow PEP 8 style guide
- Use Black for code formatting (line length: 100)
- Use isort for import sorting
- Use flake8 for linting
- Use mypy for type checking

**Documentation:**
- Docstrings for all public functions and classes
- Use Google-style docstrings
- Include type hints for all parameters and returns
- README.md for each module explaining purpose

**Testing:**
- Minimum 80% code coverage
- Unit tests for all functions
- Integration tests for APIs
- Test-driven development encouraged
- Tests run in CI/CD pipeline before merge

**Version Control:**
- Git for all source control
- Branch naming: `feature/ISSUE-XXX-description`, `bugfix/ISSUE-XXX-description`
- Commits: Clear, descriptive commit messages
- Main branch: Production-ready code only
- Dev branch: Integration branch for features

**Security:**
- No hardcoded secrets or credentials
- Use environment variables for configuration
- Security scanning in CI/CD pipeline
- OWASP Top 10 awareness and mitigation
- Regular security audits and penetration testing

---

## DEVELOPMENT WORKFLOW

### Daily Standup

**Frequency:** 10:00 AM every business day  
**Duration:** 15 minutes  
**Format:** Virtual (Zoom/Teams)

**Each Engineer Reports:**
1. What did you accomplish yesterday?
2. What are you working on today?
3. Any blockers or challenges?

**Standup Notes:**
- Recorded and shared in engineering channel
- Blockers addressed immediately or in follow-up
- Focus is collaboration and support

### Sprint Planning

**Frequency:** Every 2 weeks (Thursday)  
**Duration:** 1-2 hours  
**Participants:** All engineers, product manager, VP engineering

**Agenda:**
1. Review product roadmap and upcoming priorities
2. Define sprint goals (1-3 high-level goals)
3. Break down features into tickets
4. Engineers estimate effort in story points (1, 2, 3, 5, 8, 13)
5. Assign tickets to engineers
6. Define sprint success metrics

**Sprint Velocity:**
- Track points completed each sprint
- Target velocity: 40-50 points per sprint
- Adjust capacity if consistently over/under

### Feature Development Process

**Phase 1: Requirements and Design (1-3 days)**
- Product manager writes user story with acceptance criteria
- Engineers review and ask clarifying questions
- Technical design document created
- Architecture review with tech lead
- Approval before implementation begins

**Phase 2: Implementation (3-10 days)**
- Engineer creates feature branch
- Code written following standards
- Unit tests written alongside code
- Self-review before submitting PR
- Code ready for review

**Phase 3: Code Review (1-2 days)**
- PR submitted with description and context
- Two engineers review code
- Feedback provided on design, quality, tests
- Author addresses feedback
- Approval from both reviewers required

**Phase 4: Testing (1-3 days)**
- Automated tests run in CI/CD pipeline
- QA performs manual testing if needed
- Edge cases and error scenarios tested
- Performance testing for critical features
- Security review if handling sensitive data

**Phase 5: Deployment (1 day)**
- Feature merged to develop branch
- Tested in staging environment
- Scheduled for production release
- Release notes prepared
- Deployment to production

### Code Review Standards

**Purpose:**
- Ensure code quality and maintainability
- Share knowledge across team
- Catch bugs before production
- Maintain coding standards
- Improve team capability

**Review Criteria:**
1. **Correctness** - Does the code do what it's supposed to?
2. **Quality** - Is the code well-written and maintainable?
3. **Testing** - Are there adequate tests?
4. **Documentation** - Is the code documented?
5. **Performance** - Could this be optimized?
6. **Security** - Are there security concerns?

**Review Process:**
1. Author submits PR with description
2. Reviewer reads PR and code
3. Runs code locally if needed
4. Leaves comments and questions
5. Author responds to comments
6. Author makes changes if requested
7. Reviewer approves when satisfied

**Review Feedback Rules:**
- Be respectful and constructive
- Ask questions rather than making demands
- Suggest improvements, don't dictate
- Praise good code and approaches
- Avoid nitpicking minor issues

### Branching Strategy

**Branch Types:**

**Main Branch** (production)
- Protected branch (no direct commits)
- Always production-ready
- Deployments from main only
- Must pass all tests and reviews

**Dev Branch** (integration)
- Integration point for features
- Must pass automated tests
- Branches created from dev
- Merged back to dev after review

**Feature Branches**
- Format: `feature/ISSUE-123-description`
- Created from dev branch
- Max 5-7 days active
- Deleted after merge
- Example: `feature/ISSUE-456-add-vector-search`

**Bugfix Branches**
- Format: `bugfix/ISSUE-789-description`
- For production bugs
- Created from main
- Merged to main and dev
- Example: `bugfix/ISSUE-789-fix-memory-leak`

**Hotfix Branches**
- Format: `hotfix/ISSUE-999-description`
- For critical production issues
- Emergency process for severe bugs
- Requires VP Engineering approval

### Pull Request (PR) Guidelines

**PR Title Format:**
`[ISSUE-XXX] Brief description of change`  
Example: `[ISSUE-456] Add semantic search to document retrieval`

**PR Description Must Include:**
1. What does this PR do?
2. Why is this change needed?
3. How does it work? (technical approach)
4. Links to related issues or tickets
5. How to test/verify the change
6. Any breaking changes?
7. Any new dependencies?

**PR Checklist (Author):**
- [ ] Code follows style guide (Black, isort, flake8)
- [ ] Tests added/updated
- [ ] Tests pass locally (100%)
- [ ] Documentation updated if needed
- [ ] No hardcoded secrets or credentials
- [ ] Commit messages are clear
- [ ] No merge conflicts
- [ ] Performance impact assessed
- [ ] Security implications reviewed

**PR Review Checklist (Reviewer):**
- [ ] Understand the purpose and context
- [ ] Code is correct and solves the problem
- [ ] Code quality is good (readable, maintainable)
- [ ] Tests are adequate and pass
- [ ] Documentation is clear
- [ ] No security concerns
- [ ] No performance regressions
- [ ] Follows code standards

---

## TESTING STRATEGY

### Testing Pyramid

**Level 1: Unit Tests (70%)**
- Fast, isolated, focus on single function
- Run in seconds
- Cover all code paths
- Mock external dependencies

**Level 2: Integration Tests (20%)**
- Test interaction between components
- Use real database and services (in test environment)
- Test API endpoints
- Run in minutes

**Level 3: End-to-End Tests (10%)**
- Test complete user workflows
- Test in environment similar to production
- Slow but catch real issues
- Run on schedule or before releases

### Test Naming Convention

`test_<function_name>_<scenario>_<expected_result>`

Examples:
- `test_search_documents_with_empty_query_returns_empty_list`
- `test_user_authentication_with_valid_credentials_returns_token`
- `test_vector_ingestion_with_large_file_completes_successfully`

### Continuous Integration (CI)

**Automated on Every PR:**
1. Code formatting check (Black, isort)
2. Linting check (flake8)
3. Type checking (mypy)
4. Unit tests (pytest)
5. Integration tests
6. Code coverage report
7. Security scanning
8. Build Docker image

**Requirements to Merge:**
- All CI checks pass
- Code coverage >= 80%
- Two approvals from reviewers
- No conflicts with main/dev branch
- All conversations resolved

### Test Coverage Requirements

**Overall:** 80% minimum  
**Critical Path (Auth, Data):** 95% minimum  
**New Code:** 100% coverage required  
**Legacy Code:** 75% minimum

**Coverage Tools:**
- pytest-cov for coverage reporting
- Coverage report generated on every test run
- HTML coverage report available for detailed analysis

---

## DEPLOYMENT AND RELEASE

### Deployment Environments

**Development (Dev)**
- For active feature development
- Deployed multiple times per day
- Unstable, frequent changes
- Accessible to engineering team

**Staging**
- Pre-production environment
- Mirrors production configuration
- Deployed daily from develop branch
- Accessible to QA and product team
- Used for testing before production release

**Production (Prod)**
- Live customer environment
- Deployed from main branch only
- Stable and reliable
- Careful change management
- Monitoring and alerting active

### Release Process

**Step 1: Preparation (1 day before)**
- Ensure all PRs merged and tested
- Release branch created from develop
- Release version number determined (semantic versioning)
- Release notes drafted

**Step 2: Release Branch**
- Format: `release/v1.2.3`
- Created from develop branch
- Only bug fixes allowed on release branch
- No new features

**Step 3: Testing in Staging**
- Release deployed to staging
- QA performs regression testing
- Product team performs acceptance testing
- Critical bugs fixed on release branch
- Bugs merged back to develop

**Step 4: Production Deployment**
- Release branch merged to main
- Main branch tagged with version (v1.2.3)
- Release deployed to production
- Deployment starts early morning (7-9 AM PT)
- During low-usage period when possible

**Step 5: Post-Deployment**
- Monitor application and logs closely (1 hour)
- Monitor metrics and performance
- Check for errors or anomalies
- Rollback plan ready if issues found
- Release notes published

### Version Numbering (Semantic Versioning)

Format: `MAJOR.MINOR.PATCH`  
Example: `2.1.3`

- **MAJOR:** Breaking API changes, significant features (rare)
- **MINOR:** New features, backward compatible
- **PATCH:** Bug fixes, small improvements

**Examples:**
- v1.0.0: Initial product release
- v1.1.0: Added semantic search feature
- v1.1.1: Fixed vector store connection bug
- v2.0.0: Redesigned API (breaking changes)

### Rollback Procedure

**When to Rollback:**
- Critical bugs in production
- Severe performance degradation
- Data corruption or loss
- Security vulnerabilities discovered

**Rollback Steps:**
1. **Identify Issue** - Confirm it's related to deployment
2. **Alert Team** - Notify VP Engineering and on-call engineer
3. **Prepare Rollback** - Get previous version ready
4. **Execute Rollback** - Revert to previous stable version
5. **Verify** - Confirm system stable after rollback
6. **Communicate** - Notify stakeholders of status
7. **Post-Mortem** - Investigate root cause and prevent recurrence

**Rollback Time Target:** 15 minutes from issue identification

---

## MONITORING AND ALERTING

### Key Metrics to Monitor

**Application Metrics:**
- Response time (API latency)
- Error rate
- Request volume/throughput
- Vector search performance
- Database query performance

**Infrastructure Metrics:**
- CPU usage
- Memory usage
- Disk space
- Network bandwidth
- Database connections

**Business Metrics:**
- Document ingestion rate
- Search queries per day
- Average search latency
- Failed searches
- Vector store size

### Alerting Rules

**Critical Alerts (Page On-Call):**
- Error rate > 5% for 5 minutes
- Response time > 2 seconds (p99) for 10 minutes
- Database connection pool exhausted
- Disk space < 10% available
- Vector store unavailable

**Warning Alerts:**
- Error rate > 2% for 10 minutes
- Response time > 1 second (p95) for 10 minutes
- Memory usage > 80%
- CPU usage > 80%
- Slow queries detected

### On-Call Rotation

**Schedule:**
- One engineer on-call per week (Monday-Friday)
- Weekend on-call (rotating)
- 24/7 coverage

**Responsibilities:**
- Respond to critical alerts within 15 minutes
- Investigate and resolve issues
- Escalate if needed
- Document incident and resolution

**Tools:**
- Slack alerts for notifications
- PagerDuty for on-call management
- Datadog for monitoring dashboard

---

## TECHNICAL DEBT AND REFACTORING

### Managing Technical Debt

**Technical Debt Definition:**
Code that needs improvement for quality, performance, or maintainability but isn't breaking functionality.

**Examples:**
- Old, inefficient algorithms
- Duplicated code
- Poor naming or structure
- Missing tests
- Outdated dependencies
- Performance bottlenecks

### Refactoring Process

**Planning:**
- Identify technical debt items
- Estimate effort required
- Prioritize based on impact
- Schedule in sprint (typically 20% of capacity)

**Execution:**
- Create feature branch for refactoring
- Make small, incremental changes
- Add tests to verify behavior
- Commit frequently with clear messages
- Refactor existing tests as needed

**Review:**
- Code review as normal
- Special focus on no functional changes
- Performance benchmarking if relevant
- Verification tests still pass

**Deployment:**
- Merge to develop and main like any feature
- Monitor closely after deployment
- Roll back if any issues

### Dependency Updates

**Regular Updates (monthly):**
- Security patches: Applied immediately
- Minor version updates: Applied in next sprint
- Major version updates: Planned carefully

**Update Process:**
1. Update dependency in requirements.txt or pyproject.toml
2. Run full test suite
3. Check for breaking changes or warnings
4. Update code if needed for compatibility
5. Test thoroughly in staging

---

## DOCUMENTATION AND KNOWLEDGE SHARING

### Architecture Documentation

All major architectural decisions documented:
- Architecture Decision Records (ADRs)
- System design documents
- API documentation (OpenAPI/Swagger)
- Database schema documentation

**Location:** `/docs/architecture/`

### API Documentation

**Format:** OpenAPI 3.0 (Swagger)  
**Location:** Generated from code annotations  
**Tools:** Swagger UI for interactive documentation  
**Requirement:** All endpoints documented with examples

### README Standards

Every repository must have comprehensive README:
- Project description
- Quick start guide
- Installation instructions
- Configuration guide
- Usage examples
- Testing instructions
- Deployment guide
- Contributing guidelines
- License information

### Code Comments and Docstrings

**When to Comment:**
- Why something works this way (not what)
- Complex algorithms or business logic
- Workarounds or hacks (with explanation of why)
- TODOs and known limitations

**When NOT to Comment:**
- Obvious code that reads clearly
- Self-explanatory function names
- Redundant comments that repeat code

**Docstring Format (Google Style):**
```python
def search_documents(query: str, top_k: int = 10) -> List[Document]:
    """Search documents using semantic similarity.
    
    Args:
        query: The search query string.
        top_k: Maximum number of results to return. Defaults to 10.
    
    Returns:
        List of Document objects matching the query, ranked by relevance.
    
    Raises:
        ValueError: If query is empty or top_k is negative.
        ConnectionError: If vector store connection fails.
    """
```

### Meeting Cadence

**Daily:** Engineering Standup (10:00 AM)  
**Weekly:** Engineering Sync (Tuesday 2 PM) - broader topics, blockers  
**Bi-Weekly:** Sprint Planning (Thursday 10 AM)  
**Bi-Weekly:** Sprint Retrospective (Friday 3 PM)  
**Monthly:** Engineering Lunch & Learn (last Friday 12 PM)

---

## HIRING AND ONBOARDING

### Engineering Onboarding

**First Day:**
- Laptop setup and access
- Development environment setup guide
- Repository access and SSH keys
- Slack channels and team introductions

**First Week:**
- Complete code style setup (Black, flake8, mypy)
- Run application locally
- Make first small fix or documentation improvement
- Pair programming with team member
- Architecture overview presentation
- Meet with VP Engineering

**First Month:**
- Complete first feature or bug fix
- Contribute to code review
- Attend all team meetings
- Understand deployment process
- Familiar with testing workflow
- 30-day check-in with manager

### New Engineer Resources

- Development environment setup script
- Local testing guide
- Deployment runbook
- Architecture documentation
- Code style guide checklist
- Pair programming guide

---

## CONTACT AND RESOURCES

**VP Engineering:** David Rodriguez - david.rodriguez@ragfortress.com ext. 4101  
**Platform Lead:** (Contact VP Engineering)  
**Infrastructure Lead:** (Contact VP Engineering)  
**Engineering Email:** engineering@ragfortress.com ext. 4100

**Documentation:**
- GitHub Wiki (code documentation)
- Architecture ADRs in `/docs/architecture/`
- API docs (Swagger UI on staging)
- Deployment runbook
- On-call handbook

---

*This guide is the official engineering handbook. Updates shared during engineering syncs.*
