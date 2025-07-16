# Используем легкий образ Python
FROM python:3.11-slim

# Устанавливаем рабочую директорию
WORKDIR /app

# Копируем файлы проекта
COPY . .

# Устанавливаем зависимости
RUN pip install --no-cache-dir -r requirements.txt

# Устанавливаем переменные окружения (можно переопределить в Render)
ENV PYTHONUNBUFFERED=1

# Открываем порт (Render ждёт 8080)
EXPOSE 8080

# Запускаем бота
CMD ["python", "bot.py"]
