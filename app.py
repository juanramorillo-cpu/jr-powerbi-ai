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
    div[data-testid="metric-container"] { background-color: #F8F9FA; border-radius: 10px; border: 1px solid #EDEBE9; box-shadow: 2px 2px 5px rgba(0,0,0,0.02); }
</style>
""", unsafe_allow_html=True)

st.markdown('<p class="hero-text">JR MORILLO AI 💎</p>', unsafe_allow_html=True)
st.markdown('<p class="sub-hero">Consultoría Avanzada: DAX, Auditoría y Diseño de Dashboards</p>', unsafe_allow_html=True)
st.markdown("---")

# ==========================================
# ⚙️ 2. BARRA LATERAL (MOTORES RESTAURADOS)
# ==========================================
with st.sidebar:
    st.header("⚙️ Configuración")
    api_key = st.text_input("🔑 Gemini API Key:", type="password")
    
    if api_key: st.success("✅ Conexión Segura Establecida")
    
    st.markdown("---")
    st.header("🧠 Selección de Motor")
    
    # 🔥 MOTORES VISIBLES Y CORRECTOS 🔥
    opciones_modelo = {
        "🚀 Gemini 2.5 Flash Lite (Rápido y Seguro)": "gemini-2.5-flash-lite",
        "⚡ Gemini 2.5 Flash (Requiere validación)": "gemini-2.5-flash",
        "🧠 Gemini 3.1 Pro (Preview Potente)": "gemini-3.1-pro-preview"
    }
    
    seleccion = st.selectbox("Elige la velocidad y profundidad:", list(opciones_modelo.keys()))
    modelo_api = opciones_modelo[seleccion]
    
    # El recuadro visual que nos habíamos saltado
    st.info(f"**Motor activo:** `{modelo_api}`")

# ==========================================
# 🛡️ 3. MOTOR DE LLAMADAS (SISTEMA ANTI-503)
# ==========================================
def llamar_ia_con_respaldo(prompt_text, motor_elegido, clave_api):
    url_principal = f"https://generativelanguage.googleapis.com/v1beta/models/{motor_elegido}:generateContent?key={clave_api}"
    payload = {"contents": [{"parts": [{"text": prompt_text}]}]}
    
    try:
        # Intento 1: Con el motor que has elegido
        res = requests.post(url_principal, json=payload, timeout=60)
        
        if res.status_code == 200:
            return True, res.json()['candidates'][0]['content']['parts'][0]['text']
            
        elif res.status_code == 503:
            # SISTEMA DE EMERGENCIA: Si hay fallo 503, saltamos al Lite
            st.warning(f"⚠️ El motor seleccionado está saturado (503). Activando motor de respaldo (Flash Lite)...")
            url_respaldo = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-lite:generateContent?key={clave_api}"
            res_respaldo = requests.post(url_respaldo, json=payload, timeout=60)
            
            if res_respaldo.status_code == 200:
                st.success("✅ Resuelto con motor de respaldo.")
                return True, res_respaldo.json()['candidates'][0]['content']['parts'][0]['text']
            else:
                return False, f"Fallo total en servidores. Código: {res_respaldo.status_code}"
        else:
            return False, f"Error de Google: {res.status_code}"
            
    except requests.exceptions.Timeout:
        return False, "⏳ Tiempo de espera agotado."
    except Exception as e:
        return False, f"❌ Error de red: {e}"

# ==========================================
# 🔍 4. ESCANEO DUAL (POWER BI Y EXCEL)
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
# 🚀 5. INTERFAZ PRINCIPAL
# ==========================================
archivo = st.file_uploader("📂 Sube tu Proyecto Power BI (.zip) o Excel (.xlsx)", type=["zip", "xlsx"])

if archivo:
    with st.spinner("Analizando estructura..."):
        modelo = escanear_archivo(archivo)
    
    if modelo:
        st.markdown(f"### 📋 Resumen del Modelo Detectado: `{modelo['tipo']}`")
        col1, col2, col3 = st.columns(3)
        col1.metric("Tablas/Hojas", len(modelo['tablas']))
        col2.metric("Columnas/Campos", len(modelo['columnas']))
        col3.metric("Medidas Actuales", len(modelo['medidas']))

        st.markdown("---")
        st.markdown("### 🛠️ ¿Qué acción quieres realizar hoy?")
        
        tab1, tab2, tab3 = st.tabs(["💡 Generador DAX / Fórmulas", "🎨 Diseñador de Dashboard", "🩺 Auditor de Salud"])

        # ---------------- TAB 1: DAX ----------------
        with tab1:
            pregunta_dax = st.text_area("Describe la medida DAX o fórmula de Excel:", placeholder="Ej: Calcula el margen de beneficio...")
            if st.button("🚀 Generar Código", key="btn_dax"):
                if not api_key: st.error("Falta API Key")
                else:
                    with st.spinner("Pensando..."):
                        rol = "Experto en Excel" if "Excel" in modelo['tipo'] else "Experto en Power BI"
                        prompt = f"Actúa como {rol}. Estructura: {modelo}. Pregunta: {pregunta_dax}. Devuelve solo el código y una breve explicación."
                        exito, respuesta = llamar_ia_con_respaldo(prompt, modelo_api, api_key)
                        if exito: st.markdown(respuesta)
                        else: st.error(respuesta)

        # ---------------- TAB 2: DISEÑO ----------------
        with tab2:
            st.info("La IA actuará como diseñador UX/UI.")
            objetivo = st.text_input("¿Cuál es el objetivo principal del Dashboard?", placeholder="Ej: Control de ventas...")
            if st.button("🎨 Crear Boceto Visual", key="btn_wire"):
                if not api_key: st.error("Falta API Key")
                else:
                    with st.spinner("Diseñando interfaz..."):
                        prompt = f"Actúa como Diseñador experto en visualización. Tablas: {modelo['tablas']}. Columnas: {modelo['columnas']}. Objetivo: {objetivo}. Diseña una estructura visual indicando qué columnas usar."
                        exito, respuesta = llamar_ia_con_respaldo(prompt, modelo_api, api_key)
                        if exito: st.markdown(respuesta)
                        else: st.error(respuesta)

        # ---------------- TAB 3: AUDITORÍA ----------------
        with tab3:
            st.warning("Se escaneará tu modelo en busca de malas prácticas.")
            if st.button("🩺 Ejecutar Auditoría", key="btn_audit"):
                if not api_key: st.error("Falta API Key")
                else:
                    with st.spinner("Escaneando debilidades..."):
                        prompt = f"Actúa como Arquitecto de Datos. Analiza este modelo: {modelo}. Busca errores comunes. Devuelve un informe con Puntuación, Puntos Críticos y Puntos de Mejora."
                        exito, respuesta = llamar_ia_con_respaldo(prompt, modelo_api, api_key)
                        if exito: st.markdown(respuesta)
                        else: st.error(respuesta)

else:
    st.info("Sube un proyecto de Power BI (.zip) o un Excel (.xlsx) para desbloquear las herramientas.")
