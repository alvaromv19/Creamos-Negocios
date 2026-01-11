import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta

# --- 1. CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Agency Command Center", page_icon="🦁", layout="wide")

# CSS "Dark Mode Pro"
st.markdown("""
    <style>
        .block-container { padding-top: 1rem; padding-bottom: 3rem; }
        [data-testid="stMetricValue"] { font-size: 1.5rem !important; font-weight: 700; color: #ffffff; }
        [data-testid="stMetricLabel"] { font-size: 0.9rem !important; color: #a0a0a0; }
        .stProgress > div > div > div > div { background-color: #00CC96; }
        .stTabs [data-baseweb="tab-list"] { gap: 10px; }
        .stTabs [data-baseweb="tab"] { height: 45px; background-color: #1E1E1E; border-radius: 5px; color: white; }
        .stTabs [aria-selected="true"] { background-color: #00CC96; color: black; font-weight: bold; }
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

# --- 3. GESTIÓN DE METAS ---
if "meta_facturacion" not in st.session_state:
    st.session_state["meta_facturacion"] = 30000.0 
if "presupuesto_ads" not in st.session_state:
    st.session_state["presupuesto_ads"] = 5000.0

# --- 4. CARGA DE DATOS ---
@st.cache_data(ttl=300)
def cargar_datos():
    # LINKS
    url_budget_dic = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQGOLgPTDLie5gEbkViCbpebWfN9S_eb2h2GGlpWLjmfVgzfnwR_ncVTs4IqmKgmAFfxZTQHJlMBrIi/pub?output=csv"
    url_budget_2026 = "https://docs.google.com/spreadsheets/d/e/2PACX-1vTQKTt_taqoH2qNwWbs3t4doLsi0SuGavgdUNvpCKrqtlp5U9GaTqkTt9q-c1eWBnvPN88Qg5t0vXzK/pub?output=csv"
    url_leads_todos = "https://docs.google.com/spreadsheets/d/e/2PACX-1vTjCMjoi7DXiCeBRQdzAQZlx_L6SfpmbLlqmeRgZDHmCEdmN5_grVD_Yqa-5tzNprDS02o98ms80j1x/pub?gid=0&single=true&output=csv"
    # Link Específico Leads Calificados
    url_leads_qual = "https://docs.google.com/spreadsheets/d/e/2PACX-1vTjCMjoi7DXiCeBRQdzAQZlx_L6SfpmbLlqmeRgZDHmCEdmN5_grVD_Yqa-5tzNprDS02o98ms80j1x/pub?gid=1272057128&single=true&output=csv"
    url_ventas = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQuXaPCen61slzpr1TElxXoCROIxAgmgWT7pyWvel1dxq_Z_U1yZPrVrTbJfx9MwaL8_cluY3v2ywoB/pub?gid=0&single=true&output=csv"

    # --- BUDGET ---
    df_budget = pd.DataFrame()
    try:
        # Diciembre
        b1 = pd.read_csv(url_budget_dic)
        b1.rename(columns=lambda x: x.strip(), inplace=True)
        if 'Fecha' in b1.columns: b1['Fecha'] = pd.to_datetime(b1['Fecha'], dayfirst=True, errors='coerce')
        if 'Gasto' in b1.columns:
            if b1['Gasto'].dtype == 'O': b1['Gasto'] = b1['Gasto'].astype(str).str.replace(r'[$,]', '', regex=True)
            b1['Gasto'] = pd.to_numeric(b1['Gasto'], errors='coerce').fillna(0)
        b1['Clics'] = 0; b1['Visitas'] = 0
        b1 = b1[['Fecha', 'Gasto', 'Clics', 'Visitas']] if 'Fecha' in b1.columns else pd.DataFrame()

        # 2026
        b2 = pd.read_csv(url_budget_2026)
        b2.rename(columns={'Day': 'Fecha', 'Amount spent': 'Gasto', 'Link clicks': 'Clics', 'Landing page views': 'Visitas'}, inplace=True)
        b2['Fecha'] = pd.to_datetime(b2['Fecha'], errors='coerce')
        for col in ['Gasto', 'Clics', 'Visitas']:
            if b2[col].dtype == 'O': b2[col] = b2[col].astype(str).str.replace(r'[$,]', '', regex=True)
            b2[col] = pd.to_numeric(b2[col], errors='coerce').fillna(0)
        
        df_budget = pd.concat([b1, b2], ignore_index=True).sort_values('Fecha').dropna(subset=['Fecha'])
    except Exception as e: st.error(f"Error Budget: {e}")

    # --- LEADS (AQUÍ ESTÁ LA CORRECCIÓN) ---
    df_leads_all = pd.DataFrame()
    df_leads_qual = pd.DataFrame()
    try:
        # Todos
        l1 = pd.read_csv(url_leads_todos)
        l1.rename(columns={'Fecha Creación': 'Fecha'}, inplace=True)
        # CORRECCIÓN: Agregado dayfirst=True para que 10/01 sea 10 de Enero
        l1['Fecha'] = pd.to_datetime(l1['Fecha'], dayfirst=True, errors='coerce')
        df_leads_all = l1.dropna(subset=['Fecha'])
        
        # Calificados
        l2 = pd.read_csv(url_leads_qual)
        l2.rename(columns={'Fecha Creación': 'Fecha'}, inplace=True)
        # CORRECCIÓN: Agregado dayfirst=True vital para este archivo
        l2['Fecha'] = pd.to_datetime(l2['Fecha'], dayfirst=True, errors='coerce')
        df_leads_qual = l2.dropna(subset=['Fecha'])
    except Exception as e: st.error(f"Error Leads: {e}")

    # --- VENTAS ---
    df_ventas = pd.DataFrame()
    try:
        v = pd.read_csv(url_ventas)
        v['Fecha'] = pd.to_datetime(v['Fecha'], dayfirst=True, errors='coerce')
        v.dropna(subset=['Fecha'], inplace=True)
        
        if v['Monto ($)'].dtype == 'O': v['Monto ($)'] = v['Monto ($)'].astype(str).str.replace(r'[$,]', '', regex=True)
        v['Monto ($)'] = pd.to_numeric(v['Monto ($)'], errors='coerce').fillna(0)
        
        # Normalización Closers
        v['Closer'] = v['Closer'].astype(str).fillna("Sin Asignar")
        v['Closer'] = v['Closer'].str.strip().str.title()

        v['Resultado'] = v['Resultado'].fillna("Pendiente")
        
        def clasificar(res):
            res = str(res).lower()
            if "venta" in res: return "✅ Venta"
            if "no show" in res: return "❌ No Show"
            if "descalificado" in res: return "🚫 Descalificado"
            if "seguimiento" in res: return "👀 Seguimiento"
            return "Otro"
        v['Estado_Simple'] = v['Resultado'].apply(clasificar)
        
        def check_asistencia(res):
            res = str(res).lower()
            if "no show" in res: return 0
            if "re-agendado" in res: return 0
            return 1 
        v['Asistio'] = v['Resultado'].apply(check_asistencia)
        
        df_ventas = v
    except Exception as e: st.error(f"Error Ventas: {e}")

    return df_budget, df_leads_all, df_leads_qual, df_ventas

df_budget, df_leads_all, df_leads_qual, df_ventas = cargar_datos()

if df_ventas.empty and df_budget.empty:
    st.warning("⚠️ No hay datos.")
    st.stop()

# --- 5. SIDEBAR ---
st.sidebar.title("🎛️ Control Panel")
if st.sidebar.button("🔄 ACTUALIZAR DATOS", type="primary"):
    st.cache_data.clear()
    st.rerun()

st.sidebar.markdown("---")

filtro_tiempo = st.sidebar.selectbox("📅 Período", ["Este Mes", "Mes Anterior", "Hoy", "Ayer", "Esta Semana", "Últimos 7 días", "Últimos 30 días", "Personalizado"])
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

closers = ["Todos"] + sorted(list(df_ventas['Closer'].unique())) if not df_ventas.empty else ["Todos"]
closer_sel = st.sidebar.selectbox("👤 Closer", closers)

st.sidebar.info(f"{f_ini} al {f_fin}")

def filtrar_fecha(df):
    if df.empty: return df
    ts_ini = pd.Timestamp(f_ini)
    ts_fin = pd.Timestamp(f_fin)
    mask = (df['Fecha'].dt.normalize() >= ts_ini) & (df['Fecha'].dt.normalize() <= ts_fin)
    return df.loc[mask]

df_b_f = filtrar_fecha(df_budget)
df_la_f = filtrar_fecha(df_leads_all)
df_lq_f = filtrar_fecha(df_leads_qual)
df_v_f = filtrar_fecha(df_ventas)

if closer_sel != "Todos" and not df_v_f.empty:
    df_v_f = df_v_f[df_v_f['Closer'] == closer_sel]

# --- 6. KPI ENGINE ---
facturacion = df_v_f['Monto ($)'].sum()
gasto_ads = df_b_f['Gasto'].sum() if closer_sel == "Todos" else 0 
profit = facturacion - gasto_ads
roas = facturacion / gasto_ads if gasto_ads > 0 else 0

clics = df_b_f['Clics'].sum() if closer_sel == "Todos" else 0
visitas = df_b_f['Visitas'].sum() if closer_sel == "Todos" else 0
leads_total = len(df_la_f)
leads_qual = len(df_lq_f) 
agendas = len(df_v_f) 
shows = df_v_f['Asistio'].sum()
ventas = len(df_v_f[df_v_f['Estado_Simple'] == "✅ Venta"])

st.sidebar.markdown("---")
with st.sidebar.expander("🎯 Ajustar Metas"):
    m_fact = st.number_input("Meta Facturación", value=st.session_state["meta_facturacion"], step=1000.0)
    m_ads = st.number_input("Presupuesto Ads", value=st.session_state["presupuesto_ads"], step=500.0)
    if st.button("Guardar Metas"):
        st.session_state["meta_facturacion"] = m_fact
        st.session_state["presupuesto_ads"] = m_ads
        st.rerun()

# --- 7. HEADER ---
st.title(f"🚀 Dashboard: {f_ini} - {f_fin}")
h1, h2, h3, h4 = st.columns(4)
h1.metric("💰 Facturación", f"${facturacion:,.0f}", delta=f"{(facturacion/m_fact)*100:.1f}% Meta")
h2.metric("💸 Ad Spend", f"${gasto_ads:,.0f}", delta=f"Restante: ${m_ads-gasto_ads:,.0f}", delta_color="inverse")
h3.metric("💎 Profit", f"${profit:,.0f}", delta_color="normal")
h4.metric("🔥 ROAS", f"{roas:.2f}x", delta=f"{roas-3:.1f} vs KPI" if roas>0 else 0)
st.divider()

# --- 8. PESTAÑAS ---
tab1, tab2, tab3, tab4, tab5 = st.tabs(["👔 Visión CEO", "🌪️ Embudo y Tráfico", "📞 Performance Closer", "📢 Campañas", "🧮 Matemática Éxito"])

# === TAB 1: VISIÓN CEO ===
with tab1:
    st.subheader("📊 Resumen Ejecutivo")
    c_proj1, c_proj2, c_proj3 = st.columns(3)
    dias_restantes_mes = 30 - datetime.now().day if datetime.now().day < 30 else 0
    with c_proj1:
        st.write(f"**Progreso Meta (${m_fact:,.0f})**")
        st.progress(min(facturacion / m_fact, 1.0))
        st.caption(f"{(facturacion / m_fact)*100:.1f}% Completado")
    with c_proj2:
        st.metric("Falta para Meta", f"${max(m_fact - facturacion, 0):,.0f}")
        run_rate = (facturacion / len(pd.date_range(f_ini, f_fin))) * 30 if len(pd.date_range(f_ini, f_fin)) > 0 else 0
        st.caption(f"Proyección Cierre: ${run_rate:,.0f}")
    with c_proj3:
        inv_diaria = gasto_ads / ((f_fin - f_ini).days + 1) if ((f_fin - f_ini).days + 1) > 0 else 0
        sugerida = (m_ads - gasto_ads) / dias_restantes_mes if dias_restantes_mes > 0 else 0
        st.metric("Inversión Diaria", f"${inv_diaria:.0f}")
        st.caption(f"Sugerida: ${sugerida:.0f}/día")

    st.markdown("---")
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Conv. Global", f"{(ventas / leads_total * 100) if leads_total > 0 else 0:.2f}%")
    k2.metric("Show Rate", f"{(shows / agendas * 100) if agendas > 0 else 0:.1f}%")
    k3.metric("Close Rate", f"{(ventas / shows * 100) if shows > 0 else 0:.1f}%")
    k4.metric("Calidad Leads", f"{(leads_qual / leads_total * 100) if leads_total > 0 else 0:.1f}%")

    st.markdown("### 📈 Actividad Diaria")
    if not df_v_f.empty or not df_la_f.empty:
        # Preparamos dataframe diario combinado
        daily = pd.DataFrame(index=pd.date_range(f_ini, f_fin))
        daily.index.name = 'Fecha'
        
        # Agregamos métricas
        d_ventas = df_v_f.groupby('Fecha')['Monto ($)'].sum()
        d_count_ventas = df_v_f[df_v_f['Estado_Simple']=="✅ Venta"].groupby('Fecha').size()
        d_leads = df_la_f.groupby('Fecha').size()
        d_qual = df_lq_f.groupby('Fecha').size() if not df_lq_f.empty else pd.Series()
        
        daily['Facturación'] = d_ventas
        daily['Ventas (#)'] = d_count_ventas
        daily['Leads'] = d_leads
        daily['Calificados'] = d_qual
        daily = daily.fillna(0).reset_index()

        # Gráfico con HOVER UNIFIED (X-Ray Vision)
        fig_ecg = px.line(daily, x='Fecha', y=['Facturación', 'Leads'], 
                          title="Evolución Diaria (Pasa el mouse)", markers=True,
                          hover_data=['Ventas (#)', 'Calificados']) # Datos extra en el tooltip
        fig_ecg.update_layout(hovermode="x unified") # CLAVE: Activa el modo X-Ray
        st.plotly_chart(fig_ecg, use_container_width=True)

# === TAB 2: EMBUDO Y TRÁFICO ===
with tab2:
    st.subheader("🌪️ The Funnel Machine")
    col_fun, col_stats = st.columns([2, 1])
    
    with col_fun:
        # 4. EMBUDO HORIZONTAL (Izquierda a Derecha)
        funnel_data = pd.DataFrame({
            "Etapa": ["Clics", "Visitas", "Leads Totales", "Calificados", "Agendas", "Ventas"],
            "Cantidad": [clics, visitas, leads_total, leads_qual, agendas, ventas],
            "Color": ["#2A2D34", "#0096C7", "#48CAE4", "#90E0EF", "#ADE8F4", "#00CC96"]
        })
        # Usamos Bar con orientación 'h' para simular embudo izquierda-derecha
        fig_fun = px.bar(funnel_data, x="Cantidad", y="Etapa", orientation='h', text="Cantidad",
                         title="Conversión de Tráfico", color="Etapa", 
                         color_discrete_sequence=funnel_data["Color"].tolist())
        # Invertimos eje Y para que Clics quede arriba
        fig_fun.update_yaxes(autorange="reversed") 
        fig_fun.update_layout(showlegend=False, height=400)
        st.plotly_chart(fig_fun, use_container_width=True)
        
    with col_stats:
        st.markdown("#### 📉 Costos Unitarios")
        st.metric("CPL", f"${(gasto_ads / leads_total) if leads_total > 0 else 0:.2f}")
        st.metric("CPQL", f"${(gasto_ads / leads_qual) if leads_qual > 0 else 0:.2f}")
        st.metric("CPA", f"${(gasto_ads / ventas) if ventas > 0 else 0:.2f}")

    st.divider()
    st.subheader("📊 Tendencia: Calidad de Leads")
    # Reusamos el dataframe 'daily' que ya creamos en Tab 1 para consistencia
    if 'daily' in locals():
        fig_trend = px.line(daily, x='Fecha', y=['Leads', 'Calificados'], markers=True, 
                            title="Volumen vs Calidad", color_discrete_map={'Leads': 'cyan', 'Calificados': '#00CC96'})
        fig_trend.update_layout(hovermode="x unified") # X-Ray activado
        st.plotly_chart(fig_trend, use_container_width=True)

# === TAB 3: PERFORMANCE CLOSER ===
with tab3:
    st.subheader("🏆 Leaderboard de Ventas")
    if not df_v_f.empty:
        rank = df_v_f.groupby('Closer').apply(
            lambda x: pd.Series({
                'Facturado': x['Monto ($)'].sum(),
                'Ventas': len(x[x['Estado_Simple'] == "✅ Venta"]),
                'Agendas': len(x),
                'Shows': x['Asistio'].sum()
            })
        ).reset_index()
        rank['Show Rate'] = (rank['Shows'] / rank['Agendas']).fillna(0)
        rank['Close Rate'] = (rank['Ventas'] / rank['Shows']).fillna(0)
        rank = rank.sort_values('Facturado', ascending=False)
        st.dataframe(rank, use_container_width=True, hide_index=True,
            column_config={
                "Facturado": st.column_config.NumberColumn(format="$%d"),
                "Show Rate": st.column_config.ProgressColumn(format="%.0f%%", min_value=0, max_value=1),
                "Close Rate": st.column_config.ProgressColumn(format="%.0f%%", min_value=0, max_value=1),
            }
        )
    else:
        st.warning("No hay datos de ventas.")

# === TAB 4: CAMPAÑAS ===
with tab4:
    st.subheader("📢 Rendimiento por Origen")
    if not df_v_f.empty:
        c1, c2 = st.columns([2, 1])
        col_campana = 'Origen Campaña' if 'Origen Campaña' in df_v_f.columns else 'Fuente'
        perf_camp = df_v_f.groupby(col_campana).agg({'Monto ($)': 'sum', 'Estado_Simple': lambda x: (x=="✅ Venta").sum()}).rename(columns={'Monto ($)': 'Ingresos', 'Estado_Simple': 'Ventas'}).reset_index()
        perf_camp = perf_camp.sort_values('Ingresos', ascending=False)
        with c1:
            fig_bar = px.bar(perf_camp, x="Ingresos", y=col_campana, orientation='h', text_auto='.2s', title="Top Campañas")
            st.plotly_chart(fig_bar, use_container_width=True)
        with c2:
            st.dataframe(perf_camp, hide_index=True, column_config={"Ingresos": st.column_config.NumberColumn(format="$%d")})
    else:
        st.info("No hay datos de campañas.")

# === TAB 5: MATEMÁTICA DEL ÉXITO ===
with tab5:
    st.subheader("🧮 La Calculadora de Metas")
    restante = max(m_fact - facturacion, 0)
    col_math1, col_math2 = st.columns([1, 2])
    with col_math1:
        st.metric("Meta", f"${m_fact:,.0f}")
        st.metric("Actual", f"${facturacion:,.0f}")
        st.metric("Faltante", f"${restante:,.0f}")
    with col_math2:
        run_rate = (facturacion / datetime.now().day) * 30
        sc1, sc2, sc3 = st.columns(3)
        sc1.metric("🔴 Pesimista", f"${run_rate*0.85:,.0f}")
        sc2.metric("🟡 Realista", f"${run_rate:,.0f}")
        sc3.metric("🟢 Optimista", f"${run_rate*1.15:,.0f}")
        
        st.markdown("### 📉 Control de Presupuesto Ads")
        st.progress(min(gasto_ads/m_ads, 1.0))
        st.caption(f"Gastado: ${gasto_ads:,.0f} / ${m_ads:,.0f}")
