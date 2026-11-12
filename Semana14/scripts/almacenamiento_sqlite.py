import sqlite3
import time
import requests

# --- 1. Configuración de Adafruit IO ---
AIO_USERNAME = "cupaban" # Ej: "cupaban"
AIO_KEY = "aio_mriE47gnO3rrKe0kPUc7ml1r5fXS"               

FEED_LUZ = "luminosidad"
FEED_TEMP = "temperatura"

# Construimos las URLs para ambos feeds
URL_LUZ = f"https://io.adafruit.com/api/v2/{AIO_USERNAME}/feeds/{FEED_LUZ}/data/last"
URL_TEMP = f"https://io.adafruit.com/api/v2/{AIO_USERNAME}/feeds/{FEED_TEMP}/data/last"

HEADERS = {"X-AIO-Key": AIO_KEY}

# --- 2. Configuración inicial de SQLite ---
DB_NAME = "historico_aula.db"

def inicializar_bd():
    conexion = sqlite3.connect(DB_NAME)
    cursor = conexion.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS lecturas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            aula TEXT,
            sensor TEXT,
            valor REAL,
            fecha_hora TEXT
        )
    ''')
    conexion.commit()
    conexion.close()
    print("[OK] Base de datos lista.")

# --- 3. Funciones de Lectura y Escritura ---
def leer_adafruit(url_feed):
    try:
        respuesta = requests.get(url_feed, headers=HEADERS, timeout=5)
        respuesta.raise_for_status()
        data = respuesta.json()
        return float(data["value"]), data["created_at"]
    except Exception as e:
        print(f"[Error] Fallo al leer feed: {e}")
        return None, None

def guardar_en_sqlite(sensor_nombre, valor, timestamp, aula="AULA-101"):
    try:
        conexion = sqlite3.connect(DB_NAME)
        cursor = conexion.cursor()
        cursor.execute('''
            INSERT INTO lecturas (aula, sensor, valor, fecha_hora)
            VALUES (?, ?, ?, ?)
        ''', (aula, sensor_nombre, valor, timestamp))
        conexion.commit()
        conexion.close()
        print(f"-> Guardado: {aula} | {sensor_nombre}: {valor} | {timestamp}")
    except Exception as e:
        print(f"[Error] Fallo al guardar en SQLite: {e}")

# --- 4. Bucle Principal ---
if __name__ == "__main__":
    print("Iniciando almacenamiento de Luz y Temperatura...")
    inicializar_bd()
    
    ultima_fecha_luz = ""
    ultima_fecha_temp = ""
    
    while True:
        # Procesar Luminosidad
        valor_luz, timestamp_luz = leer_adafruit(URL_LUZ)
        if valor_luz is not None and timestamp_luz != ultima_fecha_luz:
            guardar_en_sqlite(FEED_LUZ, valor_luz, timestamp_luz)
            ultima_fecha_luz = timestamp_luz
            
        # Procesar Temperatura
        valor_temp, timestamp_temp = leer_adafruit(URL_TEMP)
        if valor_temp is not None and timestamp_temp != ultima_fecha_temp:
            guardar_en_sqlite(FEED_TEMP, valor_temp, timestamp_temp)
            ultima_fecha_temp = timestamp_temp
            
        # Esperar 15 segundos para el siguiente ciclo
        time.sleep(15)