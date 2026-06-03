FROM python:3.13

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV HF_HOME=/var/cache/huggingface

# Слой 1: PyTorch CPU (не в requirements.txt — кэшируется отдельно)
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install \
    torch==2.11.0+cpu \
    --extra-index-url https://download.pytorch.org/whl/cpu

# Слой 2: остальные зависимости
COPY requirements.txt /app/requirements.txt
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install -r /app/requirements.txt

# Слой 3: код приложения (модели HF — при первом запуске в volume, см. docker-compose)
COPY . /app

EXPOSE 8000

CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]