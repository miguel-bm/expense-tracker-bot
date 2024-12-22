# List all available commands
default:
    @just --list

# Run the application
run:
    uv run python -m app.main

# Format code with ruff
fmt:
    ruff format .

# Check code with ruff
lint:
    ruff check .
