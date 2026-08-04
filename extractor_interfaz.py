import streamlit as st
import os
import extract_msg
import json
import pandas as pd
import tempfile

# Configuración de página con branding profesional
st.set_page_config(
    page_title="TRANSPORTES CALPI, S.A. DE C.V. | Extractor & Auditor DTE",
    page_icon="💼",
    layout="wide"
)

# Estilos personalizados para un look corporativo elegante
st.markdown("""
    <style>
    .main-header {
        background-color: #1e293b;
        color: white;
        padding: 20px;
        border-radius: 8px;
        margin-bottom: 25px;
        text-align: center;
    }
    .main-header h1 {
        margin: 0;
        font-size: 24pt;
        font-weight: 600;
    }
    .main-header p {
        margin: 5px 0 0 0;
        font-size: 11pt;
        opacity: 0.9;
    }
    .metric-box {
        background-color: #f8fafc;
        border: 1px solid #e2e8f0;
        border-radius: 6px;
        padding: 15px;
        text-align: center;
    }
    </style>
""", unsafe_allow_html=True)

# Encabezado corporativo
st.markdown("""
    <div class="main-header">
        <h1>TRANSPORTES CALPI, S.A. DE C.V.</h1>
        <p>Sistema Inteligente de Auditoría y Extracción de DTEs</p>
    </div>
""", unsafe_allow_html=True)

st.sidebar.header("📁 Carga de Archivos")
uploaded_files = st.sidebar.file_uploader(
    "Sube tus correos (.msg):", 
    type=["msg"], 
    accept_multiple_files=True
)

st.subheader("🔍 Auditoría de Integridad de Documentos")
st.markdown("Analiza tus correos `.msg` para verificar que cada transacción contenga tanto su JSON como su representación en PDF.")

if not uploaded_files:
    st.info("📂 Por favor, selecciona y sube los archivos `.msg` en la barra lateral para comenzar la auditoría.")
else:
    col_info1, col_info2 = st.columns(2)
    with col_info1:
        st.info("📂 **Origen:** Carga directa en la nube")
    with col_info2:
        st.success(f"📨 **Correos .msg detectados para auditar:** {len(uploaded_files)}")

    # Botón de extracción y auditoría
    if st.button("🚀 Ejecutar Auditoría y Homogenización", type="primary"):
        auditoria_log = []
        progreso = st.progress(0)
        status_text = st.empty()
        
        for idx, uploaded_file in enumerate(uploaded_files):
            archivo_nombre = uploaded_file.name
            status_text.text(f"Auditando correo: {archivo_nombre}...")
            
            # Guardamos temporalmente el archivo subido para que extract_msg pueda leerlo de forma segura
            with tempfile.NamedTemporaryFile(delete=False, suffix=".msg") as tmp_file:
                tmp_file.write(uploaded_file.getvalue())
                tmp_path = tmp_file.name
            
            try:
                msg = extract_msg.Message(tmp_path)
                remitente = msg.sender if msg.sender else "Desconocido"
                
                datos_json_bytes = None
                datos_pdf_bytes = None
                nombre_original_json = "No contiene"
                nombre_original_pdf = "No contiene"
                
                for adjunto in msg.attachments:
                    nombre_adjunto = None
                    if hasattr(adjunto, 'getFilename'):
                        nombre_adjunto = adjunto.getFilename()
                    elif hasattr(adjunto, 'longFilename') and adjunto.longFilename:
                        nombre_adjunto = adjunto.longFilename
                    elif hasattr(adjunto, 'filename') and adjunto.filename:
                        nombre_adjunto = adjunto.filename
                    
                    if nombre_adjunto:
                        nombre_bajo = nombre_adjunto.lower()
                        if nombre_bajo.endswith('.json'):
                            datos_json_bytes = adjunto.data
                            nombre_original_json = nombre_adjunto
                        elif nombre_bajo.endswith('.pdf'):
                            datos_pdf_bytes = adjunto.data
                            nombre_original_pdf = nombre_adjunto
                
                # Intentar leer el identificador único dentro del JSON
                codigo_generacion = None
                emisor_dte = None
                
                if datos_json_bytes:
                    try:
                        contenido_json = json.loads(datos_json_bytes.decode('utf-8'))
                        dte = contenido_json.get('documento', contenido_json) if isinstance(contenido_json, dict) else contenido_json
                        
                        identificacion = dte.get('identificacion', {}) if isinstance(dte, dict) else {}
                        emisor = dte.get('emisor', {}) if isinstance(dte, dict) else {}
                        
                        codigo_generacion = identificacion.get('codigoGeneracion')
                        emisor_dte = emisor.get('nombre')
                    except Exception:
                        pass
                
                # Naming estricto
                if codigo_generacion:
                    nombre_base_homogenizado = str(codigo_generacion)
                else:
                    nombre_base_homogenizado = f"ALERTA_SIN_JSON_{os.path.splitext(archivo_nombre)[0]}"
                
                guardado_json = "❌ Faltante"
                guardado_pdf = "❌ Faltante"
                
                if datos_json_bytes:
                    guardado_json = f"{nombre_base_homogenizado}.json"
                    
                if datos_pdf_bytes:
                    guardado_pdf = f"{nombre_base_homogenizado}.pdf"
                
                # Determinar estado de la auditoría
                if datos_json_bytes and datos_pdf_bytes:
                    resultado_auditoria = "🟢 Completo (Ambos)"
                elif datos_json_bytes:
                    resultado_auditoria = "🟡 Solo JSON (Falta PDF)"
                elif datos_pdf_bytes:
                    resultado_auditoria = "🔴 Solo PDF (Falta JSON)"
                else:
                    resultado_auditoria = "⚪ Vacío (Sin DTE)"
                
                auditoria_log.append({
                    "Remitente Correo": remitente,
                    "Emisor DTE (Hacienda)": emisor_dte if emisor_dte else "N/D",
                    "Código Generación / ID": codigo_generacion if codigo_generacion else "No encontrado",
                    "Resultado Auditoría": resultado_auditoria,
                    "Archivo JSON Guardado": guardado_json,
                    "Original JSON": nombre_original_json,
                    "Archivo PDF Guardado": guardado_pdf,
                    "Original PDF": nombre_original_pdf,
                    "Correo Origen": archivo_nombre
                })
                
            except Exception as e:
                st.error(f"Error procesando {archivo_nombre}: {str(e)}")
            finally:
                if os.path.exists(tmp_path):
                    os.unlink(tmp_path)
            
            progreso.progress((idx + 1) / len(uploaded_files))
            
        status_text.empty()
        
        if auditoria_log:
            st.session_state['resultado_auditoria'] = pd.DataFrame(auditoria_log)
            st.success("¡Auditoría y homogenización finalizada!")

# Mostrar visualización de resultados si existen
if 'resultado_auditoria' in st.session_state:
    df_auditoria = st.session_state['resultado_auditoria']
    
    st.markdown("---")
    st.subheader("📋 Reporte de Auditoría y Control")
    
    # Métricas de control
    total_audits = len(df_auditoria)
    completos = len(df_auditoria[df_auditoria["Resultado Auditoría"] == "🟢 Completo (Ambos)"])
    solo_json = len(df_auditoria[df_auditoria["Resultado Auditoría"] == "🟡 Solo JSON (Falta PDF)"])
    solo_pdf = len(df_auditoria[df_auditoria["Resultado Auditoría"] == "🔴 Solo PDF (Falta JSON)"])
    
    m_col1, m_col2, m_col3, m_col4 = st.columns(4)
    with m_col1:
        st.markdown(f'<div class="metric-box"><h3>📨 Correos Analizados</h3><h2>{total_audits}</h2></div>', unsafe_allow_html=True)
    with m_col2:
        st.markdown(f'<div class="metric-box" style="border-left: 5px solid green;"><h3>🟢 DTEs Completos</h3><h2>{completos}</h2></div>', unsafe_allow_html=True)
    with m_col3:
        st.markdown(f'<div class="metric-box" style="border-left: 5px solid orange;"><h3>🟡 Solo JSON (Falta PDF)</h3><h2>{solo_json}</h2></div>', unsafe_allow_html=True)
    with m_col4:
        st.markdown(f'<div class="metric-box" style="border-left: 5px solid red;"><h3>🔴 Solo PDF (Falta JSON)</h3><h2>{solo_pdf}</h2></div>', unsafe_allow_html=True)
        
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Tabla de control interactiva
    st.dataframe(df_auditoria, use_container_width=True)
    
    st.info("💡 **Análisis de Control Interno:** Toda factura válida comparte como nombre su Código de Generación único de 36 caracteres.")
