# Contributing to AI Call Agent

We welcome contributions to the AI Call Agent project! This document provides guidelines for contributing.

## Getting Started

1. Fork the repository
2. Clone your fork: `git clone https://github.com/YOUR_USERNAME/Agcai.git`
3. Create a new branch: `git checkout -b feature/your-feature-name`
4. Make your changes
5. Test your changes
6. Commit your changes: `git commit -m "Add feature: your feature name"`
7. Push to your fork: `git push origin feature/your-feature-name`
8. Create a Pull Request

## Development Setup

```bash
# Clone the repository
git clone https://github.com/berndmarcel860-byte/Agcai.git
cd Agcai

# Run setup
chmod +x setup.sh
./setup.sh

# Activate virtual environment
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

## Code Style

- Follow PEP 8 style guide for Python code
- Use meaningful variable and function names
- Add docstrings to all functions and classes
- Keep functions focused and small
- Write comments for complex logic

## Testing

Before submitting a pull request:

1. Ensure all syntax is valid: `python -m py_compile file.py`
2. Test your changes thoroughly
3. Add tests for new functionality
4. Update documentation as needed

## Pull Request Guidelines

- Provide a clear description of the changes
- Reference any related issues
- Keep pull requests focused on a single feature/fix
- Update documentation if needed
- Ensure code passes all checks

## Reporting Issues

When reporting issues, please include:

- Description of the issue
- Steps to reproduce
- Expected behavior
- Actual behavior
- System information (OS, Python version, etc.)
- Relevant logs or error messages

## Code of Conduct

- Be respectful and inclusive
- Focus on constructive feedback
- Help others learn and grow
- Follow the Golden Rule

## Questions?

Feel free to open an issue for questions or discussions.

Thank you for contributing!
