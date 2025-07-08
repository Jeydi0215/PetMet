# Use full Python 3.12 image
FROM python:3.12.3

# Print Python version for confirmation
RUN python --version

# Environment config
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set working directory
WORKDIR /app

# Install system-level dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    libjpeg-dev \
    zlib1g-dev \
    curl \
    default-libmysqlclient-dev \
    build-essential \
    && apt-get clean

# Copy and install Python dependencies
COPY requirements.txt .
RUN pip install --upgrade pip setuptools==65.5.1 wheel
RUN pip install -r requirements.txt

# Copy project files
COPY . .

# Collect static files and apply migrations (ignore errors if settings are incomplete)
RUN python manage.py collectstatic --noinput || true
RUN python manage.py migrate || true

# Run app with Gunicorn
CMD gunicorn PetMet.wsgi:application --bind 0.0.0.0:$PORT
