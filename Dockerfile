FROM python:3.12-slim

WORKDIR /app

# Копируем файлы проекта
COPY pyproject.toml /app/
COPY app/ /app/app/

# Устанавливаем uv и зависимости из pyproject.toml
RUN pip install --upgrade pip uv \
    && uv venv \
    && . .venv/bin/activate \
    && uv pip install .

EXPOSE 8300

CMD ["uvicorn", "app.main:app", "--host", "127.0.0.2", "--port", "8300"]
