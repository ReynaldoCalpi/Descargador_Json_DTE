import streamlit as st
import mailbox
import tempfile
import os

st.title("Procesador MBOX - RI Consultores")
st.write("Sube tu archivo de respaldo de correo para extraer los documentos tributarios electrónicos (DTE).")

# Componente para subir el archivo MBOX
uploaded_file = st.file_uploader("Selecciona el archivo .mbox", type=["mbox"])

if uploaded_file is not None:
    # Creamos un archivo temporal para procesar el MBOX de forma segura
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mbox") as tmp_file:
        tmp_file.write(uploaded_file.getvalue())
        tmp_path = tmp_file.name

    try:
        with st.spinner("Procesando correos del archivo MBOX..."):
            # Abrimos el MBOX usando la librería nativa de Python
            mbox = mailbox.mbox(tmp_path)
            total_mensajes = len(mbox)
            
            st.success(f"¡Archivo cargado correctamente! Total de mensajes encontrados: {total_mensajes}")

            # Iterador básico para explorar los mensajes
            resultados = []
            for i, message in enumerate(mbox):
                subject = message.get('subject', 'Sin asunto')
                sender = message.get('from', 'Desconocido')
                date = message.get('date', 'Sin fecha')
                
                # Aquí puedes integrar tu lógica de parsing de DTE / XML / adjuntos
                resultados.gespend = {"index": i, "subject": subject, "sender": sender, "date": date}

            st.info("Estructura lista para comenzar la extracción de datos.")

    except Exception as e:
        st.error(f"Ocurrió un error al procesar el archivo MBOX: {e}")
        
    finally:
        # Aseguramos la limpieza del archivo temporal en el servidor
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)
