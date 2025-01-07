#!/bin/bash

# Check if .env file exists
if [ ! -f .env ]; then
    echo "Error: .env file not found"
    exit 1
fi

# Source the .env file to get TELEGRAM_BOT_TOKEN
source .env

# Check if TELEGRAM_BOT_TOKEN is set
if [ -z "$TELEGRAM_BOT_TOKEN_DEV" ]; then
    echo "Error: TELEGRAM_BOT_TOKEN not found in .env file"
    exit 1
fi

# Function to make API call and get updates
get_updates() {
    curl -s "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN_DEV}/getUpdates" | \
    jq -r '.result[] | "\nChat ID: \(.message.chat.id)\nChat Type: \(.message.chat.type)\nTitle/Name: \(.message.chat.title // .message.chat.first_name)\nTimestamp: \(.message.date)"' | \
    sort -u
}

# Check if jq is installed
if ! command -v jq &> /dev/null; then
    echo "Error: jq is not installed. Please install it first."
    echo "You can install it using:"
    echo "  - For Ubuntu/Debian: sudo apt-get install jq"
    echo "  - For MacOS: brew install jq"
    echo "  - For CentOS/RHEL: sudo yum install jq"
    exit 1
fi

echo "Fetching recent chats..."
RESULT=$(get_updates)

if [ -z "$RESULT" ]; then
    echo "No recent messages found. Make sure:"
    echo "1. Your bot token is correct"
    echo "2. The bot has received some messages"
    echo "3. The messages are not too old (Telegram only keeps recent updates)"
else
    echo "Recent chats where the bot received messages:"
    echo "$RESULT"
fi