import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np

# --- 1. CONFIGURACIÓN E IMPORTACIÓN ---
st.set_page_config(page_title="search lead - CN", page_icon="🕵️", layout="wide")

# Estilos Neón Cyberpunk
st.markdown("""
    <style>
        .stApp { background-color: #050505; color: white; }
        .stTextInput input { color: #0aff00 !important; border-color: #0aff00 !important; }
        div[data-testid="stMetric"] { background-color: #111; border: 1px solid #bc13fe; border-radius: 8px; padding: 10px; }
        h1, h2, h3 { color: white !important; }
        .timeline-card {
            background-color: #1a1a1a; border-left: 4px solid #00f3ff;
            padding: 15px; margin-bottom: 15px; border-radius: 0 10px 10px 0;
        }
        .success-card { border-left-color: #0aff00 !important; }
        .fail-card { border-left-color: #ff0055 !important; }
        .highlight { color: #0aff00; font-weight: bold; }
    </style>
""", unsafe_allow_html=True)

# --- 2. FUNCIÓN DE REPARACIÓN (Para la hoja de Closers) ---
def reparar_desplazamiento(df):
    """Arregla las columnas desplazadas si GHL manda datos vacíos al inicio."""
    if df.empty: return df
    df_fixed = df.copy()
    col_0 = df_fixed.columns[0]
    # Detectar si la primera columna está vacía
    filas_malas_mask = df_fixed[col_0].isna() | (df_fixed[col_0].astype(str).str.strip() == '')
    
    if filas_malas_mask.sum() > 0 and len(df_fixed.columns) >= 9:
        valores = df_fixed.values
        indices_malos = df_fixed.index[filas_malas_mask]
        for idx in indices_malos:
            fila = valores[idx]
            fila_corregida = np.roll(fila, -8) # Ajuste de 8 columnas a la izquierda
            fila_corregida[-8:] = np.nan 
            valores[idx] = fila_corregida
        df_fixed = pd.DataFrame(valores, columns=df.columns, index=df.index)
    return df_fixed

# --- 3. CARGA DE DATOS MULTI-FUENTE ---
@st.cache_data(ttl=600)
def cargar_todo():
    # LINKS PROPORCIONADOS
    link_volumen = "https://docs.google.com/spreadsheets/d/e/2PACX-1vTjCMjoi7DXiCeBRQdzAQZlx_L6SfpmbLlqmeRgZDHmCEdmN5_grVD_Yqa-5tzNprDS02o98ms80j1x/pub?gid=0&single=true&output=csv"
    link_calificados = "https://docs.google.com/spreadsheets/d/e/2PACX-1vTjCMjoi7DXiCeBRQdzAQZlx_L6SfpmbLlqmeRgZDHmCEdmN5_grVD_Yqa-5tzNprDS02o98ms80j1x/pub?gid=1272057128&single=true&output=csv"
    link_resultados = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQuXaPCen61slzpr1TElxXoCROIxAgmgWT7pyWvel1dxq_Z_U1yZPrVrTbJfx9MwaL8_cluY3v2ywoB/pub?gid=0&single=true&output=csv"

    # A) LEADS VOLUMEN
    try:
        df_vol = pd.read_csv(link_volumen)
        # Normalizar Email
        cols_email_v = [c for c in df_vol.columns if 'email' in c.lower()]
        if cols_email_v:
            df_vol.rename(columns={cols_email_v[0]: 'Email'}, inplace=True)
            df_vol['Email'] = df_vol['Email'].astype(str).str.lower().str.strip()
        
        # Buscar fecha de creación
        cols_date_v = [c for c in df_vol.columns if 'Fecha Creación' in c.lower() or 'fecha' in c.lower()]
        if cols_date_v:
            df_vol['Fecha_Ingreso'] = pd.to_datetime(df_vol[cols_date_v[0]], errors='coerce')
    except: df_vol = pd.DataFrame()

    # B) LEADS CALIFICADOS
    try:
        df_qual = pd.read_csv(link_calificados)
        cols_email_q = [c for c in df_qual.columns if 'email' in c.lower()]
        if cols_email_q:
            df_qual.rename(columns={cols_email_q[0]: 'Email'}, inplace=True)
            df_qual['Email'] = df_qual['Email'].astype(str).str.lower().str.strip()
            
        # Buscar fecha calificación (a veces es Created)
        cols_date_q = [c for c in df_qual.columns if 'Fecha Creación' in c.lower() or 'fecha' in c.lower()]
        if cols_date_q:
            df_qual['Fecha_Calificado'] = pd.to_datetime(df_qual[cols_date_q[0]], errors='coerce')
    except: df_qual = pd.DataFrame()

    # C) RESULTADOS CLOSERS (Con Reparación)
    try:
        df_res = pd.read_csv(link_resultados)
        df_res = reparar_desplazamiento(df_res) # <--- FIX DE COLUMNAS
        
        # Normalizar Email
        cols_email_r = [c for c in df_res.columns if 'email' in c.lower()]
        if cols_email_r:
            df_res.rename(columns={cols_email_r[0]: 'Email'}, inplace=True)
            df_res['Email'] = df_res['Email'].astype(str).str.lower().str.strip()
        
        # Fecha Llamada
        cols_date_r = [c for c in df_res.columns if 'fecha' in c.lower()]
        if cols_date_r:
            df_res['Fecha_Llamada'] = pd.to_datetime(df_res[cols_date_r[0]], dayfirst=True, errors='coerce')

        # Monto y Estado
        if 'Monto ($)' in df_res.columns:
             if df_res['Monto ($)'].dtype == 'O':
                df_res['Monto ($)'] = df_res['Monto ($)'].astype(str).str.replace(r'[$,]', '', regex=True)
             df_res['Monto ($)'] = pd.to_numeric(df_res['Monto ($)'], errors='coerce').fillna(0)
        
        if 'Resultado' in df_res.columns:
            df_res['Resultado'] = df_res['Resultado'].fillna('Pendiente')

    except: df_res = pd.DataFrame()

    return df_vol, df_qual, df_res

df_vol, df_qual, df_res = cargar_todo()

# --- 4. INTERFAZ PRINCIPAL ---
st.title("🕵️ DETECTIVE DE LEADS & RANKING")

# --- INICIO DEL TOGGLE DE AYUDA ---
with st.expander("ℹ️ GUÍA RÁPIDA: ¿CÓMO USAR ESTE DASHBOARD?"):
    st.markdown("""
    <div style="background-color: #111; padding: 20px; border-radius: 10px; border: 1px solid #333;">
        <h4 style="color: #00f3ff; margin-top: 0;">🔍 Pestaña 1: Buscador de Lead</h4>
        <p style="color: #aaa; font-size: 0.9rem; margin-bottom: 15px;">
            El <b>Detective</b> rastrea la historia completa de un lead usando su correo.
            <ul>
                <li><b>Ingreso:</b> Muestra cuándo llenó el formulario y la atribución (Campaña/Anuncio).</li>
                <li><b>Calificación:</b> Confirma si pasó el filtro de calidad.</li>
                <li><b>Cierre:</b> Detalla el resultado de la llamada, notas del closer y monto pagado.</li>
            </ul>
        </p>
        
        <hr style="border-color: #333;">
        
        <h4 style="color: #0aff00; margin-top: 0;">🏆 Pestaña 2: Ranking Clientes</h4>
        <p style="color: #aaa; font-size: 0.9rem;">
            Lista tus mejores clientes ordenados por <b>Facturación Total (LTV)</b>.
            <ul>
                <li><b>Suma Inteligente:</b> Si un cliente pagó en cuotas (varias filas), aquí verás el total sumado.</li>
                <li><b>Atribución:</b> Mira rápidamente de qué campaña vinieron tus mejores compradores.</li>
            </ul>
        </p>
    </div>
    """, unsafe_allow_html=True)
# --- FIN DEL TOGGLE DE AYUDA ---

tab1, tab2 = st.tabs(["🔍 Buscador de Lead", "🏆 Ranking Clientes"])

# === TAB 1: BUSCADOR (TIMELINE) ===
with tab1:
    st.markdown("### Historial completo del Lead")
    
    col_search, col_btn = st.columns([4,1])
    email_input = col_search.text_input("Ingresa el correo del Lead:", placeholder="ejemplo@gmail.com").strip().lower()
    
    if email_input:
        # 1. BUSCAR EN VOLUMEN (Origen)
        lead_vol = df_vol[df_vol['Email'] == email_input]
        
        # 2. BUSCAR EN CALIFICADOS
        lead_qual = df_qual[df_qual['Email'] == email_input]
        
        # 3. BUSCAR EN RESULTADOS (Agenda/Venta)
        lead_res = df_res[df_res['Email'] == email_input]
        
        if lead_vol.empty and lead_qual.empty and lead_res.empty:
            st.warning("❌ No se encontró información para este correo en ninguna hoja.")
        else:
            st.success(f"Resultados encontrados para: **{email_input}**")

            # --- NUEVO: OBTENER NOMBRE DEL LEAD (HEADLINE) ---
            nombre_lead = "Cliente Desconocido"
            
            # Prioridad 1: Sacarlo de la hoja de Resultados (Más fiable)
            if not lead_res.empty and 'Lead Name' in lead_res.columns:
                 val = lead_res.iloc[0]['Lead Name']
                 if val and str(val).lower() != 'nan': nombre_lead = str(val).title()
            
            # Prioridad 2: Sacarlo de la hoja de Volumen (Si no llegó a llamada)
            elif not lead_vol.empty and 'Nombre' in lead_vol.columns:
                 val = lead_vol.iloc[0]['Nombre']
                 if val and str(val).lower() != 'nan': nombre_lead = str(val).title()
            
            # MOSTRAR EL HEADLINE NOMBRE
            st.markdown(f"""
            <h1 style='color:#0aff00; font-size: 2.5rem; margin-top: 10px; margin-bottom: 5px;'>
                👤 {nombre_lead}
            </h1>
            <hr style="border-color: #0aff00; margin-top: 0px; margin-bottom: 30px; opacity: 0.5;">
            """, unsafe_allow_html=True)
            
            # --- ETAPA 1: INGRESO (Formulario) ---
            st.markdown("#### 1️⃣ Ingreso (Formulario)")
            if not lead_vol.empty:
                data = lead_vol.iloc[0]
                fecha_in = data.get('Fecha_Ingreso', 'Desconocida')
                
                # --- AQUÍ ESTÁ EL CAMBIO DE COLUMNAS CORRECTO ---
                campana = data.get('Campaña (UTM)', 'N/A')
                adset = data.get('Conjunto (ID)', 'N/A')
                anuncio = data.get('Ad Content', 'N/A')
                
                st.markdown(f"""
                <div class="timeline-card">
                    📅 <b>Fecha Registro:</b> {fecha_in}<br>
                    📢 <b>Campaña:</b> {campana}<br>
                    🎯 <b>Conjunto:</b> {adset}<br>
                    🖼️ <b>Anuncio:</b> {anuncio}
                </div>
                """, unsafe_allow_html=True)
            else:
                st.info("⚠️ No encontrado en la hoja de Volumen (Lead antiguo o manual).")

            # --- ETAPA 2: CALIFICACIÓN ---
            st.markdown("#### 2️⃣ Calificación")
            if not lead_qual.empty:
                data_q = lead_qual.iloc[0]
                fecha_q = data_q.get('Fecha_Calificado', 'Sin fecha')
                st.markdown(f"""
                <div class="timeline-card success-card">
                    ✅ <b>Lead Calificado:</b> SÍ<br>
                    📅 <b>Fecha:</b> {fecha_q}
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown("""<div class="timeline-card fail-card">❌ No aparece en lista de Calificados</div>""", unsafe_allow_html=True)

            # --- ETAPA 3: LLAMADA Y VENTA ---
            st.markdown("#### 3️⃣ Llamada y Cierre")
            if not lead_res.empty:
                # Pueden haber varias filas si pagó en cuotas, tomamos la última o iteramos
                for index, row in lead_res.iterrows():
                    fecha_call = row.get('Fecha_Llamada', 'Sin fecha')
                    closer = row.get('Closer', 'Sin asignar')
                    res = str(row.get('Resultado', '')).lower()
                    monto = row.get('Monto ($)', 0)
                    notas = row.get('Notas', '')
                    
                    # Estilo según resultado
                    css_class = "success-card" if "venta" in res else ("fail-card" if "no show" in res or "descalificado" in res else "timeline-card")
                    icono = "💰" if "venta" in res else ("❌" if "no show" in res else "📞")
                    
                    # Atribución Final (confirmada por Closer)
                    # Estas columnas están bien según lo que me dijiste del Sheet Resultados
                    atrib_camp = row.get('Origen Campaña', 'N/A')
                    atrib_ad = row.get('Nombre del Ad', 'N/A')

                    st.markdown(f"""
                    <div class="timeline-card {css_class}">
                        {icono} <b>Resultado:</b> {row.get('Resultado').upper()}<br>
                        📅 <b>Fecha Llamada:</b> {fecha_call}<br>
                        👤 <b>Closer:</b> {closer}<br>
                        💵 <b>Monto:</b> ${monto:,.2f}<br>
                        📝 <b>Notas:</b> {notas}<br>
                        <hr style="border-color: #333;">
                        🕵️ <b>Atribución Final:</b> {atrib_camp} | {atrib_ad}
                    </div>
                    """, unsafe_allow_html=True)
            else:
                 st.info("⚠️ El lead aún no ha tenido llamada o no ha sido registrado por un closer.")

# === TAB 2: RANKING ===
with tab2:
    st.markdown("### 🏆 Top Clientes (Ranking)")
    
    if not df_res.empty:
        # Filtrar solo ventas
        ventas = df_res[df_res['Resultado'].astype(str).str.lower().str.contains("venta")].copy()
        
        if not ventas.empty:
            # Agrupar por Email para sumar montos (LTV - Lifetime Value)
            ranking = ventas.groupby(['Email', 'Lead Name']).agg({
                'Monto ($)': 'sum',
                'Origen Campaña': 'first', # Toma la primera campaña registrada
                'Nombre del Ad': 'first',
                'Fecha_Llamada': 'max' # Última fecha de compra
            }).reset_index()
            
            # Ordenar
            ranking = ranking.sort_values('Monto ($)', ascending=False).reset_index(drop=True)
            ranking.index = ranking.index + 1 # Empezar ranking en 1
            
            # Mostrar Tabla Estilizada
            st.dataframe(
                ranking.style.format({'Monto ($)': '${:,.2f}'}).background_gradient(subset=['Monto ($)'], cmap='Greens'),
                use_container_width=True,
                column_config={
                    "Email": "Correo",
                    "Lead Name": "Cliente",
                    "Monto ($)": "Total Facturado",
                    "Fecha_Llamada": "Última Compra"
                }
            )
        else:
            st.warning("Aún no hay ventas registradas en la hoja de resultados.")
    else:
        st.error("No se pudo cargar la hoja de Resultados.")
