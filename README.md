# Termómetro Web App

Este proyecto implementa un sistema de monitoreo de temperatura utilizando Docker, MQTT y un backend API construido con Flask.

## Características principales

1. **Dockerizado:** Todas las partes del proyecto se ejecutan en contenedores Docker.
2. **Protocolos:** Uso de MQTT para la comunicación entre clientes y el broker Mosquitto.
3. **Simulación:** Simula sensores de temperatura que envían datos al sistema.
4. **Backend:** Implementa una API RESTful para manejar datos y consultar lecturas.

## Requisitos previos

- Docker
- Docker Compose
- Git

## Instalación y ejecución

### Clonar el repositorio

```bash
git clone https://github.com/RictalLime/ProyectoTecnologiasWeb
cd ProyectoTecnologiasWeb/termometro_web_app
```

### Construir y ejecutar los contenedores

```bash
docker-compose up --build
```

Esto iniciará los siguientes servicios:

- **Backend Flask:** Disponible en `http://localhost:5000`
- **Broker MQTT Mosquitto:** Disponible en el puerto `1883`
- **Cliente y servidor simulados**

### Finalizar los servicios

Para detener y eliminar los contenedores:

```bash
docker-compose down
```

## Estructura del proyecto

```
/
├── backend/
│   ├── app.py           # Archivo principal del servidor Flask
│   ├── requirements.txt # Dependencias del backend
├── mqtt/
│   ├── mqtt_server.py   # Cliente MQTT que interactúa con el broker
├── simulation/
│   ├── sensor_client.py # Simulador de sensores de temperatura
├── docker-compose.yml   # Configuración de Docker Compose
```

## Endpoints del API

### Listar termómetros

**GET** `/api/thermometers`

- Retorna una lista de termómetros registrados en el sistema.

### Obtener últimas lecturas

**GET** `/api/readings/latest`

- Devuelve las lecturas de temperatura más recientes por termómetro.

## Simulación de sensores

El archivo `simulation/sensor_client.py` genera datos simulados y los publica al broker MQTT. Estos datos son procesados por el servidor y almacenados en la base de datos.

Para ejecutar el simulador de manera independiente:

```bash
python3 simulation/sensor_client.py
```

---

Este proyecto cumple con las bases para el monitoreo eficiente de sensores de temperatura en tiempo real. Para más información, consulta el código fuente o contacta al desarrollador.

