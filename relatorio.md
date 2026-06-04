# Relatório Técnico de Especificação: Orquestrador do Assistente de Voz Local (v2.0)

Este documento estabelece os requisitos lógicos, o fluxo de controle e a arquitetura de execução para o script Python responsável por unificar o Whisper.cpp, o Ollama e o Piper TTS em um sistema funcional de Push-to-Talk (Pressione para Falar) no Ubuntu, garantindo total portabilidade entre ambientes X11 e Wayland sem a necessidade de privilégios de superusuário (root).

---

## 1. Arquitetura Geral e Dependências do Sistema

O script atuará como um gerenciador de processos assíncronos e orientados a eventos. Para garantir o isolamento do ambiente operacional e evitar conflitos com o ecossistema Python do Ubuntu (conforme diretrizes do PEP 668), a execução deve ocorrer estritamente dentro de um ambiente virtual (`.venv`).

### Dependências Principais do Ambiente Virtual
* **sounddevice & soundfile:** Captura nativa do fluxo de áudio do microfone e gravação direta em disco.
* **numpy:** Manipulação matemática dos buffers de áudio estruturados em matrizes.
* **jeepney / dbus-next:** Conexão de baixo nível com o barramento de mensagens do sistema (D-Bus) para comunicação com o ecossistema Linux.
* **requests:** Comunicação via HTTP REST com a API local do Ollama.

### Definições de Formato de Áudio e Rotas
* **Formato de Entrada Escrito:** O modelo Whisper.cpp exige estritamente o formato WAV, taxa de amostragem de 16000 Hz, codificação PCM de 16 bits (Little Endian) e canal Mono. O fluxo de gravação deve persistir os dados diretamente sob estas especificações em `/tmp/input_mic.wav` para evitar overhead de conversão de arquivos compactados (como MP3).
* **Endpoints:** Integração de chamadas síncronas para o gateway local do Ollama no endereço `http://localhost:11434/api/generate`.

---

## 2. Mecanismo de Captura: Integração via XDG Desktop Portal (D-Bus)

Para mitigar as restrições de segurança nativas do Wayland (que bloqueiam a captura global de teclado por bibliotecas tradicionais de espionagem de input como o `pynput`), a arquitetura adota a API oficial de atalhos globais do ecossistema Linux desktop.

```
[Script Python (frankAI)] <--- D-Bus (Jeepney) ---> [XDG Desktop Portal] <---> [Compositor Wayland / GNOME]
```

### Protocolo de Inicialização e Registro
1. **Conexão ao Barramento de Sessão:** O script abre um canal de comunicação no Session Bus apontando para o serviço `org.freedesktop.portal.Desktop` e o objeto `/org/freedesktop/portal/desktop`.
2. **Criação de Sessão:** Invoca o método `CreateSession` na interface `org.freedesktop.portal.GlobalShortcuts` para obter um descritor exclusivo de sessão controlado pelo ciclo de vida do script.
3. **Vinculação de Atalho (BindShortcuts):** Envia uma requisição contendo o identificador do gatilho (`"captura_voz"`) e a descrição textual que será indexada pelo sistema operacional.
4. **Consentimento de Segurança:** Na primeira execução, o sistema operacional intercepta a chamada e exibe um prompt nativo solicitando a autorização do usuário para o mapeamento do atalho (ex: Super + F). Uma vez concedido, o vínculo passa a ser gerenciado pelo próprio compositor de janelas do Ubuntu.

### Lógica de Captura Orientada a Sinais (Signals)
O loop principal do Python passa a operar de forma reativa, escutando o sinal `Activated` emitido pela interface de atalhos do D-Bus.

* **Sinal de Ativação (Pressionado):** Ao detectar o disparo inicial do sinal correspondente ao ID `"captura_voz"` com a flag de ativação ativa, o script altera seu estado interno para gravando e inicia a alimentação assíncrona do buffer de áudio.
* **Sinal de Liberação (Solto):** Ao detectar o término do evento de ativação, o script encerra imediatamente o fluxo de captura de áudio do microfone, fecha o arquivo WAV em disco e dispara sequencialmente a pipeline de processamento (transcrição e cognição).

---

## 3. Detalhes dos Módulos do Pipeline

Após os gatilhos disparados via D-Bus, o ciclo de processamento executa de forma linear e síncrona nos módulos de inteligência, mantendo a assincronia apenas nos módulos de hardware (áudio e subprocessos do sistema).

### Módulo 1: Captura de Áudio (sounddevice)
A gravação de áudio elimina o uso de utilitários externos do sistema (como `arecord`), centralizando o controle dentro do runtime do Python.
* **Execução:** O fluxo abre um `InputStream` assíncrono configurado nas especificações exatas do Whisper (16kHz, Mono).
* **Bufferização:** Os blocos de áudio gerados pelo hardware são acumulados na memória RAM como estruturas NumPy e gravados continuamente em disco através da biblioteca `soundfile` dentro do callback de áudio.
* **Interrupção:** O fechamento do stream ocorre de forma segura imediatamente após a notificação de subida da tecla mapeada via sinal D-Bus.

### Módulo 2: Transcrição Local (Whisper.cpp)
* **Processamento:** Invocação do executável binário `whisper-cli` via subprocesso síncrono.
* **Parâmetros:** Passagem do arquivo gerado em `/tmp`, especificação do modelo quantizado `ggml-tiny.bin` para otimização de CPU, inibição de logs (`-np`), ocultação de carimbos de tempo (`-nt`) e definição estrita do idioma com `-l pt`.
* **Retorno:** Captura do descritor de saída padrão (`stdout`) purificado, contendo apenas a string de texto transcrita.

### Módulo 3: Cognição e Filtro de Intenções (Ollama)
* **Payload:** Envio do texto transcrito estruturado em formato JSON para o modelo local Llama 3.2 1B.
* **System Prompt:** Instrução estrita para o modelo atuar de forma concisa e atuar como um classificador secundário de comandos. Caso a intenção do usuário envolva abrir utilitários do sistema, o modelo deve injetar marcações padronizadas na resposta (ex: `[EXEC:CHROME]`).
* **Tratamento de String:** O script intercepta a resposta textual, isola o texto limpo destinado à síntese de voz e extrai as tags de execução do sistema operacional através de expressões regulares ou busca direta de padrões.

### Módulo 4: Execução de Comandos do Sistema
* **Condicional de Ação:** Caso uma tag válida (como `[EXEC:CHROME]`) seja extraída do Módulo 3, o script executa uma chamada de subprocesso do sistema operacional.
* **Desacoplamento:** A chamada para inicializar o binário do aplicativo (ex: `google-chrome`) deve usar o método de criação de processo destacado (`subprocess.Popen`), impedindo que o script principal do assistente congele aguardando o fechamento da janela do navegador do usuário.

### Módulo 5: Síntese de Voz (Piper TTS)
* **Geração:** O texto limpo (isento das tags de comando) é redirecionado via pipeline de entrada (`stdin`) para o binário local do `piper`.
* **Reprodução:** O Piper processa o texto utilizando seu modelo de voz ONNX optimizado localmente e gera o áudio resultante em `/tmp/output_voice.wav`, que é reproduzido imediatamente pelo sistema de áudio através de comandos de baixo nível ou bibliotecas de áudio nativas.

---

## 4. Tratamento de Exceções e Resiliência

* **Validação de String Nula:** Caso a saída capturada do Whisper.cpp contenha strings inferiores a 3 caracteres ou strings compostas apenas por ruído/pontuação, o pipeline de requisições HTTP para o Ollama deve ser abortado sumariamente para preservar ciclos de processamento de CPU.
* **Verificação de Barramento:** O script deve validar a presença ativa da interface `org.freedesktop.portal.Desktop` no D-Bus antes de iniciar a rotina do assistente. Se o portal não estiver acessível, o script deve gerar uma saída de erro explicativa e abortar a execução.
* **Persistência de Sessão:** O descritor da sessão de atalhos gerado na inicialização deve ser encerrado explicitamente através de blocos `try/finally` ou gerenciadores de contexto para evitar o vazamento de registros fantasma no barramento do sistema operacional após o encerramento do script.