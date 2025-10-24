# Contributing to Synapse-NG

Thank you for your interest in contributing to Synapse-NG! This document provides guidelines for contributing to the project.

## Code of Conduct

This project and everyone participating in it is governed by the [Contributor Covenant Code of Conduct](CODE_OF_CONDUCT.md). By participating, you are expected to uphold this code.

## How to Contribute

There are many ways to contribute to Synapse-NG, including:

*   **Reporting bugs:** If you find a bug, please open an issue on GitHub.
*   **Suggesting enhancements:** If you have an idea for a new feature, please open an issue on GitHub.
*   **Writing documentation:** If you see an area where the documentation can be improved, please submit a pull request.
*   **Submitting code:** If you want to contribute code to the project, please follow the steps below.

## Submitting Code

1.  **Fork the repository:** Create your own fork of the Synapse-NG repository.
2.  **Create a feature branch:** Create a new branch for your feature or bug fix.
3.  **Write code:** Write your code, following the coding style guidelines below.
4.  **Write tests:** Add tests for your code to ensure that it is working correctly.
5.  **Submit a pull request:** When you are ready, submit a pull request to the main Synapse-NG repository.

## Coding Style

### Python

We follow the [PEP 8](https://www.python.org/dev/peps/pep-0008/) style guide for Python code. We use the `black` code formatter to ensure a consistent code style.

### Commit Messages

We follow the [Conventional Commits](https://www.conventionalcommits.org/en/v1.0.0/) specification for commit messages. This makes it easier to track changes and automatically generate release notes.

The commit message should be structured as follows:

```
<type>[optional scope]: <description>

[optional body]

[optional footer(s)]
```

**Example:**

```
feat(governance): add weighted voting based on reputation

Implement logarithmic vote weighting using the formula: weight = 1 + log2(reputation + 1).
High-reputation nodes now have more influence in governance decisions.

Closes #42
```
