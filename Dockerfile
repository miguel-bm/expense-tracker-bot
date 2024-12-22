FROM python:3.12.5-slim

# Set working directory
WORKDIR /expense-tracker-bot

# Install system dependencies and uv
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && curl -LsSf https://astral.sh/uv/install.sh | sh

# Copy dependency files
COPY pyproject.toml .

# Install dependencies using uv
RUN uv sync

# Copy application code
COPY app app/

# Expose the port the app runs on
EXPOSE 8000

# Command to run the application
CMD ["python", "-m", "app.main"]
