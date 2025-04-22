import spacy
from typing import Dict

try:
    nlp = spacy.load("en_core_web_sm")

except Exception:
    raise RuntimeError("Error loading spaCy model. Make sure the model is installed. Run 'python -m spacy download en_core_web_sm'")


def extract_entities(text:str) -> Dict:

    # extrae entidades clave del texto usando NER

    # text (str): Texto del cual se extraerán las entidades.
    # Returns:
    # dict: Un diccionario con las entidades encontradas y sus etiquetas.

    doc = nlp(text)
    data = {}

    # extraer nombre de la empresa (primera organización encontrada)

    for ent in doc.ents:
        if ent.label_ == "ORG" and "nombre_empresa" not in data:
            data["nombre_empresa"] = ent.text
            
            # Ejemplo de extracción de número de licencias (usando entidad CARDINAL)
        if ent.label_ == "CARDINAL" and "num_licencias" not in data:
            try:
                data["num_licencias"] = int(ent.text.replace(",", "").strip())
            except ValueError:
                continue
    return data