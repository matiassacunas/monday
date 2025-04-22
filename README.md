# Extracción de Variables - AUTODOC MONDAY

**AUTODOC MONDAY** es una aplicación Streamlit para automatizar la extracción de variables clave de propuestas comerciales basadas en información inicial (especificaciones de productos de Monday.com) y datos de reuniones o documentos (audio, video, PDF, DOCX o texto manual).

---

## Objetivo

- **Enfoque actual** asegurar que todas las variables clave se extraigan correctamente antes de generar la propuesta final en PPT (esta funcionalidad está WIP y se añadirá una vez validada la extracción).
- **Cargar** un PDF estático con las especificaciones de productos de Monday.com.
- **Procesar** múltiples archivos (audio, video, PDF, DOCX) o texto manual.
- **Combinar** la información base y el contenido extraído.
- **Extraer** entidades y refinar variables clave mediante SpaCy + LangChain (Groq).
- **Descargar** inmediatamente el JSON con las variables extraídas.
- **Reiniciar** la aplicación tras cada descarga para nuevos procesos.

---

## Características principales

1. **Carga múltiple de archivos**: acepta audio (`.mp3`, `.wav`), video (`.mp4`, `.mov`, `.avi`), PDF y DOCX en una sola operación.
2. **Información base**: incluye un PDF con precios y características de los productos Monday.com.
3. **Ingestión y transcripción**:
   - Audio → Speech-to-Text.
   - Video → extracción de audio y transcripción.
   - PDF/DOCX → extracción de texto.
   - Texto manual → ingreso directo.
4. **Extracción preliminar**: reconocimiento de entidades con SpaCy (`EntityRuler`).
5. **Refinamiento LLM**: LangChain + Groq con reintentos y back-off ante errores 503.
6. **Lógica condicional**: solo rellena horas y duración de implementación si se mencionaron explícitamente.
7. **Descarga inmediata**: botón para bajar el JSON de variables y limpiar el estado de la app.

---



Instalar con:
```bash
pip install -r requirements.txt
python -m spacy download es_core_news_md
```

---

## Configuración

1. `.env` en tu entorno:
   ```env
   GROQ_API_KEY=tu_groq_api_key
   GROQ_ENDPOINT=https://api.groq.ai/v1/chat/completions
   ```
2. Asegúrate de tener `ffmpeg` instalado y accesible en PATH.

---

## Cómo ejecutar

Desde la raíz del proyecto:
```bash
streamlit run main.py
```

1. **Sube** uno o varios archivos en el componente de carga.
2. Observa el **texto combinado** (especificaciones + entrada).
3. Revisa la **extracción preliminar** y el **JSON refinado**.
4. Haz clic en **"Descargar variables extraídas (JSON)"** para obtener el archivo.

Para **texto manual**, deja el área de carga vacía, escribe en el campo manual y pulsa **"Procesar manualmente"**.

---



