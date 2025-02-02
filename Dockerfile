FROM python:3.10-slim

WORKDIR /app

# Copy requirements first to leverage Docker cache
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt \
    && pip install gunicorn

# Copy the rest of the application
COPY . .

# Expose the port (Cloud Run will set PORT env var)
EXPOSE 8080

# Command to run the application with gunicorn
CMD exec gunicorn run_server:app -w 4 -k uvicorn.workers.UvicornWorker -b :$PORT 