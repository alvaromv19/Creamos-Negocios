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
            # Si es mensual, usamos los días restantes calculados en sidebar
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
        st.markdown("### 📝 Resultados de la Planificación")
        
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Inversión Diaria Sugerida", f"${daily_spend:,.2f}")
        m2.metric("Facturación Proyectada", f"${projected_revenue:,.2f}")
        m3.metric("Profit Estimado", f"${projected_profit:,.2f}", delta=f"{((projected_profit/budget)*100):.1f}% Margen")
        m4.metric("Ventas Necesarias", f"{int(projected_sales)}")

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
        total_days_period = days_in_month # Para el cálculo de "Total Mes"
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
        
        # 2. Optimista (+15% en eficiencia de revenue o ritmo)
        # Asumimos que aumentamos el revenue un 15% manteniendo el mismo spend proyectado, o mejoramos el ritmo.
        # Interpretación: El ritmo de facturación mejora un 15%
        daily_rev_opt = daily_avg_revenue * 1.15
        proj_rev_opt = current_revenue + (daily_rev_opt * days_future)
        proj_profit_opt = proj_rev_opt - proj_spend_real # Asumimos mismo gasto, mejor rendimiento
        
        # 3. Pesimista (-15% en ritmo)
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
        
        # Crear DataFrame para gráfico
        data_proj = {
            'Escenario': ['Pesimista (-15%)', 'Realista (Ritmo Actual)', 'Optimista (+15%)'],
            'Facturación Proyectada': [proj_rev_pes, proj_rev_real, proj_rev_opt],
            'Profit Proyectado': [proj_profit_pes, proj_profit_real, proj_profit_opt],
            'Color': ['#EF553B', '#636EFA', '#00CC96'] # Rojo, Azul, Verde
        }
        df_proj = pd.DataFrame(data_proj)

        # Gráfico con Plotly
        fig = go.Figure()
        
        # Barras de Facturación
        fig.add_trace(go.Bar(
            x=df_proj['Escenario'],
            y=df_proj['Facturación Proyectada'],
            name='Facturación Total',
            marker_color=df_proj['Color'],
            text=df_proj['Facturación Proyectada'].apply(lambda x: f"${x:,.0f}"),
            textposition='auto',
            opacity=0.6
        ))

        # Línea de Profit
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

        # Tabla detallada
        st.markdown("#### Detalle Numérico")
        st.dataframe(
            df_proj.set_index("Escenario").style.format("${:,.2f}"),
            use_container_width=True
        )

    else:
        st.info("Ingresa tu Inversión y Facturación actual para generar las proyecciones.")
