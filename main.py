# main.py
import os
import json
import streamlit as st

# Función auxiliar para convertir a entero de forma segura
def safe_int(value, default=0):
    try:
        return int(value)
    except (ValueError, TypeError):
        return default

# Importa funciones de los módulos internos
from src.ingestion.audio_extractor import transcribe_audio
from src.ingestion.video_processor import process_video
from src.ingestion.doc_extractor import extract_text_pdf, extract_text_docx
from src.nlp.entity_extraction import extract_entities
from src.nlp.groq_llm import refine_extraction
from src.utils.file_utils import ensure_directory_exists

# Directorios de trabajo
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_DIR = os.path.join(BASE_DIR, "data/uploads")
SPEC_PDF  = os.path.join(BASE_DIR, "templates/monday_product_specs.pdf")

# Asegura la existencia de los directorios necesarios
ensure_directory_exists(UPLOAD_DIR)

# Configuración de la página
st.set_page_config(
    page_title="Extracción Variables - AUTODOC MONDAY",
    layout="wide"
)
st.title("Extracción de Variables Clave - AUTODOC MONDAY")

# Carga estática de especificaciones de productos
with st.spinner("Cargando especificaciones de productos Monday..."):
    spec_text = extract_text_pdf(SPEC_PDF)
st.success("Especificaciones cargadas.")

# Función para reiniciar la app después de descarga
def reset_app():
    # Limpia todo el session_state para reiniciar la app
    for key in list(st.session_state.keys()):
        del st.session_state[key]

# Selección de archivos: múltiple y mixto: múltiple y mixto
uploaded_files = st.file_uploader(
    "Sube uno o varios archivos (Audio, Video, PDF, DOCX)",
    type=["mp3","wav","mp4","mov","avi","pdf","docx"],
    accept_multiple_files=True
)

# Construye texto combinado: info base + extracción
combined_text = spec_text + "\n\n"

if uploaded_files:
    for uploaded in uploaded_files:
        path = os.path.join(UPLOAD_DIR, uploaded.name)
        with open(path, "wb") as f:
            f.write(uploaded.getbuffer())
    st.success(f"{len(uploaded_files)} archivo(s) subido(s) correctamente.")

    # Procesa cada archivo según su extensión
    for uploaded in uploaded_files:
        ext = os.path.splitext(uploaded.name)[1].lower()
        path = os.path.join(UPLOAD_DIR, uploaded.name)
        if ext in [".mp3", ".wav"]:
            with st.spinner(f"Transcribiendo {uploaded.name}..."):
                combined_text += transcribe_audio(path) + "\n"
        elif ext in [".mp4", ".mov", ".avi"]:
            with st.spinner(f"Procesando video {uploaded.name}..."):
                combined_text += process_video(path) + "\n"
        elif ext == ".pdf":
            with st.spinner(f"Extrayendo texto PDF {uploaded.name}..."):
                combined_text += extract_text_pdf(path) + "\n"
        elif ext == ".docx":
            with st.spinner(f"Extrayendo texto DOCX {uploaded.name}..."):
                combined_text += extract_text_docx(path) + "\n"

    # Muestra el texto combinado
    st.subheader("Texto combinado (especificaciones + entradas)")
    st.text_area("", combined_text, height=250)

    # Extracción preliminar con SpaCy
    initial_data = extract_entities(combined_text)
    st.subheader("Extracción preliminar")
    st.json(initial_data)

    # Refinamiento con Groq LLMChain
    refined_data = refine_extraction(combined_text, initial_data)
    st.subheader("Variables refinadas")
    st.json(refined_data)

    # Botón para descargar JSON de variables + reset
    json_bytes = json.dumps(refined_data, ensure_ascii=False, indent=2).encode('utf-8')
    st.download_button(
        label="Descargar variables extraídas (JSON)",
        data=json_bytes,
        file_name="variables_propuesta.json",
        mime="application/json",
        on_click=reset_app
    )

# Caso: Ingreso manual sin archivos
if not uploaded_files:
    st.info("Ingrese manualmente el texto para procesar.")
    manual_text = st.text_area(
        "Texto de entrada manual",
        height=250
    )
    if st.button("Procesar manualmente"):
        combined_text = spec_text + "\n\n" + manual_text
        initial_data = extract_entities(combined_text)
        refined_data = refine_extraction(combined_text, initial_data)
        st.subheader("Variables refinadas (manual)")
        st.json(refined_data)
        json_bytes = json.dumps(refined_data, ensure_ascii=False, indent=2).encode('utf-8')
        st.download_button(
            label="Descargar variables manuales (JSON)",
            data=json_bytes,
            file_name="variables_manual.json",
            mime="application/json",
            on_click=reset_app
        )
