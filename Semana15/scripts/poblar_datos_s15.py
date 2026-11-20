import sqlite3
import random
from datetime import datetime, timedelta, timezone

DB_NAME = "historico_aula.db"

def poblar_historico_y_segunda_aula():
    conexion = sqlite3.connect(DB_NAME)
    cursor = conexion.cursor()

    # Asegurar que la tabla exista
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS lecturas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            aula TEXT,
            sensor TEXT,
            valor REAL,
            fecha_hora TEXT
        )
    ''')

    ahora = datetime.now(timezone.utc)
    registros = []

    # Generar lecturas cada 2 horas durante los últimos 7 días para AULA-101 (histórico) y AULA-205
    for horas_atras in range(168, 0, -2):
        ts = ahora - timedelta(hours=horas_atras)
        ts_iso = ts.strftime("%Y-%m-%dT%H:%M:%SZ")
        hora_col = (ts - timedelta(hours=5)).hour  # Hora local Colombia (UTC-5)

        # Curva térmica realista: más fresco en madrugada, más cálido entre 12:00 y 15:00
        ajuste_hora = 2.8 if 11 <= hora_col <= 16 else (-1.8 if hora_col < 6 or hora_col > 20 else 0.5)

        # AULA-101 (histórico previo a tus lecturas reales de hoy)
        if horas_atras > 1:
            temp_101 = round(25.5 + ajuste_hora + random.uniform(-0.8, 0.8), 2)
            luz_101 = 1000.0 if 6 <= hora_col <= 18 else 0.0
            registros.append(("AULA-101", "temperatura", temp_101, ts_iso))
            registros.append(("AULA-101", "luminosidad", luz_101, ts_iso))

        # AULA-205 (aula más cálida por mayor ocupación / exposición solar)
        temp_205 = round(27.2 + ajuste_hora + random.uniform(-0.9, 1.1), 2)
        luz_205 = 1000.0 if 6 <= hora_col <= 19 else 0.0
        registros.append(("AULA-205", "temperatura", temp_205, ts_iso))
        registros.append(("AULA-205", "luminosidad", luz_205, ts_iso))

    cursor.executemany(
        "INSERT INTO lecturas (aula, sensor, valor, fecha_hora) VALUES (?, ?, ?, ?)",
        registros
    )
    conexion.commit()
    conexion.close()
    print(f"[OK] Se insertaron {len(registros)} registros históricos (7 días) para AULA-101 y AULA-205.")
    print("Tus lecturas reales del ESP32 en AULA-101 se mantienen intactas.")

if __name__ == "__main__":
    poblar_historico_y_segunda_aula()