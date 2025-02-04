FROM python:3.10-slim

WORKDIR /app

# Create directory for Google Cloud credentials and frontend directories
RUN mkdir -p /tmp/keys && chmod 755 /tmp/keys \
    && mkdir -p frontend/templates \
    && mkdir -p frontend/static

# Copy requirements first to leverage Docker cache
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt \
    && pip install gunicorn

# Copy the frontend files first
COPY frontend/templates frontend/templates/
COPY frontend/static frontend/static/

# Copy the rest of the application
COPY . .

# Set proper permissions
RUN chmod -R 755 frontend/

# Expose the port (Cloud Run will set PORT env var)
EXPOSE 8080

# Command to run the application with gunicorn
CMD exec gunicorn run_server:app -w 4 -k uvicorn.workers.UvicornWorker -b :$PORT 