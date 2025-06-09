FROM python:3.12-alpine

RUN apk add --no-cache gcc musl-dev python3-dev

WORKDIR /app

COPY . .

RUN pip install -r requirements.txt

CMD ["python", "sensor_client.py"]