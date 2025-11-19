FROM python:3.11-slim

WORKDIR /app

# Install system dependencies including Playwright dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    wget \
    gnupg \
    libnss3 \
    libatk-bridge2.0-0 \
    libatk1.0-0 \
    libgtk-3-0 \
    libdrm2 \
    libgbm1 \
    libxkbcommon0 \
    libxcb1 \
    libxrandr2 \
    libxdamage1 \
    libxcomposite1 \
    libasound2t64 \
    libatspi2.0-0 \
    libdbus-1-3 \
    libxext6 \
    libxfixes3 \
    fonts-unifont \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements from shared
COPY services/shared/requirements.txt /app/shared-requirements.txt
COPY services/scraper-service/requirements.txt /app/requirements.txt

# Install Python dependencies
RUN pip install --no-cache-dir -r /app/shared-requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# Install Playwright browsers
RUN playwright install chromium

# Copy shared library
COPY services/shared /app/shared

# Copy application code
COPY services/scraper-service/app /app/app

# Expose port
EXPOSE 8003

# Run the application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8003"]
