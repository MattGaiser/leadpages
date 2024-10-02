FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

WORKDIR /app

COPY ../app/requirements.txt /app/
RUN pip install --upgrade pip && pip install -r requirements.txt

COPY ../app/ /app/

CMD ["celery", "-A", "leadpages_etl", "worker", "--loglevel=info", "--concurrency=4"]
