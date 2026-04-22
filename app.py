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
    .hero-text { font-size: 2.8rem !important; font-weight: 800 !important; color: #0078D4; margin-bottom: 0rem; }
    .stButton>button { width: 100%; border-radius: 8px; font-weight: 600; padding: 0.6rem; }
    .status-box { padding: 10px; border-radius: 5px; margin-bottom: 10px; border: 1px solid #ddd; }
</style>
""", unsafe_allow_html=True)

st.markdown('<p class="hero-text">JR MORILLO AI 💎</p>', unsafe_allow_html=True)
st.markdown("---")

# ==========================================
# ⚙️ 2. BARRA LATERAL (RESTAURADA TOTALMENTE)
# ==========================================
with st.sidebar:
    st.header("⚙️ Configuración")
    api_key = st.text_input("🔑 Gemini API Key:", type="password")
    
    if api_key: 
        st.success("✅ Clave detectada")
    else:
        st.warning("⚠️ Falta API Key")

    st.markdown("---")
    st.header("🧠 Selección de Motor")
    
    opciones_modelo = {
        "🚀 Gemini 2.5 Flash Lite (Más estable)": "gemini-2.5-flash-lite",
        "⚡ Gemini 2.5 Flash (Equilibrado)": "gemini-2.5-flash",
        "🧠 Gemini 3.1 Pro (Máxima potencia)": "gemini-3.1-pro-preview"
    }
    
    # Aseguramos que la variable modelo_api esté siempre disponible
    seleccion_nombre = st.selectbox("Motor inteligente:", list(opciones_modelo.keys()))
    modelo_api = opciones_modelo[seleccion_nombre]
    
    st.info(f"**Activo:** `{modelo_api}`")

# ==========================================
# 🛡️ 3. GESTOR DE LLAMADAS (ANTI-403 Y ANTI-503)
# ==========================================
def peticion_ia(prompt, modelo, clave):
    # Intentamos primero con el modelo elegido
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{modelo}:generateContent?key={clave}"
    payload = {"contents": [{"parts": [{"text": prompt}]}]}
    
    try:
        res = requests.post(url, json=payload, timeout=60)
        
        if res.status_code == 200:
            return res.json()['candidates'][0]['content']['parts'][0]['text']
        
        elif res.status_code == 403:
            return "❌ **Error 403 (Permiso Denegado):** Tu API Key no tiene permisos para este modelo. Por favor, crea una nueva clave en Google AI Studio asegurándote de que el proyecto tenga habilitada la API de Gemini."
            
        elif res.status_code == 503:
            st.warning("⚠️ Motor saturado. Saltando a Flash Lite (Emergencia)...")
            url_lite = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-lite:generateContent?key={clave}"
            res_lite = requests.post(url_lite, json=payload, timeout=60)
            if res_lite.status_code == 200:
                return res_lite.json()['candidates'][0]['content']['parts'][0]['text']
            else:
                return f"❌ Fallo masivo en Google (503). Inténtalo en un minuto."
        
        else:
            return f"❌ Error {res.status_code}: {res.text}"
            
    except Exception as e:
        return f"❌ Error de red: {str(e)}"

# ==========================================
# 🔍 4. ESCÁNER DE ARCHIVOS (REFORZADO)
# ==========================================
def analizar_archivo(file):
    resumen = {"tablas": [], "columnas": [], "medidas": [], "tipo": "Desconocido", "log": []}
    
    if file.name.endswith('.xlsx'):
        try:
            resumen["tipo"] = "Excel"
            xls = pd.ExcelFile(file)
            resumen["tablas"] = xls.sheet_names
            for hoja in xls.sheet_names:
                df = pd.read_excel(file, sheet_name=hoja, nrows=1)
                resumen["columnas"].extend([f"{hoja}[{c}]" for c in df.columns])
            return resumen
        except Exception as e:
            resumen["log"].append(f"Error Excel: {e}")
            return resumen

    # MODO ZIP (POWER BI)
    try:
        with zipfile.ZipFile(file, 'r') as z:
            nombres = z.namelist()
            resumen["log"] = nombres # Guardamos la lista de archivos para debug
            
            # Buscamos tablas en TMDL
            archivos_tmdl = [f for f in nombres if '/tables/' in f and f.endswith('.tmdl')]
            
            if archivos_tmdl:
                resumen["tipo"] = "PBI (TMDL)"
                for f in archivos_tmdl:
                    nombre_tabla = f.split('/')[-1].replace('.tmdl', '')
                    if "DateTable" not in nombre_tabla:
                        resumen["tablas"].append(nombre_tabla)
                        try:
                            content = z.read(f).decode('utf-8', errors='ignore')
                            for linea in content.split('\n'):
                                linea = linea.strip()
                                if linea.startswith('column '):
                                    col = linea.split('column ')[1].split('=')[0].strip().strip('"')
                                    resumen["columnas"].append(f"{nombre_tabla}[{col}]")
                                elif linea.startswith('measure '):
                                    med = linea.split('measure ')[1].split('=')[0].strip().strip('"')
                                    resumen["medidas"].append(med)
                        except: pass
            else:
                resumen["tipo"] = "ZIP (No es formato Proyecto PBI)"
    except Exception as e:
        resumen["log"].append(f"Error ZIP: {e}")
        
    return resumen

# ==========================================
# 🚀 5. LÓGICA DE INTERFAZ
# ==========================================
fichero = st.file_uploader("📂 Sube tu ZIP de Power BI o tu Excel", type=["zip", "xlsx"])

if fichero:
    data = analizar_archivo(fichero)
    
    # MOSTRAMOS EL CONTENIDO SIEMPRE
    st.markdown(f"### 📊 Estructura detectada ({data['tipo']})")
    
    if not data["tablas"]:
        st.error("No se han detectado tablas o carpetas de datos. Asegúrate de que el ZIP contiene la estructura de 'Proyecto de Power BI' (.pbip).")
        with st.expander("Ver archivos dentro del ZIP (Debug)"):
            st.write(data["log"])
    else:
        col1, col2, col3 = st.columns(3)
        col1.metric("Tablas", len(data["tablas"]))
        col2.metric("Columnas", len(data["columnas"]))
        col3.metric("Medidas", len(data["medidas"]))

        # PESTAÑAS DE ACCIÓN
        t1, t2, t3 = st.tabs(["💡 Generar DAX", "🎨 Diseñar Dashboard", "🩺 Auditoría"])

        with t1:
            pregunta = st.text_area("¿Qué lógica necesitas?", placeholder="Ej: Suma de ventas acumulada...")
            if st.button("🚀 Crear Código"):
                if not api_key: st.error("Falta la clave API")
                else:
                    contexto = f"Archivo: {data['tipo']}. Tablas: {data['tablas']}. Columnas: {data['columnas']}. Pregunta: {pregunta}"
                    respuesta = peticion_ia(contexto, modelo_api, api_key)
                    st.markdown(respuesta)

        with t2:
            objetivo = st.text_input("Objetivo del informe:", placeholder="Ej: Ventas por región...")
            if st.button("🎨 Generar Wireframe"):
                if not api_key: st.error("Falta la clave API")
                else:
                    contexto = f"Diseña un dashboard para: {objetivo}. Usa estas tablas: {data['tablas']}. Estructura visual clara."
                    respuesta = peticion_ia(contexto, modelo_api, api_key)
                    st.markdown(respuesta)

        with t3:
            if st.button("🩺 Analizar Salud del Modelo"):
                if not api_key: st.error("Falta la clave API")
                else:
                    contexto = f"Audita este modelo: {data}. Busca fallos de diseño o falta de tablas clave."
                    respuesta = peticion_ia(contexto, modelo_api, api_key)
                    st.markdown(respuesta)
