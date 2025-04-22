# src/ingestion/video_processor.py

import os
import tempfile
import shutil
import logging
import subprocess

import imageio_ffmpeg as iioff
import cv2
import pytesseract

from .audio_extractor import transcribe_audio

# Obtén la ruta al ejecutable de FFmpeg proporcionado por imageio-ffmpeg
FFMPEG_EXE = iioff.get_ffmpeg_exe()

def extract_audio_from_video(video_path: str) -> str:
    """
    Extrae el audio de un video (.mp4, .mov, etc.) y lo guarda en un archivo WAV temporal.
    Retorna la ruta al archivo WAV.
    """
    tmp_wav = tempfile.NamedTemporaryFile(suffix=".wav", delete=False).name
    cmd = [
        FFMPEG_EXE,
        "-i", video_path,
        "-ac", "1",          # canal mono
        "-ar", "16000",      # tasa de muestreo 16 kHz
        "-f", "wav",         # formato WAV
        tmp_wav
    ]

    try:
        subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True
        )
    except subprocess.CalledProcessError as e:
        logging.error(f"FFmpeg audio extraction failed\nstdout:\n{e.stdout}\nstderr:\n{e.stderr}")
        raise RuntimeError(f"Error extrayendo audio: {e.stderr}")

    return tmp_wav

def extract_frames_and_ocr(video_path: str, frame_interval: int = 5) -> str:
    """
    Extrae un frame cada `frame_interval` segundos y aplica OCR para extraer texto.
    Retorna todo el texto concatenado.
    """
    temp_dir = tempfile.mkdtemp()
    ocr_text = ""
    output_pattern = os.path.join(temp_dir, "frame_%03d.jpg")

    cmd = [
        FFMPEG_EXE,
        "-i", video_path,
        "-vf", f"fps=1/{frame_interval}",
        output_pattern
    ]

    try:
        subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True
        )
        for frame_file in sorted(os.listdir(temp_dir)):
            frame_path = os.path.join(temp_dir, frame_file)
            image = cv2.imread(frame_path)
            if image is not None:
                text = pytesseract.image_to_string(image, lang="spa")
                ocr_text += text + "\n"
    except subprocess.CalledProcessError as e:
        logging.error(f"FFmpeg frame extraction failed\nstdout:\n{e.stdout}\nstderr:\n{e.stderr}")
    finally:
        shutil.rmtree(temp_dir)

    return ocr_text

def process_video(video_path: str) -> str:
    """
    Procesa un video extrayendo:
      1) Audio → transcripción Whisper
      2) Frames → OCR de diapositivas

    Combina ambos textos y lo retorna.
    """
    # 1) Extrae audio a WAV temporal
    audio_path = extract_audio_from_video(video_path)

    # 2) Transcribe audio y elimina el temp WAV
    try:
        transcript = transcribe_audio(audio_path)
    finally:
        try:
            os.remove(audio_path)
        except OSError:
            pass

    # 3) OCR de frames
    ocr_text = extract_frames_and_ocr(video_path, frame_interval=5)

    # 4) Combina y retorna
    return f"{transcript}\n\nTexto extraído de diapositivas:\n{ocr_text}"



