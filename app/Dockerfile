# ---------------------------------------------------
# Stage 1: Build dependencies
# ---------------------------------------------------
FROM python:3.11-slim AS builder

WORKDIR /build

# Отключаем генерацию .pyc и включаем unbuffered-вывод логов
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Устанавливаем системные зависимости для сборки C-расширений (если понадобятся)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Создаем виртуальное окружение и устанавливаем зависимости
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# ---------------------------------------------------
# Stage 2: Final Runtime Image
# ---------------------------------------------------
FROM python:3.11-slim AS runner

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/opt/venv/bin:$PATH" \
    PYTHONPATH=/app

# Копируем виртуальное окружение из этапа builder
COPY --from=builder /opt/venv /opt/venv

# Создаем директорию для Shared Volume и системного пользователя без root-прав
RUN mkdir -p /var/shared \
    && adduser --disabled-password --gecos "" appuser \
    && chown -R appuser:appuser /app /var/shared

# Копируем исходный код приложения (контекст - папка app/)
COPY --chown=appuser:appuser . /app

# Переключаемся на безопасного пользователя
USER appuser

EXPOSE 11000

# Запуск Uvicorn сервера
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "11000"]