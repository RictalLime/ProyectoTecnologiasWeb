FROM python:3.12-alpine

RUN apk add --no-cache gcc musl-dev libffi-dev python3-dev build-base sqlite

WORKDIR /app

COPY . .

RUN pip install -r requirements.txt

EXPOSE 5000

CMD ["python", "app.py"]