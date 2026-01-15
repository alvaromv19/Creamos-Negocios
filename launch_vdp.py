import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta

# --- 1. CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="VDP Command Center", page_icon="🚀", layout="wide")

# --- 2. PANTALLA DE BIENVENIDA (Estilo Agency) ---
def pantalla_bienvenida():
    if "ingreso_confirmado" not in st.session_state:
        st.session_state["ingreso_confirmado"] = False

    if st.session_state["ingreso_confirmado"]:
        return True

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("<br><br><br>", unsafe_allow_html=True)
        st.title("🚀 VDP Command Center")
        st.subheader("Control de Tráfico y Embudo")
        st.markdown("Visualiza métricas, controla el CPL y optimiza la captación.")
        st.markdown("---")
        
        if st.button("Ingresar al Sistema ➡️", type="primary", use_container_width=True):
            st.session_state["ingreso_confirmado"] = True
            st.rerun()

    return False

if not pantalla_bienvenida():
    st.stop()

# --- 3. CARGA Y LIMPIEZA DE DATOS ---
st.sidebar.title("🎛️ Panel de Tráfico")

@st.cache_data(ttl=300) 
def cargar_datos_vdp():
    # URL de tu Google Sheet (VDP)
    url = 'https://docs.google.com/spreadsheets/d/e/2PACX-1vR726VKYI1xIW9q5U50lN2iqY58-SIyN9gusKo_t8h2-HkTa7zERkSrQ6F4OUnTB2AWEh4CSvfwdZRL/pub?gid=0&single=true&output=csv'
    
    try:
        df = pd.read_csv(url)
        df.columns = df.columns.str.strip() # Limpiar nombres de columnas
        
        # Limpieza de Monedas y Números
        def clean_currency(x):
            if isinstance(x, str):
                x = x.replace('$', '').replace(' ', '').replace('%', '')
                if 'DIV/0' in x or x.strip() == '-' or x.strip() == '':
                    return 0.0
                x = x.replace('.', '') # Quitar punto de miles europeo
                x = x.replace(',', '.') # Cambiar coma por punto decimal
                try:
                    return float(x)
                except ValueError:
                    return 0.0
            return x

        cols_to_clean = ['Spent', 'Clicks', 'Visitas LP', 'Leads Hyros', 'API Hyros', 'Grupo']
        for col in cols_to_clean:
            if col in df.columns:
                df[col] = df[col].apply(clean_currency)
        
        # Procesar Fechas
        if 'Fecha' in df.columns:
            df['Fecha'] = pd.to_datetime(df['Fecha'], dayfirst=True, errors='coerce')
            df = df.sort_values('Fecha')
        
        return df
    
    except Exception as e:
        st.error(f"Error cargando datos: {e}")
        return pd.DataFrame()

df = cargar_datos_vdp()

if df.empty:
    st.warning("⚠️ No se pudieron cargar los datos. Revisa la URL del Sheet.")
    st.stop()

# --- 4. FILTROS DE FECHA (Estilo Agency) ---
if st.sidebar.button("🔄 Actualizar Data"):
    st.cache_data.clear()
    st.rerun()

st.sidebar.markdown("---")
filtro_tiempo = st.sidebar.selectbox(
    "Selecciona Período:",
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

# Convertir a datetime para filtrar
f_inicio = pd.to_datetime(f_inicio)
f_fin = pd.to_datetime(f_fin)

# Aplicar Máscara
mask = (df['Fecha'] >= f_inicio) & (df['Fecha'] <= f_fin)
df_filtrado = df.loc[mask].copy()

# --- 5. OBJETIVOS (Trafficker Settings) ---
st.sidebar.markdown("---")
st.sidebar.subheader("🎯 KPIs Objetivo")

if "target_cpl" not in st.session_state: st.session_state["target_cpl"] = 2.0
if "budget_diario" not in st.session_state: st.session_state["budget_diario"] = 150.0

target_cpl = st.sidebar.number_input("CPL Máximo ($)", value=st.session_state["target_cpl"], step=0.1)
budget_target = st.sidebar.number_input("Budget Diario Ideal ($)", value=st.session_state["budget_diario"], step=10.0)

# --- 6. CÁLCULOS DE KPIs (Formulas) ---
# Sumatorias
spend = df_filtrado['Spent'].sum()
leads = df_filtrado['Leads Hyros'].sum()
grupo = df_filtrado['Grupo'].sum()
visitas = df_filtrado['Visitas LP'].sum()

# KPIs Calculados
cpl_real = spend / leads if leads > 0 else 0
cpg_real = spend / grupo if grupo > 0 else 0
cr_lp = (leads / visitas * 100) if visitas > 0 else 0
cr_grupo = (grupo / leads * 100) if leads > 0 else 0

# Proyección de Gasto (Pacing)
dias_selecc = (f_fin - f_inicio).days + 1
pacing_spend = spend / dias_selecc
delta_budget = pacing_spend - budget_target

# --- 7. DASHBOARD PRINCIPAL ---
st.title("📊 Métricas de Captación - VDP")
st.markdown(f"**Período:** {f_inicio.date()} al {f_fin.date()}")

# SECCIÓN 1: TARJETAS SUPERIORES (KPIs Financieros)
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("💸 Inversión (Spent)", f"${spend:,.2f}", delta=f"${pacing_spend:.0f}/día (Avg)", delta_color="off")

with col2:
    delta_cpl = target_cpl - cpl_real
    st.metric("CPL (Costo/Lead)", f"${cpl_real:.2f}", delta=f"{delta_cpl:.2f} vs Meta", delta_color="normal" if delta_cpl >= 0 else "inverse")

with col3:
    st.metric("👥 Leads Totales", int(leads), delta=f"{cr_lp:.1f}% CR Landing")

with col4:
    st.metric("📲 Grupo WhatsApp", int(grupo), delta=f"CPG: ${cpg_real:.2f}", delta_color="inverse")

st.divider()

# SECCIÓN 2: GRÁFICOS INTERACTIVOS (Plotly)

# Gráfico A: Tendencia Diaria (Barras + Línea)
# Preparamos datos diarios
if not df_filtrado.empty:
    daily_data = df_filtrado.groupby('Fecha').agg({
        'Spent': 'sum',
        'Leads Hyros': 'sum',
        'Grupo': 'sum'
    }).reset_index()
    
    daily_data['CPL'] = daily_data['Spent'] / daily_data['Leads Hyros']
    
    # Crear Figura con Doble Eje
    fig = go.Figure()

    # Barras: Leads
    fig.add_trace(go.Bar(
        x=daily_data['Fecha'], y=daily_data['Leads Hyros'],
        name='Leads', marker_color='#00CC96', opacity=0.7, yaxis='y1'
    ))
    
    # Línea: CPL
    fig.add_trace(go.Scatter(
        x=daily_data['Fecha'], y=daily_data['CPL'],
        name='CPL ($)', line=dict(color='#EF553B', width=3), mode='lines+markers', yaxis='y2'
    ))

    # Layout Profesional
    fig.update_layout(
        title="<b>Tendencia: Volumen vs Eficiencia</b>",
        xaxis_title="Fecha",
        yaxis=dict(title="Volumen (Leads)", side="left", showgrid=False),
        yaxis2=dict(title="CPL ($)", side="right", overlaying="y", showgrid=True),
        legend=dict(orientation="h", y=1.1),
        hovermode="x unified",
        height=400
    )

    col_g1, col_g2 = st.columns([2, 1])
    
    with col_g1:
        st.plotly_chart(fig, use_container_width=True)

    # Gráfico B: Embudo de Conversión (Horizontal)
    with col_g2:
        funnel_stages = ['Visitas LP', 'Leads', 'API', 'Grupo']
        funnel_values = [
            df_filtrado['Visitas LP'].sum(),
            df_filtrado['Leads Hyros'].sum(),
            df_filtrado['API Hyros'].sum(),
            df_filtrado['Grupo'].sum()
        ]
        
        fig_funnel = go.Figure(go.Funnel(
            y=funnel_stages,
            x=funnel_values,
            textposition="inside",
            textinfo="value+percent previous",
            marker = dict(color = ["#1c1c1c", "#00CC96", "#AB63FA", "#636EFA"])
        ))
        
        fig_funnel.update_layout(
            title="<b>Embudo de Conversión</b>",
            height=400,
            margin=dict(l=0, r=0, t=40, b=0)
        )
        st.plotly_chart(fig_funnel, use_container_width=True)

# SECCIÓN 3: DATA TABLE DETALLADA
with st.expander("📂 Ver Data Detallada (Click para desplegar)"):
    # Formateo para la tabla visual
    df_show = df_filtrado[['Fecha', 'Spent', 'Visitas LP', 'Leads Hyros', 'CPL_Diario', 'Grupo']].copy() if 'CPL_Diario' in df_filtrado.columns else df_filtrado.copy()
    
    # Calcular CPL Diario en vivo para la tabla si no existe
    if 'CPL_Diario' not in df_show.columns:
        df_show['CPL'] = df_show['Spent'] / df_show['Leads Hyros']
    
    st.dataframe(
        df_show.style.format({
            "Fecha": lambda t: t.strftime("%d-%m-%Y"),
            "Spent": "${:,.2f}",
            "CPL": "${:,.2f}",
            "Leads Hyros": "{:.0f}",
            "Grupo": "{:.0f}",
            "Visitas LP": "{:.0f}"
        }).background_gradient(subset=['Spent', 'Leads Hyros'], cmap="Blues"),
        use_container_width=True
    )
