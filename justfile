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

# Deploy application to server
deploy:
    #!/usr/bin/env bash
    set -euo pipefail
    
    # Load environment variables
    source .env
    
    # Create a temporary directory for deployment
    DEPLOY_DIR=$(mktemp -d)
    echo "Created temp directory: $DEPLOY_DIR"
    
    # First, copy the .env file explicitly
    echo "Copying .env file..."
    cp -v .env "$DEPLOY_DIR/"
    ls -la "$DEPLOY_DIR/.env"
    
    # Then do the rsync, but remove .env from exclusions
    echo "Running rsync..."
    rsync -av . "$DEPLOY_DIR" \
        --exclude '.*' \
        --exclude '__pycache__' \
        --exclude '*.pyc' \
        --exclude '.pytest_cache' \
        --exclude '.ruff_cache' \
        --exclude 'venv' \
        --exclude '.env.example' \
        --exclude '.idea' \
        --exclude '.vscode'

    echo "Checking deployment directory contents:"
    ls -la "$DEPLOY_DIR"
    
    # Double-check .env exists
    if [ ! -f "$DEPLOY_DIR/.env" ]; then
        echo "Error: .env file not found in deployment directory"
        exit 1
    fi
    
    # SSH into server and stop existing containers first
    echo "Stopping existing containers..."
    sshpass -p "${SERVER_PASSWORD}" ssh -o StrictHostKeyChecking=no \
        ${SERVER_USER}@${SERVER_HOST} \
        'cd /root/projects/expense-tracker-bot && docker-compose down'
    
    # Transfer files to server (including hidden files)
    echo "Deploying to ${SERVER_HOST}..."
    sshpass -p "${SERVER_PASSWORD}" scp -o StrictHostKeyChecking=no -r \
        "$DEPLOY_DIR/." \
        ${SERVER_USER}@${SERVER_HOST}:/root/projects/expense-tracker-bot
    
    # Clean up temporary directory
    rm -rf "$DEPLOY_DIR"
    
    # SSH into server and start the application
    echo "Starting application..."
    sshpass -p "${SERVER_PASSWORD}" ssh -o StrictHostKeyChecking=no \
        ${SERVER_USER}@${SERVER_HOST} \
        'cd /root/projects/expense-tracker-bot && docker-compose up -d --build'

# Get logs from the server
logs:
    #!/usr/bin/env bash
    set -euo pipefail
    
    # Load environment variables
    source .env
    
    # SSH into server and get docker-compose logs
    echo "Fetching logs from ${SERVER_HOST}..."
    sshpass -p "${SERVER_PASSWORD}" ssh -o StrictHostKeyChecking=no \
        ${SERVER_USER}@${SERVER_HOST} \
        'cd /root/projects/expense-tracker-bot && docker-compose logs --tail=100 -f'
