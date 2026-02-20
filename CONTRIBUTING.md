# Contributing to Justice Apex Skills

We welcome contributions from the community! This document provides guidelines for contributing.

## Getting Started

1. **Fork the repository** on GitHub
2. **Clone your fork**: `git clone https://github.com/YOUR_USERNAME/skills.git`
3. **Create a branch**: `git checkout -b feature/your-feature-name`
4. **Make your changes** and test thoroughly
5. **Commit with clear messages**: `git commit -m "feat: describe your change"`
6. **Push to your fork**: `git push origin feature/your-feature-name`
7. **Open a Pull Request** against the main repository

## Development Setup

```bash
# Clone repository
git clone https://github.com/justice-apex/skills.git
cd skills

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements-dev.txt

# Run tests
pytest tests/

# Run with coverage
pytest tests/ --cov=skills --cov-report=html
```

## Code Standards

### Python Style
- Follow PEP 8
- Use type hints for all function parameters and return values
- Include comprehensive docstrings (Google style)
- Aim for 85%+ test coverage

### Testing
- Write tests for all new features
- Update existing tests when modifying behavior
- All tests must pass before submitting PR
- Use `pytest` for test execution

### Documentation
- Update README.md for user-facing changes
- Add docstrings to all classes and functions
- Create examples for new features
- Update API.md for new endpoints/functions

## Commit Message Format

```
type(scope): subject

body

footer
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (no logic change)
- `refactor`: Code refactoring
- `perf`: Performance improvements
- `test`: Adding/updating tests
- `chore`: Build, deps, or tooling changes

**Examples:**
```
feat(confidence-gate): add weighted risk adjustment

fix(llm-router): fix fallback on timeout

docs(evolution-engine): add genealogy tracking example
```

## Pull Request Process

1. **Ensure tests pass**: Run `pytest tests/` locally
2. **Update documentation**: Reflect your changes in relevant docs
3. **Add changelog entry**: Note your changes (if applicable)
4. **Self-review**: Check your code before submitting
5. **Describe changes**: Clear PR description explaining what and why
6. **Link issues**: Reference any related issues (#123)
7. **Request review**: Tag maintainers for review

## Review Process

- **Automated checks** will run on your PR (tests, linting, coverage)
- **Maintainers** will review for quality and fit with project goals
- **Feedback** may be requested - we value collaborative improvement
- **Approval** once all checks pass and reviewers approve
- **Merge** by maintainer once approved

## Reporting Issues

### Bug Reports
Include:
- Clear title describing the issue
- Steps to reproduce
- Expected behavior
- Actual behavior
- Python version, OS, environment
- Code example (if applicable)
- Error message/traceback

### Feature Requests
Include:
- Clear title and description
- Use case and motivation
- Proposed solution (if any)
- Alternative approaches considered

## Community Guidelines

- **Be respectful**: We welcome diverse perspectives
- **Be constructive**: Provide helpful feedback
- **Be collaborative**: Work together to improve
- **Be inclusive**: All skill levels welcome
- **No harassment**: Violations of community standards will be handled

## Questions?

- Check existing documentation in `docs/`
- Search existing issues for answers
- Ask in GitHub Discussions
- Open an issue if stuck

## Recognition

Contributors are recognized in:
- GitHub Contributors page
- Release notes
- Project documentation

Thank you for contributing to Justice Apex Skills! 🏛️
