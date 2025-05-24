# Contributing to FlyCast

Thank you for considering contributing to FlyCast! This document provides guidelines and instructions for contributing.

## Code of Conduct

Please be respectful and considerate when interacting with others in this project. Harassment or abusive behavior will not be tolerated.

## How Can I Contribute?

### Reporting Bugs

If you encounter a bug, please create an issue using the bug report template. Include as much detail as possible:

- Steps to reproduce the bug
- Expected behavior
- Actual behavior
- Screenshots if applicable
- Your environment (macOS version, Python version, etc.)

### Suggesting Features

Have an idea for a new feature? Create an issue using the feature request template with a clear description of what you'd like to see.

### Pull Requests

1. Fork the repository
2. Create a new branch for your changes
3. Make your changes
4. Test your changes
5. Submit a pull request

When submitting a pull request, please:

- Reference any related issues
- Include a clear description of the changes
- Update documentation as needed
- Follow the existing code style

## Development Setup

1. Clone the repository
2. Create a virtual environment:
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```
3. Create a `.env` file with your Fireflies API key
4. Make the scripts executable:
   ```bash
   chmod +x *.py *.sh
   ```

## Style Guidelines

- Follow PEP 8 for Python code
- Use descriptive variable and function names
- Add comments for complex logic
- Keep functions small and focused

## Testing

- Test your changes on macOS
- Verify that the scripts work with Raycast
- Check for any Python exceptions or warnings

Thank you for your contributions!
