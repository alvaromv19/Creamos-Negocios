import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import pytz # Librería para manejar zonas horarias

# --- 1. CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Launch VDP", page_icon="🚀", layout="wide")

# Estilos CSS
st.markdown("""
<style>
    .stTabs [data-baseweb="tab-list"] { gap: 2px; }
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        white-space: pre-wrap;
        background-color: #0e1117;
        border-radius: 4px 4px 0px 0px;
        gap: 1px;
        padding-top: 10px;
        padding-bottom: 10px;
    }
    .stTabs [aria-selected="true"] {
        background-color: #262730;
        border-bottom: 2px solid #ff4b4b;
    }
    div[data-testid="stMetricValue"] { font-size: 28px; }
</style>
""", unsafe_allow_html=True)

# --- FUNCIÓN DE VISUALIZACIÓN (Salida en Pantalla) ---
def formato_euro(valor, decimales=0):
    if valor is None: return "0"
    if decimales == 0:
        return "{:,.0f}".format(valor).replace(",", ".")
    else:
        return "{:,.2f}".format(valor).replace(",", "X").replace(".", ",").replace("X", ".")

# --- 2. CARGA Y LIMPIEZA DE DATOS ---
@st.cache_data(ttl=300) 
def cargar_datos_vdp():
    url = 'https://docs.google.com/spreadsheets/d/e/2PACX-1vR726VKYI1xIW9q5U50lN2iqY58-SIyN9gusKo_t8h2-HkTa7zERkSrQ6F4OUnTB2AWEh4CSvfwdZRL/pub?gid=0&single=true&output=csv'
    try:
        # Cargamos todo como STRING para evitar problemas de interpretación
        df = pd.read_csv(url, dtype=str) 
        df.columns = df.columns.str.strip()
        
        # --- LIMPIEZA DE NÚMEROS (EUROPEA) ---
        def force_european_format(x):
            if pd.isna(x) or str(x).strip() in ["", "-"]:
                return 0.0
            
            x = str(x).replace('$', '').replace(' ', '').replace('%', '')
            x = x.replace('.', '') # Quitar miles
            x = x.replace(',', '.') # Coma decimal a punto
            
            try: return float(x)
            except ValueError: return 0.0

        cols = ['Spent', 'Clicks', 'Visitas LP', 'Leads Hyros', 'API Hyros', 'Grupo']
        for col in cols:
            if col in df.columns:
                df[col] = df[col].apply(force_european_format)
        
        # --- LIMPIEZA DE FECHAS ROBUSTA ---
        if 'Fecha' in df.columns:
            # Convertir a datetime, errores se convierten en NaT (Not a Time)
            df['Fecha'] = pd.to_datetime(df['Fecha'], dayfirst=True, errors='coerce')
            # ELIMINAR FILAS SIN FECHA VÁLIDA (Esto evita el error de fecha)
            df = df.dropna(subset=['Fecha'])
            df = df.sort_values('Fecha')
            
        return df
    except Exception as e:
        st.error(f"Error crítico cargando datos: {e}")
        return pd.DataFrame()

df = cargar_datos_vdp()

# --- 3. SIDEBAR Y ZONA HORARIA ---
st.sidebar.title("🎛️ Control de Mando")

# Debugger
mostrar_raw = st.sidebar.checkbox("🔍 Modo Debug", value=False)
if mostrar_raw:
    st.write("Data Procesada:", df.head())

st.sidebar.caption("Filtros Globales (Zona: America/Bogota)")

# --- CONFIGURACIÓN DE ZONA HORARIA ---
zona_horaria = pytz.timezone('America/Bogota')
hoy = datetime.now(zona_horaria).date() # FECHA CORRECTA SEGÚN TU ZONA

filtro_tiempo = st.sidebar.selectbox(
    "📅 Período de Análisis:",
    ["Este Mes", "Mes Anterior", "Hoy", "Ayer", "Últimos 7 días", "Últimos 30 días", "Personalizado"]
)

# Lógica de fechas ajustada a la variable 'hoy' corregida
if filtro_tiempo == "Hoy": f_inicio, f_fin = hoy, hoy
elif filtro_tiempo == "Ayer": f_inicio, f_fin = hoy - timedelta(days=1), hoy - timedelta(days=1)
elif filtro_tiempo == "Últimos 7 días": f_inicio, f_fin = hoy - timedelta(days=7), hoy
elif filtro_tiempo == "Este Mes": f_inicio, f_fin = hoy.replace(day=1), hoy
elif filtro_tiempo == "Mes Anterior":
    primer = hoy.replace(day=1)
    f_fin = primer - timedelta(days=1)
    f_inicio = f_fin.replace(day=1)
elif filtro_tiempo == "Últimos 30 días": f_inicio, f_fin = hoy - timedelta(days=30), hoy
else:
    f_inicio = st.sidebar.date_input("Inicio", hoy - timedelta(days=7))
    f_fin = st.sidebar.date_input("Fin", hoy)

f_inicio = pd.to_datetime(f_inicio)
f_fin = pd.to_datetime(f_fin)

# Filtro de Dataframe
mask = (df['Fecha'] >= f_inicio) & (df['Fecha'] <= f_fin)
df_filtrado = df.loc[mask].copy()

if df_filtrado.empty:
    st.warning(f"⚠️ No hay datos para el período seleccionado ({f_inicio.date()} al {f_fin.date()}).")
    st.stop()

# --- 4. TABS Y DASHBOARD ---
tab1, tab2, tab3 = st.tabs(["🚀 FASE 1: CAPTACIÓN", "🔥 FASE 2: NUTRICIÓN", "💰 FASE 3: VENTA"])

with tab1:
    # A. KPI CALCULATIONS
    spend = df_filtrado['Spent'].sum()
    leads = df_filtrado['Leads Hyros'].sum()
    api = df_filtrado['API Hyros'].sum()
    grupo = df_filtrado['Grupo'].sum()
    visitas = df_filtrado['Visitas LP'].sum()
    clicks = df_filtrado['Clicks'].sum()
    
    dias_activos = (df_filtrado['Fecha'].max() - df_filtrado['Fecha'].min()).days + 1
    if dias_activos < 1: dias_activos = 1

    cpl = spend / leads if leads > 0 else 0
    cpa = spend / api if api > 0 else 0
    cpg = spend / grupo if grupo > 0 else 0
    daily_spend = spend / dias_activos

    # B. METRICS
    st.markdown("### 🎯 Métricas Principales")
    k1, k2, k3, k4 = st.columns(4)

    k1.metric("💸 Inversión Total", f"${formato_euro(spend, 0)}", f"Actual ${formato_euro(daily_spend, 0)} / día", delta_color="off")
    k2.metric("👥 Leads (Hyros)", f"{formato_euro(leads, 0)}", f"CPL: ${formato_euro(cpl, 2)}", delta_color="inverse")
    k3.metric("🤖 Leads API", f"{formato_euro(api, 0)}", f"CPA: ${formato_euro(cpa, 2)}", delta_color="inverse")
    k4.metric("📲 Grupo WhatsApp", f"{formato_euro(grupo, 0)}", f"CPG: ${formato_euro(cpg, 2)}", delta_color="inverse")

    st.markdown("---")

    # C. CHARTS
    st.subheader("📈 Tendencia de Tráfico & Costos")
    
    daily = df_filtrado.groupby('Fecha').agg({
        'Spent': 'sum', 'Leads Hyros': 'sum', 'API Hyros': 'sum', 'Grupo': 'sum'
    }).reset_index()
    
    daily['CPL_Dia'] = daily.apply(lambda x: x['Spent']/x['Leads Hyros'] if x['Leads Hyros'] > 0 else 0, axis=1)
    
    fig_electro = go.Figure()

    # Volumen
    fig_electro.add_trace(go.Scatter(x=daily['Fecha'], y=daily['Leads Hyros'], name='Leads', 
                         mode='lines+markers', line=dict(color='#00CC96', width=3), marker=dict(size=6)))
    fig_electro.add_trace(go.Scatter(x=daily['Fecha'], y=daily['API Hyros'], name='API', 
                         mode='lines+markers', line=dict(color='#636EFA', width=3), marker=dict(size=6)))
    fig_electro.add_trace(go.Scatter(x=daily['Fecha'], y=daily['Grupo'], name='Grupo', 
                         mode='lines+markers', line=dict(color='#AB63FA', width=3), marker=dict(size=6)))

    # Costos
    fig_electro.add_trace(go.Scatter(x=daily['Fecha'], y=daily['CPL_Dia'], name='CPL ($)', 
                         mode='lines', line=dict(color='#EF553B', width=1, dash='dot'), yaxis='y2'))

    fig_electro.update_layout(
        height=450,
        hovermode="x unified",
        separators=",.", 
        xaxis=dict(showgrid=False),
        yaxis=dict(title="Volumen (Cantidad)", showgrid=True, gridcolor='#2c2f38'),
        yaxis2=dict(title="Costo Unitario ($)", overlaying='y', side='right', showgrid=False),
        legend=dict(orientation="h", y=1.1, x=0.5, xanchor="center"),
        margin=dict(l=0, r=0, t=40, b=0),
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)"
    )
    st.plotly_chart(fig_electro, use_container_width=True)

    # D. FUNNEL
    st.subheader("🔻 Eficiencia del Embudo")

    stages = ['Clicks Anuncios', 'Visitas LP', 'Leads Captados', 'Leads en API', 'Unidos a Grupo']
    values = [clicks, visitas, leads, api, grupo]
    
    pcts = []
    for i, val in enumerate(values):
        if i == 0: pcts.append(100)
        else:
            prev = values[i-1]
            pct = (val / prev * 100) if prev > 0 else 0
            pcts.append(pct)

    fig_bar = go.Figure()
    text_labels = [f"{formato_euro(v, 0)} ({formato_euro(p, 1)}%)" for v, p in zip(values, pcts)]
    colors = ['#545454', '#ced4da', '#00CC96', '#636EFA', '#AB63FA']

    fig_bar.add_trace(go.Bar(
        y=stages, x=values, orientation='h', text=text_labels, textposition='auto',
        marker=dict(color=colors, line=dict(color='rgba(255, 255, 255, 0.2)', width=1)),
        width=0.3, opacity=0.9
    ))

    fig_bar.update_layout(
        height=350,
        separators=",.", 
        yaxis=dict(autorange="reversed"),
        xaxis=dict(showgrid=True, gridcolor='#2c2f38', title="Cantidad"),
        margin=dict(l=0, r=0, t=20, b=0),
        plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)"
    )
    st.plotly_chart(fig_bar, use_container_width=True)

    # E. DATA TABLE
    with st.expander("📂 Ver Tabla de Datos Diarios"):
        st.dataframe(
            daily.style.format({
                'Spent': lambda x: f"${formato_euro(x, 2)}",
                'Leads Hyros': lambda x: f"{formato_euro(x, 0)}",
                'API Hyros': lambda x: f"{formato_euro(x, 0)}",
                'Grupo': lambda x: f"{formato_euro(x, 0)}",
                'CPL_Dia': lambda x: f"${formato_euro(x, 2)}"
            }).background_gradient(subset=['Leads Hyros'], cmap='Greens'),
            use_container_width=True
        )
