import argparse
import asyncio
import json
import os
from core.listener import KeyboardListener
from core.recorder import AudioRecorder
from core.transcriber import WhisperTranscriber
from core.brain import OllamaBrain
from core.speaker import PiperSpeaker

# Configuração dos parâmetros de inicialização
parser = argparse.ArgumentParser(description="frankAI Core")
parser.add_argument("--dev", action="store_true", help="Exibe o output JSON bruto do Ollama")
args, _ = parser.parse_known_args()
MODO_DEV = args.dev

recorder = AudioRecorder()
transcriber = WhisperTranscriber(model_path="whisper-models/ggml-small.bin", cli_path="bin/whisper-cli", language="pt")
brain = OllamaBrain(model_name="llama3.2")
speaker = PiperSpeaker()

async def executar_comando_linux(comando):
    if not comando:
        return
    comando = comando.strip()
    # `&` no final do comando é para o comando rode em segundo plano
    if not comando.endswith("&"):
        comando = f"{comando} &"
    
    try:
        processo = await asyncio.create_subprocess_shell(
            comando,
            stdout=asyncio.subprocess.DEVNULL,
            stderr=asyncio.subprocess.DEVNULL
        )
        asyncio.create_task(processo.wait())
    except Exception as e:
        print(f"Erro ao executar comando: {e}")

async def iniciar_gravacao():
    print("Gatilho acionado. Gravando... (Fale agora)")
    os.system("stty -echo")
    recorder.start_recording()

async def parar_gravacao():
    print("Gatilho liberado. Interrompendo gravação...")
    os.system("stty echo")
    caminho_arquivo = recorder.stop_recording()
    
    if caminho_arquivo:
        texto_transcrito = await transcriber.transcribe(caminho_arquivo)
        
        if texto_transcrito:
            print(f"\nuser: {texto_transcrito}")
            print("Pensando...")
            
            resposta_ia = await brain.ask(texto_transcrito)
            
            if MODO_DEV:
                print(f"[DEV JSON]: {json.dumps(resposta_ia, indent=2, ensure_ascii=False)}")
            
            fala = resposta_ia.get("fala", "")
            comando = resposta_ia.get("comando", "")
            
            if fala:
                print(f"frankAI: {fala}\n")
                await speaker.speak(fala)
            
            if comando:
                await executar_comando_linux(comando)
        else:
            print("Whisper não conseguiu identificar nenhuma fala")
    else:
        print("Erro: Nenhum dado de áudio foi gerado.")


async def main():
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