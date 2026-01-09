import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import os
import json

# --- 1. CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Agency Command Center", page_icon="🦁", layout="wide")

# CSS "Dark Mode Pro" con ajustes finos
st.markdown("""
    <style>
        .block-container { padding-top: 1rem; padding-bottom: 3rem; }
        [data-testid="stMetricValue"] { font-size: 1.5rem !important; font-weight: 700; color: #ffffff; }
        [data-testid="stMetricLabel"] { font-size: 0.9rem !important; color: #a0a0a0; }
        .stProgress > div > div > div > div { background-color: #00CC96; }
        .stTabs [data-baseweb="tab-list"] { gap: 10px; }
        .stTabs [data-baseweb="tab"] { height: 45px; background-color: #1E1E1E; border-radius: 5px; color: white; }
        .stTabs [aria-selected="true"] { background-color: #00CC96; color: black; font-weight: bold; }
        /* Bordes de tarjetas */
        div[data-testid="stMetric"] { background-color: #141414; padding: 15px; border-radius: 10px; border: 1px solid #333; }
    </style>
""", unsafe_allow_html=True)

# --- 2. PANTALLA DE BIENVENIDA ---
def pantalla_bienvenida():
    if "ingreso_confirmado" not in st.session_state:
        st.session_state["ingreso_confirmado"] = False

    if st.session_state["ingreso_confirmado"]:
        return True

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("<br><br><br>", unsafe_allow_html=True)
        st.title("🦁 Agency Command Center")
        st.markdown("### Creamos Negocios")
        st.markdown("Tu sistema operativo para escalar la facturación.")
        st.markdown("---")
        
        if st.button("Ingresar al Sistema ➡️", type="primary", use_container_width=True):
            st.session_state["ingreso_confirmado"] = True
            st.rerun()
    return False

if not pantalla_bienvenida():
    st.stop()

# --- 3. GESTIÓN DE METAS (SESSION STATE) ---
if "meta_facturacion" not in st.session_state:
    st.session_state["meta_facturacion"] = 30000.0 # Valor por defecto
if "presupuesto_ads" not in st.session_state:
    st.session_state["presupuesto_ads"] = 5000.0   # Valor por defecto

# --- 4. CARGA DE DATOS (EL MOTOR) ---
@st.cache_data(ttl=300)
def cargar_datos():
    # --- LINKS ---
    # 1. Budget
    url_budget_dic = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQGOLgPTDLie5gEbkViCbpebWfN9S_eb2h2GGlpWLjmfVgzfnwR_ncVTs4IqmKgmAFfxZTQHJlMBrIi/pub?output=csv"
    url_budget_2026 = "https://docs.google.com/spreadsheets/d/e/2PACX-1vTQKTt_taqoH2qNwWbs3t4doLsi0SuGavgdUNvpCKrqtlp5U9GaTqkTt9q-c1eWBnvPN88Qg5t0vXzK/pub?output=csv"
    
    # 2. Leads
    url_leads_todos = "https://docs.google.com/spreadsheets/d/e/2PACX-1vTjCMjoi7DXiCeBRQdzAQZlx_L6SfpmbLlqmeRgZDHmCEdmN5_grVD_Yqa-5tzNprDS02o98ms80j1x/pub?gid=0&single=true&output=csv"
    url_leads_qual = "https://docs.google.com/spreadsheets/d/e/2PACX-1vTjCMjoi7DXiCeBRQdzAQZlx_L6SfpmbLlqmeRgZDHmCEdmN5_grVD_Yqa-5tzNprDS02o98ms80j1x/pub?gid=1272057128&single=true&output=csv"
    
    # 3. Ventas
    url_ventas = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQuXaPCen61slzpr1TElxXoCROIxAgmgWT7pyWvel1dxq_Z_U1yZPrVrTbJfx9MwaL8_cluY3v2ywoB/pub?gid=0&single=true&output=csv"

    # --- PROCESAMIENTO BUDGET ---
    df_budget = pd.DataFrame()
    try:
        # A. Diciembre (Formato Viejo)
        b1 = pd.read_csv(url_budget_dic)
        # Intentamos estandarizar columnas
        b1.rename(columns=lambda x: x.strip(), inplace=True)
        # Mapeo manual si sabemos los nombres o por posición si es arriesgado
        # Asumimos que tiene Fecha y Gasto. Creamos Clics/Visitas en 0
        if 'Fecha' in b1.columns:
            b1['Fecha'] = pd.to_datetime(b1['Fecha'], dayfirst=True, errors='coerce')
        if 'Gasto' in b1.columns:
            if b1['Gasto'].dtype == 'O': b1['Gasto'] = b1['Gasto'].astype(str).str.replace(r'[$,]', '', regex=True)
            b1['Gasto'] = pd.to_numeric(b1['Gasto'], errors='coerce').fillna(0)
        
        b1['Clics'] = 0
        b1['Visitas'] = 0
        # Seleccionamos solo lo que nos sirve
        b1 = b1[['Fecha', 'Gasto', 'Clics', 'Visitas']] if 'Fecha' in b1.columns else pd.DataFrame()

        # B. 2026 (Formato Nuevo)
        b2 = pd.read_csv(url_budget_2026)
        b2.rename(columns={'Day': 'Fecha', 'Amount spent': 'Gasto', 'Link clicks': 'Clics', 'Landing page views': 'Visitas'}, inplace=True)
        b2['Fecha'] = pd.to_datetime(b2['Fecha'], errors='coerce') # Formato YYYY-MM-DD suele ser automático
        
        if b2['Gasto'].dtype == 'O': b2['Gasto'] = b2['Gasto'].astype(str).str.replace(r'[$,]', '', regex=True)
        b2['Gasto'] = pd.to_numeric(b2['Gasto'], errors='coerce').fillna(0)
        
        b2['Clics'] = pd.to_numeric(b2['Clics'], errors='coerce').fillna(0)
        b2['Visitas'] = pd.to_numeric(b2['Visitas'], errors='coerce').fillna(0)
        
        # Unimos
        df_budget = pd.concat([b1, b2], ignore_index=True).sort_values('Fecha')
        
    except Exception as e:
        st.error(f"Error cargando Budget: {e}")

    # --- PROCESAMIENTO LEADS ---
    df_leads_all = pd.DataFrame()
    df_leads_qual = pd.DataFrame()
    try:
        # Todos
        l1 = pd.read_csv(url_leads_todos)
        l1.rename(columns={'Fecha Creación': 'Fecha'}, inplace=True)
        l1['Fecha'] = pd.to_datetime(l1['Fecha'], errors='coerce')
        df_leads_all = l1
        
        # Calificados
        l2 = pd.read_csv(url_leads_qual)
        l2.rename(columns={'Fecha Creación': 'Fecha'}, inplace=True)
        l2['Fecha'] = pd.to_datetime(l2['Fecha'], errors='coerce')
        df_leads_qual = l2
    except Exception as e:
        st.error(f"Error cargando Leads: {e}")

    # --- PROCESAMIENTO VENTAS ---
    df_ventas = pd.DataFrame()
    try:
        v = pd.read_csv(url_ventas)
        v['Fecha'] = pd.to_datetime(v['Fecha'], dayfirst=True, errors='coerce')
        
        if v['Monto ($)'].dtype == 'O': 
            v['Monto ($)'] = v['Monto ($)'].astype(str).str.replace(r'[$,]', '', regex=True)
        v['Monto ($)'] = pd.to_numeric(v['Monto ($)'], errors='coerce').fillna(0)
        
        v['Closer'] = v['Closer'].fillna("Sin Asignar")
        v['Resultado'] = v['Resultado'].fillna("Pendiente")
        
        # Clasificación
        def clasificar(res):
            res = str(res).lower()
            if "venta" in res: return "✅ Venta"
            if "no show" in res: return "❌ No Show"
            if "descalificado" in res: return "🚫 Descalificado"
            if "seguimiento" in res: return "👀 Seguimiento"
            return "Otro"
        v['Estado_Simple'] = v['Resultado'].apply(clasificar)
        
        # Asistencia
        def check_asistencia(res):
            res = str(res).lower()
            if "no show" in res: return 0
            if "re-agendado" in res: return 0
            return 1 # Asumimos asistencia
        v['Asistio'] = v['Resultado'].apply(check_asistencia)
        
        df_ventas = v
    except Exception as e:
        st.error(f"Error cargando Ventas: {e}")

    return df_budget, df_leads_all, df_leads_qual, df_ventas

# Cargar
df_budget, df_leads_all, df_leads_qual, df_ventas = cargar_datos()

if df_ventas.empty and df_budget.empty:
    st.warning("⚠️ No hay datos disponibles.")
    st.stop()


# --- 5. SIDEBAR (FILTROS Y METAS) ---
st.sidebar.title("🎛️ Control Panel")

# Botón Actualizar
if st.sidebar.button("🔄 ACTUALIZAR DATOS", type="primary"):
    st.cache_data.clear()
    st.rerun()

st.sidebar.markdown("---")

# Filtro Fechas
filtro_tiempo = st.sidebar.selectbox(
    "📅 Período de Tiempo",
    ["Este Mes", "Mes Anterior", "Hoy", "Ayer", "Esta Semana", "Últimos 7 días", "Últimos 30 días", "Personalizado"]
)

hoy = pd.to_datetime("today").date()

if filtro_tiempo == "Hoy": f_ini, f_fin = hoy, hoy
elif filtro_tiempo == "Ayer": f_ini, f_fin = hoy - timedelta(days=1), hoy - timedelta(days=1)
elif filtro_tiempo == "Esta Semana": f_ini, f_fin = hoy - timedelta(days=hoy.weekday()), hoy
elif filtro_tiempo == "Últimos 7 días": f_ini, f_fin = hoy - timedelta(days=7), hoy
elif filtro_tiempo == "Este Mes": f_ini, f_fin = hoy.replace(day=1), hoy
elif filtro_tiempo == "Mes Anterior":
    primer = hoy.replace(day=1)
    f_fin = primer - timedelta(days=1)
    f_ini = f_fin.replace(day=1)
elif filtro_tiempo == "Últimos 30 días": f_ini, f_fin = hoy - timedelta(days=30), hoy
else:
    c1, c2 = st.sidebar.columns(2)
    f_ini = c1.date_input("Inicio", hoy)
    f_fin = c2.date_input("Fin", hoy)

# Filtro Closer (Solo afecta a Ventas)
closers = ["Todos"] + sorted(list(df_ventas['Closer'].unique())) if not df_ventas.empty else ["Todos"]
closer_sel = st.sidebar.selectbox("👤 Closer", closers)

st.sidebar.info(f"Visualizando: {f_ini} al {f_fin}")

# --- APLICAR FILTROS ---
# Función auxiliar para filtrar por fecha
def filtrar_fecha(df):
    if df.empty: return df
    mask = (df['Fecha'].dt.date >= f_ini) & (df['Fecha'].dt.date <= f_fin)
    return df.loc[mask]

df_b_f = filtrar_fecha(df_budget)
df_la_f = filtrar_fecha(df_leads_all)
df_lq_f = filtrar_fecha(df_leads_qual)
df_v_f = filtrar_fecha(df_ventas)

# Filtro Closer (Solo Ventas)
if closer_sel != "Todos" and not df_v_f.empty:
    df_v_f = df_v_f[df_v_f['Closer'] == closer_sel]

# --- 6. CÁLCULOS MAESTROS (KPIS) ---
# Dinero
facturacion = df_v_f['Monto ($)'].sum()
gasto_ads = df_b_f['Gasto'].sum() if closer_sel == "Todos" else 0 # Si filtra closer, gasto ads es 0 (no es atribuible directo aqui)
profit = facturacion - gasto_ads
roas = facturacion / gasto_ads if gasto_ads > 0 else 0

# Volúmenes
clics = df_b_f['Clics'].sum() if closer_sel == "Todos" else 0
visitas = df_b_f['Visitas'].sum() if closer_sel == "Todos" else 0
leads_total = len(df_la_f)
leads_qual = len(df_lq_f)
agendas = len(df_v_f) # Asumimos que fila en ventas es una agenda
shows = df_v_f['Asistio'].sum()
ventas = len(df_v_f[df_v_f['Estado_Simple'] == "✅ Venta"])

# Metas (Input en Sidebar para ajustar al vuelo)
st.sidebar.markdown("---")
with st.sidebar.expander("🎯 Ajustar Metas"):
    m_fact = st.number_input("Meta Facturación", value=st.session_state["meta_facturacion"], step=1000.0)
    m_ads = st.number_input("Presupuesto Ads", value=st.session_state["presupuesto_ads"], step=500.0)
    if st.button("Guardar Metas"):
        st.session_state["meta_facturacion"] = m_fact
        st.session_state["presupuesto_ads"] = m_ads
        st.rerun()

# --- 7. HEADER (ALWAYS ON) ---
st.title(f"🚀 Dashboard: {f_ini} - {f_fin}")

h1, h2, h3, h4 = st.columns(4)
h1.metric("💰 Facturación", f"${facturacion:,.0f}", delta=f"{(facturacion/m_fact)*100:.1f}% Meta")
h2.metric("💸 Ad Spend", f"${gasto_ads:,.0f}", delta=f"Restante: ${m_ads-gasto_ads:,.0f}", delta_color="inverse")
h3.metric("💎 Profit", f"${profit:,.0f}", delta_color="normal")
h4.metric("🔥 ROAS", f"{roas:.2f}x", delta=f"{roas-3:.1f} vs KPI" if roas>0 else 0)

st.divider()

# --- 8. PESTAÑAS PRINCIPALES ---
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "👔 Visión CEO", 
    "🌪️ Embudo y Tráfico", 
    "📞 Performance Closer", 
    "📢 Campañas",
    "🧮 Matemática Éxito"
])

# === TAB 1: VISIÓN CEO ===
with tab1:
    st.subheader("📊 Resumen Ejecutivo")
    
    # 1. Proyección (Barras)
    c_proj1, c_proj2, c_proj3 = st.columns(3)
    
    # Cálculos Proyección
    dias_mes = (f_fin - f_ini.replace(day=1)).days + 30 # Aprox para demo, idealmente usar calendario real
    dia_actual = datetime.now().day
    dias_restantes_mes = 30 - dia_actual if dia_actual < 30 else 0
    
    with c_proj1:
        st.write(f"**Progreso Meta (${m_fact:,.0f})**")
        prog = min(facturacion / m_fact, 1.0)
        st.progress(prog)
        st.caption(f"{prog*100:.1f}% Completado")
        
    with c_proj2:
        falta = max(m_fact - facturacion, 0)
        st.metric("Falta para Meta", f"${falta:,.0f}")
        # Proyección lineal simple
        run_rate = (facturacion / len(pd.date_range(f_ini, f_fin))) * 30 if len(pd.date_range(f_ini, f_fin)) > 0 else 0
        st.caption(f"Proyección Cierre: ${run_rate:,.0f}")

    with c_proj3:
        # Inversión Diaria
        dias_rango = (f_fin - f_ini).days + 1
        inv_diaria = gasto_ads / dias_rango if dias_rango > 0 else 0
        sugerida = (m_ads - gasto_ads) / dias_restantes_mes if dias_restantes_mes > 0 else 0
        st.metric("Inversión Diaria Actual", f"${inv_diaria:.0f}")
        st.caption(f"Sugerida para agotar budget: ${sugerida:.0f}/día")

    st.markdown("---")
    
    # 2. Eficiencia Funnel (KPIs)
    k1, k2, k3, k4 = st.columns(4)
    conv_glob = (ventas / leads_total * 100) if leads_total > 0 else 0
    show_rate = (shows / agendas * 100) if agendas > 0 else 0
    close_rate = (ventas / shows * 100) if shows > 0 else 0
    calif_rate = (leads_qual / leads_total * 100) if leads_total > 0 else 0
    
    k1.metric("Conv. Global (Lead->Venta)", f"{conv_glob:.2f}%")
    k2.metric("Show Rate (Asistencia)", f"{show_rate:.1f}%")
    k3.metric("Close Rate (Cierre)", f"{close_rate:.1f}%")
    k4.metric("Calidad Leads", f"{calif_rate:.1f}%", help="% Leads que son Calificados")

    # 3. Widget Diario (Electrocardiograma - Popups)
    st.markdown("### 📈 Actividad Diaria")
    if not df_v_f.empty:
        daily = df_v_f.groupby('Fecha').agg({'Monto ($)': 'sum', 'Estado_Simple': 'count'}).rename(columns={'Estado_Simple': 'Ventas #'})
        # Unir con leads
        d_leads = df_la_f.groupby('Fecha').size().to_frame('Leads')
        daily = daily.join(d_leads, how='outer').fillna(0)
        
        fig_ecg = px.line(daily, y=['Monto ($)', 'Leads'], title="Facturación vs Volumen Leads", markers=True)
        st.plotly_chart(fig_ecg, use_container_width=True)


# === TAB 2: EMBUDO Y TRÁFICO ===
with tab2:
    st.subheader("🌪️ The Funnel Machine")
    
    # 1. Gráfico Funnel (Izquierda) + Tabla KPIs (Derecha)
    col_fun, col_stats = st.columns([2, 1])
    
    with col_fun:
        # Preparar datos funnel
        funnel_data = dict(
            number=[clics, visitas, leads_total, leads_qual, agendas, ventas],
            stage=["Clics", "Visitas", "Leads Totales", "Calificados", "Agendas", "Ventas"]
        )
        fig_fun = go.Figure(go.Funnel(
            y = funnel_data['stage'],
            x = funnel_data['number'],
            textinfo = "value+percent previous",
            marker = {"color": ["#2A2D34", "#0096C7", "#48CAE4", "#90E0EF", "#ADE8F4", "#00CC96"]}
        ))
        fig_fun.update_layout(margin=dict(t=0, b=0, l=0, r=0), height=400, plot_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig_fun, use_container_width=True)
        
    with col_stats:
        st.markdown("#### 📉 Costos Unitarios")
        cpl = gasto_ads / leads_total if leads_total > 0 else 0
        cpql = gasto_ads / leads_qual if leads_qual > 0 else 0
        cpa = gasto_ads / ventas if ventas > 0 else 0
        
        st.metric("CPL (Costo x Lead)", f"${cpl:.2f}")
        st.metric("CPQL (Costo x Calif.)", f"${cpql:.2f}", delta_color="off")
        st.metric("CPA (Costo x Venta)", f"${cpa:.2f}")
        st.info("El CPQL ideal debe ser < $20")

    st.divider()
    
    # 2. Gráfico Tendencia (Calidad vs Cantidad)
    st.subheader("📊 Tendencia: Calidad de Leads")
    # Agrupar por dia
    trend_leads = df_la_f.groupby('Fecha').size().reset_index(name='Leads Totales')
    trend_qual = df_lq_f.groupby('Fecha').size().reset_index(name='Calificados')
    
    if not trend_leads.empty:
        trend_merged = pd.merge(trend_leads, trend_qual, on='Fecha', how='left').fillna(0)
        fig_trend = px.line(trend_merged, x='Fecha', y=['Leads Totales', 'Calificados'], 
                           color_discrete_map={'Leads Totales': '#48CAE4', 'Calificados': '#00CC96'},
                           markers=True)
        fig_trend.update_layout(hovermode="x unified")
        st.plotly_chart(fig_trend, use_container_width=True)
    else:
        st.info("No hay datos de leads en este periodo.")

# === TAB 3: PERFORMANCE CLOSER ===
with tab3:
    st.subheader("🏆 Leaderboard de Ventas")
    
    if not df_v_f.empty:
        # Agrupar
        rank = df_v_f.groupby('Closer').apply(
            lambda x: pd.Series({
                'Facturado': x['Monto ($)'].sum(),
                'Ventas': len(x[x['Estado_Simple'] == "✅ Venta"]),
                'Agendas': len(x),
                'Shows': x['Asistio'].sum()
            })
        ).reset_index()
        
        # Tasas
        rank['Show Rate'] = (rank['Shows'] / rank['Agendas']).fillna(0)
        rank['Close Rate'] = (rank['Ventas'] / rank['Shows']).fillna(0)
        
        # Ordenar
        rank = rank.sort_values('Facturado', ascending=False)
        
        # Renderizar Tabla Bonita
        st.dataframe(
            rank,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Closer": st.column_config.TextColumn("👤 Closer"),
                "Facturado": st.column_config.NumberColumn("💵 Facturado", format="$%d"),
                "Show Rate": st.column_config.ProgressColumn("Show Rate", format="%.0f%%", min_value=0, max_value=1),
                "Close Rate": st.column_config.ProgressColumn("Close Rate", format="%.0f%%", min_value=0, max_value=1),
            }
        )
    else:
        st.warning("No hay datos de ventas para mostrar.")

# === TAB 4: CAMPAÑAS ===
with tab4:
    st.subheader("📢 Rendimiento por Origen")
    
    if not df_v_f.empty:
        c1, c2 = st.columns([2, 1])
        
        # Agrupar por Origen Campaña (Columna K del sheet ventas)
        # Nota: Ajusta 'Origen Campaña' si el nombre exacto es otro en tu CSV
        col_campana = 'Origen Campaña' if 'Origen Campaña' in df_v_f.columns else 'Fuente'
        
        perf_camp = df_v_f.groupby(col_campana).agg({
            'Monto ($)': 'sum',
            'Estado_Simple': lambda x: (x=="✅ Venta").sum()
        }).rename(columns={'Monto ($)': 'Ingresos', 'Estado_Simple': 'Ventas'}).reset_index()
        
        perf_camp = perf_camp.sort_values('Ingresos', ascending=False)
        
        with c1:
            fig_bar = px.bar(perf_camp, x="Ingresos", y=col_campana, orientation='h', text_auto='.2s', 
                             title="Top Campañas por Facturación", color="Ingresos", color_continuous_scale="Greens")
            st.plotly_chart(fig_bar, use_container_width=True)
            
        with c2:
            st.dataframe(perf_camp, hide_index=True, use_container_width=True,
                         column_config={"Ingresos": st.column_config.NumberColumn(format="$%d")})
    else:
        st.info("No hay datos de campañas.")

# === TAB 5: MATEMÁTICA DEL ÉXITO ===
with tab5:
    st.subheader("🧮 La Calculadora de Metas")
    
    # Datos Base
    restante = max(m_fact - facturacion, 0)
    dias_rest = max(dias_restantes_mes, 0)
    
    col_math1, col_math2 = st.columns([1, 2])
    
    with col_math1:
        st.markdown("### 🎯 Objetivo")
        st.metric("Meta", f"${m_fact:,.0f}")
        st.metric("Actual", f"${facturacion:,.0f}")
        st.metric("Faltante", f"${restante:,.0f}", delta_color="inverse")
    
    with col_math2:
        st.markdown("### 🔮 Proyecciones (Escenarios)")
        
        # Escenarios
        run_rate = (facturacion / datetime.now().day) * 30 # Simple proyección lineal
        pesimista = run_rate * 0.85
        optimista = run_rate * 1.15
        
        sc1, sc2, sc3 = st.columns(3)
        sc1.metric("🔴 Pesimista (-15%)", f"${pesimista:,.0f}")
        sc2.metric("🟡 Realista (Actual)", f"${run_rate:,.0f}")
        sc3.metric("🟢 Optimista (+15%)", f"${optimista:,.0f}")
        
        st.markdown("---")
        
        # Requerimiento Diario
        req_diario = restante / dias_rest if dias_rest > 0 else 0
        avg_diario = facturacion / datetime.now().day
        
        st.info(f"💡 Para llegar a la meta, necesitas facturar **${req_diario:,.0f}** cada día restante.")
        if avg_diario < req_diario:
            st.warning(f"⚠️ Tu ritmo actual es **${avg_diario:,.0f}/día**. ¡Acelera!")
        else:
            st.success(f"✅ Vas bien. Tu ritmo actual es **${avg_diario:,.0f}/día**.")

    # Control de Ads (Bottom)
    st.markdown("### 📉 Control de Presupuesto Ads")
    b_rest = max(m_ads - gasto_ads, 0)
    st.progress(min(gasto_ads/m_ads, 1.0))
    st.caption(f"Presupuesto consumido: ${gasto_ads:,.0f} / ${m_ads:,.0f}")
    
    # Gráfico Lineal de Gasto vs Presupuesto Ideal (Simulado visualmente)
    if not df_b_f.empty:
        daily_spend = df_b_f.groupby('Fecha')['Gasto'].sum().reset_index()
        # Línea de "Techo" ideal (Promedio diario permitido)
        daily_spend['Límite Diario'] = m_ads / 30 
        
        fig_spend = px.line(daily_spend, x='Fecha', y=['Gasto', 'Límite Diario'], 
                            color_discrete_map={'Gasto': '#FF4B4B', 'Límite Diario': '#4CAF50'})
        fig_spend.update_layout(title="Gasto Diario vs Límite Ideal")
        st.plotly_chart(fig_spend, use_container_width=True)
