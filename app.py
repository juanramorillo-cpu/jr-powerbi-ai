import streamlit as st
import zipfile
import json
import requests
import time

# ==========================================
# 🎨 1. CONFIGURACIÓN VISUAL (SaaS Corporativo)
# ==========================================
st.set_page_config(page_title="JR Morillo AI - Power BI", layout="wide", page_icon="📊")

st.markdown("""
<style>
    .hero-text { font-size: 2.8rem !important; font-weight: 800 !important; color: #0078D4; margin-bottom: 0rem; letter-spacing: -0.5px; }
    .sub-hero { font-size: 1.1rem; color: #605E5C; margin-bottom: 2rem; font-weight: 500; }
    .stButton>button { width: 100%; border-radius: 6px; background-color: #0078D4; color: white; font-weight: 600; border: none; padding: 0.6rem; transition: all 0.2s ease; box-shadow: 0 2px 4px rgba(0, 120, 212, 0.2); }
    .stButton>button:hover { background-color: #005A9E; transform: translateY(-1px); box-shadow: 0 4px 8px rgba(0, 120, 212, 0.3); color: white; }
    div[data-testid="metric-container"] { background-color: #F8F9FA; border-radius: 8px; padding: 15px; border-left: 4px solid #0078D4; box-shadow: 0 1px 3px rgba(0,0,0,0.05); border: 1px solid #EDEBE9; }
    hr { border-top: 1px solid #EDEBE9; }
</style>
""", unsafe_allow_html=True)

# 🖼️ CABECERA
col_logo, col_texto = st.columns([1, 10])
with col_logo:
    st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/c/cf/New_Power_BI_Logo.svg/120px-New_Power_BI_Logo.svg.png", width=60)
with col_texto:
    st.markdown('<p class="hero-text">JR MORILLO AI</p>', unsafe_allow_html=True)

st.markdown('<p class="sub-hero">Asistente Analítico y Generador de DAX</p>', unsafe_allow_html=True)
st.markdown("---")

# ==========================================
# ⚙️ 2. BARRA LATERAL (CONTROL Y MOTORES)
# ==========================================
with st.sidebar:
    st.header("⚙️ Centro de Control")
    api_key = st.text_input("🔑 Gemini API Key:", type="password")
    if api_key: st.success("Conexión Segura Establecida")
    
    st.markdown("---")
    st.header("🧠 Selección de Motor")
    
    # 🔥 AÑADIDO EL MODELO LITE QUE SÍ TE FUNCIONA 🔥
    opciones_modelo = {
        "🚀 Gemini 2.5 Flash Lite (Rápido y Seguro)": "gemini-2.5-flash-lite",
        "⚡ Gemini 2.5 Flash (Requiere validación)": "gemini-2.5-flash",
        "⚖️ Gemini 2.5 Pro (Requiere validación)": "gemini-2.5-pro",
        "🧠 Gemini 3.1 Pro (Preview Potente)": "gemini-3.1-pro-preview"
    }
    
    seleccion = st.selectbox("Elige la velocidad y profundidad:", list(opciones_modelo.keys()))
    modelo_api = opciones_modelo[seleccion]
    
    st.info(f"**Motor activo:** `{modelo_api}`")
    
    st.markdown("---")
    st.info("""
    **📥 ¿Cómo subir el modelo completo?**
    1. Abre tu informe en Power BI Desktop.
    2. Ve a *Archivo > Guardar como...* y elige el formato **Proyecto de Power BI (.pbip)**.
    3. Ve a la carpeta donde lo guardaste.
    4. Selecciona las carpetas `.SemanticModel` y `.Report`.
    5. Haz clic derecho y dales a **Comprimir en archivo ZIP**.
    6. Sube ese archivo `.zip` a esta aplicación.
    """)

# ==========================================
# 🔍 3. MOTOR DE ESCANEO TOTAL (TMDL + PBIR)
# ==========================================
def escanear_archivo(file):
    datos = {"tablas": [], "columnas": [], "medidas": [], "paginas": [], "tipo": "Desconocido"}
    try:
        with zipfile.ZipFile(file, 'r') as z:
            archivos = z.namelist()
            archivos_tmdl = [f for f in archivos if f.endswith('.tmdl') and '/tables/' in f]
            if archivos_tmdl:
                datos["tipo"] = "PBIP (Nuevo Formato TMDL)"
                for f in archivos_tmdl:
                    t_name = f.split('/')[-1].replace('.tmdl', '')
                    if not t_name.startswith('DateTable') and not t_name.startswith('LocalDateTable'):
                        datos["tablas"].append(t_name)
                        content = z.read(f).decode('utf-8', errors='ignore')
                        for linea in content.split('\n'):
                            linea = linea.strip()
                            if linea.startswith('column '):
                                c_name = linea.replace('column ', '').split('=')[0].strip().strip("'\"")
                                datos["columnas"].append(f"{t_name}[{c_name}]")
                            elif linea.startswith('measure '):
                                m_name = linea.replace('measure ', '').split('=')[0].strip().strip("'\"")
                                datos["medidas"].append(m_name)
            elif any(f.endswith('model.bim') for f in archivos):
                datos["tipo"] = "PBIP (Formato Clásico BIM)"
                archivo_modelo = next(f for f in archivos if f.endswith('model.bim'))
                content = z.read(archivo_modelo).decode('utf-8', errors='ignore')
                modelo = json.loads(content)
                for t in modelo.get('model', {}).get('tables', []):
                    t_name = t.get('name')
                    if not t_name.startswith('DateTable') and not t_name.startswith('LocalDateTable'):
                        datos["tablas"].append(t_name)
                        for c in t.get('columns', []): datos["columnas"].append(f"{t_name}[{c.get('name')}]")
                        for m in t.get('measures', []): datos["medidas"].append(m.get('name'))

            archivos_paginas = [f for f in archivos if f.endswith('page.json') and '/pages/' in f]
            if archivos_paginas:
                for f in archivos_paginas:
                    try:
                        content = z.read(f).decode('utf-8', errors='ignore')
                        page_data = json.loads(content)
                        nombre_pag = page_data.get('displayName', page_data.get('name', 'Página'))
                        datos["paginas"].append(nombre_pag)
                    except: pass
    except Exception as e:
        st.error(f"Error al escanear: {e}")
        return None
    return datos

# ==========================================
# 🚀 4. INTERFAZ PRINCIPAL Y CONEXIÓN
# ==========================================
archivo_subido = st.file_uploader("📂 Sube el archivo .zip de tu Proyecto (.pbip)", type="zip")

if archivo_subido:
    with st.spinner("Analizando la matriz de datos..."):
        time.sleep(1)
        datos_modelo = escanear_archivo(archivo_subido)
    
    if datos_modelo and (datos_modelo['tablas'] or datos_modelo['paginas']):
        st.markdown(f"### 📈 Radiografía del Modelo: `{datos_modelo['tipo']}`")
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Tablas", len(datos_modelo['tablas']))
        col2.metric("Columnas", len(datos_modelo['columnas']))
        col3.metric("Medidas Actuales", len(datos_modelo['medidas']))
        col4.metric("Páginas", len(datos_modelo['paginas']))

        if datos_modelo['tablas']:
            with st.expander("👁️ Ver Estructura Interna (Tablas y Medidas)"):
                st.write("**Tablas:**", ", ".join(datos_modelo['tablas']))
                st.write("**Medidas:**", ", ".join(datos_modelo['medidas']) if datos_modelo['medidas'] else "Ninguna")

        st.markdown("---")
        st.markdown(f"### 💬 Consola DAX ({seleccion.split(' ')[1]} {seleccion.split(' ')[2]})")
        pregunta = st.text_area("¿Qué lógica necesitas programar hoy?", height=100)

        if st.button("⚡ Generar Código con IA"):
            if not api_key: st.error("❌ Introduce tu API Key en la barra lateral.")
            elif not pregunta: st.warning("⚠️ Escribe tu pregunta.")
            else:
                with st.spinner(f"🧠 Procesando con {seleccion}..."):
                    url = f"https://generativelanguage.googleapis.com/v1beta/models/{modelo_api}:generateContent?key={api_key}"
                    contexto = f"Actúa como Consultor Senior de Power BI. Páginas: {datos_modelo['paginas']}. Tablas: {datos_modelo['tablas']}. Columnas: {datos_modelo['columnas']}. Medidas existentes: {datos_modelo['medidas']}. Pregunta: {pregunta}"
                    payload = {"contents": [{"parts": [{"text": contexto}]}]}
                    
                    try:
                        res = requests.post(url, json=payload, timeout=120)
                        
                        if res.status_code == 200:
                            st.success("✅ Código generado exitosamente")
                            st.markdown(res.json()['candidates'][0]['content']['parts'][0]['text'])
                        
                        elif res.status_code == 503:
                            st.warning("⚠️ El motor seleccionado está saturado (Error 503). Activando sistema de emergencia (Gemini Flash Lite)...")
                            # 🔥 AHORA EL RESPALDO ES EL LITE QUE SABEMOS QUE FUNCIONA 🔥
                            url_emergencia = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-lite:generateContent?key={api_key}"
                            res_emergencia = requests.post(url_emergencia, json=payload, timeout=60)
                            
                            if res_emergencia.status_code == 200:
                                st.success("✅ Código generado por el motor de respaldo (Flash Lite)")
                                st.markdown(res_emergencia.json()['candidates'][0]['content']['parts'][0]['text'])
                            else:
                                st.error(f"❌ Fallo de conexión o cuota excedida. Código del respaldo: {res_emergencia.status_code}")
                                st.json(res_emergencia.json())
                        
                        else:
                            st.error(f"Error de Google: {res.status_code}")
                            st.json(res.json())
                            
                    except requests.exceptions.Timeout:
                        st.error("⏳ El modelo ha excedido el tiempo máximo. Intenta con un motor más rápido de la barra lateral.")
                    except Exception as e:
                        st.error(f"Error de red: {e}")