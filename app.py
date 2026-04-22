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
</style>
""", unsafe_allow_html=True)

st.markdown('<p class="hero-text">JR MORILLO AI 💎</p>', unsafe_allow_html=True)
st.markdown("---")

# ==========================================
# ⚙️ 2. BARRA LATERAL
# ==========================================
with st.sidebar:
    st.header("⚙️ Configuración")
    api_key = st.text_input("🔑 Gemini API Key:", type="password")
    
    if api_key: st.success("✅ Conexión Detectada")
    
    st.markdown("---")
    st.header("🧠 Motor IA")
    opciones_modelo = {
        "🚀 Gemini 2.5 Flash Lite (Estable)": "gemini-2.5-flash-lite",
        "⚡ Gemini 2.5 Flash (Rápido)": "gemini-2.5-flash",
        "🧠 Gemini 3.1 Pro (Potente)": "gemini-3.1-pro-preview"
    }
    seleccion = st.selectbox("Elegir motor:", list(opciones_modelo.keys()))
    modelo_api = opciones_modelo[seleccion]
    st.info(f"**Activo:** `{modelo_api}`")

# ==========================================
# 🛡️ 3. MOTOR DE PETICIONES
# ==========================================
def peticion_ia(prompt, modelo, clave):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{modelo}:generateContent?key={clave}"
    payload = {"contents": [{"parts": [{"text": prompt}]}]}
    try:
        res = requests.post(url, json=payload, timeout=60)
        if res.status_code == 200:
            return res.json()['candidates'][0]['content']['parts'][0]['text']
        elif res.status_code == 403:
            return "❌ **Error 403 (Permisos):** Tu clave no tiene permisos para este modelo. Genera una nueva clave en Google AI Studio en un proyecto nuevo."
        elif res.status_code == 503:
            url_lite = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-lite:generateContent?key={clave}"
            res_lite = requests.post(url_lite, json=payload, timeout=60)
            return res_lite.json()['candidates'][0]['content']['parts'][0]['text'] if res_lite.status_code == 200 else "❌ Error 503 persistente."
        else:
            return f"❌ Error {res.status_code}: {res.text}"
    except Exception as e:
        return f"❌ Error de red: {str(e)}"

# ==========================================
# 🔍 4. ESCÁNER DUAL HÍBRIDO (TMDL Y BIM)
# ==========================================
def analizar_fichero(file):
    res = {"tablas": [], "columnas": [], "medidas": [], "tipo": "Desconocido", "debug": []}
    
    # --- MODO EXCEL ---
    if file.name.lower().endswith('.xlsx'):
        try:
            res["tipo"] = "Excel"
            xls = pd.ExcelFile(file)
            res["tablas"] = xls.sheet_names
            for hoja in xls.sheet_names:
                df = pd.read_excel(file, sheet_name=hoja, nrows=1)
                res["columnas"].extend([f"{hoja}[{c}]" for c in df.columns])
            return res
        except Exception as e:
            res["debug"].append(f"Error Excel: {str(e)}")
            return res

    # --- MODO POWER BI (ZIP) ---
    if file.name.lower().endswith('.zip'):
        try:
            with zipfile.ZipFile(file, 'r') as z:
                nombres = z.namelist()
                res["debug"] = nombres
                
                tmdls = [f for f in nombres if '/tables/' in f and f.endswith('.tmdl')]
                bims = [f for f in nombres if f.endswith('model.bim')]

                # 1. Intentar leer formato clásico (BIM) <-- EL TUYO
                if bims:
                    res["tipo"] = "Power BI (Formato BIM)"
                    archivo_bim = bims[0]
                    content = z.read(archivo_bim).decode('utf-8', errors='ignore')
                    modelo_json = json.loads(content)
                    
                    for tabla in modelo_json.get('model', {}).get('tables', []):
                        t_name = tabla.get('name', '')
                        if "DateTable" not in t_name and "LocalDate" not in t_name and "Date" != t_name:
                            res["tablas"].append(t_name)
                            for col in tabla.get('columns', []):
                                res["columnas"].append(f"{t_name}[{col.get('name')}]")
                            for med in tabla.get('measures', []):
                                res["medidas"].append(med.get('name'))
                                
                # 2. Intentar leer formato nuevo (TMDL)
                elif tmdls:
                    res["tipo"] = "Power BI (Formato TMDL)"
                    for f in tmdls:
                        t_name = f.split('/')[-1].replace('.tmdl', '')
                        if "DateTable" not in t_name and "LocalDate" not in t_name:
                            res["tablas"].append(t_name)
                            content = z.read(f).decode('utf-8', errors='ignore')
                            for linea in content.split('\n'):
                                l = linea.strip()
                                if l.startswith('column '):
                                    c = l.split('column ')[1].split('=')[0].strip().strip('"')
                                    res["columnas"].append(f"{t_name}[{c}]")
                                elif l.startswith('measure '):
                                    m = l.split('measure ')[1].split('=')[0].strip().strip('"')
                                    res["medidas"].append(m)
            return res
        except Exception as e:
            res["debug"].append(f"Error ZIP: {str(e)}")
            return res
            
    return res

# ==========================================
# 🚀 5. LÓGICA DE INTERFAZ
# ==========================================
fichero = st.file_uploader("📂 Sube tu archivo (Excel .xlsx o Power BI .zip)", type=["xlsx", "zip"])

if fichero:
    data = analizar_fichero(fichero)
    
    if data["tipo"] == "Desconocido":
        st.error("Formato de archivo no soportado.")
    elif not data["tablas"]:
        if data["tipo"] == "Excel":
            st.error("No se han podido leer las hojas del Excel. Asegúrate de que no esté protegido.")
        else:
            st.error("No se ha detectado el modelo de datos (TMDL o BIM) en el archivo ZIP.")
            with st.expander("Ver contenido técnico del ZIP"):
                st.write(data["debug"])
    else:
        st.success(f"Análisis completado: {data['tipo']}")
        c1, c2, c3 = st.columns(3)
        c1.metric("Tablas/Hojas", len(data["tablas"]))
        c2.metric("Columnas", len(data["columnas"]))
        c3.metric("Medidas", len(data["medidas"]))

        st.markdown("---")
        t1, t2, t3 = st.tabs(["💡 Generar DAX/Fórmula", "🎨 Diseñar Dashboard", "🩺 Auditoría"])

        with t1:
            preg = st.text_area("¿Qué necesitas calcular?", placeholder="Ej: Varianza de ventas...")
            if st.button("🚀 Crear Código"):
                if not api_key: st.error("Falta API Key")
                else:
                    with st.spinner("Pensando..."):
                        prompt = f"Actúa como experto en {data['tipo']}. Estructura: {data}. Pregunta: {preg}. Devuelve el código y una explicación corta."
                        st.markdown(peticion_ia(prompt, modelo_api, api_key))

        with t2:
            obj = st.text_input("Objetivo del informe:", placeholder="Ej: Control de costes...")
            if st.button("🎨 Crear Wireframe"):
                if not api_key: st.error("Falta API Key")
                else:
                    with st.spinner("Diseñando..."):
                        prompt = f"Diseña un dashboard para: {obj}. Usa estas tablas: {data['tablas']}. Indica qué columnas de {data['columnas']} usar en cada gráfico."
                        st.markdown(peticion_ia(prompt, modelo_api, api_key))

        with t3:
            if st.button("🩺 Auditoría de Salud"):
                if not api_key: st.error("Falta API Key")
                else:
                    with st.spinner("Analizando..."):
                        prompt = f"Audita este modelo de {data['tipo']}: {data}. Indica errores estructurales y buenas prácticas."
                        st.markdown(peticion_ia(prompt, modelo_api, api_key))
