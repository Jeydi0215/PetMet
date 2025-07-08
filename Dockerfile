# Use full Python 3.12.3 image
FROM python:3.12.3

# Confirm Python version
RUN python --version

# Environment config
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    libjpeg-dev \
    zlib1g-dev \
    curl \
    default-libmysqlclient-dev \
    build-essential \
    && apt-get clean

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --upgrade pip setuptools==65.5.1 wheel

# Optional: Install torch from official CPU wheel index (safer for slim images or slow builds)
# RUN pip install torch --index-url https://download.pytorch.org/whl/cpu

# Install all Python dependencies
RUN pip install -r requirements.txt

# Copy all project files
COPY . .

# Collect static files and run migrations
RUN python manage.py collectstatic --noinput || true
RUN python manage.py migrate || true

# Run the Django app using Gunicorn
CMD gunicorn PetMet.wsgi:application --bind 0.0.0.0:$PORT
