# frankAI

Assistente de voz inteligente executado localmente, projetado para distribuições Linux modernas (como Linux Mint, Ubuntu e Debian). O projeto utiliza captura direta de hardware para fornecer uma experiência de Push-to-Talk estável e de baixa latência, integrando modelos locais de transcrição e síntese de voz de forma independente do ambiente de desktop utilizado.

---

## Requisitos do Sistema

* **Sistema Operacional**: Linux Mint, Ubuntu, Debian ou qualquer distribuição Linux baseada em Debian com suporte ao gerenciador de pacotes APT.
* **Servidor de Áudio**: PipeWire, PulseAudio ou ALSA (`aplay`) ativo no espaço do usuário.
* **Python**: Versão 3.12 ou superior.
* **Serviço de LLM**: Ollama instalado e rodando localmente.

---

## Arquitetura e Tecnologias

* **evdev**: Leitura direta dos eventos de input do Kernel do Linux (`/dev/input`), garantindo o funcionamento do atalho global de forma independente do servidor gráfico (X11 ou Wayland) e da interface de usuário (Cinnamon, MATE, GNOME, Xfce).
* **asyncio**: Gerenciamento assíncrono do loop de eventos para monitoramento de hardware e processamento de áudio sem bloqueio de thread.
* **SoundDevice**: Captura de áudio de alta fidelidade integrada ao servidor de som do sistema operacional.
* **Git LFS**: Gerenciamento de histórico para os binários de redes neurais (modelos Whisper e Piper).

---

## Estrutura de Diretórios Obrigatória

Para que o motor de voz (Piper), o transcritor (Whisper) e o módulo de piadas locais funcionem de forma integrada, o projeto deve seguir estritamente o layout abaixo após o download dos assets:

```text
frankAI/
├── bin/
│   ├── espeak-ng-data/
│   ├── libespeak-ng.so
│   ├── libespeak-ng.so.1
│   ├── libespeak-ng.so.1.52.0.1
│   ├── libonnxruntime.so
│   ├── libonnxruntime.so.1.14.1
│   ├── libpiper_phonemize.so
│   ├── libpiper_phonemize.so.1
│   ├── libpiper_phonemize.so.1.2.0
│   ├── piper
│   └── whisper-cli
├── voice/
│   ├── pt_BR-faber-medium.onnx
│   └── pt_BR-faber-medium.onnx.json
├── whisper-models/
│   ├── ggml-tiny.bin
│   └── ggml-small.bin
├── piadas.json
├── main.py
└── requirements.txt
```

> **Atenção:** Certifique-se de que os arquivos reais das bibliotecas dinâmicas (`.so`) foram copiados para a pasta `bin`. Links simbólicos quebrados impedirão a execução do módulo de fala.

---

## Instalação e Configuração Passo a Passo

### 1. Instalar Dependências do Sistema (APT)
Este projeto compila extensões em C (evdev) e interage com as APIs de som do sistema. Instale as ferramentas de compilação e bibliotecas necessárias rodando:

```bash
sudo apt update
sudo apt install git-lfs python3-venv python3-pip python3-dev build-essential alsa-utils xdotool libportaudio2 -y
```

Após a instalação do pacote, ative o Git LFS na sua conta de usuário global:

```bash
git lfs install
```

### 2. Clonar o Repositório e Baixar os Modelos
Com o Git LFS devidamente ativo, clone o repositório. O processo fará o download automático dos binários pesados de IA:

```bash
git clone https://github.com/renanrod4/frankAI.git
cd frankAI
```

Para garantir que nenhum modelo veio corrompido ou apenas como ponteiro de texto, force a sincronização dos blocos de dados:

```bash
git lfs pull
```

### 3. Configurar as Permissões de Hardware (Kernel)
Por padrão, o Linux bloqueia o acesso de usuários comuns aos dispositivos de entrada. Para que o software capture o atalho do teclado sem precisar de privilégios de root, execute o script de automação:

```bash
chmod +x setup.sh
sudo ./setup.sh
```

> **Aviso obrigatório sobre o Kernel:** O Linux só atualiza os grupos de permissão do usuário durante o processo de login. Para que o terminal ganhe acesso ao teclado através do grupo input, você deve encerrar a sua sessão atual (fazer Logoff) e entrar novamente, ou reiniciar o computador.

### 4. Baixar o Modelo do Ollama
Certifique-se de que o serviço do Ollama está ativo e baixe o modelo de linguagem padrão utilizado pelo cérebro do assistente:

```bash
ollama pull llama3.2
```

### 5. Criar o Ambiente Virtual Python e Instalar Dependências
Após reiniciar ou refazer o login, abra o terminal na pasta do projeto e configure o ambiente isolado do Python:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

---

## Como Utilizar

### Execução via Terminal
Com o ambiente virtual ativado, inicie o assistente em modo de escuta ativa. A flag `--dev` exibirá os payloads JSON gerados e a interceptação de intenções locais:

```bash
python3 main.py --dev
```

### Mecânica do Atalho (Push-to-Talk)
O assistente monitora a combinação de teclas **Super + F** (Tecla Windows + F) diretamente no nível de hardware do Kernel.

1. Vá até as configurações de atalhos de teclado nativos do seu sistema (Cinnamon, MATE ou GNOME) e certifique-se de que a combinação Super + F não está sendo usada por nenhuma função padrão (como abrir o gerenciador de arquivos).
2. Com o script rodando no terminal, mantenha as teclas **Super + F** pressionadas no teclado.
3. Fale o seu comando enquanto segura as teclas.
4. Solte as teclas para encerrar a captura. O áudio será automaticamente processado e enviado para a pipeline de inferência local.

---

## Solução de Problemas de Permissão

Se ao executar o script você receber um erro