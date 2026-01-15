import pandas as pd
import matplotlib.pyplot as plt
import streamlit as st # Necesario para mostrar gráficos en la web

# CONFIGURACIÓN DEL PROYECTO
ARCHIVO_CSV = 'https://docs.google.com/spreadsheets/d/e/2PACX-1vR726VKYI1xIW9q5U50lN2iqY58-SIyN9gusKo_t8h2-HkTa7zERkSrQ6F4OUnTB2AWEh4CSvfwdZRL/pub?gid=0&single=true&output=csv'
NOMBRE_FASE = "FASE 1: Captación - VDP"

def generar_dashboard():
    # 1. Cargar Data
    try:
        df = pd.read_csv(ARCHIVO_CSV)
        
        # --- FIX 1: LIMPIEZA DE COLUMNAS ---
        # Quitamos espacios en blanco al inicio y final de los nombres de columnas
        df.columns = df.columns.str.strip()
        
        # Imprimimos las columnas encontradas para depurar (Ver en logs)
        print("Columnas encontradas en el CSV:", df.columns.tolist())
        
    except Exception as e:
        st.error(f"Error cargando el archivo: {e}")
        return

    # 2. Función de Limpieza
    def clean_currency(x):
        if isinstance(x, str):
            x = x.replace('$', '').replace(' ', '').replace('%', '')
            if 'DIV/0' in x or x.strip() == '-' or x.strip() == '':
                return 0.0
            x = x.replace('.', '') 
            x = x.replace(',', '.') 
            try:
                return float(x)
            except ValueError:
                return 0.0
        return x

    # Columnas a limpiar
    cols_to_clean = ['Spent', 'Clicks', 'Visitas LP', 'Leads Hyros', 'API Hyros', 'Grupo']
    
    for col in cols_to_clean:
        if col in df.columns:
            df[col] = df[col].apply(clean_currency)
        else:
            # --- FIX 2: AVISO SI FALTA UNA COLUMNA CRÍTICA ---
            st.warning(f"⚠️ Atención: La columna '{col}' no se encuentra en el Google Sheet. Verifica el nombre.")

    # 3. Filtrar Data Valida
    if 'Spent' in df.columns:
        valid_data = df[df['Spent'] > 0].copy()
    else:
        st.error("La columna 'Spent' no existe.")
        return
    
    if valid_data.empty:
        st.warning("No hay datos con gasto registrado.")
        return

    # 4. Cálculos de KPIs Diarios (Protegidos con try/except implícito al verificar columnas antes)
    # Verificamos que existan las columnas antes de dividir
    if 'Leads Hyros' in valid_data.columns:
        valid_data['CPL_Diario'] = valid_data['Spent'] / valid_data['Leads Hyros']
    
    if 'API Hyros' in valid_data.columns:
        valid_data['CPA_Diario'] = valid_data['Spent'] / valid_data['API Hyros']
    
    if 'Grupo' in valid_data.columns:
        valid_data['CPG_Diario'] = valid_data['Spent'] / valid_data['Grupo']

    # 5. Cálculos Generales
    total_spend = valid_data['Spent'].sum()
    total_visits = valid_data['Visitas LP'].sum() if 'Visitas LP' in valid_data.columns else 0
    total_leads = valid_data['Leads Hyros'].sum() if 'Leads Hyros' in valid_data.columns else 0
    total_api = valid_data['API Hyros'].sum() if 'API Hyros' in valid_data.columns else 0
    total_group = valid_data['Grupo'].sum() if 'Grupo' in valid_data.columns else 0

    # Tasas de Conversión
    cr_visit_lead = total_leads / total_visits if total_visits else 0
    cr_lead_api = total_api / total_leads if total_leads else 0
    cr_api_group = total_group / total_api if total_api else 0

    # --- VISUALIZACIÓN EN STREAMLIT ---
    st.title(f'{NOMBRE_FASE}')
    
    # Métricas clave arriba
    col1, col2, col3 = st.columns(3)
    col1.metric("Inversión Total", f"${total_spend:,.2f}")
    col2.metric("Leads Totales", int(total_leads), f"CPL: ${total_spend/total_leads:.2f}" if total_leads else "0")
    col3.metric("Grupo Total", int(total_group), f"CPG: ${total_spend/total_group:.2f}" if total_group else "0")

    # GRÁFICO 1
    st.subheader("Tendencia Diaria")
    fig1, ax1 = plt.subplots(figsize=(12, 6))
    dates = valid_data['Fecha']
    x = range(len(dates))
    width = 0.25

    ax1.bar([p - width for p in x], valid_data['Leads Hyros'], width, label='Leads', color='#a8dadc')
    ax1.bar(x, valid_data['API Hyros'], width, label='API', color='#457b9d')
    ax1.bar([p + width for p in x], valid_data['Grupo'], width, label='Grupo', color='#1d3557')
    ax1.set_ylabel('Volumen', fontweight='bold')
    ax1.set_xticks(x)
    ax1.set_xticklabels(dates, rotation=45)
    ax1.legend(loc='upper left')

    ax2 = ax1.twinx()
    # Solo graficamos si las columnas se crearon
    if 'CPL_Diario' in valid_data.columns: ax2.plot(x, valid_data['CPL_Diario'], 'ro--', label='CPL ($)')
    ax2.set_ylabel('Costo Unitario ($)', color='red', fontweight='bold')
    
    st.pyplot(fig1) # USAR st.pyplot EN LUGAR DE plt.show()

    # GRÁFICO 2
    st.subheader("Eficiencia del Embudo")
    stages = ['Visitas LP', 'Leads (Hyros)', 'API (Hyros)', 'Grupo WhatsApp']
    values = [total_visits, total_leads, total_api, total_group]
    colors = ['#ced4da', '#a8dadc', '#457b9d', '#1d3557']
    
    conv_texts = ["", f"{cr_visit_lead:.1%}", f"{cr_lead_api:.1%}", f"{cr_api_group:.1%}"]

    fig2, ax = plt.subplots(figsize=(10, 5))
    bars = ax.barh(stages, values, color=colors)
    ax.invert_yaxis()

    for i, bar in enumerate(bars):
        w = bar.get_width()
        ax.text(w + (max(values)*0.01), bar.get_y() + bar.get_height()/2, f"{int(w)}", va='center', fontweight='bold')
        if i > 0:
            ax.text(w/2, bar.get_y() + bar.get_height()/2, conv_texts[i], ha='center', color='white', fontweight='bold')

    st.pyplot(fig2) # USAR st.pyplot

if __name__ == "__main__":
    generar_dashboard()
