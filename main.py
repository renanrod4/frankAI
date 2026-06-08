import asyncio
from core.listener import KeyboardListener
from core.recorder import AudioRecorder
from core.transcriber import WhisperTranscriber
# from core.brain import OllamaBrain
# from core.speaker import PiperSpeaker

recorder = AudioRecorder()

transcriber = WhisperTranscriber(model_path="whisper-models/ggml-small.bin", cli_path="bin/whisper-cli", language="pt")

async def iniciar_gravacao():
    print("Gatilho acionado. Gravando... (Fale agora)")
    recorder.start_recording()

async def parar_gravacao():
    print("Gatilho liberado. Interrompendo gravação...")
    caminho_arquivo = recorder.stop_recording()
    
    if caminho_arquivo:
        print("Iniciando transcrição local com Whisper...")
        
        texto_transcrito = await transcriber.transcribe(caminho_arquivo)
        
        if texto_transcrito:
            print(f"\nuser: {texto_transcrito}")
        else:
            print("Whisper não conseguiu identificar nenhuma fala")
    else:
        print("Erro: Nenhum dado de áaudio foi gerado.")


async def main():

    # listener = KeyboardListener()
    # recorder = AudioRecorder()
    # transcriber = WhisperTranscriber()
    # brain = OllamaBrain()
    # speaker = PiperSpeaker()

    try:
        listener = KeyboardListener(
            on_press_callback=iniciar_gravacao, on_release_callback=parar_gravacao
        )
        await listener.monitor_hotkey()

    except PermissionError:
        print("Erro de permissão ao acessar o hardware. Verifique o grupo input.")
    except KeyboardInterrupt:
        print("\nEncerrando o assistente frankAI.")


if __name__ == "__main__":
    asyncio.run(main())
