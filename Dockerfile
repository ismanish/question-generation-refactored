FROM python:3.10-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    python3-dev \
    git \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first (for better cache utilization)
COPY requirements.txt .

# Install standard requirements
RUN pip install --no-cache-dir -r requirements.txt

# Install GraphRAG toolkit from GitHub
RUN pip install --no-cache-dir https://github.com/awslabs/graphrag-toolkit/archive/refs/tags/v3.6.0.zip#subdirectory=lexical-graph

# Copy the rest of the application
COPY . .

# Set environment variables
ENV PYTHONPATH="${PYTHONPATH}:/app"

# Expose port for the API
EXPOSE 8000

# Use the 'main' directory as the starting point
WORKDIR /app/main

# Run the API with Uvicorn when the container starts
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
