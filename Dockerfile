# Use full Python 3.12.3 image (not slim) for better compatibility
FROM python:3.12.3

# Show Python version in build logs
RUN python --version

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set the working directory
WORKDIR /app

# Install system-level dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    libjpeg-dev \
    zlib1g-dev \
    curl \
    && apt-get clean

# Copy and show requirements for debug
COPY requirements.txt .
RUN cat requirements.txt

# Upgrade pip + install all Python packages
RUN pip install --upgrade pip setuptools==65.5.1 wheel
RUN pip install -r requirements.txt

# Copy Django project files
COPY . .

# Collect static files and apply migrations (won’t fail if settings aren’t complete)
RUN python manage.py collectstatic --noinput || true
RUN python manage.py migrate || true

# Run Gunicorn on assigned port
CMD gunicorn PetMet.wsgi:application --bind 0.0.0.0:$PORT
