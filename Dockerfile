FROM python:3.12.3

RUN python --version

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Install general dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    libjpeg-dev \
    zlib1g-dev \
    curl \
    && apt-get clean

# Copy and show requirements
COPY requirements.txt .
RUN cat requirements.txt

# Upgrade pip and build tools
RUN pip install --upgrade pip setuptools==65.5.1 wheel

# Install packages line-by-line to isolate errors (you can later collapse to -r)
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

COPY . .

RUN python manage.py collectstatic --noinput || true
RUN python manage.py migrate || true

CMD gunicorn PetMet.wsgi:application --bind 0.0.0.0:$PORT
