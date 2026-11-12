import sqlite3
import pandas as pd

DB_NAME = "historico_aula.db"

def calcular_umbral_y_verificar():
    # 1. Conectar a la base de datos local
    try:
        conexion = sqlite3.connect(DB_NAME)
        # Traer solo los datos de temperatura
        query = "SELECT valor FROM lecturas WHERE sensor = 'temperatura'"
        df = pd.read_sql_query(query, conexion)
        conexion.close()
    except Exception as e:
        print(f"Error al leer la base de datos: {e}")
        return

    # Se necesitan al menos unos cuantos datos para que la desviación estándar tenga sentido
    if len(df) < 5:
        print("Aún no hay suficientes datos para calcular el umbral dinámico. Deja el almacenamiento corriendo más tiempo.")
        return

    # 2. Calcular el umbral dinámico (Promedio + 2 Desviaciones Estándar)
    promedio = df['valor'].mean()
    desviacion = df['valor'].std(ddof=0) # ddof=0 para población
    umbral_dinamico = promedio + (2 * desviacion)

    # 3. Obtener la temperatura actual (el último registro guardado)
    temperatura_actual = df['valor'].iloc[-1]

    # 4. Imprimir el reporte en consola
    print("=== ANÁLISIS DE ALERTA DINÁMICA ===")
    print(f"Promedio histórico : {promedio:.2f} °C")
    print(f"Desviación estándar: {desviacion:.2f} °C")
    print(f"Umbral calculado   : {umbral_dinamico:.2f} °C")
    print("-" * 35)
    print(f"Temperatura actual : {temperatura_actual:.2f} °C")

    # 5. Lógica de disparo
    if temperatura_actual > umbral_dinamico:
        print(f"⚠️ ALERTA: La temperatura se desvió del comportamiento normal.")
        print("-> (Aquí se podría integrar un correo o notificación push)")
    else:
        print("✅ Estado normal. La temperatura está dentro del rango esperado.")

if __name__ == "__main__":
    calcular_umbral_y_verificar()