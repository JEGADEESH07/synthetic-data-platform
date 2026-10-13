FROM python:3.12-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

COPY pyproject.toml README.md ./

COPY src ./src
COPY config ./config

# Install CPU-only PyTorch before the application dependencies.
RUN pip install --no-cache-dir \
    --index-url https://download.pytorch.org/whl/cpu \
    "torch==2.14.1+cpu"

# Install the platform and its remaining dependencies.
RUN pip install --no-cache-dir .

RUN mkdir -p data/input data/output/jobs

EXPOSE 8000

CMD ["uvicorn", "synthetic_data.api.app:app", "--host", "0.0.0.0", "--port", "8000"]