FROM python:3.10.2

WORKDIR /app

COPY requirements.txt /app/

RUN pip install --no-cache-dir -r requirements.txt

COPY . /app

ENV KAFKA_BROKER=localhost:9092

CMD ["python", "app/main.py"]
