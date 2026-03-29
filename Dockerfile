# 1. Используем официальный образ Python 3.14
FROM python:3.14-slim

# 2. Устанавливаем системные зависимости для работы графики (SDL2)
# Это нужно, чтобы pygame-ce мог инициализироваться внутри Linux-контейнера
RUN apt-get update && apt-get install -y \
    libsdl2-2.0-0 \
    libsdl2-image-2.0-0 \
    libsdl2-mixer-2.0-0 \
    libsdl2-ttf-2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# 3. Рабочая папка
WORKDIR /app

# 4. Устанавливаем конкретную версию pygame-ce
RUN pip install --no-cache-dir pygame-ce==2.5.7

# 5. Копируем файлы игры
COPY . .

# 6. Команда запуска
CMD ["python", "ShooterPlatformer.py"]