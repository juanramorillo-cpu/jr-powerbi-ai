import streamlit as st
import zipfile
import json
import requests
import time
import pandas as pd

# ==========================================
# 🎨 1. CONFIGURACIÓN VISUAL
# ==========================================
st.set_page_config(page_title="JR Morillo AI - Premium", layout="wide", page_icon="💎")

st.markdown("""
<style>
    .hero-text { font-size: 3rem !important; font-weight: 800 !important; color: #0078D4; margin-bottom: 0rem; }
    .sub-hero { font-size: 1.2rem; color: #605E5C; margin-bottom: 2rem; font-weight: 500; }
    .stButton>button { width: 100%; border-radius: 8px; font-weight: 600; padding: 0.7rem; transition: all 0.3s; }
    .btn-dax { background-color: #0078D4; color: white !important; }
    .btn-audit { background-color: #D13438; color: white !important; }
    .btn-wire { background-color: #107C10; color: white !important; }
    div[data-testid="metric-container"] { background-color: #F8F9FA; border-radius: 10px; border: 1px solid #EDEBE9; box-shadow: 2px 2px 5px rgba(0,0,0,0.02); }
    .report-card { background: white; padding: 20px; border-radius: 10px; border: 1px solid #E1DFDD; margin-top: 15px; }
</style>
""", unsafe_allow_html=True)

st.markdown('<p class="hero-text">JR MORILLO AI 💎</p>', unsafe_allow_html=True)
st.markdown('<p class="sub-hero">Consultoría Avanzada: DAX, Auditoría y Diseño de Dashboards</p>', unsafe_allow_html=True)
st.markdown("---")

# ==========================================
# ⚙️ 2. BARRA LATERAL
# ==========================================
with st.sidebar:
    st.header("⚙️ Configuración")
    api_key = st.text_input("🔑 Gemini API Key:", type="password")       
    if api_key: st.success("✅ Conexión Segura Establecida") 
    
    st.markdown("---")
    st.header("🧠 Motor de Inteligencia")

# ==========================================
# 🔍 3. ESCANEO DE ARCHIVOS
# ==========================================
def escanear_archivo(file):
    datos = {"tablas": [], "columnas": [], "medidas": [], "tipo": "Desconocido"}
    if file.name.endswith('.xlsx'):
        try:
            excel = pd.ExcelFile(file)
            datos["tipo"] = "Excel (.xlsx)"
            datos["tablas"] = excel.sheet_names
            for sheet in excel.sheet_names:
                df = pd.read_excel(file, sheet_name=sheet, nrows=1)
                datos["columnas"].extend([f"{sheet}[{c}]" for c in df.columns])
            return datos
        except: return None

    try:
        with zipfile.ZipFile(file, 'r') as z:
            archivos = z.namelist()
            archivos_tmdl = [f for f in archivos if f.endswith('.tmdl') and '/tables/' in f]
            if archivos_tmdl:
                datos["tipo"] = "Power BI (TMDL)"
                for f in archivos_tmdl:
                    t_name = f.split('/')[-1].replace('.tmdl', '')
                    if not t_name.startswith('DateTable') and not t_name.startswith('LocalDate'):
                        datos["tablas"].append(t_name)
                        content = z.read(f).decode('utf-8', errors='ignore')
                        for linea in content.split('\n'):
                            linea = linea.strip()
                            if linea.startswith('column '): datos["columnas"].append(f"{t_name}[{linea.split('column ')[1].split('=')[0].strip().strip('\"')}]")
                            elif linea.startswith('measure '): datos["medidas"].append(linea.split('measure ')[1].split('=')[0].strip().strip('\"'))
            return datos
    except: return None

# ==========================================
# 🚀 4. INTERFAZ PRINCIPAL
# ==========================================
archivo = st.file_uploader("📂 Sube tu Proyecto Power BI (.zip) o Excel (.xlsx)", type=["zip", "xlsx"])

if archivo:
    with st.spinner("Analizando estructura..."):
        modelo = escanear_archivo(archivo)
    
    if modelo:
        st.markdown(f"### 📋 Resumen del Modelo Detectado")
        col1, col2, col3 = st.columns(3)
        col1.metric("Tablas/Hojas", len(modelo['tablas']))
        col2.metric("Columnas/Campos", len(modelo['columnas']))
        col3.metric("Medidas DAX", len(modelo['medidas']))

        st.markdown("---")
        st.markdown("### 🛠️ ¿Qué acción quieres realizar?")
        
        tab1, tab2, tab3 = st.tabs(["💡 Generador DAX", "🎨 Diseñador de Dashboard", "🩺 Auditor de Salud"])

        # ---------------- TAB 1: DAX ----------------
        with tab1:
            pregunta_dax = st.text_area("Describe la medida o lógica que necesitas:", placeholder="Ej: Calcula el margen de beneficio comparando con el año anterior...")
            if st.button("🚀 Generar Código DAX", key="btn_dax"):
                if not api_key: st.error("Introduce la API Key")
                else:
                    with st.spinner("Programando..."):
                        prompt = f"Actúa como Experto Senior en Power BI. Estructura: {modelo}. Pregunta: {pregunta_dax}. Devuelve solo el código DAX y una breve explicación."
                        url = f"https://generativelanguage.googleapis.com/v1beta/models/{modelo_api}:generateContent?key={api_key}"
                        res = requests.post(url, json={"contents": [{"parts": [{"text": prompt}]}]})
                        st.markdown(res.json()['candidates'][0]['content']['parts'][0]['text'])

        # ---------------- TAB 2: WIREFRAME ----------------
        with tab2:
            st.info("La IA diseñará la distribución visual ideal basada en tus tablas y columnas.")
            objetivo = st.text_input("¿Cuál es el objetivo de este Dashboard?", placeholder="Ej: Control de ventas y rentabilidad por agente...")
            if st.button("🎨 Crear Boceto Visual", key="btn_wire"):
                with st.spinner("Diseñando interfaz..."):
                    prompt = f"Actúa como Diseñador de UX/UI experto en Power BI. Analiza estas tablas: {modelo['tablas']} y columnas: {modelo['columnas']}. El objetivo es: {objetivo}. Diseña una estructura de Dashboard (Header, Filtros, KPIs, Gráficos principales) indicando exactamente qué columnas usar en cada objeto visual. Estructura la respuesta con Markdown para que sea fácil de leer."
                    url = f"https://generativelanguage.googleapis.com/v1beta/models/{modelo_api}:generateContent?key={api_key}"
                    res = requests.post(url, json={"contents": [{"parts": [{"text": prompt}]}]})
                    st.markdown(res.json()['candidates'][0]['content']['parts'][0]['text'])

        # ---------------- TAB 3: AUDITORÍA ----------------
        with tab3:
            st.warning("Se analizará el modelo en busca de fallos de diseño o falta de tablas clave.")
            if st.button("🩺 Ejecutar Auditoría de Salud", key="btn_audit"):
                with st.spinner("Escaneando debilidades..."):
                    prompt = f"Actúa como Arquitecto de Datos experto. Analiza la estructura de este modelo: {modelo}. Busca errores comunes como: falta de tabla calendario, nombres de tablas poco claros, exceso de columnas, falta de medidas calculadas, etc. Devuelve un informe con: 1. Estado General (0-100), 2. Puntos Críticos encontrados, 3. Sugerencias de mejora."
                    url = f"https://generativelanguage.googleapis.com/v1beta/models/{modelo_api}:generateContent?key={api_key}"
                    res = requests.post(url, json={"contents": [{"parts": [{"text": prompt}]}]})
                    st.markdown(res.json()['candidates'][0]['content']['parts'][0]['text'])

else:
    st.info("Sube un archivo para desbloquear las herramientas de análisis.")
