# Esse script é responsável por processar as mensagens de texto transcritas e envia-las para o modelo Ollama

import asyncio
import json
import urllib.request
import platform
from datetime import date
import os
from collections import deque
import random

class OllamaBrain:
    def __init__(self, model_name="llama3.2", api_url="http://localhost:11434/api/generate"):
        self.model_name = model_name
        self.api_url = api_url
        self.history = deque(maxlen=20)
        
        # Define o caminho para o arquivo piadas.json na raiz do projeto
        self.piadas_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "piadas.json"))
        self.wordlist_piadas = self._load_piadas()

    def _load_piadas(self):
        try:
            with open(self.piadas_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"Aviso: Não foi possível carregar o arquivo de piadas ({e}). Usando fallback.")
            return [{
                "pergunta": "Por que o computador foi ao médico?",
                "resposta": "Porque ele estava com vírus."
            }]

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
            f"Você é o frankAI, um assistente de voz integrado"
            f"Contexto do ambiente: {contexto_sistema}. "
            "Você deve responder SEMPRE no formato JSON abaixo, sem qualquer outro texto complementar:\n"
            "{\n"
            '  "fala": "Uma frase direta e casual em português para responder a pergunta do usuário",\n'
            '  "comando": "Um comando bash para executar no terminal se o usuário pediu uma ação (ex: google-chrome), ou string vazia caso não seja um pedido de comando",\n'
            "}\n\n"
            "Tabela de mapeamento para comandos do Linux Mint (use estes binários exatos):\n"
            "- 'google chrome' ou 'chrome' -> google-chrome\n"
            "- 'Brave' -> brave-browser\n"
            "- 'firefox' ou 'navegador internet' -> firefox\n"
            "  * 'abrir site do google' -> xdg-open https://google.com\n"
            "- 'calculadora' -> gnome-calculator\n"
            "  * 'abrir pasta home' ou 'meus arquivos' -> xdg-open ~\n"
            "- 'terminal' -> gnome-terminal\n"
            "- 'cria pasta' -> mkdir\n\n"
            "- considere como 'home' o /home/{nome do usário que você tem acesso} ou simplesmente use o atalho ~ para se referir a esta pasta. Exemplo: 'abra a pasta de downloads' -> 'xdg-open ~/Downloads'\n"
            "Se o comando exigir interface gráfica (como abrir a pasta ou calculadora), "
            "apenas envie o binário correspondente no campo 'comando' sem o caractere '&'."
            "Responda comandos sempre no gerúndio, EXEMPLO: 'abrindo o google chrome' ou 'abrindo a calculadora', nunca 'abri o google chrome' ou 'abri a calculadora'."
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
            "options": {
                "temperature": 0.1
            }
        }
        
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            self.api_url, 
            data=data, 
            headers={"Content-Type": "application/json"}
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
            return {
                "fala": f"Erro de comunicação com o cérebro: {e}",
                "comando": ""
            }

    async def ask(self, prompt):
        if not prompt:
            return ""

        # Caso 1: Verifica se a última interação foi uma piada e o usuário está pedindo a punchline
        if self.history:
            ultima_interacao = self.history[-1]
            if ultima_interacao.get("role") == "Assistente" and "punchline" in ultima_interacao:
                resposta_final = ultima_interacao["punchline"]
                resposta_mock = {"fala": resposta_final, "comando": ""}
                
                # Atualiza o histórico para incluir a punchline como parte da resposta do assistente
                self.history.append({"role": "Usuário", "content": prompt})
                self.history.append({"role": "Assistente", "content": json.dumps(resposta_mock)})
                return resposta_mock

        # Caso 2: Usuário pede uma nova piada
        prompt_normalizado = prompt.lower()
        if "piada" in prompt_normalizado or "conte uma piada" in prompt_normalizado:
            joke = random.choice(self.wordlist_piadas)
            resposta_mock = {"fala": joke["pergunta"], "comando": ""}
            
            
            self.history.append({"role": "Usuário", "content": prompt})
            self.history.append({
                "role": "Assistente", 
                "content": json.dumps(resposta_mock), 
                "punchline": joke["resposta"]
            })
            
            return resposta_mock

        return await asyncio.to_thread(self._send_request, prompt)