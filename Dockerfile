FROM python:3.12-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

COPY pyproject.toml README.md ./

COPY src ./src
COPY config ./config

RUN pip install --no-cache-dir .

COPY data/input ./data/input

RUN mkdir -p data/output

ENTRYPOINT ["sdp"]