import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import json
import os
import extra_streamlit_components as stx 

# --- CONFIGURACIÓN DE PÁGINA (ESTÉTICA PRO) ---
st.set_page_config(
    page_title="Agency Command Center",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- INYECCIÓN DE CSS (BRANDING) ---
st.markdown("""
    <style>
        /* Ajustar márgenes superiores */
        .block-container { padding-top: 1rem; padding-bottom: 2rem; }
        /* Ocultar menú default de Streamlit y footer */
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        /* Estilizar métricas */
        [data-testid="stMetricValue"] {
            font-size: 1.8rem !important;
            font-weight: 700;
        }
        /* Spinner oculto para cookies */
        .stSpinner { display:none; }
    </style>
""", unsafe_allow_html=True)

# --- PANTALLA DE BIENVENIDA CON COOKIES ---
def pantalla_bienvenida():
    cookie_manager = stx.CookieManager(key="cookie_manager_dashboard")
    cookie_val = cookie_manager.get(cookie="ingreso_ok")

    if cookie_val == "true":
        return True

    if "ingreso_confirmado" in st.session_state and st.session_state["ingreso_confirmado"]:
        return True

    # Diseño de Landing
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("<br><br><br>", unsafe_allow_html=True)
        st.title("🔒 Acceso Restringido")
        st.subheader("Agency Command Center")
        st.info("Sistema de monitoreo de High-Ticket Funnels.")
        
        if st.button("Autenticar Acceso ➡️", type="primary", use_container_width=True):
            st.session_state["ingreso_confirmado"] = True
            cookie_manager.set("ingreso_ok", "true", expires_at=datetime.now() + timedelta(days=30))
            st.rerun()

    return False

if not pantalla_bienvenida():
    st.stop()

# --- GESTIÓN DE METAS ---
ARCHIVO_METAS = 'metas_config.json'

def cargar_metas():
    if os.path.exists(ARCHIVO_METAS):
        with open(ARCHIVO_METAS, 'r') as f:
            return json.load(f)
    return {"meta_facturacion": 10000.0, "presupuesto_ads": 3000.0}

def guardar_metas_archivo(fact, ads):
    with open(ARCHIVO_METAS, 'w') as f:
        json.dump({"meta_facturacion": fact, "presupuesto_ads": ads}, f)

# --- CARGA DE DATOS ---
@st.cache_data(ttl=300) 
def cargar_datos():
    url_ventas = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQuXaPCen61slzpr1TElxXoCROIxAgmgWT7pyWvel1dxq_Z_U1yZPrVrTbJfx9MwaL8_cluY3v2ywoB/pub?gid=0&single=true&output=csv"
    url_gastos = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQGOLgPTDLie5gEbkViCbpebWfN9S_eb2h2GGlpWLjmfVgzfnwR_ncVTs4IqmKgmAFfxZTQHJlMBrIi/pub?gid=0&single=true&output=csv"

    # VENTAS
    try:
        df_v = pd.read_csv(url_ventas)
        df_v['Fecha'] = pd.to_datetime(df_v['Fecha'], dayfirst=True, errors='coerce')
        if df_v['Monto ($)'].dtype == 'O': 
            df_v['Monto ($)'] = df_v['Monto ($)'].astype(str).str.replace(r'[$,]', '', regex=True)
        df_v['Monto ($)'] = pd.to_numeric(df_v['Monto ($)'], errors='coerce').fillna(0)
        
        df_v['Closer'] = df_v['Closer'].fillna("Sin Asignar")
        df_v['Resultado'] = df_v['Resultado'].fillna("Pendiente")
        
        # Normalización de Estados
        def clasificar_estado(texto):
            texto = str(texto).lower()
            if "venta" in texto: return "✅ Venta"
            if "no show" in texto: return "❌ No Show"
            if "descalificado" in texto: return "🚫 Descalificado"
            if "seguimiento" in texto: return "👀 Seguimiento"
            if "re-agendado" in texto or "reagendado" in texto: return "📅 Re-Agendado"
            return "Otro/Pendiente"
        df_v['Estado_Simple'] = df_v['Resultado'].apply(clasificar_estado)

        # Lógica de Asistencia (Show)
        # Asistió si NO es 'No Show' y NO es 'Descalificado' (depende de tu criterio, a veces descalificado asiste y se descalifica en llamada)
        def es_asistencia_valida(row):
            res = str(row['Resultado']).lower()
            estado = row['Estado_Simple']
            if estado == "❌ No Show": return False
            if estado == "📅 Re-Agendado": return False # No asistió hoy
            return True # Asumimos que Venta, Seguimiento y Descalificado (en llamada) sí asistieron
            
        df_v['Es_Asistencia'] = df_v.apply(es_asistencia_valida, axis=1)
        
        # Día de la semana para análisis
        df_v['Dia_Semana'] = df_v['Fecha'].dt.day_name()

    except Exception as e:
        df_v = pd.DataFrame()

    # GASTOS
    try:
        df_g = pd.read_csv(url_gastos)
        df_g['Fecha'] = pd.to_datetime(df_g['Fecha'], dayfirst=True, errors='coerce')
        if df_g['Gasto'].dtype == 'O':
            df_g['Gasto'] = df_g['Gasto'].astype(str).str.replace(r'[$,]', '', regex=True)
        df_g['Gasto'] = pd.to_numeric(df_g['Gasto'], errors='coerce').fillna(0)
    except Exception as e:
        df_g = pd.DataFrame()

    return df_v, df_g

df_ventas, df_gastos = cargar_datos()

if df_ventas.empty:
    st.error("⚠️ No se pudieron cargar los datos. Verifica la conexión con Google Sheets.")
    st.stop()

# --- SIDEBAR ---
st.sidebar.markdown("### 🎛️ Control Panel")
if st.sidebar.button("🔄 Refresh Data", use_container_width=True):
    st.cache_data.clear()
    st.rerun()

# Filtros de Fecha
st.sidebar.markdown("---")
filtro_tiempo = st.sidebar.selectbox("📅 Período", ["Este Mes", "Esta Semana", "Hoy", "Últimos 30 días", "Personalizado"])
hoy = pd.to_datetime("today").date()

if filtro_tiempo == "Hoy": f_inicio, f_fin = hoy, hoy
elif filtro_tiempo == "Esta Semana": f_inicio, f_fin = hoy - timedelta(days=hoy.weekday()), hoy
elif filtro_tiempo == "Este Mes": f_inicio, f_fin = hoy.replace(day=1), hoy
elif filtro_tiempo == "Últimos 30 días": f_inicio, f_fin = hoy - timedelta(days=30), hoy
else:
    c1, c2 = st.sidebar.columns(2)
    f_inicio = c1.date_input("Desde", hoy)
    f_fin = c2.date_input("Hasta", hoy)

# Filtro Closer
lista_closers = ["Todos"] + sorted([c for c in df_ventas['Closer'].unique() if c])
closer_sel = st.sidebar.selectbox("👤 Closer", lista_closers)

# Aplicar Filtros
mask_v = (df_ventas['Fecha'].dt.date >= f_inicio) & (df_ventas['Fecha'].dt.date <= f_fin)
df_v_filtrado = df_ventas.loc[mask_v].copy()
if closer_sel != "Todos": df_v_filtrado = df_v_filtrado[df_v_filtrado['Closer'] == closer_sel]

if not df_gastos.empty:
    mask_g = (df_gastos['Fecha'].dt.date >= f_inicio) & (df_gastos['Fecha'].dt.date <= f_fin)
    df_g_filtrado = df_gastos.loc[mask_g].copy()
else: df_g_filtrado = pd.DataFrame(columns=['Fecha', 'Gasto'])

# --- METAS (Sidebar Bottom) ---
st.sidebar.markdown("---")
metas = cargar_metas()
with st.sidebar.expander("⚙️ Configurar Objetivos"):
    m_fact = st.number_input("Meta Facturación", value=float(metas["meta_facturacion"]))
    m_ads = st.number_input("Presupuesto Ads", value=float(metas["presupuesto_ads"]))
    if st.button("Guardar"):
        guardar_metas_archivo(m_fact, m_ads)
        st.rerun()

# --- KPI ENGINE ---
facturacion = df_v_filtrado['Monto ($)'].sum()
inversion = df_g_filtrado['Gasto'].sum() if closer_sel == "Todos" else 0
profit = facturacion - inversion
roas = (facturacion / inversion) if inversion > 0 else 0

total_leads = len(df_v_filtrado) # Total filas
ventas = len(df_v_filtrado[df_v_filtrado['Estado_Simple'] == "✅ Venta"])
# Asumimos que "Descalificado" también cuenta como Lead procesado
leads_calificados = len(df_v_filtrado[~df_v_filtrado['Estado_Simple'].isin(["🚫 Descalificado"])]) 
asistencias = df_v_filtrado['Es_Asistencia'].sum()

# Tasas
show_rate = (asistencias / leads_calificados * 100) if leads_calificados > 0 else 0
close_rate = (ventas / asistencias * 100) if asistencias > 0 else 0
conversion_global = (ventas / total_leads * 100) if total_leads > 0 else 0

# --- DASHBOARD HEADER ---
st.title("🚀 Agency Growth Dashboard")
st.markdown(f"**Vista:** {f_inicio} al {f_fin} | **Closer:** {closer_sel}")
st.markdown("---")

# --- ROW 1: HIGH LEVEL FINANCIALS ---
col1, col2, col3, col4 = st.columns(4)
col1.metric("💰 Facturación", f"${facturacion:,.0f}", delta=f"{facturacion/metas['meta_facturacion']*100:.1f}% de Meta")
col2.metric("💸 Ad Spend", f"${inversion:,.0f}")
col3.metric("💎 Profit", f"${profit:,.0f}", delta_color="normal")
col4.metric("🔥 ROAS", f"{roas:.2f}x", delta=f"{roas-2:.1f} vs KPI" if roas>0 else 0)

# --- ROW 2: FUNNEL VISUALIZATION (THE PRO FEATURE) ---
st.markdown("### 🌪️ Sales Funnel Efficiency")
c_funnel, c_metrics = st.columns([2, 1])

with c_funnel:
    # Datos para el Funnel
    # Etapa 1: Leads Totales (Formularios)
    # Etapa 2: Agendados/Calificados (Quitamos descalificados)
    # Etapa 3: Shows (Asistieron a la llamada)
    # Etapa 4: Ventas (Cierres)
    
    stages = ["Total Leads", "Calificados", "Calls (Shows)", "Ventas"]
    values = [total_leads, leads_calificados, asistencias, ventas]
    
    fig_funnel = go.Figure(go.Funnel(
        y = stages,
        x = values,
        textinfo = "value+percent initial",
        marker = {"color": ["#636EFA", "#AB63FA", "#FFA15A", "#00CC96"]}
    ))
    fig_funnel.update_layout(margin=dict(l=0, r=0, t=0, b=0), height=300)
    st.plotly_chart(fig_funnel, use_container_width=True)

with c_metrics:
    st.markdown("#### Tasas de Conversión")
    st.markdown("---")
    st.metric("Show Rate (Asistencia)", f"{show_rate:.1f}%", help="De los Agendados Calificados, cuántos aparecen.")
    st.metric("Close Rate (Cierre)", f"{close_rate:.1f}%", help="De los que aparecen, cuántos compran.")
    st.metric("Conv. Global", f"{conversion_global:.1f}%", help="De Lead Total a Venta.")

# --- ROW 3: HEATMAP & TRENDS ---
st.markdown("---")

# 3.1 GRÁFICO: MEJORES DÍAS (FULL WIDTH)
st.subheader("📅 Mejores Días para Cerrar")
if not df_v_filtrado.empty:
    # Agrupar ventas por día de la semana
    ventas_dia = df_v_filtrado[df_v_filtrado['Estado_Simple'] == "✅ Venta"].groupby('Dia_Semana')['Monto ($)'].sum().reindex(
        ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    ).fillna(0).reset_index()
    
    fig_bar = px.bar(ventas_dia, x="Dia_Semana", y="Monto ($)", color="Monto ($)", 
                     color_continuous_scale="Greens", title="Facturación Acumulada por Día")
    
    # Ajuste para que se vea bien extendido
    fig_bar.update_layout(height=400) 
    st.plotly_chart(fig_bar, use_container_width=True)
else:
    st.info("No hay datos de ventas en este período.")

st.divider() # Separador visual

# 3.2 GRÁFICO: TENDENCIA DIARIA (FULL WIDTH)
st.subheader("📈 Tendencia Diaria de Leads y Facturación")
if not df_v_filtrado.empty:
    # Leads vs Ventas diario
    diario = df_v_filtrado.groupby('Fecha').agg({
        'Estado_Simple': 'count', # Total Leads
        'Monto ($)': 'sum' # Facturación
    }).rename(columns={'Estado_Simple': 'Leads'}).reset_index()
    
    fig_trend = px.line(diario, x='Fecha', y='Leads', title="Volumen vs. Ingresos", markers=True)
    fig_trend.add_bar(x=diario['Fecha'], y=diario['Monto ($)'], name="Facturación", yaxis="y2", opacity=0.3)
    
    fig_trend.update_layout(
        yaxis2=dict(title="Facturación ($)", overlaying="y", side="right", showgrid=False),
        height=450, # Un poco más alto para ver detalles
        legend=dict(orientation="h", y=1.1, x=0) # Leyenda arriba para no estorbar
    )
    st.plotly_chart(fig_trend, use_container_width=True)

# --- ROW 4: RANKING DETALLADO ---
st.markdown("### 🏆 Performance de Equipo")
if not df_v_filtrado.empty:
    ranking = df_v_filtrado.groupby('Closer').apply(
        lambda x: pd.Series({
            'Leads': len(x),
            'Facturado': x['Monto ($)'].sum(),
            'Shows': x['Es_Asistencia'].sum(),
            'Ventas': x['Estado_Simple'].eq("✅ Venta").sum()
        })
    ).reset_index()
    
    # Cálculos adicionales
    ranking['Show Rate'] = (ranking['Shows'] / ranking['Leads']).fillna(0) # Lo dejamos en decimal (0.5) para que Streamlit lo formatee a %
    ranking['Close Rate'] = (ranking['Ventas'] / ranking['Shows']).fillna(0)
    ranking['Ticket Promedio'] = (ranking['Facturado'] / ranking['Ventas']).fillna(0)
    
    ranking = ranking.sort_values('Facturado', ascending=False)
    
    # CORRECCIÓN: Usamos column_config en lugar de .style para evitar errores
    st.dataframe(
        ranking,
        use_container_width=True,
        column_order=["Closer", "Leads", "Shows", "Ventas", "Show Rate", "Close Rate", "Ticket Promedio", "Facturado"],
        hide_index=True,
        column_config={
            "Closer": st.column_config.TextColumn("👤 Closer"),
            "Leads": st.column_config.NumberColumn("📥 Leads"),
            "Shows": st.column_config.NumberColumn("📞 Shows"),
            "Ventas": st.column_config.NumberColumn("✅ Ventas"),
            "Show Rate": st.column_config.ProgressColumn(
                "Show Rate",
                format="%.1f%%",
                min_value=0,
                max_value=1,
            ),
            "Close Rate": st.column_config.ProgressColumn(
                "Close Rate",
                format="%.1f%%",
                min_value=0,
                max_value=1,
            ),
            "Ticket Promedio": st.column_config.NumberColumn(
                "Ticket Prom.",
                format="$%d"
            ),
            "Facturado": st.column_config.NumberColumn(
                "💰 Facturado",
                format="$%d",
            )
        }
    )
