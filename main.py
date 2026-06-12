import argparse
import asyncio
import json
import os
import sys
from multiprocessing import Process, Queue

from core.listener import KeyboardListener
from core.recorder import AudioRecorder
from core.transcriber import WhisperTranscriber
from core.brain import OllamaBrain
from core.speaker import PiperSpeaker
from core.notifications import disparar_notificacao


def rodar_indicador(fila_status):

    from PyQt6.QtWidgets import QApplication
    from PyQt6.QtCore import QTimer
    from core.indicator import FrankIndicator

    app = QApplication(sys.argv)
    indicador = FrankIndicator()
    indicador.show()

    def checar_fila():
        # Lê todas as atualizações enviadas pelo backend sem travar a interface
        while not fila_status.empty():
            status = fila_status.get_nowait()
            indicador.atualizar_status(status)

    # Verifica a fila de mensagens do sistema a cada 50ms
    timer = QTimer()
    timer.timeout.connect(checar_fila)
    timer.start(50)

    sys.exit(app.exec())


# Fila global e thread-safe para comunicação unidirecional (Main -> Qt)
fila_indicador = Queue()

def mudar_cor_indicador(status):
    # Envia o comando para o processo do PyQt
    fila_indicador.put(status)


# Configuração dos parâmetros de inicialização
parser = argparse.ArgumentParser(description="frankAI Core")
parser.add_argument("--dev", action="store_true", help="Exibe o output JSON bruto do Ollama")
args, _ = parser.parse_known_args()
MODO_DEV = args.dev

async def executar_comando_linux(comando):
    if not comando:
        return
    comando = comando.strip()
    if not comando.endswith("&"):
        comando = f"{comando} &"

    try:
        processo = await asyncio.create_subprocess_shell(
            comando,
            stdout=asyncio.subprocess.DEVNULL,
            stderr=asyncio.subprocess.DEVNULL,
        )
        asyncio.create_task(processo.wait())
    except Exception as e:
        print(f"Erro ao executar comando: {e}")
        disparar_notificacao(
            titulo="Falha na Execução",
            mensagem=f"Não foi possível rodar o comando gerado.",
            icone="dialog-error",
        )


async def iniciar_gravacao():
    print("Gatilho acionado. Gravando... (Fale agora)")
    os.system("stty -echo")
    
    mudar_cor_indicador("ouvindo")
    recorder.start_recording()


async def parar_gravacao():
    os.system("stty echo")
    print("\r\033[KGatilho liberado. processando o áudio...")
    
    mudar_cor_indicador("pensando")
    
    disparar_notificacao(
        titulo="Frank AI está processando sua fala",
        mensagem="Ele fará o que você precisa em breve",
        icone="dialog-information",
    )
    caminho_arquivo = recorder.stop_recording()

    if caminho_arquivo:
        texto_transcrito = await transcriber.transcribe(caminho_arquivo)

        if texto_transcrito:
            print(f"\nuser: {texto_transcrito}")
            print("Pensando...")

            try:
                resposta_ia = await brain.ask(texto_transcrito)
            except Exception as e:
                print(f"Erro ao conectar ao Ollama: {e}")
                disparar_notificacao(
                    titulo="FrankAI: Erro no Modelo",
                    mensagem="O serviço do Ollama parece estar offline ou inacessível.",
                    icone="dialog-error",
                )
                mudar_cor_indicador("inativo")
                return

            if MODO_DEV:
                print(f"[DEV JSON]: {json.dumps(resposta_ia, indent=2, ensure_ascii=False)}")

            fala = resposta_ia.get("fala", "")
            comando = resposta_ia.get("comando", "")

            if not fala and not comando:
                disparar_notificacao(
                    titulo="FrankAI: Comando não reconhecido",
                    mensagem="A intenção não foi compreendida. Tente reformular a frase.",
                    icone="dialog-information",
                )
                mudar_cor_indicador("inativo")
                return

            mudar_cor_indicador("sucesso")

            if fala:
                print(f"frankAI: {fala}\n")
                await speaker.speak("... ... " + fala)

            if comando:
                await executar_comando_linux(comando)
        else:
            print("Whisper não conseguiu identificar nenhuma fala")
            disparar_notificacao(
                titulo="FrankAI não conseguiu entender nenhuma fala",
                mensagem="Talvez seu microfone não esteja conectado ou tente falar mais alto",
                icone="dialog-warning",
            )
            mudar_cor_indicador("inativo")
    else:
        print("Erro: Nenhum dado de áudio foi gerado.")
        mudar_cor_indicador("inativo")


async def main():
    # Inicializa a bolinha como um processo daemon (ela morre quando o main.py morre)
    processo_ui = Process(target=rodar_indicador, args=(fila_indicador,), daemon=True)
    processo_ui.start()

    try:
        listener = KeyboardListener(
            on_press_callback=iniciar_gravacao, on_release_callback=parar_gravacao
        )
        print("Seja bem-vindo ao frankAI! Pressione Super + F para falar com o assistente. Ctrl+C para sair...\n")

        await listener.monitor_hotkey()

    except PermissionError:
        print("Erro de permissão ao acessar o hardware. Verifique o grupo input.")
        disparar_notificacao(
            titulo="FrankAI: Erro Crítico",
            mensagem="Sem permissão para acessar os inputs de hardware. Verifique o grupo input.",
            icone="dialog-error",
        )
    except KeyboardInterrupt:
        print("\nEncerrando o assistente frankAI.")
    finally:
        # Garante que o processo da interface seja limpo ao sair
        if processo_ui.is_alive():
            processo_ui.terminate()


if __name__ == "__main__":
    global recorder, transcriber, brain, speaker
    recorder = AudioRecorder()
    transcriber = WhisperTranscriber(model_size="small", device="cpu", compute_type="int8")
    brain = OllamaBrain(model_name="llama3.2")
    speaker = PiperSpeaker()
    
    asyncio.run(main())