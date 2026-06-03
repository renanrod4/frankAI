# Relatório Técnico de Especificação: Orquestrador do Assistente de Voz Local

Este documento estabelece os requisitos lógicos, o fluxo de controle e a arquitetura de execução para o script Python responsável por unificar o Whisper.cpp, o Ollama e o Piper TTS em um sistema funcional de Push-to-Talk (Pressione para Falar).

---

## 1. Arquitetura Geral e Variáveis Globais

O script atuará como um gerenciador de processos assíncronos. Ele deve centralizar os caminhos absolutos do sistema para evitar falhas de escopo.

### Definições de Caminhos e Alvos
* **Rotas dos Executáveis:** Caminhos para `whisper-cli`, `piper` e o modelo de voz `.onnx`.
* **Arquivos Temporários:** Armazenamento do áudio de entrada (`/tmp/input_mic.wav`) e do áudio de saída sintetizado (`/tmp/output_voice.wav`).
* **Endpoint da API:** URL local do Ollama (`http://localhost:11434/api/generate`).

### Estruturas de Controle de Estado
Como o monitoramento do teclado ocorre de forma assíncrona, o script precisa manter o controle de três estados globais:
* Um conjunto (set) para registrar as teclas atualmente pressionadas (evitando conflitos de atalhos).
* Uma flag booleana para indicar se a gravação está ativa.
* Uma referência ao ponteiro do processo de gravação, permitindo sua interrupção a qualquer momento.

---

## 2. Mecanismo de Captura: Push-to-Talk (PTT)

O maior desafio técnico nesta etapa é o comportamento do Linux conhecido como Key Repeat (repetição de tecla). Quando uma tecla é mantida pressionada, o sistema operacional dispara continuamente eventos de "pressionado". O script deve ignorar essas repetições e focar apenas no primeiro evento de descida e no evento final de subida.

### Lógica do Evento: Ao Pressionar (on_press)
1. Verificar se a tecla capturada é a tecla modificadora (Super/Windows) ou a tecla de ação (F).
2. Adicionar a tecla correspondente ao conjunto de teclas pressionadas.
3. Avaliar a condição de ativação: Se "Super" e "F" estiverem simultaneamente no conjunto E a flag de gravação for falsa:
    * Alterar a flag de gravação para verdadeira.
    * Iniciar o subsetor de captura de áudio.

### Lógica do Evento: Ao Soltar (on_release)
1. Remover a tecla liberada do conjunto de teclas pressionadas.
2. Avaliar a condição de encerramento: Se a tecla liberada for o "F" E a flag de gravação for verdadeira:
    * Alterar a flag de gravação para falsa.
    * Interromper imediatamente o subsetor de captura de áudio.
    * Disparar o pipeline de processamento de dados (transcrição, inteligência e resposta).

---

## 3. Detalhes dos Módulos do Pipeline

Após a gestão dos gatilhos de teclado, o script executa uma cadeia linear de processamento dividida em cinco etapas independentes.