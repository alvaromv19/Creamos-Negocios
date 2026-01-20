import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import date, timedelta
import calendar

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(
    page_title="Proyecciones Ads Master",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- ESTILOS CSS PERSONALIZADOS (Para un look más 'Pro') ---
st.markdown("""
<style>
    .metric-card {
        background-color: #f0f2f6;
        border-radius: 10px;
        padding: 20px;
        box-shadow: 2px 2px 10px rgba(0,0,0,0.1);
    }
    .platform-card {
        background-color: #e8f4f8; /* Color suave para las tarjetas de plataformas */
        border-radius: 10px;
        padding: 15px;
        border: 1px solid #d1e7ef;
        margin-bottom: 10px;
    }
    .stMetric label {
        font-weight: bold;
        color: #555;
    }
    .big-font {
        font-size: 20px !important;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

# --- FUNCIONES DE UTILIDAD ---
def get_days_in_month(year, month):
    return calendar.monthrange(year, month)[1]

def calculate_remaining_days(target_date):
    today = date.today()
    delta = target_date - today
    return max(0, delta.days)

# --- TÍTULO ---
st.title("📈 Calculadora Estratégica de Ads")
st.markdown("---")

# --- INSTRUCCIONES / ONBOARDING ---
with st.expander("📘 GUÍA DE USO: ¿Cómo sacarle el jugo a esta herramienta? (Clic para abrir)"):
    st.markdown("""
    ### 🎯 Objetivo
    Esta calculadora elimina las suposiciones manuales. Nos ayuda a responder dos preguntas críticas en segundos:
    1. **Planificación:** *"¿Cuánto debo invertir para lograr X facturación?"*
    2. **Proyección (Pacing):** *"Al ritmo que vamos hoy, ¿cómo cerraremos el mes?"*

    ---

    ### 🛠️ Paso a Paso

    #### 1️⃣ Pestaña: Planificador de Inversión (Futuro)
    *Úsala antes de lanzar campañas o al definir presupuestos.*
    1. **Define tu Budget:** Elige si invertirás un monto total mensual o un monto específico por unos días (test).
    2. **Métricas Objetivo:** Ingresa el precio de tu producto y el **ROAS** que aspiramos tener.
    3. **Distribución por Canal:** Usa los sliders para repartir el presupuesto entre Meta, TikTok, YouTube y Otros.
    4. **Resultado:** Verás cuánto gastar **por día en cada plataforma**.

    #### 2️⃣ Pestaña: Analizador de Rendimiento (Presente)
    *Úsala para reportes diarios/semanales.*
    1. **Ingresa la Realidad:** Copia de tus Ads Managers el gasto actual (`Amount Spent`), facturación (`Conversion Value`) y ventas.
    2. **Elige la Proyección:** Final de Mes o Personalizada.
    3. **Interpreta los Escenarios:** Pesimista (-15%), Realista (Ritmo actual), Optimista (+15%).
    """)

# --- SIDEBAR: DATOS GENERALES ---
with st.sidebar:
    st.header("⚙️ Configuración Global")
    today = st.date_input("Fecha Actual", date.today())
    
    # Cálculo automático de fin de mes
    last_day_month = date(today.year, today.month, get_days_in_month(today.year, today.month))
    days_in_month = last_day_month.day
    days_passed = today.day
    days_remaining_month = days_in_month - days_passed
    
    st.info(f"📅 Estamos en el día **{days_passed}** del mes.\nQuedan **{days_remaining_month}** días para cerrar el mes.")

# --- PESTAÑAS PRINCIPALES ---
tab1, tab2 = st.tabs(["🔭 Planificador de Inversión", "📊 Analizador de Rendimiento Actual"])

# ==============================================================================
# TAB 1: PLANIFICADOR (¿Cuánto invertir para lograr X?)
# ==============================================================================
with tab1:
    st.subheader("Simulador de Escenarios Futuros")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 1. Definición de Budget y Tiempo")
        investment_mode = st.radio(
            "¿Cómo quieres calcular la inversión?",
            ["Presupuesto Total Mensual", "Presupuesto para X Días Específicos"],
            horizontal=True
        )
        
        budget = st.number_input("💰 Presupuesto a Invertir ($)", min_value=0.0, value=1000.0, step=50.0)
        
        if investment_mode == "Presupuesto Total Mensual":
            days_to_calculate = days_remaining_month
            st.success(f"Calculando distribución para los **{days_to_calculate} días** restantes del mes.")
        else:
            days_to_calculate = st.number_input("⏳ Días de campaña a proyectar", min_value=1, value=10, step=1)
    
    with col2:
        st.markdown("### 2. Métricas del Producto")
        product_price = st.number_input("🏷️ Precio del Producto ($)", min_value=0.0, value=50.0)
        target_roas = st.number_input("🎯 ROAS Objetivo (Ej: 3.0)", min_value=0.1, value=3.0, step=0.1)

    # --- CÁLCULOS PLANIFICADOR ---
    if days_to_calculate > 0 and budget > 0:
        daily_spend = budget / days_to_calculate
        projected_revenue = budget * target_roas
        projected_sales = projected_revenue / product_price if product_price > 0 else 0
        projected_profit = projected_revenue - budget
        
        st.markdown("---")
        st.markdown("### 📝 Resultados Generales")
        
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Inversión Diaria Total", f"${daily_spend:,.2f}")
        m2.metric("Facturación Proyectada", f"${projected_revenue:,.2f}")
        m3.metric("Profit Estimado", f"${projected_profit:,.2f}", delta=f"{((projected_profit/budget)*100):.1f}% Margen")
        m4.metric("Ventas Totales Necesarias", f"{int(projected_sales)}")

        # --- NUEVA SECCIÓN: DISTRIBUCIÓN POR PLATAFORMA ---
        st.markdown("---")
        st.subheader("📢 Distribución de Presupuesto por Canal (Traffic Source)")
        st.markdown("Ajusta el porcentaje (%) para ver cuánto dinero destinar a cada plataforma.")

        # Contenedores para sliders
        p_col1, p_col2, p_col3, p_col4 = st.columns(4)
        
        # Diccionario para guardar valores
        distribucion = {}

        # 1. Meta Ads
        with p_col1:
            st.markdown("**🔵 Meta Ads (FB/IG)**")
            pct_meta = st.slider("Asignación Meta %", 0, 100, 50, key="slider_meta")
            distribucion["Meta"] = pct_meta

        # 2. TikTok Ads
        with p_col2:
            st.markdown("**⚫ TikTok Ads**")
            pct_tiktok = st.slider("Asignación TikTok %", 0, 100, 30, key="slider_tiktok")
            distribucion["TikTok"] = pct_tiktok

        # 3. YouTube Ads
        with p_col3:
            st.markdown("**🔴 YouTube Ads**")
            pct_youtube = st.slider("Asignación YouTube %", 0, 100, 10, key="slider_youtube")
            distribucion["YouTube"] = pct_youtube
        
        # 4. Otros
        with p_col4:
            st.markdown("**🟠 Otros / Testing**")
            pct_others = st.slider("Asignación Otros %", 0, 100, 10, key="slider_others")
            distribucion["Otros"] = pct_others

        # Validación de suma 100%
        total_pct = sum(distribucion.values())
        if total_pct != 100:
            if total_pct > 100:
                st.error(f"⚠️ ¡Cuidado! Estás asignando un **{total_pct}%** del presupuesto. Reduce {total_pct - 100}% para cuadrar.")
            else:
                st.warning(f"⚠️ Tienes asignado un **{total_pct}%**. Te falta asignar un {100 - total_pct}% del presupuesto.")
        else:
            st.success("✅ Distribución perfecta (100%)")

        # Mostrar tarjetas de resultados con estilos
        st.markdown("#### 💰 Detalle de Inversión Sugerida")
        
        # Columnas para las tarjetas
        res_col1, res_col2, res_col3, res_col4 = st.columns(4)
        
        # Iteramos sobre las columnas y los datos para pintar las tarjetas
        columns_refs = [res_col1, res_col2, res_col3, res_col4]
        nombres = ["Meta Ads", "TikTok Ads", "YouTube Ads", "Otros"]
        valores_pct = [pct_meta, pct_tiktok, pct_youtube, pct_others]
        colores_borde = ["#1877F2", "#000000", "#FF0000", "#FF9900"] # Colores representativos
        
        for i in range(4):
            with columns_refs[i]:
                pct_actual = valores_pct[i]
                # Cálculo de montos
                monto_total_asignado = budget * (pct_actual / 100)
                monto_diario_asignado = daily_spend * (pct_actual / 100)
                
                # HTML Card personalizado
                st.markdown(f"""
                <div style="
                    background-color: white;
                    border-left: 5px solid {colores_borde[i]};
                    padding: 15px;
                    border-radius: 5px;
                    box-shadow: 2px 2px 5px rgba(0,0,0,0.05);
                    margin-bottom: 10px;">
                    <h4 style="margin:0; color: #333;">{nombres[i]}</h4>
                    <p style="font-size: 14px; color: #666; margin-bottom: 10px;">Asignación: <b>{pct_actual}%</b></p>
                    <hr style="margin: 5px 0;">
                    <p style="margin:0; font-size:12px;">Total Asignado:</p>
                    <p style="font-size: 18px; font-weight: bold; color: #333; margin:0;">${monto_total_asignado:,.2f}</p>
                    <div style="margin-top: 10px; background-color: #f9f9f9; padding: 5px; border-radius: 4px;">
                        <p style="margin:0; font-size:11px; color: #555;">🔥 Diario Sugerido:</p>
                        <p style="margin:0; font-size: 16px; font-weight: bold; color: {colores_borde[i]};">${monto_diario_asignado:,.2f}</p>
                    </div>
                </div>
                """, unsafe_allow_html=True)

    else:
        st.warning("Configura los días y el presupuesto para ver los cálculos.")

# ==============================================================================
# TAB 2: ANALIZADOR (Proyecciones basadas en datos reales)
# ==============================================================================
with tab2:
    st.subheader("Proyección basada en Ritmo Actual (Pacing)")
    
    # Inputs de datos actuales
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        current_spend = st.number_input("💸 Inversión Acumulada (Month to Date)", min_value=0.0, value=550.0)
    with c2:
        current_revenue = st.number_input("💵 Facturación Acumulada", min_value=0.0, value=1200.0)
    with c3:
        current_sales = st.number_input("📦 Ventas Totales", min_value=0, value=20)
    with c4:
        prod_price_analysis = st.number_input("🏷️ Precio Producto (Análisis)", value=50.0)

    # Selección de periodo de proyección
    st.markdown("#### Configuración de Proyección")
    projection_mode = st.radio(
        "Proyectar hacia:",
        ["Final de Mes (Automático)", "Periodo Personalizado"],
        horizontal=True
    )
    
    if projection_mode == "Final de Mes (Automático)":
        days_future = days_remaining_month
        total_days_period = days_in_month 
    else:
        days_future = st.number_input("Días adicionales a proyectar", min_value=1, value=15)
        total_days_period = days_passed + days_future

    if current_spend > 0 and days_passed > 0:
        # --- CÁLCULOS ACTUALES ---
        current_profit = current_revenue - current_spend
        current_roas = current_revenue / current_spend
        cpa_actual = current_spend / current_sales if current_sales > 0 else 0
        
        # Ritmos Diarios (Velocity)
        daily_avg_spend = current_spend / days_passed
        daily_avg_revenue = current_revenue / days_passed
        daily_avg_profit = current_profit / days_passed

        # --- ESCENARIOS ---
        # 1. Realista (Mantiene el ritmo)
        proj_rev_real = current_revenue + (daily_avg_revenue * days_future)
        proj_spend_real = current_spend + (daily_avg_spend * days_future)
        proj_profit_real = proj_rev_real - proj_spend_real
        
        # 2. Optimista (+15%)
        daily_rev_opt = daily_avg_revenue * 1.15
        proj_rev_opt = current_revenue + (daily_rev_opt * days_future)
        proj_profit_opt = proj_rev_opt - proj_spend_real 
        
        # 3. Pesimista (-15%)
        daily_rev_pes = daily_avg_revenue * 0.85
        proj_rev_pes = current_revenue + (daily_rev_pes * days_future)
        proj_profit_pes = proj_rev_pes - proj_spend_real

        # --- VISUALIZACIÓN DE ESTADO ACTUAL ---
        st.markdown("### 🚦 Estado Actual")
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("ROAS Actual", f"{current_roas:.2f}")
        m2.metric("Profit Actual", f"${current_profit:,.2f}")
        m3.metric("CPA Actual", f"${cpa_actual:,.2f}")
        m4.metric("Velocidad de Gasto (Diario)", f"${daily_avg_spend:,.2f}")

        # --- GRÁFICOS Y PROYECCIONES ---
        st.markdown("### 🔮 Proyecciones al Cierre del Periodo")
        
        data_proj = {
            'Escenario': ['Pesimista (-15%)', 'Realista (Ritmo Actual)', 'Optimista (+15%)'],
            'Facturación Proyectada': [proj_rev_pes, proj_rev_real, proj_rev_opt],
            'Profit Proyectado': [proj_profit_pes, proj_profit_real, proj_profit_opt],
            'Color': ['#EF553B', '#636EFA', '#00CC96']
        }
        df_proj = pd.DataFrame(data_proj)

        fig = go.Figure()
        
        fig.add_trace(go.Bar(
            x=df_proj['Escenario'],
            y=df_proj['Facturación Proyectada'],
            name='Facturación Total',
            marker_color=df_proj['Color'],
            text=df_proj['Facturación Proyectada'].apply(lambda x: f"${x:,.0f}"),
            textposition='auto',
            opacity=0.6
        ))

        fig.add_trace(go.Scatter(
            x=df_proj['Escenario'],
            y=df_proj['Profit Proyectado'],
            name='Profit Neto',
            mode='lines+markers+text',
            text=df_proj['Profit Proyectado'].apply(lambda x: f"${x:,.0f}"),
            textposition='top center',
            line=dict(color='black', width=3, dash='dot')
        ))

        fig.update_layout(
            title="Comparativa de Escenarios al final del periodo",
            xaxis_title="Escenario",
            yaxis_title="Monto ($)",
            legend_title="Métricas",
            template="plotly_white"
        )
        
        st.plotly_chart(fig, use_container_width=True)

        st.markdown("#### Detalle Numérico")
        columns_to_show = ['Facturación Proyectada', 'Profit Proyectado']
        st.dataframe(
            df_proj.set_index("Escenario")[columns_to_show].style.format("${:,.2f}"),
            use_container_width=True
        )

    else:
        st.info("Ingresa tu Inversión y Facturación actual para generar las proyecciones.")
