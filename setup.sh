#!/bin/bash
# Configura as permissões do sistema adicionando o usuário real ao grupo 'input' e gerando uma regra Udev para permitir que o frankAI capture os atalhos de hardware sem exigir privilégios de root.

if [ "$EUID" -ne 0 ]; then
  echo "Erro: Por favor, execute este script usando sudo."
  echo "Exemplo: sudo ./setup.sh"
  exit 1
fi

REAL_USER=$SUDO_USER

if [ -z "$REAL_USER" ]; then
  REAL_USER=$(logname 2>/dev/null || echo $USER)
fi

if [ "$REAL_USER" = "root" ]; then
  echo "Erro: Não foi possível determinar o usuário comum do sistema."
  echo "Execute o script usando: sudo ./setup.sh"
  exit 1
fi

echo "Iniciando a configuração do ambiente para frankAI..."
echo "Usuário detectado para aplicação das permissões: $REAL_USER"
echo "--------------------------------------------------------"

echo "[1/3] Adicionando $REAL_USER ao grupo 'input'..."
usermod -aG input "$REAL_USER"

echo "[2/3] Criando regra de hardware em /etc/udev/rules.d/..."
RULE_FILE="/etc/udev/rules.d/99-input.rules"

echo 'KERNEL=="event*", NAME="input/%k", MODE="0660", GROUP="input"' > "$RULE_FILE"

echo "[3/3] Atualizando os gatilhos do Kernel (Udev)..."
udevadm control --reload-rules
udevadm trigger

echo "--------------------------------------------------------"
echo "Configuração do sistema concluída com sucesso!"
echo "AVISO IMPORTANTE:"
echo "Para que o Ubuntu aplique as novas permissões de grupo,"
echo "o usuário '$REAL_USER' precisa encerrar a sessão (Logoff) e"
echo "entrar novamente, ou reiniciar o computador."
echo "--------------------------------------------------------"