import whisper

model = whisper.load_model("base")

def listen():
    result = model.transcribe("voice.wav")
    return result["text"]