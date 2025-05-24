.PHONY: install install-dev lint format test pre-commit setup-hooks

# Install production dependencies
install:
	pip install -r requirements.txt

# Install all dependencies including dev
install-dev: install
	pre-commit install

# Run linting
lint:
	ruff check .

# Run formatting
format:
	ruff check --fix .
	ruff format .

# Run tests
test:
	pytest tests/ -v

# Run pre-commit on all files
pre-commit:
	pre-commit run --all-files

# Set up git hooks
setup-hooks:
	pre-commit install
	@echo "✅ Pre-commit hooks installed!"
	@echo "Hooks will now run automatically on git commit."
	@echo "To run manually: make pre-commit"
