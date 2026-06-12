import asyncio
import os
from core.notifications import disparar_notificacao


class PiperSpeaker:
    def __init__(
        self, model_path="voice/pt_BR-faber-medium.onnx", cli_path="bin/piper"
    ):
        self.model_path = model_path
        self.cli_path = cli_path

    async def speak(self, text):
        if not text:
            return
        try:
            abs_cli_path = os.path.abspath(self.cli_path)
            abs_model_path = os.path.abspath(self.model_path)
            bin_dir = os.path.dirname(abs_cli_path)

            # Injeta 0.4s de silêncio real (8820 samples de 2 bytes a 22050Hz) antes do áudio bruto do Piper
            # Para evitar cortes no início da fala
            comando_pipe = f"(dd if=/dev/zero bs=2 count=8820 2>/dev/null && LD_LIBRARY_PATH=. ./piper --model {abs_model_path} --output_raw) | aplay -t raw -f S16_LE -r 22050 -c 1 -D default"

            processo = await asyncio.create_subprocess_shell(
                comando_pipe,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.DEVNULL,
                stderr=asyncio.subprocess.PIPE,
                cwd=bin_dir,
            )

            # Envia o texto para o processo do Piper
            _, stderr = await processo.communicate(input=text.encode("utf-8"))

            if processo.returncode != 0 and stderr:
                print(
                    f"\n[Erro no Terminal do Speaker]: {stderr.decode('utf-8', errors='ignore')}"
                )
                disparar_notificacao(
                    titulo="FrankAI: Erro na Voz",
                    mensagem="Ocorreu uma falha no terminal ao tentar reproduzir o áudio.",
                    icone="dialog-error",
                )

        except Exception as e:
            print(f"Erro no módulo de voz: {e}")
