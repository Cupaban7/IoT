import sqlite3
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

DB_NAME = "historico_aula.db"

def generar_dashboard():
    # 1. Conectar a SQLite y leer los datos
    try:
        conexion = sqlite3.connect(DB_NAME)
        # Leemos toda la tabla 'lecturas' y la convertimos en un DataFrame de pandas
        query = "SELECT * FROM lecturas"
        df = pd.read_sql_query(query, conexion)
        conexion.close()
    except Exception as e:
        print(f"Error al leer la base de datos: {e}")
        return

    if df.empty:
        print("La base de datos está vacía. Deja que el script de almacenamiento guarde algunos datos primero.")
        return

    # 2. Preparar los datos (convertir la columna de texto a formato fecha/hora real)
    # Adafruit usa un formato ISO (ej. '2026-11-12T22:14:47Z')
    df['fecha_hora'] = pd.to_datetime(df['fecha_hora'])

    # 3. Separar los datos por sensor
    df_temp = df[df['sensor'] == 'temperatura'].copy()
    df_luz = df[df['sensor'] == 'luminosidad'].copy()

    # 4. Crear la figura con múltiples paneles (Subplots)
    # La rúbrica pide al menos 3 paneles. Haremos: Tendencia Temp, Tendencia Luz, y una Tabla.
    fig = make_subplots(
        rows=3, cols=1,
        subplot_titles=("Tendencia de Temperatura", "Tendencia de Luminosidad", "Resumen Estadístico (Temperatura)"),
        specs=[[{"type": "xy"}], [{"type": "xy"}], [{"type": "table"}]]
    )

    # --- Panel 1: Tendencia de Temperatura (Gráfico de Línea) ---
    if not df_temp.empty:
        fig.add_trace(
            go.Scatter(x=df_temp['fecha_hora'], y=df_temp['valor'], mode='lines+markers', name='Temp (°C)', line=dict(color='red')),
            row=1, col=1
        )

    # --- Panel 2: Tendencia de Luminosidad (Gráfico de Línea) ---
    if not df_luz.empty:
        fig.add_trace(
            go.Scatter(x=df_luz['fecha_hora'], y=df_luz['valor'], mode='lines+markers', name='Luz (Lux)', line=dict(color='orange')),
            row=2, col=1
        )

    # --- Panel 3: Tabla de Agregaciones (Promedio, Máx, Mín) ---
    if not df_temp.empty:
        promedio_temp = df_temp['valor'].mean()
        max_temp = df_temp['valor'].max()
        min_temp = df_temp['valor'].min()
        
        # Obtenemos la última fecha registrada para mostrar en la tabla
        ultima_fecha = df_temp['fecha_hora'].max().strftime('%Y-%m-%d')

        fig.add_trace(
            go.Table(
                header=dict(values=['Fecha', 'Promedio (°C)', 'Máxima (°C)', 'Mínima (°C)'],
                            fill_color='paleturquoise', align='center'),
                cells=dict(values=[[ultima_fecha], [f"{promedio_temp:.2f}"], [f"{max_temp:.2f}"], [f"{min_temp:.2f}"]],
                           fill_color='lavender', align='center')
            ),
            row=3, col=1
        )

    # 5. Ajustar diseño y exportar
    fig.update_layout(height=900, title_text="Dashboard de Monitoreo - Proyecto IoT Aula", showlegend=False)
    
    # Exportar a un archivo HTML
    nombre_archivo = "dashboard_aula.html"
    fig.write_html(nombre_archivo)
    print(f"¡Dashboard generado con éxito! Abre el archivo '{nombre_archivo}' en tu navegador web.")

if __name__ == "__main__":
    generar_dashboard()