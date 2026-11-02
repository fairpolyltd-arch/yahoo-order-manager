# Production Dockerfile for 24/7 Cloud Hosting
FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Install system dependencies for PDF / Excel processing
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy dependency definition and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source code
COPY backend ./backend
COPY run_backend.py .

# Expose port (default 8000 or dynamic $PORT)
EXPOSE 8000

ENV PORT=8000
ENV PYTHONUNBUFFERED=1

# Start the FastAPI server
CMD ["python", "run_backend.py"]
