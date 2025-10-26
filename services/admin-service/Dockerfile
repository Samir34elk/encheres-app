FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements from shared
COPY services/shared/requirements.txt /app/shared-requirements.txt
COPY services/admin-service/requirements.txt /app/requirements.txt

# Install Python dependencies
RUN pip install --no-cache-dir -r /app/shared-requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# Copy shared library
COPY services/shared /app/shared

# Copy application code
COPY services/admin-service/app /app/app

# Expose port
EXPOSE 8005

# Run the application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8005"]
