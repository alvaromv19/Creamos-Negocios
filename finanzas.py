import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import extra_streamlit_components as stx # <--- LIBRERÍA NECESARIA

# --- 1. CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="CFO Dashboard | Creamos Negocios", page_icon="💼", layout="wide")

# --- 2. ESTILOS CSS PERSONALIZADOS ---
st.markdown("""
    <style>
    .metric-card {
        background-color: #0E1117;
        border: 1px solid #262730;
        padding: 20px;
        border-radius: 10px;
        text-align: center;
    }
    div[data-testid="stMetricValue"] {
        font-size: 28px;
        font-weight: bold;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 3. PANTALLA DE BIENVENIDA (CON COOKIES) ---
def pantalla_bienvenida():
    # Inicializar el Gestor de Cookies
    cookie_manager = stx.CookieManager(key="cookie_manager_finanzas")
    
    # Verificamos si ya existe la cookie de acceso
    cookie_auth = cookie_manager.get(cookie="acceso_concedido")

    # Si la cookie es válida, pasamos directo
    if cookie_auth == "FinanzasCN2026_OK":
        st.session_state["ingreso_confirmado"] = True
        return True

    # Si ya está en session_state (para la sesión actual), pasamos
    if "ingreso_confirmado" in st.session_state and st.session_state["ingreso_confirmado"]:
        return True

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("<br><br>", unsafe_allow_html=True)
        st.title("💼 CENTRO DE FINANZAS💸")
        st.subheader("Creamos Negocios")
        st.info("Visión financiera de alto nivel: Rentabilidad, ROI y Eficiencia.")
        
        # --- SECCIÓN DE CONTRASEÑA ---
        password = st.text_input("Contraseña de Acceso", type="password", placeholder="Ingresa la clave...")

        if st.button("Acceder a Finanzas CN📊", type="primary", use_container_width=True):
            if password == "FinanzasCN2026":
                # 1. Guardar en Session State (Inmediato)
                st.session_state["ingreso_confirmado"] = True
                
                # 2. Guardar Cookie (Persistente 1 día)
                # expires_at define cuándo caduca. Aquí puesto a 1 día.
                cookie_manager.set("acceso_concedido", "FinanzasCN2026_OK", expires_at=datetime.now() + timedelta(days=1))
                
                # 3. Recargar para aplicar cambios
                st.rerun()
            else:
                st.error("🔒 Contraseña incorrecta. Intenta de nuevo.")
                
    return False

if not pantalla_bienvenida():
    st.stop()

# --- 4. CARGA DE DATOS ---
st.title("💼 Dashboard Financiero & Rentabilidad")

@st.cache_data(ttl=300) 
def cargar_datos():
    # URLS
    url_ventas = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQuXaPCen61slzpr1TElxXoCROIxAgmgWT7pyWvel1dxq_Z_U1yZPrVrTbJfx9MwaL8_cluY3v2ywoB/pub?gid=0&single=true&output=csv"
    url_gastos_dic = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQGOLgPTDLie5gEbkViCbpebWfN9S_eb2h2GGlpWLjmfVgzfnwR_ncVTs4IqmKgmAFfxZTQHJlMBrIi/pub?gid=0&single=true&output=csv"
    url_gastos_anual = "https://docs.google.com/spreadsheets/d/e/2PACX-1vTQKTt_taqoH2qNwWbs3t4doLsi0SuGavgdUNvpCKrqtlp5U9GaTqkTt9q-c1eWBnvPN88Qg5t0vXzK/pub?output=csv"
    
    # Procesar Ventas
    try:
        df_v = pd.read_csv(url_ventas)
        df_v['Fecha'] = pd.to_datetime(df_v['Fecha'], dayfirst=True, errors='coerce')
        if df_v['Monto ($)'].dtype == 'O': 
            df_v['Monto ($)'] = df_v['Monto ($)'].astype(str).str.replace(r'[$,]', '', regex=True)
        df_v['Monto ($)'] = pd.to_numeric(df_v['Monto ($)'], errors='coerce').fillna(0)
        df_v['Resultado'] = df_v['Resultado'].fillna("Pendiente")
        
        def clasificar_estado(texto):
            texto = str(texto).lower()
            if "venta" in texto: return "✅ Venta"
            if "no show" in texto: return "❌ No Show"
            if "descalificado" in texto: return "🚫 Descalificado"
            if "seguimiento" in texto: return "👀 Seguimiento"
            return "Otro/Pendiente"
        df_v['Estado_Simple'] = df_v['Resultado'].apply(clasificar_estado)

        def es_asistencia_valida(row):
            res = str(row['Resultado']).lower()
            if "venta" in res or "seguimiento" in res or "descalificado" in res: return True
            if "asistió" in res and "no show" not in res: return True
            return False
        df_v['Es_Asistencia'] = df_v.apply(es_asistencia_valida, axis=1)
    except:
        df_v = pd.DataFrame()

    # Procesar Gastos
    try:
        df_g1 = pd.read_csv(url_gastos_dic)
        df_g1['Fecha'] = pd.to_datetime(df_g1['Fecha'], dayfirst=True, errors='coerce')
        if df_g1['Gasto'].dtype == 'O': df_g1['Gasto'] = df_g1['Gasto'].astype(str).str.replace(r'[$,]', '', regex=True)
        df_g1['Gasto'] = pd.to_numeric(df_g1['Gasto'], errors='coerce').fillna(0)
        if {'Fecha', 'Gasto'}.issubset(df_g1.columns): df_g1 = df_g1[['Fecha', 'Gasto']]
        
        df_g2 = pd.read_csv(url_gastos_anual)
        df_g2 = df_g2.iloc[:, 0:2]
        df_g2.columns = ['Fecha', 'Gasto'] 
        df_g2['Fecha'] = pd.to_datetime(df_g2['Fecha'], errors='coerce')
        if df_g2['Gasto'].dtype == 'O': df_g2['Gasto'] = df_g2['Gasto'].astype(str).str.replace(r'[$,]', '', regex=True)
        df_g2['Gasto'] = pd.to_numeric(df_g2['Gasto'], errors='coerce').fillna(0)

        df_g = pd.concat([df_g1, df_g2], ignore_index=True).sort_values('Fecha')
    except:
        df_g = pd.DataFrame(columns=['Fecha', 'Gasto'])

    return df_v, df_g

df_ventas, df_gastos = cargar_datos()

if df_ventas.empty:
    st.error("❌ Error de conexión con los datos.")
    st.stop()

# --- 5. SIDEBAR FINANCIERA ---
st.sidebar.header("⚙️ Configuración")

# Filtros de Tiempo
filtro_tiempo = st.sidebar.selectbox(
    "📅 Período de Análisis:",
    ["Este Mes", "Mes Anterior", "Últimos 30 días", "Este Trimestre", "Año Actual"]
)

# Inputs Financieros
st.sidebar.subheader("💰 Estructura de Costos")
meta_fact = st.sidebar.number_input("Meta Facturación ($)", value=30000.0, step=1000.0)
presupuesto_ads = st.sidebar.number_input("Presupuesto Ads ($)", value=5000.0, step=100.0) 
pct_operativo = st.sidebar.slider("% Gastos Operativos (Agencia)", 0, 100, 40, help="Porcentaje de la facturación destinado a equipo, herramientas y gastos fijos.")

# Lógica de Fechas
hoy = pd.to_datetime("today").date()

if filtro_tiempo == "Este Mes":
    f_inicio, f_fin = hoy.replace(day=1), hoy
elif filtro_tiempo == "Mes Anterior":
    primer = hoy.replace(day=1)
    f_fin = primer - timedelta(days=1)
    f_inicio = f_fin.replace(day=1)
elif filtro_tiempo == "Últimos 30 días":
    f_inicio, f_fin = hoy - timedelta(days=30), hoy
elif filtro_tiempo == "Este Trimestre":
    mes_inicio_trimestre = ((hoy.month - 1) // 3) * 3 + 1
    f_inicio = hoy.replace(month=mes_inicio_trimestre, day=1)
    f_fin = hoy
else: # Año Actual
    f_inicio = hoy.replace(month=1, day=1)
    f_fin = hoy

st.sidebar.success(f"Analizando: {f_inicio} ➡ {f_fin}")
st.sidebar.markdown("---")

# Filtrado de DataFrames
mask_v = (df_ventas['Fecha'].dt.date >= f_inicio) & (df_ventas['Fecha'].dt.date <= f_fin)
df_v_filtrado = df_ventas.loc[mask_v].copy()

mask_g = (df_gastos['Fecha'].dt.date >= f_inicio) & (df_gastos['Fecha'].dt.date <= f_fin)
df_g_filtrado = df_gastos.loc[mask_g].copy()

# --- 6. CÁLCULOS FINANCIEROS AVANZADOS ---

# 1. Ingresos y Ventas
facturacion_total = df_v_filtrado['Monto ($)'].sum()
conteo_ventas = len(df_v_filtrado[df_v_filtrado['Estado_Simple'] == "✅ Venta"])
avo = (facturacion_total / conteo_ventas) if conteo_ventas > 0 else 0

# 2. Egresos
gasto_ads = df_g_filtrado['Gasto'].sum()
gasto_operativo = facturacion_total * (pct_operativo / 100)
costo_total = gasto_ads + gasto_operativo

# 3. Resultados
profit_neto = facturacion_total - gasto_ads

# 4. Ratios
roi_custom = (facturacion_total / costo_total) if costo_total > 0 else 0
roas = (facturacion_total / gasto_ads) if gasto_ads > 0 else 0
margen_neto_pct = (profit_neto / facturacion_total * 100) if facturacion_total > 0 else 0

# --- 7. VISUALIZACIÓN DEL DASHBOARD ---

# SECCIÓN 1: ESTADO FINANCIERO (BRUTO + BARRAS)
st.markdown("### 💰 Estado Financiero (Reporte Neto)")

if meta_fact > 0:
    progreso_fact = min(facturacion_total / meta_fact, 1.0)
else:
    progreso_fact = 0

if presupuesto_ads > 0:
    progreso_ads = min(gasto_ads / presupuesto_ads, 1.0)
else:
    progreso_ads = 0

k1, k2, k3, k4 = st.columns(4)

with k1:
    st.metric("Facturación", f"${facturacion_total:,.2f}")
    st.progress(progreso_fact)
    faltante = max(meta_fact - facturacion_total, 0)
    st.caption(f"Meta: ${meta_fact:,.0f} (Faltan ${faltante:,.0f})")

with k2:
    color_profit = "normal" if profit_neto > 0 else "inverse"
    st.metric("Profit", f"${profit_neto:,.2f}", delta=f"{margen_neto_pct:.1f}% Margen", delta_color=color_profit)

with k3:
    st.metric("Inversión Ads", f"${gasto_ads:,.2f}")
    st.progress(progreso_ads)
    st.caption(f"{progreso_ads*100:.1f}% del Budget (${presupuesto_ads:,.0f})")

with k4:
    st.metric("ROAS", f"{roas:.2f}x", delta="Objetivo > 2x") 

st.markdown("---")

# SECCIÓN 2: ESTADO DE RESULTADOS (P&L)
st.markdown("### 📉 Estado de Resultados (P&L)")
r1, r2, r3, r4 = st.columns(4)
r1.metric("Facturación", f"${facturacion_total:,.2f}")
r2.metric("Inversión Ads", f"${gasto_ads:,.2f}")
r3.metric("Gasto Operativo", f"${gasto_operativo:,.2f}", help=f"Equivale al {pct_operativo}% de la facturación")
r4.metric("ROI Global", f"{roi_custom:.2f}x", help="Facturación / (Gasto ads + Gastos Operativos)")

st.markdown("---")

# SECCIÓN 3: UNIT ECONOMICS & UTILIDAD
st.markdown("### 📊 Utilidad & Ticket Promedio (AVO)")
u1, u2, u3, u4 = st.columns(4)
u1.metric("Facturación", f"${facturacion_total:,.2f}")
u2.metric("Gasto Total (Ads+Ops)", f"${costo_total:,.2f}", delta="Costo Estructural", delta_color="inverse")
u3.metric("Utilidad Neta", f"${profit_neto:,.2f}", delta_color="normal" if profit_neto > 0 else "inverse")
u4.metric("Ticket Promedio (AVO)", f"${avo:,.2f}", help="Valor Promedio por Venta Cerrada")

st.markdown("---")

# SECCIÓN 4: GRÁFICOS (WATERFALL & GAUGE)
c1, c2 = st.columns([2, 1])

with c1:
    st.subheader("💧 Flujo de Rentabilidad (Waterfall)")
    fig_waterfall = go.Figure(go.Waterfall(
        name = "20", orientation = "v",
        measure = ["relative", "relative", "relative", "total"],
        x = ["Facturación", "Gasto Ads", "Gastos Ops", "Profit Neto"],
        textposition = "outside",
        text = [f"${facturacion_total/1000:.1f}k", f"-${gasto_ads/1000:.1f}k", f"-${gasto_operativo/1000:.1f}k", f"${profit_neto/1000:.1f}k"],
        y = [facturacion_total, -gasto_ads, -gasto_operativo, profit_neto],
        connector = {"line":{"color":"rgb(63, 63, 63)"}},
        decreasing = {"marker":{"color":"#EF553B"}},
        increasing = {"marker":{"color":"#00CC96"}},
        totals = {"marker":{"color":"#636EFA"}}
    ))
    fig_waterfall.update_layout(title="Desglose: Dónde se va el dinero", showlegend=False, height=400)
    st.plotly_chart(fig_waterfall, use_container_width=True)

with c2:
    st.subheader("🚀 Velocímetro ROI")
    fig_gauge = go.Figure(go.Indicator(
        mode = "gauge+number",
        value = roi_custom,
        title = {'text': "ROI Global"},
        gauge = {
            'axis': {'range': [None, 5]},
            'bar': {'color': "#636EFA"},
            'steps': [
                {'range': [0, 1], 'color': "#EF553B"},
                {'range': [1, 1.5], 'color': "lightgray"},
                {'range': [1.5, 5], 'color': "#00CC96"}
            ],
            'threshold': {'line': {'color': "red", 'width': 4}, 'thickness': 0.75, 'value': 1.0}
        }
    ))
    fig_gauge.update_layout(height=400)
    st.plotly_chart(fig_gauge, use_container_width=True)

# SECCIÓN 5: PROYECCIONES & GRÁFICO DIARIO (MODIFICADO VERTICALMENTE)
st.markdown("---")
st.subheader("📈 Proyecciones & Dinámica Diaria")

# Cálculos de fechas (Se mantienen igual)
dias_mes = (pd.Timestamp(year=hoy.year, month=hoy.month, day=1) + pd.tseries.offsets.MonthEnd(0)).day
dia_actual = hoy.day
progreso_mes = dia_actual / dias_mes
proyeccion_cierre = (facturacion_total / dia_actual * dias_mes) if dia_actual > 0 else 0

# --- CÁLCULO DEL PORCENTAJE PARA EL TEXTO ---
if meta_fact > 0:
    ratio_pacing = facturacion_total / meta_fact
    pct_pacing = ratio_pacing * 100
    barra_valor = min(ratio_pacing, 1.0) # La barra no acepta más de 1.0
else:
    pct_pacing = 0
    barra_valor = 0

# Emoji dinámico: Si vas mejor que el tiempo transcurrido = Fuego, si no = Tortuga
emoji_status = "🔥" if ratio_pacing >= progreso_mes else "🐢"

# --- PARTE 1: PACING CON TEXTO DINÁMICO ---
# Aquí está el cambio: Agregamos el porcentaje al título
st.markdown(f"#### 🎯 Pacing vs Meta: **{pct_pacing:.1f}%** {emoji_status}")
st.progress(barra_valor)

# Usamos columnas INTERNAS solo para las métricas pequeñas, para que queden alineadas
p1, p2, p3 = st.columns(3) 
p1.metric("Meta", f"${meta_fact:,.2f}")
p2.metric("Proyección Cierre", f"${proyeccion_cierre:,.2f}", delta=f"{proyeccion_cierre-meta_fact:,.2f}")
p3.metric("Tiempo Transcurrido", f"{progreso_mes*100:.1f}%")

st.divider() # Línea separadora visual

# --- PARTE 2: GRÁFICO DIARIO (Ahora ocupa todo el ancho y está debajo) ---
st.markdown("#### 📉 Dinámica Diaria: Ingreso, Costo y Utilidad")

if not df_v_filtrado.empty and not df_g_filtrado.empty:
    v_dia = df_v_filtrado.groupby('Fecha')['Monto ($)'].sum().reset_index()
    g_dia = df_g_filtrado.groupby('Fecha')['Gasto'].sum().reset_index()
    
    df_chart = pd.merge(v_dia, g_dia, on='Fecha', how='outer').fillna(0)
    
    # Cálculos
    df_chart['Costo_Real_Diario'] = df_chart['Gasto'] + (df_chart['Monto ($)'] * (pct_operativo/100))
    df_chart['Utilidad_Diaria'] = df_chart['Monto ($)'] - df_chart['Costo_Real_Diario']
    
    # Gráfico
    fig_trend = px.line(
        df_chart, 
        x='Fecha', 
        y=['Monto ($)', 'Costo_Real_Diario', 'Utilidad_Diaria'], 
        color_discrete_map={
            "Monto ($)": "#00CC96",          # Verde
            "Costo_Real_Diario": "#EF553B",  # Rojo
            "Utilidad_Diaria": "#636EFA"     # Azul
        }
    )
    fig_trend.update_layout(hovermode="x unified")
    
    # Al estar fuera de una columna restringida, el gráfico se expandirá más
    st.plotly_chart(fig_trend, use_container_width=True)
else:
    st.info("Falta data diaria para graficar tendencias.")


# SECCIÓN 6: FUNNEL
st.markdown("---")
st.subheader("📢 Eficiencia del Embudo Comercial")

leads = len(df_v_filtrado)
asistencias = df_v_filtrado['Es_Asistencia'].sum()
ventas = len(df_v_filtrado[df_v_filtrado['Estado_Simple'] == "✅ Venta"])

if leads > 0:
    fig_funnel = go.Figure(go.Funnel(
        y = ["Total Leads", "Asistencias", "Ventas Cerradas"],
        x = [leads, asistencias, ventas],
        textinfo = "value+percent initial",
        marker = {"color": ["#636EFA", "#AB63FA", "#00CC96"]}
    ))
    fig_funnel.update_layout(title="Conversión del Embudo", height=350)
    st.plotly_chart(fig_funnel, use_container_width=True)
else:
    st.warning("No hay datos de leads para este período.")
