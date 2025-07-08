# Use Python 3.12 image
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Install system packages (for some wheels like psycopg2 or mysqlclient)
RUN apt-get update && apt-get install -y gcc libpq-dev

COPY requirements.txt .
RUN pip install --upgrade pip setuptools wheel
RUN pip install -r requirements.txt

COPY . .

RUN python manage.py collectstatic --noinput || true
RUN python manage.py migrate || true

CMD gunicorn PetMet.wsgi:application --bind 0.0.0.0:$PORT
