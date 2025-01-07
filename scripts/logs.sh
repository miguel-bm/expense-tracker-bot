#!/usr/bin/env bash
set -euo pipefail

# Load environment variables
source .env

# SSH into server and get docker-compose logs
echo "Fetching logs from ${SERVER_HOST}..."
sshpass -p "${SERVER_PASSWORD}" ssh -o StrictHostKeyChecking=no \
    ${SERVER_USER}@${SERVER_HOST} \
    'cd /root/projects/expense-tracker-bot && docker-compose logs --tail=100 -f' 