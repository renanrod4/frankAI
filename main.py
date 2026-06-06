import asyncio
from core.listener import KeyboardListener
from core.recorder import AudioRecorder
from core.transcriber import WhisperTranscriber
from core.brain import OllamaBrain
from core.speaker import PiperSpeaker

async def main():
    
    listener = KeyboardListener()
    recorder = AudioRecorder()
    transcriber = WhisperTranscriber()
    brain = OllamaBrain()
    speaker = PiperSpeaker()

    print("frankAI pronto e operando de fundo.")

if __name__ == "__main__":
    asyncio.run(main())