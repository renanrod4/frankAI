import asyncio
from core.listener import KeyboardListener
from core.recorder import AudioRecorder
# from core.transcriber import WhisperTranscriber
# from core.brain import OllamaBrain
# from core.speaker import PiperSpeaker

recorder = AudioRecorder()

async def iniciar_gravacao():
    print("[Main] Gatilho acionado. Gravando... (Fale agora)")
    recorder.start_recording()

async def parar_gravacao():
    print("[Main] Gatilho liberado. Interrompendo gravação...")
    caminho_arquivo = recorder.stop_recording()
    
    if caminho_arquivo:
        print(f"[Main] Áudio salvo com sucesso em: {caminho_arquivo}")
        # O próximo passo será enviar este arquivo para core/transcriber.py
    else:
        print("[Main] Erro: Nenhum dado de áudio foi capturado.")


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
