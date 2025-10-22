# Contributing to Synapse-NG

Thank you for your interest in contributing to Synapse-NG! This document provides guidelines and instructions for contributing to the project.

## 🚀 Getting Started

### Prerequisites

- Python 3.9 or higher
- Docker and Docker Compose
- `jq` (for running test scripts)
- Git

### Setting Up Your Development Environment

1. **Fork and clone the repository**

```bash
git clone https://github.com/fabriziosalmi/synapse-ng.git
cd synapse-ng
```

2. **Install dependencies**

```bash
pip install -r requirements.txt
```

3. **Run a local node**

```bash
# Using Docker
docker-compose up --build

# Or run locally
python -m uvicorn app.main:app --reload --port 8000
```

4. **Verify the setup**

```bash
# Check node status
curl http://localhost:8000/state | jq

# Run the test suite
./test_suite.sh
```

## 🧪 Testing

**All contributions must include tests.** Before submitting a pull request:

1. **Run the complete test suite**

```bash
./test_suite.sh
```

2. **Add tests for new features**

- Add unit tests for new functions/classes
- Add integration tests for new features
- Update `test_suite.sh` if needed

3. **Test your changes in different modes**

```bash
# Rendezvous mode
docker-compose up --build

# Pure P2P mode
docker-compose -f docker-compose.p2p.yml up --build
```

## 💻 Code Style

### Python Code Style

We follow [PEP 8](https://pep8.org/) with some additional conventions:

- **Formatter**: Use `black` for code formatting
- **Line length**: 100 characters (configured in `pyproject.toml` if present)
- **Imports**: Group imports as: stdlib → third-party → local
- **Type hints**: Use type hints for function signatures

```python
# Good
def create_task(title: str, channel_id: str) -> dict:
    """Create a new task in the specified channel."""
    return {"id": generate_id(), "title": title, "channel": channel_id}

# Bad
def create_task(title, channel_id):
    return {"id": generate_id(), "title": title, "channel": channel_id}
```

### Formatting Your Code

```bash
# Install black
pip install black

# Format your code
black app/ rendezvous/
```

## 📝 Commit Messages

Follow the [Conventional Commits](https://www.conventionalcommits.org/) specification. See [docs/COMMIT_MESSAGE.md](docs/COMMIT_MESSAGE.md) for detailed guidelines.

### Format

```
<type>(<scope>): <subject>

<body>

<footer>
```

### Types

- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `test`: Test additions/changes
- `refactor`: Code refactoring
- `perf`: Performance improvements
- `chore`: Build/tooling changes

### Examples

```
feat(governance): add weighted voting based on reputation

Implement logarithmic vote weighting using formula: weight = 1 + log2(reputation + 1).
High-reputation nodes now have more influence in governance decisions.

Closes #42
```

```
fix(webrtc): prevent connection leak when peer disconnects

Added proper cleanup of RTCPeerConnection objects and DataChannel listeners
when a peer disconnects unexpectedly.

Fixes #87
```

## 🔄 Pull Request Process

### Before Submitting

1. **Create a feature branch**

```bash
git checkout -b feat/my-new-feature
# or
git checkout -b fix/issue-123
```

2. **Make your changes**

- Write clean, documented code
- Add tests for new functionality
- Update documentation as needed

3. **Test thoroughly**

```bash
# Run all tests
./test_suite.sh

# Test specific scenarios
./test_webrtc.sh
./test_p2p.sh
./test_network_operations.sh
```

4. **Commit your changes**

```bash
git add .
git commit -m "feat(scope): description"
```

5. **Push to your fork**

```bash
git push origin feat/my-new-feature
```

### Submitting the Pull Request

1. Go to the main Synapse-NG repository
2. Click "New Pull Request"
3. Select your fork and branch
4. Fill out the PR template with:
   - **Title**: Clear, descriptive title following commit message conventions
   - **Description**: What changes were made and why
   - **Testing**: How you tested the changes
   - **Related Issues**: Link to related issues (e.g., "Closes #42")

### PR Review Process

- Maintainers will review your PR within a few days
- Address any requested changes
- Once approved, your PR will be merged

## 🐛 Reporting Bugs

Use GitHub Issues to report bugs. Include:

1. **Environment**
   - OS and version
   - Python version
   - Docker version (if applicable)

2. **Steps to reproduce**
   - Exact steps to trigger the bug
   - Expected behavior
   - Actual behavior

3. **Logs and errors**
   - Relevant log output
   - Error messages
   - Stack traces

4. **Additional context**
   - Screenshots (if applicable)
   - Configuration files
   - Network topology (number of nodes, mode, etc.)

### Example Bug Report

```markdown
**Environment:**
- OS: Ubuntu 22.04
- Python: 3.10.2
- Docker: 20.10.12

**Steps to reproduce:**
1. Start 3 nodes in P2P mode
2. Create a task on node-1
3. Wait 30 seconds
4. Check task on node-3

**Expected:** Task appears on node-3
**Actual:** Task not found on node-3

**Logs:**
```
[node-3] ERROR: Failed to process MESSAGE: KeyError 'channel'
```

**Additional context:**
All nodes subscribed to `dev_ui` channel via `SUBSCRIBED_CHANNELS`.
```

## 💡 Suggesting Features

We welcome feature suggestions! Before opening an issue:

1. **Check existing issues** to avoid duplicates
2. **Describe the use case** - what problem does it solve?
3. **Propose a solution** - how would you implement it?
4. **Consider alternatives** - are there other ways to solve this?

### Feature Request Template

```markdown
**Problem:**
Describe the problem or limitation this feature would address.

**Proposed Solution:**
Describe how you envision this feature working.

**Alternatives Considered:**
List alternative approaches you've considered.

**Additional Context:**
Any other relevant information, examples, or references.
```

## 🏗️ Architecture Guidelines

When contributing, please respect these architectural principles:

### Core Principles

1. **Decentralization First**
   - No mandatory central servers
   - All features must work in pure P2P mode
   - Rendezvous server is optional for convenience only

2. **CRDT Convergence**
   - All state changes must converge deterministically
   - Use Last-Write-Wins (LWW) or appropriate CRDT
   - No server-side authority for conflict resolution

3. **Topic-Based Communication**
   - Use SynapseSub protocol for all gossip
   - Respect channel subscriptions
   - No direct node-to-node state synchronization

4. **Schema Validation**
   - All data structures must have schemas (see `app/schemas.py`)
   - Validate at creation and gossip time
   - Reject invalid data early

### Adding New Features

When adding a new feature:

1. **Define the schema** in `app/schemas.py`
2. **Add API endpoints** in `app/main.py`
3. **Implement gossip logic** using SynapseSub topics
4. **Add CRDT merge logic** for state convergence
5. **Write comprehensive tests** in `test_suite.sh`
6. **Document in `docs/`** if it's a major feature

## 📚 Documentation

### When to Update Documentation

- **New features**: Add detailed documentation in `docs/`
- **API changes**: Update `docs/API_EXAMPLES.md`
- **Architecture changes**: Update `docs/SYNAPSE_COMPLETE_ARCHITECTURE.md`
- **Breaking changes**: Add migration guide

### Documentation Style

- Use clear, concise language
- Include code examples
- Add diagrams for complex flows
- Keep examples up to date with code

## 🤝 Community Guidelines

- **Be respectful** and constructive
- **Help others** learn and grow
- **Share knowledge** through issues and discussions
- **Collaborate** openly and transparently

## 📞 Getting Help

- **GitHub Issues**: For bugs and feature requests
- **GitHub Discussions**: For questions and general discussion
- **Documentation**: Check `docs/` for detailed guides

## 🙏 Recognition

Contributors will be recognized in:
- Git commit history
- Release notes
- Project documentation (if major contribution)

Thank you for contributing to Synapse-NG! 🧠✨
