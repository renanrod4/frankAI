# frankAI explicado de um jeito simples

Esse projeto é um assistente de voz local para Linux. A ideia é simples: você segura um atalho do teclado, fala alguma coisa, o programa grava o áudio, transcreve com Whisper, manda o texto para o Ollama pensar, e depois responde com voz usando Piper. Se o modelo entender que o usuário quer abrir algo no sistema, ele também pode devolver um comando para rodar no terminal.

## Como o fluxo funciona

1. O programa começa em [main.py](main.py).
2. Ele tenta identificar o teclado correto com o módulo de [core/listener.py](core/listener.py).
3. Quando detecta o atalho Super + F, chama o gravador de áudio em [core/recorder.py](core/recorder.py).
4. Quando a tecla é solta, o áudio salvo em `samples/input.wav` vai para a transcrição em [core/transcriber.py](core/transcriber.py).
5. O texto transcrito segue para o cérebro do assistente em [core/brain.py](core/brain.py), que conversa com o Ollama.
6. Se vier uma resposta falada, o Piper em [core/speaker.py](core/speaker.py) lê isso em voz alta.
7. Se vier um comando, o [main.py](main.py) roda esse comando no Linux em segundo plano.

A diferença importante da versão atual é que a detecção do teclado não depende só de um nome genérico. Ele prioriza dispositivos em `/dev/input/by-id` e `/dev/input/by-path`, e ainda aceita um caminho fixo via `--device` ou `FRANKAI_DEVICE`, o que reduz muito os erros em máquinas diferentes

## O que cada arquivo faz

### [main.py](main.py)

É o ponto de entrada do projeto. Aqui fica a ligação de tudo: cria o gravador, o transcritor, o cérebro e o falador. Também trata a flag `--dev`, que mostra o JSON bruto vindo do Ollama.

A partir da versão atual, o código também aceita:

- `--device`: caminho explícito do teclado em `/dev/input/...`
- `FRANKAI_DEVICE`: mesma funcionalidade via variável de ambiente

Funções importantes:

- `iniciar_gravacao()`: desliga o eco do terminal e começa a captura de áudio.
- `parar_gravacao()`: encerra a gravação, transcreve o áudio, manda o texto para o cérebro, fala a resposta e executa comando se existir.
- `executar_comando_linux()`: dispara comandos via shell, sempre tentando deixar em segundo plano com `&`.

### [core/listener.py](core/listener.py)

Esse arquivo cuida da escuta do teclado no nível do sistema. Ele usa `evdev` para ler eventos diretamente de `/dev/input`, sem depender do ambiente gráfico.

Na prática, ele agora:

- procura primeiro dispositivos mais estáveis em `/dev/input/by-id` e `/dev/input/by-path`
- verifica se o device tem as teclas necessárias (`F` e `Super/Windows`)
- aceita um `device_path` explícito para forçar o teclado correto
- mantém o comportamento de busca automática caso o usuário não informe nada

Ou seja, ele deixa de depender só do nome do hardware e passa a escolher de forma bem mais robusta entre ambientes diferentes.

### [core/recorder.py](core/recorder.py)

É o gravador de áudio. Ele abre um stream com `sounddevice`, recebe os blocos de som pelo callback e junta tudo numa fila até a gravação terminar.

Quando para, ele monta um WAV com `wave`, salva em `samples/input.wav` e devolve o caminho do arquivo para a próxima etapa da pipeline.

### [core/transcriber.py](core/transcriber.py)

Esse módulo chama o binário `whisper-cli` para transformar o áudio em texto.

Ele verifica se o modelo e o binário existem, monta a linha de comando com idioma `pt`, executa o processo e filtra respostas vazias ou retornos que o Whisper às vezes devolve quando não entendeu nada.

### [core/brain.py](core/brain.py)

Esse é o cérebro de verdade do projeto. Ele conversa com o Ollama local, usa o modelo `llama3.2` e tenta devolver sempre um JSON com dois campos:

- `fala`: o que o assistente vai dizer.
- `comando`: um comando de shell, se fizer sentido executar alguma ação.

Ele também puxa algumas informações do sistema, como data atual, sistema operacional e usuário logado, para montar contexto.

Tem mais duas regras interessantes aqui:

- Se o usuário pedir piada, ele pode responder usando o conteúdo de [piadas.json](piadas.json).
- Ele mantém um histórico curto das últimas interações, para ele manter um contexto ao falar com o usuário

### [core/speaker.py](core/speaker.py)

Esse módulo transforma texto em voz usando o Piper.

Ele chama o binário em [bin/piper](bin/piper) com o modelo em [voice/pt_BR-faber-medium.onnx](voice/pt_BR-faber-medium.onnx) e toca o áudio com `aplay`. Antes de sair falando, ele injeta um pequeno trecho de silêncio para não cortar o começo da frase.

### [core/**init**.py](core/__init__.py)

É só o arquivo que marca o diretório `core` como pacote Python. Aqui não tem lógica pesada, é mais para organização e importação.

## O que tem em cada pasta

### [core/](core)

Aqui mora a lógica principal do assistente. Cada arquivo dentro dela cuida de uma parte do fluxo, e o `main.py` só junta tudo.

### [bin/](bin)

Essa pasta guarda os binários e bibliotecas nativas que o projeto precisa para funcionar sem depender do sistema inteiro:

- `piper`: gera a fala em áudio.
- `whisper-cli`: faz a transcrição local.
- `espeak-ng`, `libespeak-ng*`, `libpiper_phonemize*`, `libonnxruntime*`: dependências nativas usadas pelo motor de voz.
- `espeak-ng-data/`: dados de idioma e pronúncia usados pelas bibliotecas de fala.
- `pt_BR-faber-medium.onnx` e arquivos relacionados quando estão dentro de `bin/`: ativos do modelo de voz, embora neste projeto o modelo principal esteja em `voice/`.

Resumindo: se essa pasta quebra, o assistente perde a fala ou a transcrição.

### [voice/](voice)

Guarda o modelo de voz do Piper. O arquivo `pt_BR-faber-medium.onnx` é o modelo em si, e o `.json` complementar traz metadados e configuração do modelo.

### [whisper-models/](whisper-models)

É onde ficam os modelos do Whisper usados na transcrição local. O projeto está apontado para `ggml-small.bin`, mas outros modelos compatíveis podem existir aí também.

### [samples/](samples)

Pasta de saída dos áudios gravados. O `AudioRecorder` salva o arquivo temporário `input.wav` aqui antes de mandar para o Whisper.

### [piadas.json](piadas.json)

Banco de piadas do assistente. O `brain.py` usa esse arquivo quando detecta pedido de piada, em vez de chamar o Ollama para tudo.

### [setup.sh](setup.sh)

Script de preparação do sistema. Ele adiciona o usuário ao grupo `input` e cria a regra do `udev` para permitir leitura dos eventos do teclado sem precisar rodar o app como root.

### [requirements.txt](requirements.txt)

Arquivo de dependências Python do projeto. No estado atual ele inclui as bibliotecas fundamentais para a captura e o uso do teclado em nível do Linux:

- `numpy`: processamento de áudio e manipulação dos blocos capturados;
- `sounddevice`: captura do stream de áudio do microfone;
- `evdev`: leitura de eventos de teclado em `/dev/input`.

Essas três bibliotecas são as principais dependências do runtime Python do assistente.

### [.gitattributes](.gitattributes)

Ajuda a controlar como certos arquivos são tratados pelo Git, principalmente quando o projeto usa arquivos grandes ou binários.

## Coisas importantes para quem for mexer

- O atalho depende de permissão no `input`, então `setup.sh` importa de verdade.
- O Whisper e o Piper dependem de binários e modelos locais, então não é só instalar Python e sair rodando.
- O Ollama precisa estar ativo em `localhost:11434`.
- Se o `--dev` estiver ligado, dá para ver o JSON bruto que o cérebro devolve, o que ajuda bastante a debugar.
- Se a máquina tiver mais de um teclado ou a identificação mudar entre ambientes, pode usar `--device /dev/input/by-id/...` para forçar o correto.
- O programa continua procurando automaticamente quando nenhum device é informado.

## Como rodar com teclado específico

```bash
python main.py --device /dev/input/by-id/usb-XXXX-event-kbd
```

Ou:

```bash
export FRANKAI_DEVICE=/dev/input/by-id/usb-XXXX-event-kbd
python main.py
```

Se o usuário não informar nada, o programa continua tentando localizar automaticamente o teclado válido.
