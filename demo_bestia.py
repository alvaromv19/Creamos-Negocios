import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
from datetime import datetime, timedelta

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Agency Beast Demo", page_icon="🦁", layout="wide")

# CSS para darle look "Pro"
st.markdown("""
    <style>
        .block-container { padding-top: 2rem; padding-bottom: 3rem; }
        [data-testid="stMetricValue"] { font-size: 1.6rem !important; font-weight: 700; }
        .stTabs [data-baseweb="tab-list"] { gap: 20px; }
        .stTabs [data-baseweb="tab"] { height: 50px; white-space: pre-wrap; background-color: #0E1117; border-radius: 5px; gap: 1px; padding-top: 10px; padding-bottom: 10px; }
        .stTabs [aria-selected="true"] { background-color: #262730; border-bottom: 2px solid #FF4B4B; }
    </style>
""", unsafe_allow_html=True)

# --- GENERADOR DE DATA FICTICIA (SIMULADOR) ---
@st.cache_data
def generar_data_fake():
    # Fechas: Últimos 30 días
    fechas = pd.date_range(end=datetime.today(), periods=30)
    
    # 1. DATA TRÁFICO (GHL + META)
    data_trafico = []
    for fecha in fechas:
        clics = np.random.randint(200, 500)
        visitas = int(clics * np.random.uniform(0.7, 0.9)) # 70-90% de clics llegan a la web
        leads = int(visitas * np.random.uniform(0.1, 0.2)) # 10-20% conversión landing
        calificados = int(leads * np.random.uniform(0.3, 0.5)) # 30-50% califican
        gasto = clics * np.random.uniform(0.5, 1.5) # CPC variable
        
        data_trafico.append({
            "Fecha": fecha, "Clics": clics, "Visitas": visitas, 
            "Leads": leads, "Calificados": calificados, "Gasto_Ads": gasto
        })
    df_trafico = pd.DataFrame(data_trafico)

    # 2. DATA VENTAS (CLOSERS)
    closers = ["Pedro", "Juan", "Maria"]
    campanas = ["VSL_Frio_Enero", "Retargeting_Testimonio", "YouTube_Organic"]
    resultados = ["✅ Venta", "❌ No Show", "🚫 Descalificado", "👀 Seguimiento", "📅 Re-Agendado"]
    
    data_ventas = []
    # Simulamos que los leads calificados se agendan (con algo de lag o pérdida)
    total_agendados = df_trafico['Calificados'].sum() 
    
    for _ in range(total_agendados):
        fecha_venta = np.random.choice(fechas)
        closer = np.random.choice(closers)
        campana = np.random.choice(campanas, p=[0.6, 0.3, 0.1]) # VSL trae más tráfico
        resultado = np.random.choice(resultados, p=[0.15, 0.20, 0.20, 0.30, 0.15])
        
        monto = 0
        if resultado == "✅ Venta":
            monto = np.random.choice([1000, 1500, 3000]) # Precios High Ticket
            
        data_ventas.append({
            "Fecha": fecha_venta, "Closer": closer, "Campaña": campana,
            "Resultado": resultado, "Monto": monto
        })
        
    df_ventas = pd.DataFrame(data_ventas)
    
    # Lógica de Asistencia
    def check_asistencia(res):
        if res in ["❌ No Show", "📅 Re-Agendado"]: return 0
        return 1
    df_ventas['Asistio'] = df_v_fake = df_ventas['Resultado'].apply(check_asistencia)
    
    return df_trafico, df_ventas

# Cargar Data
df_trafico, df_ventas = generar_data_fake()

# --- SIDEBAR ---
st.sidebar.title("🎛️ Control Panel")
st.sidebar.info("Modo: Simulación / Demo")
closer_filter = st.sidebar.selectbox("Filtrar Closer", ["Todos"] + list(df_ventas['Closer'].unique()))
meta_facturacion = st.sidebar.number_input("Meta Mensual ($)", value=50000)

# Filtrado básico
if closer_filter != "Todos":
    df_ventas = df_ventas[df_ventas['Closer'] == closer_filter]
    # Nota: No filtramos tráfico por closer porque el tráfico es "antes" del closer.

# --- CÁLCULOS GLOBALES ---
gasto_total = df_trafico['Gasto_Ads'].sum()
facturacion_total = df_ventas['Monto'].sum()
profit = facturacion_total - gasto_total
roas = facturacion_total / gasto_total if gasto_total > 0 else 0

# --- HEADER (ALWAYS ON) ---
st.title("🦁 Agency Beast Dashboard")
st.markdown("---")

col1, col2, col3, col4 = st.columns(4)
col1.metric("💰 Facturación", f"${facturacion_total:,.0f}", delta=f"{facturacion_total/meta_facturacion*100:.1f}% Meta")
col2.metric("💸 Ad Spend", f"${gasto_total:,.0f}", delta="-Investido")
col3.metric("💎 Profit", f"${profit:,.0f}", delta_color="normal")
col4.metric("🔥 ROAS", f"{roas:.2f}x")

st.markdown("---")

# --- PESTAÑAS (LA ESTRUCTURA NUEVA) ---
tab1, tab2, tab3, tab4 = st.tabs([
    "👔 Visión CEO", 
    "🌪️ Embudo & Tráfico", 
    "📞 Performance Closers", 
    "📢 Campañas"
])

# === TAB 1: VISIÓN CEO ===
with tab1:
    st.subheader("📊 Salud General del Negocio")
    
    # KPIs de Alto Nivel
    total_leads = df_trafico['Leads'].sum()
    total_ventas = len(df_ventas[df_ventas['Resultado']=="✅ Venta"])
    total_shows = df_ventas['Asistio'].sum()
    
    conv_global = (total_ventas / total_leads * 100) if total_leads > 0 else 0
    show_rate_global = (total_shows / len(df_ventas) * 100) if len(df_ventas) > 0 else 0
    
    c1, c2, c3 = st.columns(3)
    c1.metric("Conversión Global (Leads -> Venta)", f"{conv_global:.2f}%")
    c2.metric("Tasa Asistencia Global (Show Rate)", f"{show_rate_global:.1f}%")
    c3.metric("Ticket Promedio", f"${facturacion_total/total_ventas:,.0f}" if total_ventas > 0 else "$0")
    
    st.divider()
    
    # Proyección (Simulada)
    st.write("#### 🎯 Proyección de Cierre de Mes")
    progreso = min(facturacion_total / meta_facturacion, 1.0)
    st.progress(progreso)
    st.caption(f"Has logrado el {progreso*100:.1f}% de la meta de ${meta_facturacion:,.0f}")

# === TAB 2: EMBUDO & TRÁFICO (MARKETING VIEW) ===
with tab2:
    st.subheader("🌪️ Full Funnel & Eficiencia")
    
    # Preparar datos para el "Super Embudo"
    suma_trafico = df_trafico.sum()
    agendas_total = len(df_ventas) # Asumimos que fila en ventas = agendado
    ventas_total = len(df_ventas[df_ventas['Resultado']=="✅ Venta"])
    
    # 1. VISUALIZACIÓN EMBUDO
    col_funnel, col_kpis = st.columns([2, 1])
    
    with col_funnel:
        fig_funnel = go.Figure(go.Funnel(
            y = ["Clics", "Visitas", "Leads Totales", "Calificados", "Agendas", "Ventas"],
            x = [suma_trafico['Clics'], suma_trafico['Visitas'], suma_trafico['Leads'], 
                 suma_trafico['Calificados'], agendas_total, ventas_total],
            textinfo = "value+percent previous",
            marker = {"color": ["#1f77b4", "#00b4d8", "#0096c7", "#48cae4", "#caf0f8", "#00CC96"]}
        ))
        fig_funnel.update_layout(title="Conversión Paso a Paso", height=400)
        st.plotly_chart(fig_funnel, use_container_width=True)
        
    with col_kpis:
        st.write("#### Costos & Calidad")
        cpl = gasto_total / suma_trafico['Leads'] if suma_trafico['Leads'] > 0 else 0
        cpql = gasto_total / suma_trafico['Calificados'] if suma_trafico['Calificados'] > 0 else 0
        cpa = gasto_total / ventas_total if ventas_total > 0 else 0
        
        st.metric("CPL (Costo x Lead)", f"${cpl:.2f}")
        st.metric("CPQL (Costo x Calif)", f"${cpql:.2f}", delta_color="off")
        st.metric("CPA (Costo x Venta)", f"${cpa:.2f}", help="Cuánto gastamos para cerrar 1 cliente")
        
        st.info(f"💡 De {suma_trafico['Leads']:.0f} leads, solo el **{(suma_trafico['Calificados']/suma_trafico['Leads']*100):.1f}%** calificaron.")

    st.divider()
    
    # 2. GRÁFICO TEMPORAL (Calidad vs Cantidad)
    st.subheader("📈 Calidad de Tráfico en el Tiempo")
    fig_line = px.line(df_trafico, x="Fecha", y=["Leads", "Calificados"], markers=True, 
                       color_discrete_map={"Leads": "cyan", "Calificados": "lime"})
    st.plotly_chart(fig_line, use_container_width=True)

# === TAB 3: CLOSERS (SALES VIEW) ===
with tab3:
    st.subheader("🏆 Ranking & Performance de Equipo")
    
    # Agrupar data por Closer
    ranking = df_ventas.groupby('Closer').apply(
        lambda x: pd.Series({
            'Agendas': len(x),
            'Shows': x['Asistio'].sum(),
            'Ventas': len(x[x['Resultado']=="✅ Venta"]),
            'Facturado': x['Monto'].sum()
        })
    ).reset_index()
    
    # Calcular Tasas
    ranking['Show Rate'] = (ranking['Shows'] / ranking['Agendas']).fillna(0)
    ranking['Close Rate'] = (ranking['Ventas'] / ranking['Shows']).fillna(0)
    ranking = ranking.sort_values('Facturado', ascending=False)
    
    # Mostrar con Column Config (Barras de progreso)
    st.dataframe(
        ranking,
        use_container_width=True,
        hide_index=True,
        column_order=["Closer", "Agendas", "Shows", "Ventas", "Show Rate", "Close Rate", "Facturado"],
        column_config={
            "Show Rate": st.column_config.ProgressColumn("Show Rate", format="%.1f%%", min_value=0, max_value=1),
            "Close Rate": st.column_config.ProgressColumn("Close Rate", format="%.1f%%", min_value=0, max_value=1),
            "Facturado": st.column_config.NumberColumn("Facturado ($)", format="$%d"),
        }
    )

# === TAB 4: CAMPAÑAS (MEDIA BUYER VIEW) ===
with tab4:
    st.subheader("📢 Rendimiento por Campaña de Origen")
    
    col_camp1, col_camp2 = st.columns([2, 1])
    
    # Agrupar por campaña
    perf_camp = df_ventas.groupby('Campaña').agg({
        'Monto': 'sum',
        'Resultado': lambda x: (x=="✅ Venta").sum() # Conteo de ventas
    }).rename(columns={'Monto': 'Ingresos Generados', 'Resultado': 'Ventas Cerradas'}).reset_index()
    
    perf_camp = perf_camp.sort_values('Ingresos Generados', ascending=False)
    
    with col_camp1:
        fig_camp = px.bar(perf_camp, x="Ingresos Generados", y="Campaña", orientation='h', 
                          text_auto='.2s', color="Ingresos Generados", title="Ingresos por Campaña")
        st.plotly_chart(fig_camp, use_container_width=True)
        
    with col_camp2:
        st.write("#### Detalle")
        st.dataframe(
            perf_camp, 
            hide_index=True,
            column_config={"Ingresos Generados": st.column_config.NumberColumn(format="$%d")}
        )
