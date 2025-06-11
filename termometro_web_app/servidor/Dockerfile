FROM python:3.12-alpine

RUN apk add --no-cache gcc musl-dev python3-dev

WORKDIR /app

COPY . .

RUN pip install paho-mqtt

CMD ["python", "mqtt_server.py"]