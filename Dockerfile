FROM python:3.12-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY app/ ./app/
COPY config/ ./config/
COPY scripts/ ./scripts/
COPY tests/ ./tests/

RUN mkdir -p data/input data/output


ENTRYPOINT ["python", "-m", "app.cli"]