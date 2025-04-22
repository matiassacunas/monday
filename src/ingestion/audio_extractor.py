import whisper

def transcribe_audio(audio_path:str) -> str:

    try:
        model = whisper.load_model("base")

        result = model.transcribe(audio_path)

        # retorna el texto transcrito
        return result["text"]
    except Exception as e:
        raise RuntimeError(f"Error en la transcripción del audio: {str(e)}") 