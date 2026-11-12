# 🏫 Proyecto IoT - Semana 14: Almacenamiento Avanzado y Visualización

Este repositorio contiene la implementación de la Fase de Almacenamiento Avanzado para el monitoreo ambiental del aula, superando el límite de 30 días de los planes gratuitos en la nube. 

## 🚀 Tecnologías Utilizadas
* **Hardware:** ESP32, Sensor DHT11 (Temperatura), Sensor LDR digital (Luminosidad).
* **Nube:** Adafruit IO (Broker MQTT).
* **Almacenamiento Local:** Base de datos **SQLite** (ligera, sin necesidad de servidor dedicado).
* **Visualización y Datos:** Python (`pandas`, `plotly`).

## ⚙️ Instrucciones de Instalación
Para ejecutar este proyecto en cualquier computadora con Python instalado, sigue estos pasos:

1. Clonar el repositorio.
2. Instalar las dependencias necesarias ejecutando en la terminal:
   ```bash
   pip install requests pandas plotly
