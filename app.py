import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta
import json
import os
import extra_streamlit_components as stx 

# --- PANTALLA DE BIENVENIDA CON COOKIES (PERSISTENTE) ---
def pantalla_bienvenida():
    st.markdown("""
        <style>
            .stSpinner { display:none; }
        </style>
    """, unsafe_allow_html=True)

    cookie_manager = stx.CookieManager(key="cookie_manager_dashboard")
    
    # Manejo de error silencioso por si las cookies tardan en cargar
    try:
        cookie_val = cookie_manager.get(cookie="ingreso_ok")
    except:
        cookie_val = None

    if cookie_val == "true":
        return True

    if "ingreso_confirmado" in st.session_state and st.session_state["ingreso_confirmado"]:
        return True

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("<br><br>", unsafe_allow_html=True)
        st.title("🚀 Bienvenido al Dashboard")
        st.subheader("Creamos Negocios")
        st.markdown("Tu centro de comando para visualizar métricas y escalar resultados.")
        st.markdown("---")
        
        if st.button("Ingresar al Sistema ➡️", type="primary", use_container_width=True):
            st.session_state["ingreso_confirmado"] = True
            try:
                cookie_manager.set("ingreso_ok", "true", expires_at=datetime.now() + timedelta(days=30))
            except:
                pass 
            st.rerun()

    return False 

# --- CONFIGURACIÓN DE METAS (PERSISTENCIA) ---
ARCHIVO_METAS = 'metas_config.json'

def cargar_metas():
    if os.path.exists(ARCHIVO_METAS):
        with open(ARCHIVO_METAS, 'r') as f:
            return json.load(f)
    return {"meta_facturacion": 10000.0, "presupuesto_ads": 3000.0}

def guardar_metas_archivo(fact, ads):
    with open(ARCHIVO_METAS, 'w') as f:
        json.dump({"meta_facturacion": fact, "presupuesto_ads": ads}, f)

# --- AQUÍ EMPIEZA TU DASHBOARD ---
st.title("🚀 Creamos Negocios - Dashboard")

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
        
        def clasificar_estado(texto):
            texto = str(texto).lower()
            if "venta" in texto: return "✅ Venta"
            if "no show" in texto: return "❌ No Show"
            if "descalificado" in texto: return "🚫 Descalificado"
            if "seguimiento" in texto: return "👀 Seguimiento"
            if "re-agendado" in texto or "reagendado" in texto: return "📅 Re-Agendado"
            return "Otro/Pendiente"
        df_v['Estado_Simple'] = df_v['Resultado'].apply(clasificar_estado)

        def es_asistencia_valida(row):
            res = str(row['Resultado']).lower()
            if "venta" in res: return True
            if "seguimiento" in res: return True 
            if "descalificado" in res: return True 
            if "asistió" in res and "no show" not in res: return True
            return False
        df_v['Es_Asistencia'] = df_v.apply(es_asistencia_valida, axis=1)

    except Exception as e:
        st.error(f"Error cargando Ventas: {e}")
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

if not pantalla_bienvenida():
    st.stop()

df_ventas, df_gastos = cargar_datos()

if df_ventas.empty:
    st.warning("Esperando datos... Revisa conexión.")
    st.stop()

# --- SIDEBAR: CONFIGURACIÓN Y METAS ---
st.sidebar.header("🎛️ Panel de Control")
if st.sidebar.button("🔄 Actualizar Datos"):
    st.cache_data.clear()
    st.rerun()

# --- SECCIÓN: METAS PERSISTENTES ---
st.sidebar.markdown("---")
st.sidebar.subheader("🎯 Configuración de Objetivos")

metas_actuales = cargar_metas()
# Usamos min_value=1.0 para evitar ceros accidentales en la UI
meta_facturacion = st.sidebar.number_input("Meta Facturación ($)", value=float(metas_actuales["meta_facturacion"]), step=500.0, min_value=1.0)
presupuesto_ads = st.sidebar.number_input("Presupuesto Ads ($)", value=float(metas_actuales["presupuesto_ads"]), step=100.0)

if st.sidebar.button("💾 Guardar Objetivos"):
    guardar_metas_archivo(meta_facturacion, presupuesto_ads)
    st.sidebar.success("¡Objetivos actualizados!")
    st.rerun()

st.sidebar.markdown("---")

# --- FILTROS (INCLUYE MES ANTERIOR) ---
filtro_tiempo = st.sidebar.selectbox(
    "Selecciona Período:",
    ["Este Mes", "Mes Anterior", "Hoy", "Ayer", "Esta Semana", "Últimos 7 días", "Últimos 30 días", "Personalizado"]
)

hoy = pd.to_datetime("today").date()

if filtro_tiempo == "Hoy":
    f_inicio, f_fin = hoy, hoy
elif filtro_tiempo == "Ayer":
    f_inicio, f_fin = hoy - timedelta(days=1), hoy - timedelta(days=1)
elif filtro_tiempo == "Esta Semana":
    f_inicio = hoy - timedelta(days=hoy.weekday())
    f_fin = hoy
elif filtro_tiempo == "Últimos 7 días":
    f_inicio, f_fin = hoy - timedelta(days=7), hoy
elif filtro_tiempo == "Este Mes":
    f_inicio, f_fin = hoy.replace(day=1), hoy
elif filtro_tiempo == "Mes Anterior":
    primer_dia_este_mes = hoy.replace(day=1)
    f_fin = primer_dia_este_mes - timedelta(days=1)
    f_inicio = f_fin.replace(day=1)
elif filtro_tiempo == "Últimos 30 días":
    f_inicio, f_fin = hoy - timedelta(days=30), hoy
else:
    f_inicio = st.sidebar.date_input("Inicio", hoy)
    f_fin = st.sidebar.date_input("Fin", hoy)

lista_closers = ["Todos"] + sorted([c for c in df_ventas['Closer'].unique() if c])
closer_sel = st.sidebar.selectbox("Closer", lista_closers)

st.sidebar.info(f"📅 Visualizando: {f_inicio} al {f_fin}")

mask_v = (df_ventas['Fecha'].dt.date >= f_inicio) & (df_ventas['Fecha'].dt.date <= f_fin)
df_v_filtrado = df_ventas.loc[mask_v].copy()

if not df_gastos.empty:
    mask_g = (df_gastos['Fecha'].dt.date >= f_inicio) & (df_gastos['Fecha'].dt.date <= f_fin)
    df_g_filtrado = df_gastos.loc[mask_g].copy()
else:
    df_g_filtrado = pd.DataFrame(columns=['Fecha', 'Gasto'])

if closer_sel != "Todos":
    df_v_filtrado = df_v_filtrado[df_v_filtrado['Closer'] == closer_sel]

# --- CÁLCULOS PRINCIPALES ---
facturacion = df_v_filtrado['Monto ($)'].sum()
inversion_ads = df_g_filtrado['Gasto'].sum() if closer_sel == "Todos" else 0
profit = facturacion - inversion_ads 
roas = (facturacion / inversion_ads) if inversion_ads > 0 else 0

total_leads = len(df_v_filtrado)
total_asistencias = df_v_filtrado['Es_Asistencia'].sum()
ventas_cerradas = len(df_v_filtrado[df_v_filtrado['Estado_Simple'] == "✅ Venta"])
tasa_asistencia = (total_asistencias / total_leads * 100) if total_leads > 0 else 0
tasa_cierre = (ventas_cerradas / total_asistencias * 100) if total_asistencias > 0 else 0

# --- LÓGICA DE PROYECCIONES ---
mes_actual = hoy.month
anio_actual = hoy.year
dias_en_mes = (pd.Timestamp(year=anio_actual, month=mes_actual, day=1) + pd.tseries.offsets.MonthEnd(0)).day
dia_hoy = hoy.day
dias_restantes = dias_en_mes - dia_hoy

# CORRECCIÓN DE LA LÍNEA 220: Validación de seguridad
# Validamos que meta_facturacion no sea None (puede pasar si borras el campo) ni 0
if meta_facturacion and meta_facturacion > 0:
    progreso_facturacion = min(facturacion / meta_facturacion, 1.0)
    faltante_facturacion = max(meta_facturacion - facturacion, 0)
else:
    progreso_facturacion = 0
    faltante_facturacion = 0

proyeccion_cierre = (facturacion / dia_hoy) * dias_en_mes if dia_hoy > 0 else 0

# NUEVO: Facturación Sugerida Diaria
if dias_restantes > 0:
    facturacion_necesaria_diaria = faltante_facturacion / dias_restantes
else:
    facturacion_necesaria_diaria = faltante_facturacion 

# Proyección Gasto Ads (Budget Pacing)
gasto_mes_total = df_gastos[
    (df_gastos['Fecha'].dt.month == mes_actual) & 
    (df_gastos['Fecha'].dt.year == anio_actual)
]['Gasto'].sum()

presupuesto_restante = max(presupuesto_ads - gasto_mes_total, 0)
gasto_ideal_diario = presupuesto_restante / dias_restantes if dias_restantes > 0 else 0
gasto_promedio_actual = gasto_mes_total / dia_hoy if dia_hoy > 0 else 0

# --- VISUALES ---

# 1. SECCIÓN PROYECCIONES (SOLO SI VEMOS "ESTE MES")
if filtro_tiempo == "Este Mes":
    st.markdown("### 🎯 Proyecciones del Mes (Pacing)")
    col_p1, col_p2, col_p3 = st.columns(3)
    
    with col_p1:
        st.metric("Meta Facturación", f"${meta_facturacion:,.0f}")
        st.progress(progreso_facturacion)
        st.caption(f"Progreso: {progreso_facturacion*100:.1f}%")
        
    with col_p2:
        st.metric("Falta para Meta", f"${faltante_facturacion:,.0f}", delta=f"Proy. Cierre: ${proyeccion_cierre:,.0f}")
        st.info(f"💡 Debes facturar **${facturacion_necesaria_diaria:,.0f}/día** los próximos {dias_restantes} días.")

    with col_p3:
        st.metric("Budget Disponible Diario", f"${gasto_ideal_diario:.0f}/día")
        delta_gasto = gasto_ideal_diario - gasto_promedio_actual
        if delta_gasto < 0:
            st.warning(f"⚠️ Estás gastando ${abs(delta_gasto):.0f} de MÁS por día.")
        else:
            st.caption(f"Estás gastando ${gasto_promedio_actual:.0f}/día (Bien)")

    st.divider()

# 2. FINANZAS
st.markdown("### 💰 Estado Financiero")
k1, k2, k3, k4 = st.columns(4)
k1.metric("Facturación", f"${facturacion:,.0f}")
k2.metric("Profit", f"${profit:,.0f}", delta=profit)
k3.metric("Inversión Ads", f"${inversion_ads:,.0f}")
delta_roas = roas - 1
k4.metric("ROAS", f"{roas:.2f}x", delta=f"{delta_roas:.2f} vs Objetivo" if roas > 0 else 0)

st.divider()

# 3. EFICIENCIA
st.markdown("### 📞 Eficiencia Comercial")
e1, e2, e3, e4 = st.columns(4)
e1.metric("Total Leads", total_leads)
e2.metric("Asistencias", total_asistencias, help="Ventas + Seguimiento + Descalificados")
e3.metric("Tasa Asistencia", f"{tasa_asistencia:.1f}%")
e4.metric("Tasa Cierre", f"{tasa_cierre:.1f}%")

st.markdown("---")
st.subheader("🔍 Desglose de Leads (Widget)")

c_venta = len(df_v_filtrado[df_v_filtrado['Estado_Simple'] == "✅ Venta"])
c_noshow = len(df_v_filtrado[df_v_filtrado['Estado_Simple'] == "❌ No Show"])
c_descalif = len(df_v_filtrado[df_v_filtrado['Estado_Simple'] == "🚫 Descalificado"])
c_agendado = len(df_v_filtrado[df_v_filtrado['Estado_Simple'].isin(["📅 Re-Agendado", "Otro/Pendiente"])])
c_seguimiento = len(df_v_filtrado[df_v_filtrado['Estado_Simple'] == "👀 Seguimiento"])

w1, w2, w3, w4, w5 = st.columns(5)
w1.metric("✅ Ventas", c_venta)
w2.metric("👀 Seguimiento", c_seguimiento)
w3.metric("❌ No Show", c_noshow)
w4.metric("🚫 Descalif.", c_descalif)
w5.metric("📅 Agend/Otro", c_agendado)

if not df_v_filtrado.empty:
    daily_status = df_v_filtrado.groupby(['Fecha', 'Estado_Simple']).size().reset_index(name='Cantidad')
    fig_status = px.bar(
        daily_status, x="Fecha", y="Cantidad", color="Estado_Simple", 
        title="Evolución Diaria de Leads",
        color_discrete_map={
            "✅ Venta": "#00CC96", 
            "❌ No Show": "#EF553B",
            "🚫 Descalificado": "#FFA15A",
            "👀 Seguimiento": "#636EFA",
            "📅 Re-Agendado": "#AB63FA",
            "Otro/Pendiente": "#d3d3d3"
        }
    )
    st.plotly_chart(fig_status, use_container_width=True)

tab1, tab2 = st.tabs(["🏆 Ranking Closers", "📊 Facturación vs Ads"])

with tab1:
    if not df_v_filtrado.empty:
        ranking = df_v_filtrado.groupby('Closer').apply(
            lambda x: pd.Series({
                'Facturado': x['Monto ($)'].sum(),
                'Asistencias': x['Es_Asistencia'].sum(),
                'Ventas': x['Estado_Simple'].eq("✅ Venta").sum()
            })
        ).reset_index()
        ranking['% Cierre'] = (ranking['Ventas'] / ranking['Asistencias'] * 100).fillna(0)
        ranking = ranking.sort_values('Facturado', ascending=False)
        st.dataframe(ranking.style.format({'Facturado': '${:,.0f}', '% Cierre': '{:.1f}%'}), use_container_width=True)

with tab2:
    v_dia = df_v_filtrado.groupby('Fecha')['Monto ($)'].sum().reset_index()
    fig_fin = px.bar(v_dia, x='Fecha', y='Monto ($)', title="Ingresos Diarios")
    if closer_sel == "Todos" and not df_g_filtrado.empty:
        g_dia = df_g_filtrado.groupby('Fecha')['Gasto'].sum().reset_index()
        fig_fin.add_scatter(x=g_dia['Fecha'], y=g_dia['Gasto'], mode='lines+markers', name='Gasto Ads', line=dict(color='red'))
    st.plotly_chart(fig_fin, use_container_width=True)
