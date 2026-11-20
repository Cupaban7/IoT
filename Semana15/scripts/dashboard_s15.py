import sqlite3
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

DB_NAME = "historico_aula.db"

def generar_dashboard_s15():
    conexion = sqlite3.connect(DB_NAME)
    df = pd.read_sql_query("SELECT * FROM lecturas", conexion)
    conexion.close()

    if df.empty:
        print("[Error] La base de datos está vacía.")
        return

    # Convertir fechas ISO a hora local Colombia (UTC-5)
    df["fecha_hora"] = pd.to_datetime(df["fecha_hora"], format="ISO8601", utc=True).dt.tz_convert("America/Bogota")
    df = df.sort_values("fecha_hora")

    ahora = df["fecha_hora"].max()
    hace_24h = ahora - pd.Timedelta(hours=24)
    hace_7d = ahora - pd.Timedelta(days=7)

    # Subconjuntos de datos
    df_24h_101 = df[(df["fecha_hora"] >= hace_24h) & (df["aula"] == "AULA-101")]
    df_24h_temp_101 = df_24h_101[df_24h_101["sensor"] == "temperatura"]
    df_24h_luz_101 = df_24h_101[df_24h_101["sensor"] == "luminosidad"]

    df_7d_temp = df[(df["fecha_hora"] >= hace_7d) & (df["sensor"] == "temperatura")].copy()
    df_temp_101 = df_7d_temp[df_7d_temp["aula"] == "AULA-101"]
    df_temp_205 = df_7d_temp[df_7d_temp["aula"] == "AULA-205"]

    # Cálculo del Umbral Dinámico para AULA-101 (Media + 2*Desviación Estándar)
    media_101 = df_temp_101["valor"].mean()
    std_101 = df_temp_101["valor"].std(ddof=0)
    umbral_preventivo = media_101 + std_101       # Zona amarilla (Media + 1*sigma)
    umbral_dinamico = media_101 + (2 * std_101)   # Zona roja (Media + 2*sigma)
    temp_actual = df_temp_101["valor"].iloc[-1]

    # Agregaciones diarias (últimos 7 días)
    df_7d_temp["dia"] = df_7d_temp["fecha_hora"].dt.strftime("%Y-%m-%d")
    resumen = (
        df_7d_temp.groupby(["dia", "aula"])["valor"]
        .agg(Promedio="mean", Maxima="max", Minima="min")
        .reset_index()
        .sort_values(["dia", "aula"], ascending=[False, True])
    )

    # Crear cuadrícula de 4 paneles (2x2)
    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=(
            "1. Tendencia Temp. y Luminosidad – AULA-101 (Últimas 24h)",
            "2. Comparativa de Temperatura: AULA-101 vs AULA-205",
            "3. Agregaciones Diarias – Última Semana (Temp. °C)",
            f"4. Estado Actual AULA-101 (Umbral Dinámico: {umbral_dinamico:.2f} °C)"
        ),
        specs=[
            [{"secondary_y": True}, {"type": "xy"}],
            [{"type": "table"}, {"type": "indicator"}]
        ],
        vertical_spacing=0.14,
        horizontal_spacing=0.08
    )

    # --- PANEL 1: Tendencia Temp y Luminosidad (24h) ---
    fig.add_trace(
        go.Scatter(
            x=df_24h_temp_101["fecha_hora"], y=df_24h_temp_101["valor"],
            mode="lines+markers", name="Temp AULA-101 (°C)",
            line=dict(color="#E53E3E", width=2.5), marker=dict(size=5)
        ),
        row=1, col=1, secondary_y=False
    )
    fig.add_trace(
        go.Scatter(
            x=df_24h_luz_101["fecha_hora"], y=df_24h_luz_101["valor"],
            mode="lines", name="Luz AULA-101 (Lux)",
            line=dict(color="#D69E2E", width=1.8, dash="dot"),
            fill="tozeroy", fillcolor="rgba(214, 158, 46, 0.12)"
        ),
        row=1, col=1, secondary_y=True
    )

    # --- PANEL 2: Comparativa entre 2 Aulas ---
    fig.add_trace(
        go.Scatter(
            x=df_temp_101["fecha_hora"], y=df_temp_101["valor"],
            mode="lines", name="AULA-101 (°C)",
            line=dict(color="#2B6CB0", width=2.2)
        ),
        row=1, col=2
    )
    fig.add_trace(
        go.Scatter(
            x=df_temp_205["fecha_hora"], y=df_temp_205["valor"],
            mode="lines", name="AULA-205 (°C)",
            line=dict(color="#DD6B20", width=2.2)
        ),
        row=1, col=2
    )

    # --- PANEL 3: Tabla de Agregaciones Diarias (7 días) ---
    fig.add_trace(
        go.Table(
            header=dict(
                values=["<b>Fecha</b>", "<b>Aula</b>", "<b>Promedio (°C)</b>", "<b>Máxima (°C)</b>", "<b>Mínima (°C)</b>"],
                fill_color="#1B365D",
                font=dict(color="white", size=12),
                align="center",
                height=30
            ),
            cells=dict(
                values=[
                    resumen["dia"],
                    resumen["aula"],
                    resumen["Promedio"].map(lambda x: f"{x:.2f}"),
                    resumen["Maxima"].map(lambda x: f"{x:.2f}"),
                    resumen["Minima"].map(lambda x: f"{x:.2f}")
                ],
                fill_color=[["#F7FAFC", "#EDF2F7"] * (len(resumen) // 2 + 1)],
                font=dict(color="#1A202C", size=11),
                align="center",
                height=24
            )
        ),
        row=2, col=1
    )

    # --- PANEL 4: Gauge con colores Verde / Amarillo / Rojo según Umbral Dinámico ---
    rango_max = max(42.0, round(temp_actual + 4, 1), round(umbral_dinamico + 6, 1))
    color_barra = "#38A169" if temp_actual < umbral_preventivo else ("#D69E2E" if temp_actual <= umbral_dinamico else "#E53E3E")

    fig.add_trace(
        go.Indicator(
            mode="gauge+number+delta",
            value=temp_actual,
            number={"suffix": " °C", "font": {"size": 36}},
            delta={"reference": media_101, "suffix": " °C vs media", "increasing": {"color": "#E53E3E"}, "decreasing": {"color": "#38A169"}},
            gauge={
                "axis": {"range": [15, rango_max], "tickwidth": 1},
                "bar": {"color": color_barra, "thickness": 0.3},
                "bgcolor": "white",
                "steps": [
                    {"range": [15, umbral_preventivo], "color": "rgba(56, 161, 105, 0.30)"},
                    {"range": [umbral_preventivo, umbral_dinamico], "color": "rgba(214, 158, 46, 0.35)"},
                    {"range": [umbral_dinamico, rango_max], "color": "rgba(229, 62, 62, 0.35)"}
                ],
                "threshold": {
                    "line": {"color": "#9B2C2C", "width": 4},
                    "thickness": 0.8,
                    "value": umbral_dinamico
                }
            }
        ),
        row=2, col=2
    )

    # Selector interactivo (Dropdown de filtro de aulas para el Panel 2)
    # Trazas en orden: [0] Temp101(24h), [1] Luz101(24h), [2] Comp101, [3] Comp205, [4] Tabla, [5] Gauge
    fig.update_layout(
        title=dict(
            text="<b>Dashboard Consolidado IoT – Monitoreo Ambiental UTS (Semana 15)</b>",
            x=0.5, font=dict(size=20, color="#1B365D")
        ),
        template="plotly_white",
        height=920,
        margin=dict(t=110, b=40, l=50, r=50),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        updatemenus=[
            dict(
                type="dropdown",
                direction="down",
                x=0.01, y=1.09,
                xanchor="left", yanchor="top",
                bgcolor="#EDF2F7",
                bordercolor="#CBD5E0",
                buttons=[
                    dict(label="Filtro Comparativa: Ambas Aulas", method="update",
                         args=[{"visible": [True, True, True, True, True, True]}]),
                    dict(label="Solo AULA-101 (ESP32 Real)", method="update",
                         args=[{"visible": [True, True, True, False, True, True]}]),
                    dict(label="Solo AULA-205 (Referencia)", method="update",
                         args=[{"visible": [True, True, False, True, True, True]}]),
                ]
            )
        ]
    )

    # Etiquetas de ejes
    fig.update_yaxes(title_text="Temperatura (°C)", row=1, col=1, secondary_y=False)
    fig.update_yaxes(title_text="Luminosidad (Lux)", row=1, col=1, secondary_y=True, range=[0, 1200])
    fig.update_yaxes(title_text="Temperatura (°C)", row=1, col=2)

    archivo_salida = "dashboard_consolidado_s15.html"
    fig.write_html(archivo_salida)
    print(f"[OK] Dashboard generado: {archivo_salida}")
    print(f"     Media AULA-101: {media_101:.2f} °C | Desv. Est.: {std_101:.2f} °C | Umbral Dinámico: {umbral_dinamico:.2f} °C")

if __name__ == "__main__":
    generar_dashboard_s15()