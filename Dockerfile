FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 8000
ENV ORINASA_DB_PATH=/app/data/orinasa.sqlite
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
