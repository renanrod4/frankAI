# Este scrpipt é responsavel por enviar notificações para o desktop do usuario
import subprocess

def disparar_notificacao(titulo, mensagem, icone="dialog-information"):

    try:
        subprocess.run(["notify-send", titulo, mensagem, "-i", icone], check=True)
    except Exception as e:
        # Fallback silencioso caso o notify-send não esteja disponível
        print(f"Erro ao enviar notificação: {e}")