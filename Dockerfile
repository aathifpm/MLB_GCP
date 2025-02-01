FROM python:3.10-slim

WORKDIR /app

# Copy requirements first to leverage Docker cache
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

# Set environment variable for the port
ENV PORT=8080

# Expose the port
EXPOSE 8080

# Command to run the application
CMD exec uvicorn run_server:app --host 0.0.0.0 --port $PORT 