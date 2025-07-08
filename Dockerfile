FROM python:3.12.3-slim

RUN python --version  # ✅ this will print "Python 3.12.3" in build logs

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    libjpeg-dev \
    zlib1g-dev \
    curl \
    && apt-get clean

COPY requirements.txt .
RUN pip install --upgrade pip setuptools wheel
RUN pip install -r requirements.txt

COPY . .

RUN python manage.py collectstatic --noinput || true
RUN python manage.py migrate || true

CMD gunicorn PetMet.wsgi:application --bind 0.0.0.0:$PORT
