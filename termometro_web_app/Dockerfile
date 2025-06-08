# Dockerfile
FROM python:3.12-alpine

# Instala dependencias del sistema necesarias para compilar paho-mqtt y SQLite
RUN apk add --no-cache gcc musl-dev libffi-dev python3-dev build-base

# Copia los archivos de la app
WORKDIR /app
COPY . .

# Instala dependencias de Python
RUN pip install flask paho-mqtt

# Expone el puerto Flask (ajústalo si usas otro)
EXPOSE 5000

# Comando para ejecutar Flask
CMD ["python", "app.py"]

# comand para instalar dependencias adicionales
RUN pip install flask flask_cors paho-mqtt

