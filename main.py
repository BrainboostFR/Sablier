import sys
import json
import os
import random
from PySide6.QtWidgets import (QApplication, QWidget, QMainWindow, QVBoxLayout, 
                             QLabel, QSpinBox, QPushButton, QSystemTrayIcon, 
                             QMenu, QStyle)
from PySide6.QtCore import Qt, QTimer, QPoint, QRectF, QPointF, QVariantAnimation, QEasingCurve
from PySide6.QtGui import QPainter, QColor, QAction, QPen, QPainterPath, QLinearGradient

SETTINGS_FILE = "settings.json"

class Particle:
    def __init__(self, x, y):
        self.pos = QPointF(x, y)
        self.speed = random.uniform(2, 4)
        self.size = random.uniform(0.5, 1.5)

class HourglassOverlay(QWidget):
    def __init__(self, settings):
        super().__init__()
        self.settings = settings
        
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        self.total_seconds = self.settings.get("duration", 60)
        self.remaining_seconds = self.total_seconds
        self.is_flipped = False 
        self.particles = []
        self._rotation_angle = 0.0
        
        self._drag_pos = QPoint()
        self._is_moving = False
        self._start_click_pos = QPoint()

        self.rot_anim = QVariantAnimation(self)
        self.rot_anim.setDuration(600)
        self.rot_anim.setEasingCurve(QEasingCurve.InOutQuad)
        self.rot_anim.valueChanged.connect(self._update_rotation)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_logic)
        self.timer.start(20) 
        
        self.apply_settings()

    def _update_rotation(self, value):
        self._rotation_angle = value
        self.update()

    def apply_settings(self):
        size = max(32, min(self.settings.get("size", 64), 128))
        self.settings["size"] = size
        
        buffer = int(size * 1.6)
        self.setFixedSize(buffer, buffer)
        self.move(self.settings.get("x", 100), self.settings.get("y", 100))
        self.total_seconds = self.settings.get("duration", 60)
        self.update()

    def update_logic(self):
        is_rotating = self.rot_anim.state() == QVariantAnimation.Running
        
        if not is_rotating and self.remaining_seconds > 0:
            self.remaining_seconds -= 0.02
            if self.remaining_seconds < 0: self.remaining_seconds = 0
            
            if self.remaining_seconds > 0 and len(self.particles) < 15:
                self.particles.append(Particle(self.width()/2, self.height()/2))
        
        for p in self.particles[:]:
            p.pos.setY(p.pos.y() + p.speed)
            if p.pos.y() > self.height() * 0.8:
                self.particles.remove(p)
        self.update()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._start_click_pos = event.globalPosition().toPoint()
            self._drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            self._is_moving = False

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton:
            if (event.globalPosition().toPoint() - self._start_click_pos).manhattanLength() > 5:
                self._is_moving = True
                new_pos = event.globalPosition().toPoint() - self._drag_pos
                self.move(new_pos)
                self.settings["x"], self.settings["y"] = new_pos.x(), new_pos.y()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton and not self._is_moving:
            self.flip_hourglass()

    def flip_hourglass(self):
        if self.rot_anim.state() == QVariantAnimation.Running: return
        self.remaining_seconds = self.total_seconds - self.remaining_seconds
        self.is_flipped = not self.is_flipped
        self.particles = []
        start = self._rotation_angle
        self.rot_anim.setStartValue(start)
        self.rot_anim.setEndValue(start + 180)
        self.rot_anim.start()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        w, h = float(self.width()), float(self.height())
        size = float(self.settings.get("size", 64))
        mid_y = h / 2
        
        margin_w = (w - size) / 2
        margin_h = (h - (size * 1.3)) / 2
        
        painter.save()
        painter.translate(w/2, h/2)
        painter.rotate(self._rotation_angle)
        painter.translate(-w/2, -h/2)

        glass_path = QPainterPath()
        glass_path.moveTo(margin_w, margin_h)
        glass_path.lineTo(w - margin_w, margin_h)
        cp_off = size * 0.3
        glass_path.cubicTo(w - margin_w, margin_h + cp_off, w/2 + 4, mid_y - 5, w/2 + 4, mid_y)
        glass_path.cubicTo(w/2 + 4, mid_y + 5, w - margin_w, h - margin_h - cp_off, w - margin_w, h - margin_h)
        glass_path.lineTo(margin_w, h - margin_h)
        glass_path.cubicTo(margin_w, h - margin_h - cp_off, w/2 - 4, mid_y + 5, w/2 - 4, mid_y)
        glass_path.cubicTo(w/2 - 4, mid_y - 5, margin_w, margin_h + cp_off, margin_w, margin_h)

        painter.setPen(QPen(QColor(255, 255, 255, 150), 1.5 if size > 40 else 1.0))
        painter.setBrush(QColor(255, 255, 255, 20))
        painter.drawPath(glass_path)
        painter.restore()

        if self.rot_anim.state() != QVariantAnimation.Running:
            ratio = self.remaining_seconds / self.total_seconds if self.total_seconds > 0 else 0
            
            painter.save()
            painter.translate(w/2, h/2)
            painter.rotate(self._rotation_angle)
            painter.translate(-w/2, -h/2)
            painter.setClipPath(glass_path)
            
            painter.translate(w/2, h/2)
            painter.rotate(-self._rotation_angle)
            painter.translate(-w/2, -h/2)

            painter.setPen(Qt.NoPen)
            painter.setBrush(QColor(230, 190, 100))

            h_fill_top = margin_h + (mid_y - margin_h) * (1 - ratio)
            painter.drawRect(QRectF(0, h_fill_top, w, mid_y - h_fill_top))

            inv_ratio = 1 - ratio
            h_fill_bot = (h - margin_h) - (mid_y - margin_h) * inv_ratio
            painter.drawRect(QRectF(0, h_fill_bot, w, (h - margin_h) - h_fill_bot))
            
            painter.restore()

        if self.rot_anim.state() != QVariantAnimation.Running and 0 < ratio < 1:
            painter.setBrush(QColor(230, 190, 100))
            for p in self.particles:
                painter.drawEllipse(p.pos, p.size, p.size)

class SettingsWindow(QMainWindow):
    def __init__(self, overlay, save_callback):
        super().__init__()
        self.overlay = overlay
        self.save_callback = save_callback
        self.setWindowTitle("Réglages")
        self.setFixedSize(250, 200)
        self.setWindowFlags(Qt.WindowStaysOnTopHint)
        
        layout = QVBoxLayout()
        layout.addWidget(QLabel("Taille (32 à 128 px) :"))
        self.size_spin = QSpinBox()
        self.size_spin.setRange(32, 128)
        self.size_spin.setValue(self.overlay.settings["size"])
        self.size_spin.valueChanged.connect(self.update_settings)
        layout.addWidget(self.size_spin)
        
        layout.addWidget(QLabel("Temps (sec) :"))
        self.time_spin = QSpinBox()
        self.time_spin.setRange(5, 36000)
        self.time_spin.setValue(self.overlay.settings["duration"])
        self.time_spin.valueChanged.connect(self.update_settings)
        layout.addWidget(self.time_spin)

        btn = QPushButton("Remplir")
        btn.clicked.connect(self.reset)
        layout.addWidget(btn)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

    def update_settings(self):
        self.overlay.settings["size"] = self.size_spin.value()
        self.overlay.settings["duration"] = self.time_spin.value()
        self.overlay.apply_settings()
        self.save_callback()

    def reset(self):
        self.overlay.remaining_seconds = self.overlay.total_seconds
        self.overlay.is_flipped = False
        self.overlay._rotation_angle = 0
        self.overlay.update()

class HourglassApp:
    def __init__(self):
        self.app = QApplication(sys.argv)
        self.app.setQuitOnLastWindowClosed(False)
        self.load_settings()
        self.overlay = HourglassOverlay(self.settings)
        self.overlay.show()
        self.settings_window = SettingsWindow(self.overlay, self.save_settings)
        self.setup_tray()
        sys.exit(self.app.exec())

    def load_settings(self):
        if os.path.exists(SETTINGS_FILE):
            try:
                with open(SETTINGS_FILE, "r") as f: self.settings = json.load(f)
            except: self.default_settings()
        else: self.default_settings()

    def default_settings(self):
        self.settings = {"x": 200, "y": 200, "size": 64, "duration": 60}

    def save_settings(self):
        self.settings["x"], self.settings["y"] = self.overlay.x(), self.overlay.y()
        with open(SETTINGS_FILE, "w") as f: json.dump(self.settings, f)

    def setup_tray(self):
        icon = self.app.style().standardIcon(QStyle.StandardPixmap.SP_ComputerIcon)
        self.tray = QSystemTrayIcon(icon, self.app)
        menu = QMenu()
        act_set = QAction("Réglages", menu)
        act_set.triggered.connect(self.settings_window.show)
        act_quit = QAction("Quitter", menu)
        act_quit.triggered.connect(self.quit_app)
        menu.addAction(act_set)
        menu.addSeparator()
        menu.addAction(act_quit)
        self.tray.setContextMenu(menu)
        self.tray.show()

    def quit_app(self):
        self.save_settings()
        self.tray.hide()
        QApplication.quit()

if __name__ == "__main__":
    HourglassApp()
