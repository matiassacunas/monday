from pdfminer.high_level import extract_text as pdf_extract_text
from docx import Document

def extract_text_pdf(pdf_path: str) -> str:
    """
    Extrae el texto de un archivo PDF.
    
    Args:
        pdf_path (str): Ruta al archivo PDF.
    
    Returns:
        str: Texto extraído.
    """
    try:
        text = pdf_extract_text(pdf_path)
        return text
    except Exception as e:
        raise RuntimeError(f"Error al extraer texto de PDF: {str(e)}")

def extract_text_docx(docx_path: str) -> str:
    """
    Extrae el texto de un archivo DOCX.
    
    Args:
        docx_path (str): Ruta al archivo DOCX.
    
    Returns:
        str: Texto extraído.
    """
    try:
        doc = Document(docx_path)
        full_text = [para.text for para in doc.paragraphs]
        return "\n".join(full_text)
    except Exception as e:
        raise RuntimeError(f"Error al extraer texto de DOCX: {str(e)}")
