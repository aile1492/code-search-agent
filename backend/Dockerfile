FROM python:3.12-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY app/ app/

# Create directories for runtime data
RUN mkdir -p models chroma_db

# Expose port
EXPOSE 8002

# Start server
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8002"]
