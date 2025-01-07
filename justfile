# List all available commands
default:
    @just --list

# Build the application
build:
    docker build -t expense-tracker-bot .

# Run the application
run:
    docker-compose down
    export DEBUG=True && docker-compose up --build

# Format code with ruff
fmt:
    ruff format .

# Check code with ruff
lint:
    ruff check .

# Deploy application to server
deploy:
    chmod +x scripts/deploy.sh
    ./scripts/deploy.sh

# Get logs from the server
logs:
    chmod +x scripts/logs.sh
    ./scripts/logs.sh
