# Esse script é responsável por transcrever o áudio gravado usando o modelo Whisper, usando o whisper-cli
import asyncio
import os

class WhisperTranscriber:
    def __init__(self, model_path="whisper-models/ggml-tiny.bin", cli_path="bin/whisper-cli",language="pt"):
        self.model_path = model_path
        self.cli_path = cli_path
        self.language = language

        if not os.path.exists(self.cli_path):
            raise FileNotFoundError(f"Binário do Whisper não encontrado em {self.cli_path}")
        if not os.path.exists(self.model_path):
            raise FileNotFoundError(f"Modelo do Whisper não encontrado em {self.model_path}")

    async def transcribe(self, audio_path):
        if not audio_path or not os.path.exists(audio_path):
            return ""
        cmd = [
            self.cli_path,
            "-m", self.model_path,
            "-f", audio_path,
            "-l", self.language,
            "-nt"
        ]

        try:
            # chama o whisper-cli
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()

            if process.returncode != 0:
                print(f"[Transcriber] Erro na execução do Whisper: {stderr.decode().strip()}")
                return ""
            text_output = stdout.decode("utf-8").strip()
            
            # O whisper-cli às vezes retorna mensagens entre colchetes quando não consegue transcrever nada, então vamos filtrar isso
            if text_output.startswith("[") and text_output.endswith("]"):
                return ""

            return text_output

        except Exception as e:
            print(f"[Transcriber] falha GIGANTOSSAURICA no subprocesso: {e}")
            return ""