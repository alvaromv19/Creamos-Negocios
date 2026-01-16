import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta

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
        # Cargamos todo como STRING para limpieza estricta manual
        df = pd.read_csv(url, dtype=str) 
        df.columns = df.columns.str.strip()
        
        # --- FUNCIÓN DE LIMPIEZA ESTRICTA (EUROPEA) ---
        def force_european_format(x):
            if pd.isna(x) or str(x).strip() == "" or str(x).strip() == "-":
                return 0.0
            
            x = str(x).replace('$', '').replace(' ', '').replace('%', '')
            # 1. Quitamos los puntos de miles (ej: 1.200 -> 1200)
            x = x.replace('.', '')
            # 2. Cambiamos la coma decimal por punto (ej: 50,5 -> 50.5)
            x = x.replace(',', '.')
            
            try:
                return float(x)
            except ValueError:
                return 0.0

        cols = ['Spent', 'Clicks', 'Visitas LP', 'Leads Hyros', 'API Hyros', 'Grupo']
        for col in cols:
            if col in df.columns:
                df[col] = df[col].apply(force_european_format)
        
        if 'Fecha' in df.columns:
            df['Fecha'] = pd.to_datetime(df['Fecha'], dayfirst=True, errors='coerce')
            df = df.sort_values('Fecha')
            
        return df
    except Exception as e:
        st.error(f"Error crítico cargando datos: {e}")
        return pd.DataFrame()

df = cargar_datos_vdp()

# --- 3. SIDEBAR Y DEBUGGER ---
st.sidebar.title("🎛️ Control de Mando")

# Debugger
mostrar_raw = st.sidebar.checkbox("🔍 Modo Debug (Ver Data)", value=False)
if mostrar_raw:
    st.warning("MODO DEBUG ACTIVADO")
    st.write("Primeras 5 filas procesadas:", df.head())

st.sidebar.caption("Filtros Globales")

filtro_tiempo = st.sidebar.selectbox(
    "📅 Período de Análisis:",
    ["Este Mes", "Mes Anterior", "Hoy", "Ayer", "Últimos 7 días", "Últimos 30 días", "Personalizado"]
)

hoy = pd.to_datetime("today").date()
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

f_inicio, f_fin = pd.to_datetime(f_inicio), pd.to_datetime(f_fin)

mask = (df['Fecha'] >= f_inicio) & (df['Fecha'] <= f_fin)
df_filtrado = df.loc[mask].copy()

if df_filtrado.empty:
    st.warning("⚠️ No hay datos para las fechas seleccionadas.")
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
    # NUEVO: Calculamos Clics
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

    k1.metric("💸 Inversión Total", f"${formato_euro(spend,,2f)}", f"Actual ${formato_euro(daily_spend, 0)} / día", delta_color="off")
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

    # D. FUNNEL (MODIFICADO: Agregado Clicks al inicio)
    st.subheader("🔻 Eficiencia del Embudo")

    # 1. Agregamos 'Clicks Anuncios' al inicio de las etapas
    stages = ['Clicks Anuncios', 'Visitas LP', 'Leads Captados', 'Leads en API', 'Unidos a Grupo']
    # 2. Agregamos el valor de clicks al inicio de los valores
    values = [clicks, visitas, leads, api, grupo]
    
    pcts = []
    for i, val in enumerate(values):
        if i == 0: 
            pcts.append(100) # El primer paso es el 100% de referencia
        else:
            prev = values[i-1]
            # Calcula el % respecto al paso anterior (ej: Visitas / Clicks)
            pct = (val / prev * 100) if prev > 0 else 0
            pcts.append(pct)

    fig_bar = go.Figure()
    text_labels = [f"{formato_euro(v, 0)} ({formato_euro(p, 1)}%)" for v, p in zip(values, pcts)]

    # Colores: Agregamos un Gris Oscuro ('#545454') para Clicks al inicio
    colors = ['#545454', '#ced4da', '#00CC96', '#636EFA', '#AB63FA']

    fig_bar.add_trace(go.Bar(
        y=stages, x=values, orientation='h', text=text_labels, textposition='auto',
        marker=dict(color=colors, line=dict(color='rgba(255, 255, 255, 0.2)', width=1)),
        width=0.3, opacity=0.9
    ))

    fig_bar.update_layout(
        height=350, # Aumenté un poco la altura para que quepa la nueva barra
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
