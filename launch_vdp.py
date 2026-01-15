import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta

# --- 1. CONFIGURACIÓN DE PÁGINA PRO ---
st.set_page_config(page_title="Launch Command Center", page_icon="🚀", layout="wide")

# Estilos CSS personalizados para dar el toque "PRO" y ajustar márgenes
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

# --- 2. CARGA DE DATOS ---
@st.cache_data(ttl=300) 
def cargar_datos_vdp():
    url = 'https://docs.google.com/spreadsheets/d/e/2PACX-1vR726VKYI1xIW9q5U50lN2iqY58-SIyN9gusKo_t8h2-HkTa7zERkSrQ6F4OUnTB2AWEh4CSvfwdZRL/pub?gid=0&single=true&output=csv'
    try:
        df = pd.read_csv(url)
        df.columns = df.columns.str.strip()
        
        def clean_currency(x):
            if isinstance(x, str):
                x = x.replace('$', '').replace(' ', '').replace('%', '')
                if 'DIV/0' in x or x.strip() == '-' or x.strip() == '': return 0.0
                x = x.replace('.', '').replace(',', '.')
                try: return float(x)
                except ValueError: return 0.0
            return x

        cols = ['Spent', 'Clicks', 'Visitas LP', 'Leads Hyros', 'API Hyros', 'Grupo']
        for col in cols:
            if col in df.columns: df[col] = df[col].apply(clean_currency)
        
        if 'Fecha' in df.columns:
            df['Fecha'] = pd.to_datetime(df['Fecha'], dayfirst=True, errors='coerce')
            df = df.sort_values('Fecha')
        return df
    except Exception as e:
        st.error(f"Error de conexión: {e}")
        return pd.DataFrame()

df = cargar_datos_vdp()

# --- 3. SIDEBAR (FILTROS) ---
st.sidebar.title("🎛️ Control de Mando")
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

# Filtrar Dataframe Globalmente
mask = (df['Fecha'] >= f_inicio) & (df['Fecha'] <= f_fin)
df_filtrado = df.loc[mask].copy()

if df_filtrado.empty:
    st.warning("⚠️ No hay datos para las fechas seleccionadas.")
    st.stop()

# --- 4. ESTRUCTURA DE PESTAÑAS (TABS) ---
tab1, tab2, tab3 = st.tabs(["🚀 FASE 1: CAPTACIÓN", "🔥 FASE 2: NUTRICIÓN (Coming Soon)", "💰 FASE 3: VENTA (Coming Soon)"])

with tab1:
    # --- A. CÁLCULOS KPI ---
    spend = df_filtrado['Spent'].sum()
    leads = df_filtrado['Leads Hyros'].sum()
    api = df_filtrado['API Hyros'].sum()
    grupo = df_filtrado['Grupo'].sum()
    visitas = df_filtrado['Visitas LP'].sum()
    dias_activos = (df_filtrado['Fecha'].max() - df_filtrado['Fecha'].min()).days + 1
    if dias_activos < 1: dias_activos = 1

    # Costos Unitarios Globales
    cpl = spend / leads if leads > 0 else 0
    cpa = spend / api if api > 0 else 0
    cpg = spend / grupo if grupo > 0 else 0
    daily_spend = spend / dias_activos

    # --- B. HEADER DE MÉTRICAS (4 COLUMNAS) ---
    st.markdown("### 🎯 Métricas Principales")
    k1, k2, k3, k4 = st.columns(4)

    # 1. Inversión (Delta: Diario)
    k1.metric("💸 Inversión Total", f"${spend:,.0f}", f"${daily_spend:,.0f} / día (Avg)", delta_color="off")

    # 2. Leads Hyros (Delta: CPL)
    k2.metric("👥 Leads (Hyros)", f"{int(leads):,}", f"CPL: ${cpl:.2f}", delta_color="inverse")

    # 3. API Hyros (Delta: Costo API)
    k3.metric("🤖 Leads API", f"{int(api):,}", f"CPA: ${cpa:.2f}", delta_color="inverse")

    # 4. Grupo WhatsApp (Delta: Costo Grupo)
    k4.metric("📲 Grupo WhatsApp", f"{int(grupo):,}", f"CPG: ${cpg:.2f}", delta_color="inverse")

    st.markdown("---")

    # --- C. GRÁFICO 1: ELECTROCARDIOGRAMA (Líneas + Nodos) ---
    st.subheader("📈 Tendencia de Tráfico & Costos")
    
    # Preparar datos diarios
    daily = df_filtrado.groupby('Fecha').agg({
        'Spent': 'sum', 'Leads Hyros': 'sum', 'API Hyros': 'sum', 'Grupo': 'sum'
    }).reset_index()
    
    # Calcular costos diarios para el gráfico (evitando div/0)
    daily['CPL_Dia'] = daily.apply(lambda x: x['Spent']/x['Leads Hyros'] if x['Leads Hyros'] > 0 else 0, axis=1)
    
    fig_electro = go.Figure()

    # EJE Y IZQUIERDO (VOLUMEN) - LÍNEAS SÓLIDAS
    fig_electro.add_trace(go.Scatter(x=daily['Fecha'], y=daily['Leads Hyros'], name='Leads', 
                         mode='lines+markers', line=dict(color='#00CC96', width=3), marker=dict(size=6)))
    fig_electro.add_trace(go.Scatter(x=daily['Fecha'], y=daily['API Hyros'], name='API', 
                         mode='lines+markers', line=dict(color='#636EFA', width=3), marker=dict(size=6)))
    fig_electro.add_trace(go.Scatter(x=daily['Fecha'], y=daily['Grupo'], name='Grupo', 
                         mode='lines+markers', line=dict(color='#AB63FA', width=3), marker=dict(size=6)))

    # EJE Y DERECHO (COSTOS) - LÍNEAS PUNTEADAS
    fig_electro.add_trace(go.Scatter(x=daily['Fecha'], y=daily['CPL_Dia'], name='CPL ($)', 
                         mode='lines', line=dict(color='#EF553B', width=1, dash='dot'), yaxis='y2'))

    fig_electro.update_layout(
        height=450,
        hovermode="x unified",
        xaxis=dict(showgrid=False),
        yaxis=dict(title="Volumen (Cantidad)", showgrid=True, gridcolor='#2c2f38'),
        yaxis2=dict(title="Costo Unitario ($)", overlaying='y', side='right', showgrid=False),
        legend=dict(orientation="h", y=1.1, x=0.5, xanchor="center"),
        margin=dict(l=0, r=0, t=40, b=0),
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)"
    )
    st.plotly_chart(fig_electro, use_container_width=True)

    # --- D. GRÁFICO 2: BARRA DE PROGRESO FINA (FUNNEL) ---
    st.subheader("🔻 Eficiencia del Embudo")

    # Datos del Embudo
    stages = ['Visitas LP', 'Leads Captados', 'Leads en API', 'Unidos a Grupo']
    values = [visitas, leads, api, grupo]
    
    # Calcular porcentajes relativos al paso anterior
    pcts = []
    for i, val in enumerate(values):
        if i == 0: pcts.append(100)
        else:
            prev = values[i-1]
            pct = (val / prev * 100) if prev > 0 else 0
            pcts.append(pct)

    # Colores Neón para las barras
    colors = ['#ced4da', '#00CC96', '#636EFA', '#AB63FA']

    fig_bar = go.Figure()

    fig_bar.add_trace(go.Bar(
        y=stages,
        x=values,
        orientation='h',
        text=[f"{v:,.0f} ({p:.1f}%)" for v, p in zip(values, pcts)],
        textposition='auto',
        marker=dict(
            color=colors,
            line=dict(color='rgba(255, 255, 255, 0.2)', width=1) # Borde sutil
        ),
        width=0.3, # BARRAS FINAS (Estilo Slider)
        opacity=0.9
    ))

    fig_bar.update_layout(
        height=300,
        yaxis=dict(autorange="reversed"), # Invierte para que Visitas esté arriba
        xaxis=dict(showgrid=True, gridcolor='#2c2f38', title="Cantidad"),
        margin=dict(l=0, r=0, t=20, b=0),
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)"
    )
    st.plotly_chart(fig_bar, use_container_width=True)

    # --- E. DETALLE DE DATOS (Expander) ---
    with st.expander("📂 Ver Tabla de Datos Diarios"):
        st.dataframe(
            daily.style.format({
                'Spent': '${:,.2f}',
                'Leads Hyros': '{:.0f}',
                'API Hyros': '{:.0f}',
                'Grupo': '{:.0f}',
                'CPL_Dia': '${:,.2f}'
            }).background_gradient(subset=['Leads Hyros'], cmap='Greens'),
            use_container_width=True
        )
