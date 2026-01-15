import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker

# CONFIGURACIÓN DEL PROYECTO
ARCHIVO_CSV = 'VDP - L1 - Database - F1 - Meta.csv' # Asegurate que este sea el nombre exacto
NOMBRE_FASE = "FASE 1: Captación - VDP"

def generar_dashboard():
    # 1. Cargar Data
    try:
        df = pd.read_csv(ARCHIVO_CSV)
    except FileNotFoundError:
        print(f"Error: No se encuentra el archivo {ARCHIVO_CSV}")
        return

    # 2. Función de Limpieza (Para formato Europeo 1.000,00 y errores #DIV/0!)
    def clean_currency(x):
        if isinstance(x, str):
            x = x.replace('$', '').replace(' ', '').replace('%', '')
            if 'DIV/0' in x or x.strip() == '-' or x.strip() == '':
                return 0.0
            x = x.replace('.', '') # Quitar punto de miles
            x = x.replace(',', '.') # Cambiar coma decimal
            try:
                return float(x)
            except ValueError:
                return 0.0
        return x

    # Columnas a limpiar (Asegurate que los nombres coincidan con tu CSV)
    cols_to_clean = ['Spent', 'Clicks', 'Visitas LP', 'Leads Hyros', 'API Hyros', 'Grupo']
    for col in cols_to_clean:
        if col in df.columns:
            df[col] = df[col].apply(clean_currency)

    # 3. Filtrar Data Valida (Eliminar días futuros sin gasto)
    valid_data = df[df['Spent'] > 0].copy()
    
    if valid_data.empty:
        print("No hay datos con gasto registrado.")
        return

    # 4. Cálculos de KPIs Diarios
    valid_data['CPL_Diario'] = valid_data['Spent'] / valid_data['Leads Hyros']
    valid_data['CPA_Diario'] = valid_data['Spent'] / valid_data['API Hyros']
    valid_data['CPG_Diario'] = valid_data['Spent'] / valid_data['Grupo']

    # 5. Cálculos Generales (Totales)
    total_spend = valid_data['Spent'].sum()
    total_visits = valid_data['Visitas LP'].sum()
    total_leads = valid_data['Leads Hyros'].sum()
    total_api = valid_data['API Hyros'].sum()
    total_group = valid_data['Grupo'].sum()

    # Tasas de Conversión Globales
    cr_visit_lead = total_leads / total_visits if total_visits else 0
    cr_lead_api = total_api / total_leads if total_leads else 0
    cr_api_group = total_group / total_api if total_api else 0

    # --- GRÁFICO 1: ELECTROCARDIOGRAMA (Tendencia Diaria) ---
    fig, ax1 = plt.subplots(figsize=(12, 6))
    dates = valid_data['Fecha'] # Asumiendo columna 'Fecha'
    x = range(len(dates))
    width = 0.25

    # Barras (Volumen)
    ax1.bar([p - width for p in x], valid_data['Leads Hyros'], width, label='Leads', color='#a8dadc')
    ax1.bar(x, valid_data['API Hyros'], width, label='API', color='#457b9d')
    ax1.bar([p + width for p in x], valid_data['Grupo'], width, label='Grupo', color='#1d3557')
    
    ax1.set_ylabel('Volumen', fontweight='bold')
    ax1.set_xticks(x)
    ax1.set_xticklabels(dates, rotation=45)
    
    # Líneas (Costos)
    ax2 = ax1.twinx()
    ax2.plot(x, valid_data['CPL_Diario'], 'ro--', label='CPL ($)')
    ax2.plot(x, valid_data['CPA_Diario'], 'rs-', label='Costo API ($)')
    ax2.plot(x, valid_data['CPG_Diario'], 'r^:', label='Costo Grupo ($)')
    
    ax2.set_ylabel('Costo Unitario ($)', color='red', fontweight='bold')
    
    plt.title(f'{NOMBRE_FASE} - Tendencia Diaria', fontsize=14, fontweight='bold')
    plt.tight_layout()
    plt.show()

    # --- GRÁFICO 2: EMBUDO HORIZONTAL (Eficiencia) ---
    stages = ['Visitas LP', 'Leads (Hyros)', 'API (Hyros)', 'Grupo WhatsApp']
    values = [total_visits, total_leads, total_api, total_group]
    colors = ['#ced4da', '#a8dadc', '#457b9d', '#1d3557']
    
    conv_texts = [
        "", 
        f"{cr_visit_lead:.1%}", 
        f"{cr_lead_api:.1%}", 
        f"{cr_api_group:.1%}"
    ]

    fig, ax = plt.subplots(figsize=(10, 5))
    bars = ax.barh(stages, values, color=colors)
    ax.invert_yaxis()

    for i, bar in enumerate(bars):
        w = bar.get_width()
        ax.text(w + (max(values)*0.01), bar.get_y() + bar.get_height()/2, f"{int(w)}", va='center', fontweight='bold')
        if i > 0:
            ax.text(w/2, bar.get_y() + bar.get_height()/2, conv_texts[i], ha='center', color='white', fontweight='bold')

    plt.title(f'{NOMBRE_FASE} - Eficiencia del Embudo', fontsize=14, fontweight='bold')
    plt.tight_layout()
    plt.show()

    # Imprimir Resumen en Consola
    print(f"--- RESUMEN GENERAL: {NOMBRE_FASE} ---")
    print(f"Inversión Total: ${total_spend:,.2f}")
    print(f"Leads Totales: {int(total_leads)} (CPL Promedio: ${total_spend/total_leads:.2f})")
    print(f"Grupo Total: {int(total_group)} (Costo Promedio: ${total_spend/total_group:.2f})")

# Ejecutar
if __name__ == "__main__":
    generar_dashboard()
