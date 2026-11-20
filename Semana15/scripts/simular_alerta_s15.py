import sqlite3
import pandas as pd
from datetime import datetime, timezone

DB_NAME = "historico_aula.db"
LOG_FILE = "registro_alertas.log"

def calcular_umbral_dinamico(aula="AULA-101"):
    conexion = sqlite3.connect(DB_NAME)
    query = "SELECT valor FROM lecturas WHERE aula = ? AND sensor = 'temperatura'"
    df = pd.read_sql_query(query, conexion, params=(aula,))
    conexion.close()

    if len(df) < 5:
        return None, None, None

    media = df["valor"].mean()
    desviacion = df["valor"].std(ddof=0)
    umbral = media + (2 * desviacion)
    return media, desviacion, umbral

def inyectar_anomalia(valor_anomalo=36.5, aula="AULA-101"):
    ts_iso = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    conexion = sqlite3.connect(DB_NAME)
    cursor = conexion.cursor()
    cursor.execute(
        "INSERT INTO lecturas (aula, sensor, valor, fecha_hora) VALUES (?, ?, ?, ?)",
        (aula, "temperatura", valor_anomalo, ts_iso)
    )
    conexion.commit()
    conexion.close()
    print(f"[INYECCIÓN] Dato anómalo insertado en SQLite -> {aula}: {valor_anomalo} °C ({ts_iso})")
    return ts_iso

def registrar_log(mensaje):
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(mensaje + "\n")

def ejecutar_prueba_alerta():
    aula = "AULA-101"
    # 1. Calcular el umbral con el comportamiento histórico normal (antes de la anomalía)
    media, desviacion, umbral = calcular_umbral_dinamico(aula)
    if umbral is None:
        print("[Error] No hay suficientes datos históricos en SQLite.")
        return

    print("============================================================")
    print("  SISTEMA DE ALERTAS INTELIGENTES - PRUEBA DE ANOMALÍA S15")
    print("============================================================")
    print(f"Aula evaluada       : {aula}")
    print(f"Promedio histórico  : {media:.2f} °C")
    print(f"Desviación estándar : {desviacion:.2f} °C")
    print(f"Umbral dinámico     : {umbral:.2f} °C  (Media + 2*Desv)")
    print("------------------------------------------------------------")

    # 2. Simular una anomalía térmica real inyectando un dato alto en SQLite
    temp_anomala = round(umbral + 4.5, 2)
    timestamp = inyectar_anomalia(temp_anomala, aula)

    # 3. Evaluar la lectura recién ingresada contra el umbral dinámico
    if temp_anomala > umbral:
        mensaje_alerta = (
            f"[{timestamp}] [ALERTA CRÍTICA] {aula} registró {temp_anomala:.2f} °C, "
            f"superando el umbral dinámico de {umbral:.2f} °C "
            f"(Media: {media:.2f} °C, Desv: {desviacion:.2f} °C)."
        )
        print("\n>>> ¡ALERTA DISPARADA! <<<")
        print(mensaje_alerta)
        registrar_log(mensaje_alerta)
        print(f"\n[OK] Evidencia registrada en '{LOG_FILE}'.")
    else:
        print(f"[NORMAL] {temp_anomala:.2f} °C está dentro del rango permitido.")

if __name__ == "__main__":
    ejecutar_prueba_alerta()