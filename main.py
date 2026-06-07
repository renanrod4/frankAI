import asyncio
from core.listener import KeyboardListener
# from core.recorder import AudioRecorder
# from core.transcriber import WhisperTranscriber
# from core.brain import OllamaBrain
# from core.speaker import PiperSpeaker


async def iniciar_gravacao():
    print("[Main] Evento recebido: Iniciando gravação do microfone...")


async def parar_gravacao():
    print("[Main] Evento recebido: Parando gravação. Enviando para processamento...")


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
