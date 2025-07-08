# Use a stable Python 3.12 image (non-slim if needed)
FROM python:3.12.3-slim

# Confirm Python version
RUN python --version

# Avoid .pyc files and force unbuffered logs
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set the working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    build-essential \
    libopenblas-dev \
    liblapack-dev \
    libpq-dev \
    libjpeg-dev \
    zlib1g-dev \
    curl \
    && apt-get clean

# Copy and display requirements.txt (for debug)
COPY requirements.txt .
RUN cat requirements.txt

# Upgrade pip and install wheel tools
RUN pip install --upgrade pip setuptools==65.5.1 wheel

# Install Python dependencies individually to isolate errors
RUN pip install django
RUN pip install djangorestframework
RUN pip install djangorestframework-simplejwt
RUN pip install numpy==1.23.5
RUN pip install spacy
RUN pip install nltk
RUN pip install geopy
RUN pip install pytz
RUN pip install psycopg2-binary
RUN pip install dj-database-url
RUN pip install "whitenoise[brotli]"
RUN pip install gunicorn
RUN pip install django-cors-headers
RUN pip install Pillow

# Copy your Django project files
COPY . .

# Collect static files and apply migrations
RUN python manage.py collectstatic --noinput || true
RUN python manage.py migrate || true

# Run the app using Gunicorn on the correct port
CMD gunicorn PetMet.wsgi:application --bind 0.0.0.0:$PORT
