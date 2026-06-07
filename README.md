# frankAI

Assistente de voz inteligente executado localmente, projetado para distribuições Linux modernas (como Linux Mint, Ubuntu e Debian). O projeto utiliza captura direta de hardware para fornecer uma experiência de Push-to-Talk estável e de baixa latência, integrando modelos locais de transcrição e síntese de voz de forma independente do ambiente de desktop utilizado.

---

## Requisitos do Sistema

* Sistema Operacional: Linux Mint, Ubuntu, Debian ou qualquer distribuição Linux baseada em Debian com suporte ao gerenciador de pacotes APT.
* Servidor de Áudio: PipeWire ou PulseAudio ativo no espaço do usuário.
* Python: Versão 3.12 ou superior.

---

## Arquitetura e Tecnologias

* **evdev**: Leitura direta dos eventos de input do Kernel do Linux (/dev/input), garantindo o funcionamento do atalho global de forma independente do servidor gráfico (X11 ou Wayland) e da interface de usuário (Cinnamon, MATE, GNOME, Xfce).
* **asyncio**: Gerenciamento assíncrono do loop de eventos para monitoramento de hardware e processamento de áudio sem bloqueio de thread.
* **SoundDevice**: Captura de áudio de alta fidelidade integrada ao servidor de som do sistema operacional.
* **Git LFS**: Gerenciamento de histórico para os binários de redes neurais (modelos Whisper e Piper).

---

## Instalação e Configuração Passo a Passo

### 1. Instalar e Configurar o Git LFS (Obrigatório)
Este projeto utiliza arquivos de modelos de IA pesados (acima de 400 MB). O Git tradicional não consegue baixá-los diretamente sem o Git LFS (Large File Storage). Se você clonar o repositório sem instalar o LFS primeiro, os modelos virarão arquivos de texto corrompidos.

Abra o terminal e instale o suporte ao LFS no seu sistema operacional:

```bash
sudo apt update
sudo apt install git-lfs -y
```

Agora, ative o Git LFS na sua conta de usuário global do sistema:

```bash
git lfs install
```

### 2. Clonar o Repositório e Baixar os Modelos
Com o Git LFS devidamente ativo no sistema, clone o repositório. O processo de download pode demorar um pouco mais do que o normal devido ao tamanho dos arquivos binários.

```bash
git clone https://github.com/renanrod4/frankAI.git
cd frankAI
```

Para garantir que todos os arquivos grandes foram baixados com sucesso e não ficaram apenas como ponteiros de texto, force o download dos blocos de dados:

```bash
git lfs pull
```

### 3. Configurar as Permissões de Hardware (Kernel)
Por padrão, o Linux bloqueia o acesso direto de usuários comuns aos dispositivos de entrada por questões de segurança. Para que o software capture o atalho do teclado sem precisar rodar como root (o que quebraria o servidor de áudio), execute o script de automação fornecido:

```bash
chmod +x setup.sh
sudo ./setup.sh
```

**Aviso obrigatório sobre o Kernel:** O Linux só atualiza os grupos de um usuário durante o processo de login. Para que o seu terminal ganhe acesso ao teclado através do grupo input, você deve encerrar a sua sessão atual (fazer Logoff) e entrar novamente, ou simplesmente reiniciar o computador.

### 4. Criar o Ambiente Virtual Python e Instalar Dependências
Após reiniciar o computador ou refazer o login, abra o terminal na pasta do projeto e configure o ambiente virtual isolado do Python:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

---

## Como Utilizar

### Execução via Terminal
Com o ambiente virtual ativado, inicie o assistente em modo de escuta ativa:

```bash
python3 main.py
```

### Mecânica do Atalho (Push-to-Talk)
O assistente monitora a combinação de teclas **Super + F** (Tecla Windows + F) diretamente no nível de hardware do Kernel.

1. Vá até as configurações de atalhos de teclado nativos do seu sistema (Cinnamon, MATE ou GNOME) e certifique-se de que a combinação Super + F não está sendo usada por nenhuma função padrão (como abrir o gerenciador de arquivos).
2. Com o script rodando no terminal, mantenha as teclas Super + F pressionadas no teclado.
3. Fale o seu comando enquanto segura as teclas.
4. Solte as teclas para encerrar a captura. O áudio será automaticamente processado e enviado para a pipeline do Whisper e do Piper.

---

## Solução de Problemas de Permissão

Se ao executar o script você receber um erro do tipo `RuntimeError: Nenhum dispositivo de entrada acessível`, valide o ambiente com os seguintes passos:

1. Verifique se o seu usuário foi de fato adicionado ao grupo de hardware:
   ```bash
   groups
   ```
   O grupo 'input' deve aparecer no retorno do comando. Se não aparecer, o logoff não foi realizado corretamente.

2. Verifique se as permissões dos arquivos de evento foram aplicadas pelo Kernel:
   ```bash
   ls -l /dev/input/event*
   ```
   Os arquivos devem exibir o grupo 'input' com permissão de leitura e escrita ('crw-rw----').