import json
import time
import streamlit as st
from typing import Dict
from src.utils.config import GROQ_API_KEY
from langchain import LLMChain, PromptTemplate
from langchain_groq import ChatGroq

def refine_extraction(text: str, initial_data: Dict) -> Dict:
    """
    Refina la extracción de información para la propuesta comercial de Seidor.
    Incorpora texto base de especificaciones (Monday Product Spec) junto con transcripciones.
    Extrae y prepara dos secciones: Suscripciones e Implementación.
    Implementa reintentos con back-off en caso de errores 503.
    """
    template = """
Eres un asistente experto en generación de propuestas comerciales para Seidor, en español.
Tienes **información base** de productos Monday.com (precios, características, usos) proveniente de un PDF estático incluido en el proyecto.
Cuando proceses las distintas fuentes de información (audio, video, PDF, DOCX, ingreso manual), debes combinar las necesidades concretas del cliente con esa información base.

Tienes **información base** de productos Monday.com, seguida del texto transcrito de la reunión.

### Información base de productos:
{text}

### Datos de cliente (transcripción + NER preliminar):
Datos iniciales:
{initial_data}

### Tareas:
1. **Suscripciones:**
   - Lista productos solicitados (1–4).
   - Para cada uno:
     - producto: Work Management, CRM, Dev o Service.
     - detalle: (precio usuario)×(usuarios)×12 meses.
     - monto_total_anual: «<valor> + IVA».
   - total_suscripciones_anual: suma de cada monto_total_anual + IVA.

2. **Implementación:**
   - Solo rellena **horas_de_implementacion** y **duracion_proyecto_implementacion** si en la reunión o documentación se mencionaron explícitamente horas o duración del proyecto.
   - Si no se mencionan estos detalles, deja ambos campos como cadena vacía.
   - Cuando apliquen, reporta:
     * servicio: 'Proyecto de Implementación'.
     * duracion: 'X horas / Y semanas'.
     * valor: '1.5 UF / Hora'.
     * monto_implementacion_anual: 'horas×1.5 UF + IVA'.

**Instrucciones:**
- Deja campos no encontrados como "".
- emails siempre vacío.

Devuelve **solo** un JSON con estas claves:
```json
{{
  "nombre_empresa": "",
  "descripcion_empresa": "",
  "requerimientos_y_desafios": [],
  "cantidad_licencias": "",
  "vigencia_contrato": "",
  "tipo_licencia": [],
  "suscripciones": [
    {{"producto":"","detalle":"","monto_total_anual":"<valor> + IVA"}}
  ],
  "total_suscripciones_anual": "<suma> + IVA",
  "horas_implementacion": "",
  "duracion_proyecto_implementacion": "",
  "monto_implementacion_anual": "<horas> × 1.5 UF + IVA",
  "emails": ""
}}```

Texto combinado: tras información base y datos iniciales.
"""
    prompt = PromptTemplate(template=template, input_variables=["initial_data","text"])
    llm = ChatGroq(
        groq_api_key=GROQ_API_KEY,
        model_name="meta-llama/llama-4-maverick-17b-128e-instruct",
        temperature=0
    )
    chain = LLMChain(llm=llm, prompt=prompt)

    max_attempts = 3
    for attempt in range(1, max_attempts + 1):
        try:
            generated = chain.run(
                initial_data=json.dumps(initial_data, ensure_ascii=False),
                text=text
            )
            start = generated.find("{")
            end = generated.rfind("}")
            if start != -1 and end > start:
                return json.loads(generated[start:end+1])
            return initial_data

        except Exception as e:
            msg = str(e)
            # Si es un 503 o Service Unavailable, reintenta
            if "503" in msg or "Service Unavailable" in msg:
                wait = 2 ** attempt
                st.warning(f"Groq no disponible (intento {attempt}/{max_attempts}), reintentando en {wait}s...")
                time.sleep(wait)
                continue
            # Otro error: termina y retorna preliminares
            st.error(f"Error inesperado en LLMChain: {e}")
            return initial_data

    st.error("El servicio de extracción LLM no está disponible tras varios intentos; usando datos preliminares.")
    return initial_data

