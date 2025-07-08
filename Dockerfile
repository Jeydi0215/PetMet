# Use Python 3.12 slim image
FROM python:3.12-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Install system dependencies required by psycopg2 and Pillow
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    libjpeg-dev \
    zlib1g-dev \
    curl \
    && apt-get clean

# Install Python dependencies
COPY requirements.txt .
RUN pip install --upgrade pip setuptools wheel
RUN pip install -r requirements.txt

# Copy the rest of the app
COPY . .

# Collect static files (ignore error if settings aren't ready yet)
RUN python manage.py collectstatic --noinput || true
RUN python manage.py migrate || true

# Start Gunicorn
CMD gunicorn PetMet.wsgi:application --bind 0.0.0.0:$PORT
