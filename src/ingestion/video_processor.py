# src/ingestion/video_processor.py

import os
import ffmpeg
import tempfile
import shutil
import cv2
import pytesseract
from .audio_extractor import transcribe_audio

def extract_audio_from_video(video_path: str, audio_output_path: str) -> None:
    """
    Extrae el audio del video y lo guarda en formato WAV compatible con Whisper.
    """
    try:
        (
            ffmpeg
            .input(video_path)
            .output(audio_output_path, ac=1, ar=16000, format="wav")
            .overwrite_output()
            .run(quiet=True)
        )
    except Exception as e:
        raise RuntimeError(f"Error extrayendo audio del video: {str(e)}")

def extract_frames_and_ocr(video_path: str, frame_interval: int = 5) -> str:
    """
    Extrae cuadros del video a intervalos regulares y aplica OCR para extraer el texto (por ejemplo, de diapositivas).
    
    Args:
        video_path (str): Ruta del archivo de video.
        frame_interval (int): Intervalo en segundos entre cuadros a extraer.
        
    Returns:
        str: Texto combinado extraído de los cuadros.
    """
    ocr_text = ""
    # Crear un directorio temporal para almacenar los cuadros extraídos
    temp_dir = tempfile.mkdtemp()

    try:
        # Extraer cuadros usando ffmpeg: se guarda un frame cada 'frame_interval' segundos.
        ffmpeg.input(video_path).output(os.path.join(temp_dir, "frame_%03d.jpg"), vf=f"fps=1/{frame_interval}").overwrite_output().run(quiet=True)
        
        # Obtener la lista de archivos (cuadros)
        frame_files = sorted(os.listdir(temp_dir))
        
        for frame_file in frame_files:
            frame_path = os.path.join(temp_dir, frame_file)
            image = cv2.imread(frame_path)
            if image is not None:
                # Aplicar OCR en la imagen (usando el idioma español)
                text = pytesseract.image_to_string(image, lang="spa")
                ocr_text += text + "\n"
    except Exception as e:
        print(f"Error en extracción de cuadros u OCR: {e}")
    finally:
        # Limpiar el directorio temporal
        shutil.rmtree(temp_dir)
    
    return ocr_text

def process_video(video_path: str) -> str:
    """
    Procesa un video extrayendo el audio y transcribiéndolo con Whisper, además de extraer el texto de cuadros 
    (por ejemplo, diapositivas) mediante OCR. Combina ambos textos para que el LLM tenga mayor contexto.
    
    Args:
        video_path (str): Ruta al archivo de video.
    
    Returns:
        str: Texto combinado (transcripción de audio y texto extraído de las diapositivas).
    """
    # Definir el nombre del archivo de audio temporal
    audio_output_path = video_path.rsplit(".", 1)[0] + "_audio.wav"
    # Extraer el audio
    extract_audio_from_video(video_path, audio_output_path)
    
    # Transcribir el audio usando Whisper (la función transcribe_audio ya usa el modelo Whisper)
    transcript = transcribe_audio(audio_output_path)
    
    # Extraer texto de cuadros (por ejemplo, de las diapositivas del video)
    ocr_text = extract_frames_and_ocr(video_path, frame_interval=5)
    
    # Combinar ambos textos para proporcionar un mayor contexto
    combined_text = transcript + "\n\n" + "Texto extraído de diapositivas:" + "\n" + ocr_text
    return combined_text
