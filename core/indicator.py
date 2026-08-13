import sys
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtWidgets import QApplication, QWidget
from PyQt6.QtGui import QPainter, QColor, QRadialGradient

class FrankIndicator(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()
        
        # Variáveis para a animação fluida de "respiração"
        self.raio_base = 15.0
        self.raio_animado = self.raio_base
        self.animacao_crescente = True
        
        self.timer_animacao = QTimer()
        self.timer_animacao.timeout.connect(self.animar_respiracao)
        
        self.estado_atual = "inativo"

    def init_ui(self):
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint | 
            Qt.WindowType.WindowStaysOnTopHint | 
            Qt.WindowType.Tool | 
            Qt.WindowType.WindowTransparentForInput |
            Qt.WindowType.WindowDoesNotAcceptFocus |
            Qt.WindowType.BypassWindowManagerHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        # Aumentamos o tamanho da janela invisível para caber a animação de pulso
        self.setFixedSize(60, 60) 
        
        screen = QApplication.primaryScreen().geometry()
        
        self.move(int(screen.width()/2-30), screen.height()-140)
        
        # Cores iniciais (totalmente transparentes)
        self.cor_centro = QColor(0, 0, 0, 0)
        self.cor_borda = QColor(0, 0, 0, 0)

    def animar_respiracao(self):
        # Altera suavemente o tamanho do raio para criar o efeito de pulsar 
        if self.animacao_crescente:
            self.raio_animado += 0.5
            if self.raio_animado >= 22.0:
                self.animacao_crescente = False
        else:
            self.raio_animado -= 0.5
            if self.raio_animado <= 15.0:
                self.animacao_crescente = True
                
        self.update() # Força o redesenho da tela

    def paintEvent(self, event):
        if self.estado_atual == "inativo":
            return
            
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        centro_x = self.width() / 2
        centro_y = self.height() / 2
        
        # Cria um gradiente radial para um visual moderno e brilhante
        gradiente = QRadialGradient(centro_x, centro_y, self.raio_animado)
        gradiente.setColorAt(0.0, self.cor_centro)              # Miolo mais claro
        gradiente.setColorAt(0.7, self.cor_borda)               # Cor principal
        gradiente.setColorAt(1.0, QColor(0, 0, 0, 0))           # Borda esfumaçada (fade out)
        
        painter.setBrush(gradiente)
        painter.setPen(Qt.PenStyle.NoPen)
        
        # Desenha a esfera com o tamanho atual calculado pela animação
        painter.drawEllipse(
            int(centro_x - self.raio_animado), 
            int(centro_y - self.raio_animado), 
            int(self.raio_animado * 2), 
            int(self.raio_animado * 2)
        )

    def atualizar_status(self, status):
        self.estado_atual = status
        
        if status == "ouvindo":
            # Vermelho neon / Coral
            self.cor_centro = QColor(255, 150, 150, 255)
            self.cor_borda = QColor(235, 64, 52, 220)
            if not self.timer_animacao.isActive():
                self.timer_animacao.start(30) # Atualiza a cada 30ms para 60fps
                
        elif status == "pensando":
            # Azul neon / Ciano (Remete ao processamento de Inteligência Artificial)
            self.cor_centro = QColor(150, 220, 255, 255)
            self.cor_borda = QColor(52, 152, 235, 220)
            if not self.timer_animacao.isActive():
                self.timer_animacao.start(30)
                
        elif status == "sucesso":
            # Verde vibrante
            self.cor_centro = QColor(150, 255, 180, 255)
            self.cor_borda = QColor(52, 235, 113, 220)
            
            # Para a animação de pulsar e reseta o tamanho
            self.timer_animacao.stop()
            self.raio_animado = self.raio_base
            
            QTimer.singleShot(1500, lambda: self.atualizar_status("inativo"))
            
        else:
            # Inativo
            self.timer_animacao.stop()
            self.cor_centro = QColor(0, 0, 0, 0)
            self.cor_borda = QColor(0, 0, 0, 0)
            
        self.update()