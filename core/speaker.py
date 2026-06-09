import asyncio
import os

class PiperSpeaker:
    def __init__(self, model_path="voice/pt_BR-faber-medium.onnx", cli_path="bin/piper"):
        self.model_path = model_path
        self.cli_path = cli_path

    async def speak(self, text):
        if not text:
            return
        try:
            abs_cli_path = os.path.abspath(self.cli_path)
            abs_model_path = os.path.abspath(self.model_path)
            bin_dir = os.path.dirname(abs_cli_path)

            comando_pipe = f"LD_LIBRARY_PATH=. ./piper --model {abs_model_path} --output_file - | aplay -D default"
            
            processo = await asyncio.create_subprocess_shell(
                comando_pipe,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.DEVNULL,
                stderr=asyncio.subprocess.PIPE,
                cwd=bin_dir 
            )
            
            # Envia o texto para o processo do Piper
            _, stderr = await processo.communicate(input=text.encode("utf-8"))
            
            if processo.returncode != 0 and stderr:
                print(f"\n[Erro no Terminal do Speaker]: {stderr.decode('utf-8', errors='ignore')}")
            
        except Exception as e:
            print(f"Erro no módulo de voz: {e}")