import os
import tempfile
import shutil
import logging
import imageio_ffmpeg as iioff
import ffmpeg
import cv2
import pytesseract
from .audio_extractor import transcribe_audio

# 1) Apunto ffmpeg-python al binario de imageio-ffmpeg
os.environ["FFMPEG_BINARY"] = iioff.get_ffmpeg_exe()

def extract_audio_from_video(video_path: str) -> str:
    """
    Extrae el audio del video y lo guarda en un WAV temporal.
    Retorna la ruta al archivo WAV.
    """
    tmp_wav = tempfile.NamedTemporaryFile(suffix=".wav", delete=False).name

    try:
        # Quitamos quiet=True para que aparezcan posibles warnings
        ffmpeg.input(video_path) \
              .output(tmp_wav, ac=1, ar=16000, format="wav") \
              .overwrite_output() \
              .run(capture_stdout=True, capture_stderr=True)
    except ffmpeg.Error as e:
        stderr = e.stderr.decode("utf-8", errors="ignore")
        logging.error(f"ffmpeg stderr:\n{stderr}")
        raise RuntimeError(f"Error extrayendo audio: {stderr}")

    return tmp_wav

def extract_frames_and_ocr(video_path: str, frame_interval: int = 5) -> str:
    """
    Extrae cuadros del video a intervalos regulares y aplica OCR para extraer texto.
    """
    ocr_text = ""
    temp_dir = tempfile.mkdtemp()

    try:
        ffmpeg.input(video_path) \
              .output(os.path.join(temp_dir, "frame_%03d.jpg"), vf=f"fps=1/{frame_interval}") \
              .overwrite_output() \
              .run(quiet=True)

        for frame_file in sorted(os.listdir(temp_dir)):
            frame_path = os.path.join(temp_dir, frame_file)
            image = cv2.imread(frame_path)
            if image is not None:
                text = pytesseract.image_to_string(image, lang="spa")
                ocr_text += text + "\n"
    except Exception as e:
        logging.error(f"Error en extracción de cuadros u OCR: {e}", exc_info=True)
    finally:
        shutil.rmtree(temp_dir)

    return ocr_text

def process_video(video_path: str) -> str:
    """
    Procesa un video extrayendo el audio (Whisper) y texto de cuadros (OCR),
    combina ambos textos para darle contexto al LLM.
    """
    # 1) Extrae audio a WAV temporal
    audio_path = extract_audio_from_video(video_path)

    # 2) Transcribe y limpia archivo
    try:
        transcript = transcribe_audio(audio_path)
    finally:
        try:
            os.remove(audio_path)
        except OSError:
            pass

    # 3) OCR de cuadros
    ocr_text = extract_frames_and_ocr(video_path, frame_interval=5)

    # 4) Combina y retorna
    return f"{transcript}\n\nTexto extraído de diapositivas:\n{ocr_text}"

