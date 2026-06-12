import asyncio
import json
import urllib.request
import platform
from datetime import date
import os
from collections import deque
import random
from core.notifications import disparar_notificacao


class OllamaBrain:
    def __init__(
        self, model_name="llama3.2", api_url="http://localhost:11434/api/generate"
    ):
        self.model_name = model_name
        self.api_url = api_url
        self.history = deque(maxlen=20)

        # Define o caminho para o arquivo piadas.json na raiz do projeto
        self.piadas_path = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "..", "piadas.json")
        )
        self.wordlist_piadas = self._load_piadas()

    def _load_piadas(self):
        try:
            with open(self.piadas_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(
                f"Aviso: Não foi possível carregar o arquivo de piadas ({e}). Usando fallback."
            )
            return [
                {
                    "pergunta": "Por que o computador foi ao médico?",
                    "resposta": "Porque ele estava com vírus.",
                }
            ]

    def _get_system_info(self):
        try:
            import os

            usuario = os.getlogin()
        except Exception:
            usuario = "usuario"

        info_pc = f"{platform.system()} {platform.release()} {platform.machine()}"
        data_atual = date.today().isoformat()

        return f"Data atual: {data_atual}, Info do PC: {info_pc}, Usuário logado: {usuario}"

    def _send_request(self, prompt):
        contexto_sistema = self._get_system_info()

        system_context = (
            f"Você é o frankAI, um assistente de voz inteligente integrado ao sistema Linux.\n"
            f"Contexto atual do sistema: {contexto_sistema}.\n\n"
            "Sua principal função é traduzir a intenção de voz do usuário em ações diretas no terminal. "
            "Você deve responder SEMPRE no formato JSON abaixo, sem qualquer outro texto complementar:\n"
            "{\n"
            "  \"fala\": \"Uma frase direta e casual em português para responder ao usuário (ex: 'Abrindo o Chrome...' ou 'Reiniciando o sistema agora...')\",\n"
            '  "comando": "O comando Bash válido para executar a action solicitada, ou string vazia "" se for apenas uma conversa/pergunta sem pedido de ação"\n'
            "}\n\n"
            "REGRAS DE AUTONOMIA E GERAÇÃO DE COMANDOS:\n"
            "1. Não se limite à tabela abaixo. Você tem total autonomia para usar QUALQUER comando Bash nativo do Linux para atender ao pedido do usuário (ex: se o usuário pedir para reiniciar, use 'reboot'; se pedir para desligar, use 'poweroff').\n"
            "2. Se o usuário pedir para abrir um programa que não está na tabela, use o seu conhecimento de Linux para deduzir o binário correto (ex: 'libreoffice', 'vlc', 'spotify').\n"
            "3. Se o comando exigir interface gráfica, envie apenas o binário correspondente no campo 'comando' sem o caractere '&'.\n"
            "4. Considere como 'home' o diretório ~ para se referir à pasta do usuário (ex: 'abra a pasta de downloads' -> 'xdg-open ~/Downloads').\n\n"
            "TABELA DE PREFERÊNCIAS (Diretrizes para mapeamentos comuns):\n"
            "- 'google chrome' ou 'chrome' -> google-chrome\n"
            "- 'Brave' -> brave-browser\n"
            "- 'firefox' ou 'navegador internet' -> firefox\n"
            "- 'abrir site do google' -> xdg-open https://google.com\n"
            "- 'calculadora' -> gnome-calculator\n"
            "- 'abrir pasta home' ou 'meus arquivos' -> xdg-open ~\n"
            "- 'terminal' -> x-terminal-emulator\n"
            "- 'cria pasta [nome]' -> mkdir [nome]\n"
        )

        historico_txt = ""
        for interacao in self.history:
            historico_txt += f"{interacao['role']}: {interacao['content']}\n"

        payload = {
            "model": self.model_name,
            "prompt": f"{system_context}\n\n{historico_txt}Usuário: {prompt}\nAssistente:",
            "stream": False,
            "format": "json",
            "keep_alive": -1,
            "options": {"temperature": 0.1},
        }

        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            self.api_url, data=data, headers={"Content-Type": "application/json"}
        )

        try:
            with urllib.request.urlopen(req, timeout=65) as response:
                res_body = response.read().decode("utf-8")
                res_json = json.loads(res_body)
                raw_response = res_json.get("response", "").strip()

                self.history.append({"role": "Usuário", "content": prompt})
                self.history.append({"role": "Assistente", "content": raw_response})

                return json.loads(raw_response)
        except Exception as e:
            if isinstance(e, TimeoutError) or "timeout" in str(e).lower():
                disparar_notificacao(
                    titulo="FRANK AI DEMOROU MUITO PARA RESPONDER",
                    mensagem="Tempo limite atingido, comando cancelado",
                    icone="dialog-warning",
                )
            else:
                disparar_notificacao(
                    titulo="FRANK AI: ERRO DE CONEXÃO",
                    mensagem="O serviço do Ollama está offline ou inacessível no momento",
                    icone="dialog-error",
                )
            return {"fala": "", "comando": ""}

    async def ask(self, prompt):
        if not prompt:
            return ""

        # Caso 1: Verifica se a última interação foi uma piada e o usuário está pedindo a punchline
        if self.history:
            ultima_interacao = self.history[-1]
            if (
                ultima_interacao.get("role") == "Assistente"
                and "punchline" in ultima_interacao
            ):
                resposta_final = ultima_interacao["punchline"]
                resposta_mock = {"fala": resposta_final, "comando": ""}

                # Atualiza o histórico para incluir a punchline como parte da resposta do assistente
                self.history.append({"role": "Usuário", "content": prompt})
                self.history.append(
                    {"role": "Assistente", "content": json.dumps(resposta_mock)}
                )
                return resposta_mock

        # Caso 2: Usuário pede uma nova piada
        prompt_normalizado = prompt.lower()
        if "piada" in prompt_normalizado or "conte uma piada" in prompt_normalizado:
            joke = random.choice(self.wordlist_piadas)
            resposta_mock = {"fala": joke["pergunta"], "comando": ""}

            self.history.append({"role": "Usuário", "content": prompt})
            self.history.append(
                {
                    "role": "Assistente",
                    "content": json.dumps(resposta_mock),
                    "punchline": joke["resposta"],
                }
            )

            return resposta_mock

        return await asyncio.to_thread(self._send_request, prompt)
