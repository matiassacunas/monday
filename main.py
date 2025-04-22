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
from src.ingestion.video_processor import (
    process_video,
    extract_audio_from_video,
    extract_frames_and_ocr,
)
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
    for key in list(st.session_state.keys()):
        del st.session_state[key]

# Selector de archivos
uploaded_files = st.file_uploader(
    "Sube uno o varios archivos (Audio, Video, PDF, DOCX)",
    type=["mp3","wav","mp4","mov","avi","pdf","docx"],
    accept_multiple_files=True
)

# Comienza a construir el texto combinado
combined_text = spec_text + "\n\n"

if uploaded_files:
    # Guardar todos los archivos
    for uploaded in uploaded_files:
        dest = os.path.join(UPLOAD_DIR, uploaded.name)
        with open(dest, "wb") as f:
            f.write(uploaded.getbuffer())
    st.success(f"{len(uploaded_files)} archivo(s) subido(s) correctamente.")

    # Barra de progreso global por archivo
    total = len(uploaded_files)
    file_bar = st.progress(0)

    # Procesar cada archivo
    for idx, uploaded in enumerate(uploaded_files):
        ext = os.path.splitext(uploaded.name)[1].lower()
        path = os.path.join(UPLOAD_DIR, uploaded.name)

        # Actualiza la barra global
        file_bar.progress((idx + 1) / total)

        if ext in [".mp3", ".wav"]:
            with st.spinner(f"Transcribiendo {uploaded.name}…"):
                combined_text += transcribe_audio(path) + "\n"

        elif ext in [".mp4", ".mov", ".avi"]:
            # Barra detallada para vídeo
            placeholder = st.empty()
            step_bar   = st.progress(0)

            placeholder.info(f"1/4 Extrayendo audio de {uploaded.name}…")
            audio_path = extract_audio_from_video(path)
            step_bar.progress(25)

            placeholder.info("2/4 Transcribiendo audio…")
            transcript = transcribe_audio(audio_path)
            step_bar.progress(50)
            try:
                os.remove(audio_path)
            except OSError:
                pass

            placeholder.info("3/4 Extrayendo texto con OCR…")
            ocr_text = extract_frames_and_ocr(path, frame_interval=5)
            step_bar.progress(75)

            placeholder.info("4/4 Combinando resultados…")
            combined_text += (
                transcript
                + "\n\nTexto extraído de diapositivas:\n"
                + ocr_text
                + "\n"
            )
            step_bar.progress(100)
            placeholder.success("Procesamiento de video completado.")

        elif ext == ".pdf":
            with st.spinner(f"Extrayendo texto PDF {uploaded.name}…"):
                combined_text += extract_text_pdf(path) + "\n"

        elif ext == ".docx":
            with st.spinner(f"Extrayendo texto DOCX {uploaded.name}…"):
                combined_text += extract_text_docx(path) + "\n"

    # Mostrar resultados
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

    # Botón para descargar JSON y resetear
    json_bytes = json.dumps(refined_data, ensure_ascii=False, indent=2).encode('utf-8')
    st.download_button(
        label="Descargar variables extraídas (JSON)",
        data=json_bytes,
        file_name="variables_propuesta.json",
        mime="application/json",
        on_click=reset_app
    )

# Caso de ingreso manual sin archivos
else:
    st.info("Ingrese manualmente el texto para procesar.")
    manual_text = st.text_area(
        "Texto de entrada manual",
        height=250
    )
    if st.button("Procesar manualmente"):
        combined = spec_text + "\n\n" + manual_text
        initial_data = extract_entities(combined)
        refined_data = refine_extraction(combined, initial_data)
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

