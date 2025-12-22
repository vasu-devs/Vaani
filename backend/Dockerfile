FROM python:3.11-slim

WORKDIR /app

# Install system dependencies (needed for audio processing/LiveKit)
# build-essential is often needed for compiling python packages
RUN apt-get update && apt-get install -y \
    build-essential \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first to leverage Docker cache
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

# Set python path to include current directory
ENV PYTHONPATH=/app

# Default command (can be overridden by the platform to run 'run_agent.py' instead)
CMD ["python", "run_server.py"]
