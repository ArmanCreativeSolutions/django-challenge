FROM python:3.10-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
RUN useradd --create-home --uid 10001 app && chown -R app:app /app

FROM base AS development
USER app
EXPOSE 8000
CMD ["gunicorn", "volleyball_ticketing.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "3", "--timeout", "30", "--access-logfile", "-"]

FROM base AS production
USER app
EXPOSE 8000
CMD ["gunicorn", "volleyball_ticketing.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "3", "--timeout", "30", "--access-logfile", "-"]

