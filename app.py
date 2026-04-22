import streamlit as st
import zipfile
import json
import requests
import time
import pandas as pd # <-- Nueva librería para Excel

# ==========================================
# 🎨 1. CONFIGURACIÓN VISUAL
# ==========================================
st.set_page_config(page_title="JR Morillo AI - Universal", layout="wide", page_icon="📊")

st.markdown("""
<style>
    .hero-text { font-size: 2.8rem !important; font-weight: 800 !important; color: #0078D4; margin-bottom: 0rem; }
    .sub-hero { font-size: 1.1rem; color: #605E5C; margin-bottom: 2rem; font-weight: 500; }
    .stButton>button { width: 100%; border-radius: 6px; background-color: #0078D4; color: white; font-weight: 600; border: none; padding: 0.6rem; }
    div[data-testid="metric-container"] { background-color: #F8F9FA; border-radius: 8px; padding: 15px; border-left: 4px solid #0078D4; border: 1px solid #EDEBE9; }
</style>
""", unsafe_allow_html=True)

st.markdown('<p class="hero-text">JR MORILLO AI</p>', unsafe_allow_html=True)
st.markdown('<p class="sub-hero">Asistente Analítico Universal: Power BI & Excel</p>', unsafe_allow_html=True)
st.markdown("---")

# ==========================================
# ⚙️ 2. BARRA LATERAL
# ==========================================
with st.sidebar:
    st.header("⚙️ Configuración")
    api_key = st.text_input("🔑 Gemini API Key:", type="password")
    
    st.markdown("---")
    st.header("🧠 Motor IA")
    opciones_modelo = {
        "🚀 Gemini 2.5 Flash Lite (Recomendado)": "gemini-2.5-flash-lite",
        "⚡ Gemini 2.5 Flash": "gemini-2.5-flash",
        "🧠 Gemini 3.1 Pro": "gemini-3.1-pro-preview"
    }
    seleccion = st.selectbox("Velocidad:", list(opciones_modelo.keys()))
    modelo_api = opciones_modelo[seleccion]

    st.markdown("---")
    st.info("**Soporta:**\n- Proyectos Power BI (.zip)\n- Libros Excel (.xlsx)")

# ==========================================
# 🔍 3. MOTOR DE ESCANEO DUAL (PBI + EXCEL)
# ==========================================
def escanear_archivo(file):
    datos = {"tablas": [], "columnas": [], "medidas": [], "paginas": [], "tipo": "Desconocido"}
    
    # --- CASO A: EXCEL ---
    if file.name.endswith('.xlsx'):
        try:
            datos["tipo"] = "Libro de Excel (.xlsx)"
            # Leemos todas las hojas
            excel = pd.ExcelFile(file)
            datos["tablas"] = excel.sheet_names
            for sheet in excel.sheet_names:
                df = pd.read_excel(file, sheet_name=sheet, nrows=1) # Solo leemos cabeceras para ir rápido
                for col in df.columns:
                    datos["columnas"].append(f"{sheet}[{col}]")
            return datos
        except Exception as e:
            st.error(f"Error leyendo Excel: {e}")
            return None

    # --- CASO B: ZIP (POWER BI) ---
    try:
        with zipfile.ZipFile(file, 'r') as z:
            archivos = z.namelist()
            archivos_tmdl = [f for f in archivos if f.endswith('.tmdl') and '/tables/' in f]
            if archivos_tmdl:
                datos["tipo"] = "Proyecto Power BI (TMDL)"
                for f in archivos_tmdl:
                    t_name = f.split('/')[-1].replace('.tmdl', '')
                    if not t_name.startswith('DateTable'):
                        datos["tablas"].append(t_name)
                        content = z.read(f).decode('utf-8', errors='ignore')
                        for linea in content.split('\n'):
                            linea = linea.strip()
                            if linea.startswith('column '):
                                c_name = linea.replace('column ', '').split('=')[0].strip().strip("'\"")
                                datos["columnas"].append(f"{t_name}[{c_name}]")
            return datos
    except:
        return None

# ==========================================
# 🚀 4. INTERFAZ Y CONSULTA
# ==========================================
archivo_subido = st.file_uploader("📂 Sube tu archivo ZIP o Excel", type=["zip", "xlsx"])

if archivo_subido:
    datos_modelo = escanear_archivo(archivo_subido)
    
    if datos_modelo:
        st.markdown(f"### 📊 Análisis de: `{datos_modelo['tipo']}`")
        c1, c2 = st.columns(2)
        c1.metric("Tablas/Hojas", len(datos_modelo['tablas']))
        c2.metric("Campos detectados", len(datos_modelo['columnas']))

        with st.expander("👁️ Ver estructura"):
            st.write(f"**Tablas/Hojas:** {', '.join(datos_modelo['tablas'])}")

        st.markdown("---")
        pregunta = st.text_area("¿Qué fórmula o análisis necesitas?", height=100, placeholder="Ej: Hazme una fórmula para calcular el margen en Excel...")

        if st.button("⚡ Generar con IA"):
            if not api_key: st.error("Falta API Key")
            else:
                with st.spinner("Pensando..."):
                    url = f"https://generativelanguage.googleapis.com/v1beta/models/{modelo_api}:generateContent?key={api_key}"
                    rol = "Experto en Power BI y Excel." if "Excel" in datos_modelo['tipo'] else "Consultor Senior Power BI."
                    contexto = f"Actúa como {rol}. Tipo de archivo: {datos_modelo['tipo']}. Estructura: {datos_modelo['tablas']}. Columnas: {datos_modelo['columnas']}. Pregunta: {pregunta}"
                    
                    res = requests.post(url, json={"contents": [{"parts": [{"text": contexto}]}]})
                    if res.status_code == 200:
                        st.success("Listo!")
                        st.markdown(res.json()['candidates'][0]['content']['parts'][0]['text'])
                    else:
                        st.error(f"Error {res.status_code}. Prueba el motor Flash Lite.")
