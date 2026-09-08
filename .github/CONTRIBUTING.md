# Contributing to `amocatlas`

Thank you for your interest in contributing to `amocatlas`! 🎉

We welcome contributions of all kinds — from improving documentation, to adding new readers, tests, and features.

Please follow these steps to get started:

## Quick Start

1. **Fork the repository** and clone your fork.
2. **Create a new branch** for your work.
3. **Set up the development environment:**
   - Create a virtual environment
   - Install the package with its development extras:
     ```bash
     pip install -e ".[dev]"
     ```
4. **Make your changes** — remember to write clear commits!
5. **Run tests and quality checks:**
   ```bash
   pytest
   ruff check . && ruff format .
   ```
6. **Push to your fork** and open a pull request.

Your pull request will automatically trigger our continuous integration checks.

## Code Guidelines

- Follow our [coding conventions](https://amoccommunity.github.io/amocatlas/conventions.html).
- Write clear docstrings (NumPy style).
- Add tests for any new features or fixes.
- Keep functions small and focused.

For full details, see our [Developer Guide](https://amoccommunity.github.io/amocatlas/developer_guide.html).

## Communication

If you’re unsure about anything, open a draft PR early or start a discussion. We’re happy to help!

---

*This project guide and contribution workflow were prepared with assistance from ChatGPT to support clear and collaborative development.*

