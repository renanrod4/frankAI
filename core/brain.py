# Esse script é responsável por processar as mensagens de texto transcritas e envia-las para o modelo Ollama

import asyncio
import json
import urllib.request
import platform
from datetime import date
import os
class OllamaBrain:
    def __init__(self, model_name="llama3.2", api_url="http://localhost:11434/api/generate"):
        self.model_name = model_name
        self.api_url = api_url
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
            "- considere como 'home' o /home/{nome do usário que você tem acesso} ou simplemente use o atalho ~ para se referir a esta pasta. Exemplo: 'abra a pasta de downloads' -> 'xdg-open ~/Downloads'\n"
            "Se o comando exigir interface gráfica (como abrir a pasta ou calculadora), "
            "apenas envie o binário correspondente no campo 'comando' sem o caractere '&'."
            "Responda comandos sempre no gerúndio, EXEMPLO: 'abrindo o google chrome' ou 'abrindo a calculadora', nunca 'abri o google chrome' ou 'abri a calculadora'."
        )
        
        payload = {
            "model": self.model_name,
            "prompt": f"{system_context}\n\nUsuário: {prompt}\nAssistente:",
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
            # Ollama pode demorar um pouco para responder, especialmente se o modelo for grande ou se o prompt for complexo. Por isso, o timeout de 65 segundos
            with urllib.request.urlopen(req, timeout=65) as response:
                res_body = response.read().decode("utf-8")
                res_json = json.loads(res_body)
                raw_response = res_json.get("response", "").strip()
                
                # Converte a string JSON do Llama em um dicionário Python funcional
                return json.loads(raw_response)
        except Exception as e:
            return {
                "fala": f"Erro de comunicação com o cérebro: {e}",
                "comando": ""
            }
    async def ask(self, prompt):
        if not prompt:
            return ""

        return await asyncio.to_thread(self._send_request, prompt)