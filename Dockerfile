# Use an official Python runtime as a parent image
FROM python:3.11

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    netcat-openbsd \
    build-essential \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies


COPY app/requirements.txt /app/
COPY setup.py /
COPY alembic.ini /

RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install -e ..

# Copy the application code

COPY app /app/

# Expose the port FastAPI is running on
EXPOSE 8000

# Command to run the application using Uvicorn
RUN chmod +x /app/start.sh
CMD ["/app/start.sh"]
