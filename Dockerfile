# Use a specific, stable Python version
FROM python:3.12.3-slim

# Show Python version for verification
RUN python --version

# Set environment variables to prevent .pyc files and buffer logs
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set working directory
WORKDIR /app

# Install system dependencies required by Pillow, psycopg2, and build tools
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    libjpeg-dev \
    zlib1g-dev \
    curl \
    && apt-get clean

# Copy and show requirements.txt (for debugging)
COPY requirements.txt .
RUN cat requirements.txt

# Upgrade pip + install core build tools
RUN pip install --upgrade pip setuptools wheel

# Install dependencies one-by-one to isolate failures
# Comment this line if you want to switch to full batch install
# RUN pip install -r requirements.txt

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

# Copy the rest of your project files
COPY . .

# Run collectstatic and migrations (won't fail the build if settings aren't ready yet)
RUN python manage.py collectstatic --noinput || true
RUN python manage.py migrate || true

# Run Gunicorn on the correct port
CMD gunicorn PetMet.wsgi:application --bind 0.0.0.0:$PORT
