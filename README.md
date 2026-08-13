# frankAI

Assistente de voz inteligente executado localmente em Python, projetado para distribuições Linux modernas (como Linux Mint, Ubuntu e Debian). O projeto combina `evdev`, `sounddevice`, `asyncio`, `Whisper` e `Piper` para oferecer uma experiência de Push-to-Talk estável e de baixa latência, com transcrição local em português, processamento de intenção via Ollama e síntese de fala em voz natural, tudo de forma independente do ambiente de desktop utilizado.

---

## Arquitetura e Tecnologias

- **evdev**: Leitura direta dos eventos de input do Kernel do Linux (`/dev/input`), garantindo o funcionamento do atalho global de forma independente do servidor gráfico (X11 ou Wayland) e da interface de usuário (Cinnamon, MATE, GNOME, Xfce).
- **asyncio**: Gerenciamento assíncrono do loop de eventos para monitoramento de hardware e processamento de áudio sem bloqueio de thread.
- **SoundDevice**: Captura de áudio de alta fidelidade integrada ao servidor de som do sistema operacional.
- **PyQt6**: Indicador visual do estado do assistente, mostrando quando ele está ouvindo, pensando ou em erro.
- **Notificações do sistema**: Mensagens de desktop para avisos de erro, início do processamento e confirmação de ações importantes.
- **Git LFS**: Gerenciamento de histórico para os binários de redes neurais (modelos Whisper e Piper).

---

## Requisitos do Sistema

- **Sistema Operacional**: Linux Mint, Ubuntu, Debian ou qualquer distribuição Linux baseada em Debian com suporte ao gerenciador de pacotes APT.
- **Servidor de Áudio**: PipeWire, PulseAudio ou ALSA (`aplay`) ativo no espaço do usuário.
- **Python**: Versão 3.12 ou superior.
- **Serviço de LLM**: Ollama instalado e rodando localmente.

---

## Estrutura de Diretórios Obrigatória

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
├── core/
│   ├── __init__.py
│   ├── brain.py
│   ├── indicator.py
│   ├── listener.py
│   ├── notifications.py
│   ├── recorder.py
│   ├── speaker.py
│   └── transcriber.py
├── voice/
│   ├── pt_BR-faber-medium.onnx
│   └── pt_BR-faber-medium.onnx.json
├── whisper-models/
│   ├── ggml-tiny.bin
│   └── ggml-small.bin
├── piadas.json
├── main.py
├── requirements.txt
├── setup.sh
├── ARCHITECTURE.md
├── comandos.json
├── README.md
└── .gitignore
```

---

## Instalação e Configuração Passo a Passo

### 1. Instalar Dependências do Sistema (APT)

```bash
sudo apt update
sudo apt install git-lfs python3-venv python3-pip python3-dev build-essential alsa-utils xdotool libportaudio2 -y
```

### 2. Clonar o Repositório e Baixar os Modelos

```bash
git clone https://github.com/renanrod4/frankAI.git
cd frankAI
git lfs pull
```

### 3. Configurar as Permissões de Hardware

```bash
chmod +x setup.sh
sudo ./setup.sh
```

> Será necessário reiniciar o computador após a execução do `setup.sh`

### 4. Baixar o Modelo do Ollama

```bash
ollama pull llama3.2
```

### 5. Criar o Ambiente Virtual e Instalar Dependências

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

---

## Como Utilizar

### Execução via Terminal

```bash
python main.py --dev
```

### Atalho do Push-to-Talk

O assistente monitora a combinação **Super + F** no nível do kernel.

1. Mantenha `Super + F` pressionado.
2. Fale o comando.
3. Solte a combinação.
4. O áudio é processado e a resposta é falada ou executada.

### Indicador visual e notificações

A partir da versão atual, o projeto também inclui:

- um indicador visual do status em [core/indicator.py](core/indicator.py), mostrando se o assistente está ouvindo, pensando ou em erro;
- notificações do desktop em [core/notifications.py](core/notifications.py), para avisos e confirmação de processamento.

### Forçar um teclado específico

```bash
python main.py --device /dev/input/by-id/usb-XXXX-event-kbd
```

Ou:

```bash
export FRANKAI_DEVICE=/dev/input/by-id/usb-XXXX-event-kbd
python main.py
```

Se nenhum device for informado, o sistema continua procurando automaticamente.

---

## Observações Importantes

- O grupo `input` é obrigatório para escutar teclados em nível de hardware.
- O Ollama precisa estar ativo em `http://localhost:11434`.
- O Whisper e o Piper dependem de modelos locais presentes em `whisper-models/` e `voice/`.
- O projeto também inclui feedback visual e notificações do sistema para uso em sessão real.
- Se o teclado mudar entre máquinas, use `--device` para garantir o dispositivo correto.

---

## Solução de Problemas

Se o atalho não disparar, verifique:

```bash
ls -l /dev/input/by-id /dev/input/by-path
```

E confirme se:

- o usuário está no grupo `input`;
- a sessão foi reiniciada após a execução do `setup.sh`;
- o atalho `Super + F` não está sendo usado por outro programa do sistema;
- o dispositivo correto foi selecionado com `--device` ou `FRANKAI_DEVICE` em máquinas com mais de um teclado.

O sistema prioriza dispositivos em `/dev/input/by-id` e `/dev/input/by-path`, o que reduz falhas entre ambientes Linux diferentes.

---
## Equipe

A construção do FrankAI contou com a colaboração de estudantes e do professor orientador, reunindo trabalho de desenvolvimento, prototipagem e validação em hardware real.

- [Renan Rodrigues](https://github.com/renanrod4/)
- [Pedro Henrique](https://github.com/percels)
- [Gabriel Madureira](https://github.com/geargabs)
- Professor [Trovão](https://www.linkedin.com/in/luizjs/)

## Licença e Observações

Este projeto foi desenvolvido como uma solução de IA local para Linux, inspirada na ideia de um computador de baixo custo e em contexto acadêmico e de prototipagem. A base da ideia nasceu a partir da visão do professor [Trovão](https://www.linkedin.com/in/luizjs/), que propôs a construção de um sistema autônomo, offline e acessível, com foco em privacidade, baixo consumo de recursos e execução em hardware modesto.

### Por que Python?

A escolha de Python foi motivada principalmente pelo prazo extremamente apertado do desafio: em apenas **7 dias**, era preciso transformar uma ideia ambiciosa em uma prova de conceito funcional, com integração de áudio, transcrição, processamento local e síntese de voz. Nesse cenário, Python foi uma decisão estratégica porque oferece uma enorme variedade de bibliotecas nativas e ecosistemas maduros para automação, processamento de áudio e interação com sistemas Linux.

Além disso, a linguagem permitiu prototipar rapidamente o fluxo completo do projeto, conectar ferramentas como `evdev`, `sounddevice`, `Ollama`, `Whisper` e `Piper`, e iterar em tempo real sem perder produtividade. Em um desafio de curto prazo, essa agilidade foi essencial para validar a ideia antes do prazo de apresentação.

### História

O FrankAI surgiu a partir de um projeto maior chamado FRANK: um computador montado com peças doadas por alunos e colaboradores do professor [Trovão](https://www.linkedin.com/in/luizjs/), peça por peça. A proposta era simples, mas desafiadora: criar uma IA offline que funcionasse como uma assistente doméstica local, rodando em um PC com 8 GB de RAM e processador de terceira geração.

Esse desafio exigiu uma arquitetura eficiente e decisões de engenharia bem específicas para reduzir custo computacional sem perder a funcionalidade principal.

### Objetivo

- Criar uma IA local que funcione como uma "Alexa" para comandos no computador;
- Rodar esse sistema no FRANK sem depender de nuvem;
- Maximizar velocidade e eficiência no uso de memória e CPU;
- Entregar uma prova de conceito funcional em apenas **7 dias** para apresentação no [SEBRAE](https://sebrae.com.br/).

### Estratégia

Como a RAM do FRANK era limitada a 8 GB, não era viável executar todas as etapas de processamento em paralelo, como se faz em arquiteturas mais pesadas. Por isso, a solução foi dividida em três blocos distintos:

- **Escuta**: captura do áudio e ativação por atalho do teclado;
- **Pensamento**: processamento do texto em um modelo local via `Ollama`;
- **Fala**: síntese de resposta com `Piper`.

Além disso, a transcrição foi feita com `Whisper-cli`, que trabalha em modo local e reduz a dependência de serviços externos. Como o Ollama em versões maiores consumia uma quantidade relevante de memória, foi necessário otimizar a carga de trabalho e utilizar modelos mais enxutos sempre que possível.

### Modelos utilizados

O projeto combina ferramentas e modelos locais para manter a operação offline e acessível:

- **Whisper**: modelo de transcrição em português, usado pela pasta `whisper-models/`;
    - `whisper-models/ggml-small.bin` — modelo principal configurado no projeto;
    - `whisper-models/ggml-tiny.bin` — alternativa mais leve para testes ou ambientes com menor capacidade.
- **Piper**: modelo de síntese de voz em português;
    - `voice/pt_BR-faber-medium.onnx` — voz principal do assistente;
    - `voice/pt_BR-faber-medium.onnx.json` — metadados do modelo.
- **Ollama**: runtime de modelos locais, com o modelo `llama3.2` utilizado para raciocínio e geração de resposta textual.
- **Binários nativos**: `bin/whisper-cli` e `bin/piper`, usados para executar a transcrição e a fala sem depender de serviços em nuvem.

### Observações finais

A ideia central do projeto era equilibrar **privacidade**, **desempenho** e **baixo consumo de recursos**. Em vez de depender de APIs externas, o FrankAI tenta resolver a maior parte do processamento diretamente no computador, o que torna o sistema mais rápido, mais discreto e mais apropriado para ambientes locais e de prova de conceito.

Em resumo, o projeto busca demonstrar que é possível criar uma experiência de assistente de voz funcional em hardware modesto, com modelos locais, boa eficiência e baixa latência.
