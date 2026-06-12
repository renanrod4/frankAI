# Esse script é responsável por transcrever o áudio gravado usando o modelo Whisper, usando o whisper-cli

import os
import asyncio
from faster_whisper import WhisperModel
from core.notifications import disparar_notificacao

class WhisperTranscriber:
    def __init__(self, model_size="tiny", device="cpu", compute_type="int8"):
        # Carrega o modelo de voz na memória RAM para iniciar instantaneamente
        try:
            # int8 e 4 threads fazem o modelo rodar leve e sem travar o computador
            self.model = WhisperModel(
                model_size, 
                device=device, 
                compute_type=compute_type,
                cpu_threads=4
            )
        except Exception as e:
            # Avisa se o modelo der erro ao carregar logo na inicialização do script
            disparar_notificacao(
                "FrankAI - Erro de Inicialização",
                f"Não foi possível carregar o modelo de transcrição: {e}",
                "dialog-error"
            )

    async def transcribe(self, audio_path="/dev/shm/input.wav"):
        # Recebe o áudio da gravação e inicia o processo de conversão para texto
        if not os.path.exists(audio_path):
            # Se o arquivo de áudio não estiver na memória RAM, avisa o usuário e para
            disparar_notificacao(
                "FrankAI - Transcrição",
                "Arquivo de áudio temporário não foi encontrado pelo sistema.",
                "dialog-warning"
            )
            return ""

        try:
            # Roda o processamento em segundo plano para não travar as teclas de atalho
            texto_transcrito = await asyncio.to_thread(self._processar_audio, audio_path)
            return texto_transcrito
        except Exception as e:
            # Avisa caso aconteça algum problema interno na hora de traduzir o áudio
            disparar_notificacao(
                "FrankAI - Falha no Mecanismo",
                f"Ocorreu um erro durante a inferência local: {e}",
                "dialog-error"
            )
            return ""

    def _processar_audio(self, audio_path):
        # Lista de palavras textuais que o assistente deve esperar encontrar no áudio
        palavras_chave = "FrankAI, Firefox, Google , Chrome, Spotify, VS Code, Visual studio code, Discord, terminal, YouTube, GitHub, sudo, execute o comando, abra o, feche a"
        
        # Transcreve o áudio gerado ignorando o silêncio ou barulhos de fundo
        segments, info = self.model.transcribe(
            audio_path, 
            beam_size=1, 
            language="pt",
            vad_filter=True,
            initial_prompt=palavras_chave # Alimenta o modelo com o vocabulário correto antes da inferência
        )
        
        # Junta todos os pedaços de texto encontrados em uma única frase limpa
        return "".join([segment.text for segment in segments]).strip()