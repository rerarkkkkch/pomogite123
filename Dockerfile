
FROM python:3.10-slim

# Устанавливаем рабочую директорию внутри контейнера
WORKDIR /app

# Копируем файл с зависимостями
COPY requirements.txt .

# Устанавливаем зависимости. Флаг --no-cache-dir уменьшает размер образа
RUN pip install --no-cache-dir -r requirements.txt

# Копируем всё остальное содержимое проекта в контейнер
COPY . .

# Открываем порт, который использует Streamlit
EXPOSE 8501

# Команда для запуска приложения
# --server.address=0.0.0.0 обязательно, чтобы приложение было доступно извне контейнера [citation:3][citation:7][citation:12]
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
