#!/usr/bin/env bash

# frankAI - Script de Configuração e Instalação do Ambiente Linux
#
# Este script:
#? 1. Configura permissões de hardware (grupo 'input' e regras Udev).
#? 2. Instala pacotes do sistema via APT (build-essential, alsa-utils, libportaudio2, etc.).
#? 3. Baixa e extrai as bibliotecas nativas C++ e binários do Piper/eSpeak em bin/.
#? 4. Ajusta permissões de execução (chmod +x) e garante posse dos arquivos para o usuário comum.


set -eo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[OK]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[AVISO]${NC} $1"; }
log_error() { echo -e "${RED}[ERRO]${NC} $1"; }

# Validação de Privilégios
if [ "$EUID" -ne 0 ]; then
  log_error "Este script precisa ser executado com privilégios de superusuário (sudo)."
  echo "Uso correto: sudo ./setup.sh"
  exit 1
fi

# Identificação do Usuário Comum
REAL_USER=$SUDO_USER
if [ -z "$REAL_USER" ]; then
  REAL_USER=$(logname 2>/dev/null || echo "$USER")
fi

if [ "$REAL_USER" = "root" ] || [ -z "$REAL_USER" ]; then
  log_error "Não foi possível determinar o usuário comum do sistema."
  echo "Por favor, execute o script utilizando: sudo ./setup.sh"
  exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "--------------------------------------------------------"
log_info "Iniciando a configuração do ambiente para frankAI"
log_info "Usuário detectado: $REAL_USER"
log_info "Diretório do projeto: $SCRIPT_DIR"
echo "--------------------------------------------------------"

#? 1. Permissões de Hardware (Udev e Grupo input)
log_info "[1/4] Configurando permissões de hardware..."

if id -nG "$REAL_USER" | grep -qw "input"; then
  log_success "Usuário '$REAL_USER' já pertence ao grupo 'input'."
else
  usermod -aG input "$REAL_USER"
  log_success "Usuário '$REAL_USER' adicionado ao grupo 'input'."
fi

RULE_FILE="/etc/udev/rules.d/99-input.rules"
log_info "Criando/atualizando regras Udev em $RULE_FILE..."
echo 'KERNEL=="event*", NAME="input/%k", MODE="0660", GROUP="input"' > "$RULE_FILE"

udevadm control --reload-rules
udevadm trigger
log_success "Regras Udev aplicadas e recarregadas no Kernel."

#? 2. Instalação de Pacotes do Sistema (APT)

log_info "[2/4] Verificando e instalando dependências de sistema (APT)..."
apt-get update -qq
apt-get install -y -qq wget curl tar python3-venv python3-pip python3-dev build-essential alsa-utils xdotool libportaudio2 >/dev/null
log_success "Pacotes do sistema verificados/instalados."

#? 3. Download e Configuração do Piper (Libs Nativas C++)

log_info "[3/4] Verificando dependências nativas do Piper em bin/..."

BIN_DIR="$SCRIPT_DIR/bin"
mkdir -p "$BIN_DIR"

PIPER_BINARY="$BIN_DIR/piper"
LIB_ESPEAK="$BIN_DIR/libespeak-ng.so"

if [ -f "$PIPER_BINARY" ] && [ -f "$LIB_ESPEAK" ]; then
  log_success "Bibliotecas nativas e binário do Piper já estão presentes em bin/."
else
  log_info "Baixando pacote de binários nativos do Piper (x86_64)..."
  TMP_DIR=$(mktemp -d)
  PIPER_TAR="$TMP_DIR/piper.tar.gz"
  PIPER_URL="https://github.com/rhasspy/piper/releases/download/2023.8.15-2/piper_amd64.tar.gz"

  if wget -q --show-progress -O "$PIPER_TAR" "$PIPER_URL"; then
    log_info "Extraindo arquivos para $BIN_DIR..."
    tar -xzf "$PIPER_TAR" -C "$TMP_DIR"
    cp -r "$TMP_DIR/piper/"* "$BIN_DIR/"
    rm -rf "$TMP_DIR"
    log_success "Piper e bibliotecas C++ (.so) instalados em bin/."
  else
    log_error "Falha ao baixar o pacote do Piper."
    rm -rf "$TMP_DIR"
    exit 1
  fi
fi

#? 4. Permissões de Execução e Ownership
log_info "[4/4] Ajustando permissões de execução e ownership dos arquivos..."

if [ -f "$BIN_DIR/piper" ]; then
  chmod +x "$BIN_DIR/piper"
fi

if [ -f "$BIN_DIR/whisper-cli" ]; then
  chmod +x "$BIN_DIR/whisper-cli"
fi

# Verifica se todo o diretorio do projeto pertença ao usuário comum
chown -R "$REAL_USER:$REAL_USER" "$SCRIPT_DIR"
log_success "Permissões e propriedade dos arquivos ajustadas."

# Finalização
echo "--------------------------------------------------------"
log_success "Configuração do frankAI concluída com sucesso!"
echo ""
log_warn "ATENÇÃO:"
echo "Para que as novas permissões do grupo 'input' entrem em vigor,"
echo "o usuário '$REAL_USER' precisa encerrar a sessão (Logoff) e"
echo "fazer login novamente ou reiniciar o computador."
echo "--------------------------------------------------------"