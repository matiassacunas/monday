# src/nlp/entity_extraction.py
import spacy
from spacy.cli import download
import logging
from typing import Dict

MODEL_NAME = "en_core_web_sm"

# Carga (o descarga) el modelo de spaCy
try:
    nlp = spacy.load(MODEL_NAME)
except OSError as e:
    logging.info(f"spaCy model '{MODEL_NAME}' no encontrado: {e}. Descargando...")
    download(MODEL_NAME)
    nlp = spacy.load(MODEL_NAME)
except Exception as e:
    raise RuntimeError(f"Error inesperado al cargar el modelo spaCy '{MODEL_NAME}': {e}")

def extract_entities(text: str) -> Dict:
    """
    Extrae entidades clave del texto usando NER.
    """
    doc = nlp(text)
    data = {}

    # Nombre de la empresa (primera organización encontrada)
    for ent in doc.ents:
        if ent.label_ == "ORG" and "nombre_empresa" not in data:
            data["nombre_empresa"] = ent.text

        # Número de licencias (CARDINAL)
        if ent.label_ == "CARDINAL" and "num_licencias" not in data:
            try:
                data["num_licencias"] = int(ent.text.replace(",", "").strip())
            except ValueError:
                continue

    return data
