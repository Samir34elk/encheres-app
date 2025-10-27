FROM python:3.11-slim

WORKDIR /app

# Install system dependencies including Playwright dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    wget \
    gnupg \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements from shared
COPY shared/requirements.txt /app/shared-requirements.txt
COPY scraper-service/requirements.txt /app/requirements.txt

# Install Python dependencies
RUN pip install --no-cache-dir -r /app/shared-requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# Install Playwright browsers
RUN playwright install --with-deps chromium

# Copy shared library
COPY shared /app/shared

# Copy application code
COPY scraper-service/app /app/app

# Expose port
EXPOSE 8003

# Run the application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8003"]
