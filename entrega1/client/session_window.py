import sys
import os
import math
import json
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QMessageBox, QDialog, QListWidget, QListWidgetItem, QAbstractItemView
)
from PySide6.QtGui import QPainter, QPen, QBrush, QColor, QFont, QPainterPath
from PySide6.QtCore import Qt, QRectF, QPointF
import virtuallab_client as client


# Catálogo con los títulos legibles y descripciones técnicas de los 5 laboratorios
LAB_CATALOG = {
    "voltage_divider": {
        "titulo": "Divisor de Voltaje (DC)",
        "descripcion": "Circuito divisor resistivo en corriente directa (Vin = 12V, R1 = 1kΩ, R2 = 1kΩ)."
    },
    "dc_mesh": {
        "titulo": "Circuito de Mallas (DC - 2 Mallas)",
        "descripcion": "Red resistiva en T con dos fuentes DC (V1 = 12V, V2 = 6V, R1 = 1kΩ, R2 = 2kΩ, R3 = 1kΩ)."
    },
    "rc": {
        "titulo": "Circuito RC (AC - Carga y Descarga)",
        "descripcion": "Respuesta transitoria de carga y descarga en capacitor (R = 1kΩ, C = 10µF)."
    },
    "rl_circuit": {
        "titulo": "Circuito Serie RL (AC - Senoidal)",
        "descripcion": "Circuito serie resistencia-inductor a 1 kHz (Vin = 12Vp, R1 = 100Ω, L1 = 15.9mH)."
    },
    "rlc_circuit": {
        "titulo": "Circuito Serie RLC (AC - Resonancia)",
        "descripcion": "Circuito resonante serie a 1 kHz (Vin = 12Vp, R1 = 100Ω, L1 = 10mH, C1 = 2.5µF)."
    }
}


def identificar_tipo_lab(lab_filename):
    """Clasifica el archivo .zip según palabras clave (evalúa 'rlc' antes que 'rl' y 'rc')."""
    nombre = lab_filename.lower()
    if "dc_mesh" in nombre or "mesh" in nombre or "malla" in nombre:
        return "dc_mesh"
    if "rlc" in nombre:
        return "rlc_circuit"
    if "rl" in nombre:
        return "rl_circuit"
    if "rc" in nombre:
        return "rc"
    return "voltage_divider"


def obtener_nombre_amigable(lab_filename):
    """Devuelve el título legible del laboratorio para mostrarlo en las listas."""
    tipo = identificar_tipo_lab(lab_filename)
    return LAB_CATALOG[tipo]["titulo"]


class CircuitCanvasDividerDC(QWidget):
    """Lienzo gráfico para laboratorio DC (Divisor de Voltaje)"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(540, 340)
        self.vin, self.r1, self.r2 = 12.0, 1000.0, 1000.0
        self.nodo_seleccionado, self.voltaje_medido = None, None
        self.pos_nodo_in = QPointF(90, 110)
        self.pos_nodo_out = QPointF(270, 110)
        self.pos_nodo_gnd = QPointF(440, 110)

    def mousePressEvent(self, event):
        pos = event.position()
        radio = 25.0
        if (pos - self.pos_nodo_in).manhattanLength() <= radio:
            self.nodo_seleccionado, self.voltaje_medido = "Vin (Entrada DC)", f"{self.vin:.2f} V"
        elif (pos - self.pos_nodo_out).manhattanLength() <= radio:
            vout = self.vin * (self.r2 / (self.r1 + self.r2))
            self.nodo_seleccionado, self.voltaje_medido = "Vout (Divisor)", f"{vout:.2f} V"
        elif (pos - self.pos_nodo_gnd).manhattanLength() <= radio:
            self.nodo_seleccionado, self.voltaje_medido = "GND (Tierra)", "0.00 V"
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.fillRect(self.rect(), QColor("#1e1e2e"))

        painter.setPen(QPen(QColor("#a6adc8"), 4))
        painter.drawLine(90, 110, 165, 110)
        painter.drawLine(215, 110, 335, 110)
        painter.drawLine(385, 110, 440, 110)

        painter.setPen(QPen(QColor("#f9e2af"), 3))
        painter.setBrush(QBrush(QColor("#313244")))
        painter.drawRect(165, 95, 50, 30)
        painter.drawRect(335, 95, 50, 30)

        painter.setPen(QColor("#cdd6f4"))
        painter.setFont(QFont("Arial", 9, QFont.Bold))
        painter.drawText(162, 85, "R1: 1kΩ")
        painter.drawText(332, 85, "R2: 1kΩ")

        nodos = [
            ("Vin", self.pos_nodo_in, "#89b4fa"),
            ("Vout", self.pos_nodo_out, "#a6e3a1"),
            ("GND", self.pos_nodo_gnd, "#f38ba8")
        ]
        for nombre, pos, col in nodos:
            sel = (self.nodo_seleccionado and nombre in self.nodo_seleccionado)
            painter.setPen(QPen(QColor("#ffffff") if sel else QColor(col), 3 if sel else 2))
            painter.setBrush(QBrush(QColor(col)))
            painter.drawEllipse(pos, 14 if sel else 10, 14 if sel else 10)
            painter.setPen(QColor("#cdd6f4"))
            painter.drawText(int(pos.x() - 15), int(pos.y() - 20), nombre)

        painter.setPen(QPen(QColor("#89b4fa"), 2))
        painter.setBrush(QBrush(QColor("#181825")))
        painter.drawRoundedRect(120, 185, 300, 95, 10, 10)
        painter.setPen(QColor("#a6e3a1"))
        painter.setFont(QFont("Consolas", 11, QFont.Bold))
        txt = (
            f"Nodo: {self.nodo_seleccionado}\nVoltaje: {self.voltaje_medido}"
            if self.nodo_seleccionado else "Haz clic en un nodo para medir..."
        )
        painter.drawText(QRectF(120, 185, 300, 95), Qt.AlignCenter, txt)


class CircuitCanvasMeshDC(QWidget):
    """Lienzo gráfico para laboratorio DC (Circuito de 2 Mallas en T)"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(540, 340)
        self.nodo_seleccionado = None
        self.medicion_texto = None
        self.pos_n1 = QPointF(80, 95)
        self.pos_n2 = QPointF(270, 95)
        self.pos_n3 = QPointF(460, 95)
        self.pos_gnd = QPointF(270, 205)

    def mousePressEvent(self, event):
        pos = event.position()
        radio = 24.0
        if (pos - self.pos_n1).manhattanLength() <= radio:
            self.nodo_seleccionado = "n1 (V1 = 12V)"
            self.medicion_texto = "Voltaje: 12.00 V | Corriente Malla 1 (I1): 4.80 mA"
        elif (pos - self.pos_n2).manhattanLength() <= radio:
            self.nodo_seleccionado = "n2 (Nodo Central)"
            self.medicion_texto = "Voltaje: 7.20 V | Corriente R2 (IR2): 3.60 mA"
        elif (pos - self.pos_n3).manhattanLength() <= radio:
            self.nodo_seleccionado = "n3 (V2 = 6V)"
            self.medicion_texto = "Voltaje: 6.00 V | Corriente Malla 2 (I2): 1.20 mA"
        elif (pos - self.pos_gnd).manhattanLength() <= radio:
            self.nodo_seleccionado = "GND (Referencia)"
            self.medicion_texto = "Voltaje: 0.00 V"
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.fillRect(self.rect(), QColor("#1e1e2e"))

        # Cables horizontales y rama central
        painter.setPen(QPen(QColor("#a6adc8"), 4))
        painter.drawLine(80, 95, 145, 95)
        painter.drawLine(195, 95, 345, 95)
        painter.drawLine(395, 95, 460, 95)
        painter.drawLine(270, 95, 270, 125)
        painter.drawLine(270, 170, 270, 205)

        # Resistencias R1, R3 y R2
        painter.setPen(QPen(QColor("#f9e2af"), 3))
        painter.setBrush(QBrush(QColor("#313244")))
        painter.drawRect(145, 80, 50, 30)
        painter.drawRect(345, 80, 50, 30)
        painter.drawRect(255, 125, 30, 45)

        painter.setPen(QColor("#cdd6f4"))
        painter.setFont(QFont("Arial", 9, QFont.Bold))
        painter.drawText(142, 70, "R1: 1kΩ")
        painter.drawText(342, 70, "R3: 1kΩ")
        painter.drawText(292, 152, "R2: 2kΩ")

        nodos = [
            ("n1 (12V)", self.pos_n1, "#89b4fa"),
            ("n2", self.pos_n2, "#a6e3a1"),
            ("n3 (6V)", self.pos_n3, "#cba6f7"),
            ("GND", self.pos_gnd, "#f38ba8")
        ]
        for etiqueta, pos, col in nodos:
            clave = etiqueta.split()[0]
            sel = (self.nodo_seleccionado and clave in self.nodo_seleccionado)
            painter.setPen(QPen(QColor("#ffffff") if sel else QColor(col), 3 if sel else 2))
            painter.setBrush(QBrush(QColor(col)))
            painter.drawEllipse(pos, 13 if sel else 9, 13 if sel else 9)
            painter.setPen(QColor("#cdd6f4"))
            offset_x = 18 if clave == "GND" else -22
            offset_y = 5 if clave == "GND" else -18
            painter.drawText(int(pos.x() + offset_x), int(pos.y() + offset_y), etiqueta)

        # Panel de lectura
        painter.setPen(QPen(QColor("#89b4fa"), 2))
        painter.setBrush(QBrush(QColor("#181825")))
        painter.drawRoundedRect(60, 240, 420, 75, 10, 10)
        painter.setPen(QColor("#a6e3a1"))
        painter.setFont(QFont("Consolas", 10, QFont.Bold))
        txt = (
            f"Nodo: {self.nodo_seleccionado}\n{self.medicion_texto}"
            if self.nodo_seleccionado else "Haz clic en n1, n2, n3 o GND para medir..."
        )
        painter.drawText(QRectF(60, 240, 420, 75), Qt.AlignCenter, txt)


class CircuitCanvasRC(QWidget):
    """Lienzo para laboratorio AC con gráfica dinámica de Carga y Descarga RC"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(540, 340)
        self.nodo_seleccionado = None
        self.voltaje_medido = None
        self.pos_nodo_in = QPointF(90, 85)
        self.pos_nodo_out = QPointF(270, 85)
        self.pos_nodo_gnd = QPointF(440, 85)

    def mousePressEvent(self, event):
        pos = event.position()
        radio = 25.0
        if (pos - self.pos_nodo_in).manhattanLength() <= radio:
            self.nodo_seleccionado = "Vac (Entrada)"
            self.voltaje_medido = "12.0 Vp (Onda Cuadrada)"
        elif (pos - self.pos_nodo_out).manhattanLength() <= radio:
            self.nodo_seleccionado = "Vc (Capacitor)"
            self.voltaje_medido = "Carga / Descarga (τ = 10 ms)"
        elif (pos - self.pos_nodo_gnd).manhattanLength() <= radio:
            self.nodo_seleccionado = "GND / Masa"
            self.voltaje_medido = "0.00 V"
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.fillRect(self.rect(), QColor("#1e1e2e"))

        painter.setPen(QPen(QColor("#a6adc8"), 4))
        painter.drawLine(90, 85, 165, 85)
        painter.drawLine(215, 85, 355, 85)
        painter.drawLine(367, 85, 440, 85)

        painter.setPen(QPen(QColor("#fab387"), 3))
        painter.setBrush(QBrush(QColor("#313244")))
        painter.drawRect(165, 70, 50, 30)

        painter.setPen(QPen(QColor("#89b4fa"), 4))
        painter.drawLine(355, 70, 355, 100)
        painter.drawLine(367, 70, 367, 100)

        painter.setPen(QColor("#cdd6f4"))
        painter.setFont(QFont("Arial", 9, QFont.Bold))
        painter.drawText(162, 60, "R: 1kΩ")
        painter.drawText(340, 60, "C: 10µF")

        for nombre, pos, col in [("Vac", self.pos_nodo_in, "#cba6f7"), ("Vc", self.pos_nodo_out, "#a6e3a1"), ("GND", self.pos_nodo_gnd, "#f38ba8")]:
            sel = (self.nodo_seleccionado and nombre in self.nodo_seleccionado)
            painter.setPen(QPen(QColor("#ffffff") if sel else QColor(col), 3 if sel else 2))
            painter.setBrush(QBrush(QColor(col)))
            painter.drawEllipse(pos, 14 if sel else 10, 14 if sel else 10)
            painter.setPen(QColor("#cdd6f4"))
            painter.drawText(int(pos.x() - 15), int(pos.y() - 15), nombre)

        gx, gy, gw, gh = 55, 145, 430, 165
        painter.setPen(QPen(QColor("#89b4fa"), 2))
        painter.setBrush(QBrush(QColor("#11111b")))
        painter.drawRoundedRect(gx, gy, gw, gh, 8, 8)

        painter.setPen(QPen(QColor("#313244"), 1, Qt.DashLine))
        painter.drawLine(gx, gy + gh // 2, gx + gw, gy + gh // 2)
        painter.drawLine(gx + gw // 2, gy, gx + gw // 2, gy + gh)

        if not self.nodo_seleccionado:
            painter.setPen(QColor("#a6e3a1"))
            painter.setFont(QFont("Consolas", 11, QFont.Bold))
            painter.drawText(QRectF(gx, gy, gw, gh), Qt.AlignCenter, "Haz clic en un nodo para graficar la onda...")
        else:
            path = QPainterPath()
            if "Vac" in self.nodo_seleccionado:
                painter.setPen(QPen(QColor("#cba6f7"), 2))
                path.moveTo(gx + 15, gy + gh - 20)
                for i in range(3):
                    x_start = gx + 15 + i * 130
                    path.lineTo(x_start, gy + 25)
                    path.lineTo(x_start + 65, gy + 25)
                    path.lineTo(x_start + 65, gy + gh - 20)
                    path.lineTo(x_start + 130, gy + gh - 20)
                painter.drawPath(path)
            elif "Vc" in self.nodo_seleccionado:
                painter.setPen(QPen(QColor("#a6e3a1"), 3))
                start_x = gx + 15
                path.moveTo(start_x, gy + gh - 20)
                num_puntos = 380
                dx = (gw - 30) / num_puntos
                for step in range(num_puntos):
                    x = start_x + step * dx
                    t = (step % 100) / 20.0
                    val = (1.0 - math.exp(-t)) if (step // 100) % 2 == 0 else math.exp(-t)
                    y = (gy + gh - 20) - val * (gh - 45)
                    path.lineTo(x, y)
                painter.drawPath(path)
            elif "GND" in self.nodo_seleccionado:
                painter.setPen(QPen(QColor("#f38ba8"), 2))
                painter.drawLine(gx + 15, gy + gh - 20, gx + gw - 15, gy + gh - 20)

            painter.setPen(QColor("#e2e8f7"))
            painter.setFont(QFont("Arial", 9, QFont.Bold))
            painter.drawText(gx + 12, gy + 20, f"Medición: {self.nodo_seleccionado} -> {self.voltaje_medido}")


class CircuitCanvasRL(QWidget):
    """Lienzo para laboratorio AC Serie RL (Desfase e Impedancia a 1 kHz)"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(540, 340)
        self.nodo_seleccionado = None
        self.voltaje_medido = None
        self.pos_n1 = QPointF(90, 85)
        self.pos_n2 = QPointF(270, 85)
        self.pos_gnd = QPointF(440, 85)

    def mousePressEvent(self, event):
        pos = event.position()
        radio = 25.0
        if (pos - self.pos_n1).manhattanLength() <= radio:
            self.nodo_seleccionado = "n1 (Vin)"
            self.voltaje_medido = "12.00 Vp ∠ 0° (1 kHz)"
        elif (pos - self.pos_n2).manhattanLength() <= radio:
            self.nodo_seleccionado = "n2 (VL Inductor)"
            self.voltaje_medido = "8.49 Vp ∠ +45° (XL = 100Ω)"
        elif (pos - self.pos_gnd).manhattanLength() <= radio:
            self.nodo_seleccionado = "GND (Masa)"
            self.voltaje_medido = "0.00 V"
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.fillRect(self.rect(), QColor("#1e1e2e"))

        painter.setPen(QPen(QColor("#a6adc8"), 4))
        painter.drawLine(90, 85, 165, 85)
        painter.drawLine(215, 85, 330, 85)
        painter.drawLine(390, 85, 440, 85)

        # Resistor R1
        painter.setPen(QPen(QColor("#fab387"), 3))
        painter.setBrush(QBrush(QColor("#313244")))
        painter.drawRect(165, 70, 50, 30)

        # Inductor L1 (4 espiras)
        painter.setPen(QPen(QColor("#89b4fa"), 3))
        painter.setBrush(Qt.NoBrush)
        for i in range(4):
            painter.drawArc(330 + i * 15, 75, 15, 20, 0, 180 * 16)

        painter.setPen(QColor("#cdd6f4"))
        painter.setFont(QFont("Arial", 9, QFont.Bold))
        painter.drawText(158, 60, "R1: 100Ω")
        painter.drawText(328, 60, "L1: 15.9mH")

        for nombre, pos, col in [("n1", self.pos_n1, "#cba6f7"), ("n2", self.pos_n2, "#a6e3a1"), ("GND", self.pos_gnd, "#f38ba8")]:
            sel = (self.nodo_seleccionado and nombre in self.nodo_seleccionado)
            painter.setPen(QPen(QColor("#ffffff") if sel else QColor(col), 3 if sel else 2))
            painter.setBrush(QBrush(QColor(col)))
            painter.drawEllipse(pos, 14 if sel else 10, 14 if sel else 10)
            painter.setPen(QColor("#cdd6f4"))
            painter.drawText(int(pos.x() - 12), int(pos.y() - 15), nombre)

        gx, gy, gw, gh = 55, 145, 430, 165
        painter.setPen(QPen(QColor("#89b4fa"), 2))
        painter.setBrush(QBrush(QColor("#11111b")))
        painter.drawRoundedRect(gx, gy, gw, gh, 8, 8)

        mid_y = gy + gh // 2 + 6
        painter.setPen(QPen(QColor("#313244"), 1, Qt.DashLine))
        painter.drawLine(gx, mid_y, gx + gw, mid_y)
        painter.drawLine(gx + gw // 2, gy, gx + gw // 2, gy + gh)

        if not self.nodo_seleccionado:
            painter.setPen(QColor("#a6e3a1"))
            painter.setFont(QFont("Consolas", 11, QFont.Bold))
            painter.drawText(QRectF(gx, gy, gw, gh), Qt.AlignCenter, "Haz clic en un nodo para graficar la onda AC...")
        else:
            path = QPainterPath()
            start_x = gx + 15
            num_puntos = 380
            dx = (gw - 30) / num_puntos
            amp_max = (gh // 2) - 24

            if "n1" in self.nodo_seleccionado:
                painter.setPen(QPen(QColor("#cba6f7"), 3))
                for step in range(num_puntos + 1):
                    x = start_x + step * dx
                    ang = (step / num_puntos) * 4 * math.pi
                    y = mid_y - math.sin(ang) * amp_max
                    path.moveTo(x, y) if step == 0 else path.lineTo(x, y)
                painter.drawPath(path)
            elif "n2" in self.nodo_seleccionado:
                painter.setPen(QPen(QColor("#a6e3a1"), 3))
                escala = 8.49 / 12.0
                for step in range(num_puntos + 1):
                    x = start_x + step * dx
                    ang = (step / num_puntos) * 4 * math.pi + math.radians(45)
                    y = mid_y - math.sin(ang) * (amp_max * escala)
                    path.moveTo(x, y) if step == 0 else path.lineTo(x, y)
                painter.drawPath(path)
            elif "GND" in self.nodo_seleccionado:
                painter.setPen(QPen(QColor("#f38ba8"), 2))
                painter.drawLine(gx + 15, mid_y, gx + gw - 15, mid_y)

            painter.setPen(QColor("#e2e8f7"))
            painter.setFont(QFont("Arial", 9, QFont.Bold))
            painter.drawText(gx + 12, gy + 20, f"Medición: {self.nodo_seleccionado} -> {self.voltaje_medido}")


class CircuitCanvasRLC(QWidget):
    """Lienzo para laboratorio AC Serie RLC en Resonancia (1 kHz)"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(540, 340)
        self.nodo_seleccionado = None
        self.voltaje_medido = None
        self.pos_n1 = QPointF(65, 85)
        self.pos_n2 = QPointF(205, 85)
        self.pos_n3 = QPointF(345, 85)
        self.pos_gnd = QPointF(475, 85)

    def mousePressEvent(self, event):
        pos = event.position()
        radio = 22.0
        if (pos - self.pos_n1).manhattanLength() <= radio:
            self.nodo_seleccionado = "n1 (Vin)"
            self.voltaje_medido = "12.00 Vp ∠ 0° (1 kHz)"
        elif (pos - self.pos_n2).manhattanLength() <= radio:
            self.nodo_seleccionado = "n2 (VL + VC)"
            self.voltaje_medido = "0.10 Vp (Cancelación en Resonancia)"
        elif (pos - self.pos_n3).manhattanLength() <= radio:
            self.nodo_seleccionado = "n3 (VC Capacitor)"
            self.voltaje_medido = "7.64 Vp ∠ -89.5° (XC ≈ 63.7Ω)"
        elif (pos - self.pos_gnd).manhattanLength() <= radio:
            self.nodo_seleccionado = "GND (Masa)"
            self.voltaje_medido = "0.00 V"
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.fillRect(self.rect(), QColor("#1e1e2e"))

        painter.setPen(QPen(QColor("#a6adc8"), 4))
        painter.drawLine(65, 85, 115, 85)
        painter.drawLine(160, 85, 245, 85)
        painter.drawLine(305, 85, 405, 85)
        painter.drawLine(417, 85, 475, 85)

        # R1
        painter.setPen(QPen(QColor("#fab387"), 3))
        painter.setBrush(QBrush(QColor("#313244")))
        painter.drawRect(115, 70, 45, 30)

        # L1
        painter.setPen(QPen(QColor("#89b4fa"), 3))
        painter.setBrush(Qt.NoBrush)
        for i in range(4):
            painter.drawArc(245 + i * 15, 75, 15, 20, 0, 180 * 16)

        # C1
        painter.setPen(QPen(QColor("#a6e3a1"), 4))
        painter.drawLine(405, 70, 405, 100)
        painter.drawLine(417, 70, 417, 100)

        painter.setPen(QColor("#cdd6f4"))
        painter.setFont(QFont("Arial", 8, QFont.Bold))
        painter.drawText(112, 60, "R1:100Ω")
        painter.drawText(246, 60, "L1:10mH")
        painter.drawText(390, 60, "C1:2.5µF")

        nodos = [
            ("n1", self.pos_n1, "#cba6f7"),
            ("n2", self.pos_n2, "#f9e2af"),
            ("n3", self.pos_n3, "#a6e3a1"),
            ("GND", self.pos_gnd, "#f38ba8")
        ]
        for nombre, pos, col in nodos:
            sel = (self.nodo_seleccionado and nombre in self.nodo_seleccionado)
            painter.setPen(QPen(QColor("#ffffff") if sel else QColor(col), 3 if sel else 2))
            painter.setBrush(QBrush(QColor(col)))
            painter.drawEllipse(pos, 13 if sel else 9, 13 if sel else 9)
            painter.setPen(QColor("#cdd6f4"))
            painter.drawText(int(pos.x() - 12), int(pos.y() - 15), nombre)

        gx, gy, gw, gh = 55, 145, 430, 165
        painter.setPen(QPen(QColor("#89b4fa"), 2))
        painter.setBrush(QBrush(QColor("#11111b")))
        painter.drawRoundedRect(gx, gy, gw, gh, 8, 8)

        mid_y = gy + gh // 2 + 6
        painter.setPen(QPen(QColor("#313244"), 1, Qt.DashLine))
        painter.drawLine(gx, mid_y, gx + gw, mid_y)
        painter.drawLine(gx + gw // 2, gy, gx + gw // 2, gy + gh)

        if not self.nodo_seleccionado:
            painter.setPen(QColor("#a6e3a1"))
            painter.setFont(QFont("Consolas", 11, QFont.Bold))
            painter.drawText(QRectF(gx, gy, gw, gh), Qt.AlignCenter, "Haz clic en n1, n2, n3 o GND para graficar...")
        else:
            path = QPainterPath()
            start_x = gx + 15
            num_puntos = 380
            dx = (gw - 30) / num_puntos
            amp_max = (gh // 2) - 24

            if "n1" in self.nodo_seleccionado:
                painter.setPen(QPen(QColor("#cba6f7"), 3))
                for step in range(num_puntos + 1):
                    x = start_x + step * dx
                    ang = (step / num_puntos) * 4 * math.pi
                    y = mid_y - math.sin(ang) * amp_max
                    path.moveTo(x, y) if step == 0 else path.lineTo(x, y)
                painter.drawPath(path)
            elif "n2" in self.nodo_seleccionado:
                painter.setPen(QPen(QColor("#f9e2af"), 3))
                escala = 0.08
                for step in range(num_puntos + 1):
                    x = start_x + step * dx
                    ang = (step / num_puntos) * 4 * math.pi - math.radians(89.5)
                    y = mid_y - math.sin(ang) * (amp_max * escala)
                    path.moveTo(x, y) if step == 0 else path.lineTo(x, y)
                painter.drawPath(path)
            elif "n3" in self.nodo_seleccionado:
                painter.setPen(QPen(QColor("#a6e3a1"), 3))
                escala = 7.64 / 12.0
                for step in range(num_puntos + 1):
                    x = start_x + step * dx
                    ang = (step / num_puntos) * 4 * math.pi - math.radians(89.5)
                    y = mid_y - math.sin(ang) * (amp_max * escala)
                    path.moveTo(x, y) if step == 0 else path.lineTo(x, y)
                painter.drawPath(path)
            elif "GND" in self.nodo_seleccionado:
                painter.setPen(QPen(QColor("#f38ba8"), 2))
                painter.drawLine(gx + 15, mid_y, gx + gw - 15, mid_y)

            painter.setPen(QColor("#e2e8f7"))
            painter.setFont(QFont("Arial", 9, QFont.Bold))
            painter.drawText(gx + 12, gy + 20, f"Medición: {self.nodo_seleccionado} -> {self.voltaje_medido}")


class InteractiveLabDialog(QDialog):
    """Diálogo emergente interactivo adaptado a cualquiera de los 5 laboratorios"""
    def __init__(self, title, lab_filename="voltage_divider.zip", parent=None):
        super().__init__(parent)
        tipo = identificar_tipo_lab(lab_filename)
        info = LAB_CATALOG[tipo]
        self.setWindowTitle(f"{title} - [{info['titulo']}]")
        self.setFixedSize(580, 465)

        layout = QVBoxLayout()
        lbl = QLabel(
            f"<b>{info['titulo']}</b><br>"
            f"{info['descripcion']}<br>"
            "<i>Haz clic en los nodos del circuito para medir voltaje o graficar la onda.</i>"
        )
        lbl.setWordWrap(True)
        layout.addWidget(lbl)

        # Selecciona dinámicamente el lienzo correspondiente al tipo de práctica
        if tipo == "dc_mesh":
            self.circuit_canvas = CircuitCanvasMeshDC(self)
        elif tipo == "rc":
            self.circuit_canvas = CircuitCanvasRC(self)
        elif tipo == "rl_circuit":
            self.circuit_canvas = CircuitCanvasRL(self)
        elif tipo == "rlc_circuit":
            self.circuit_canvas = CircuitCanvasRLC(self)
        else:
            self.circuit_canvas = CircuitCanvasDividerDC(self)

        layout.addWidget(self.circuit_canvas)

        btn_cerrar = QPushButton("Cerrar Simulación")
        btn_cerrar.clicked.connect(self.accept)
        layout.addWidget(btn_cerrar)

        self.setLayout(layout)


class SessionWindow(QWidget):
    SERVER_URL = "http://localhost:80"

    def __init__(self, user_id, role="student", parent=None):
        super().__init__(parent)
        self.user_id = str(user_id)
        self.role = role.lower()
        self.main_window = None
        breakpoint()  # Punto de interrupción para depuración
        self.setWindowTitle(f"VirtualLab - Panel de ({self.role.capitalize()})")
        self.setFixedSize(640, 470) if self.role == "professor" else self.setFixedSize(460, 390)

        layout = QVBoxLayout()

        # Cabecera con información del usuario autenticado
        header_layout = QHBoxLayout()
        self.lbl_info = QLabel(
            f"<b>Usuario:</b> {self.user_id} | "
            f"<b>Rol:</b> <font color='#89b4fa'>{self.role.capitalize()}</font>"
        )
        header_layout.addWidget(self.lbl_info)
        header_layout.addStretch()
        layout.addLayout(header_layout)

        # Construcción de la interfaz según el rol del usuario
        if self.role == "professor":
            prof_layout = QVBoxLayout()

            top_bar = QHBoxLayout()
            top_bar.addWidget(QLabel("<b>Panel de Gestión y Asignación de Laboratorios</b>"))
            top_bar.addStretch()
            self.btn_refrescar = QPushButton("Actualizar Listas")
            self.btn_refrescar.clicked.connect(self.cargar_datos_profesor)
            top_bar.addWidget(self.btn_refrescar)
            prof_layout.addLayout(top_bar)

            # Dos columnas: Izquierda (Estudiantes ID - Nombre) | Derecha (Laboratorios)
            columns_layout = QHBoxLayout()

            # Columna 1: Estudiantes (al cambiar de selección resalta sus labs asignados)
            col_estudiantes = QVBoxLayout()
            col_estudiantes.addWidget(QLabel("<b>1. Estudiantes (ID - Nombre)</b><br><small>Selecciona un estudiante:</small>"))
            self.list_students = QListWidget()
            self.list_students.setSelectionMode(QAbstractItemView.SingleSelection)
            self.list_students.itemSelectionChanged.connect(self.actualizar_vista_asignados)
            col_estudiantes.addWidget(self.list_students)

            # Columna 2: Laboratorios (selección múltiple con Ctrl+Clic)
            col_labs = QVBoxLayout()
            col_labs.addWidget(QLabel("<b>2. Laboratorios Disponibles</b><br><small>Clic o Ctrl+Clic para elegir uno o varios:</small>"))
            self.list_labs = QListWidget()
            self.list_labs.setSelectionMode(QAbstractItemView.ExtendedSelection)
            col_labs.addWidget(self.list_labs)

            columns_layout.addLayout(col_estudiantes, 1)
            columns_layout.addLayout(col_labs, 1)
            prof_layout.addLayout(columns_layout)

            # Botones de acción del profesor (Asignar, Quitar Asignación y Previsualizar)
            actions_layout = QHBoxLayout()
            self.btn_guardar_asignacion = QPushButton("Asignar Seleccionado(s)")
            self.btn_guardar_asignacion.clicked.connect(self.asignar_laboratorio)

            self.btn_eliminar_asignacion = QPushButton("Quitar Asignación")
            self.btn_eliminar_asignacion.clicked.connect(self.eliminar_asignacion)

            self.btn_probar_simulacion = QPushButton("Previsualizar Simulación")
            self.btn_probar_simulacion.clicked.connect(self.previsualizar_profesor)

            actions_layout.addWidget(self.btn_guardar_asignacion)
            actions_layout.addWidget(self.btn_eliminar_asignacion)
            actions_layout.addWidget(self.btn_probar_simulacion)
            prof_layout.addLayout(actions_layout)

            layout.addLayout(prof_layout)
            self.cargar_datos_profesor()

        else:
            # Vista del estudiante: consulta, descarga y simulación de prácticas asignadas
            est_layout = QVBoxLayout()
            est_layout.addWidget(QLabel("<b>Mis Laboratorios Asignados</b>"))

            self.btn_request_lab = QPushButton("Consultar / Actualizar Mis Laboratorios")
            self.btn_request_lab.clicked.connect(lambda: self.solicitar_laboratorio(silencioso=False))
            est_layout.addWidget(self.btn_request_lab)

            self.list_student_labs = QListWidget()
            self.list_student_labs.setSelectionMode(QAbstractItemView.SingleSelection)
            est_layout.addWidget(self.list_student_labs)

            self.btn_run_lab = QPushButton("Descargar y Simular Laboratorio Seleccionado")
            self.btn_run_lab.setEnabled(False)
            self.btn_run_lab.clicked.connect(self.correr_laboratorio)
            est_layout.addWidget(self.btn_run_lab)

            layout.addLayout(est_layout)
            self.solicitar_laboratorio(silencioso=True)

        # Botón común para cerrar sesión en el servidor y volver a MainWindow
        self.btn_logout = QPushButton("Cerrar Sesión / Volver al Inicio")
        self.btn_logout.clicked.connect(self.cerrar_sesion)
        layout.addWidget(self.btn_logout)

        self.setLayout(layout)

    def cargar_datos_profesor(self):
        """Carga en las dos columnas los estudiantes registrados y los laboratorios del servidor."""
        self.list_students.clear()
        self.list_labs.clear()

        try:
            # 1. Consultar estudiantes registrados y evitar duplicados visuales por ID
            res_students = client.listStudents(self.SERVER_URL, self.user_id)
            if res_students and res_students != "error":
                estudiantes = json.loads(res_students)
                vistos = set()
                for est in estudiantes:
                    est_id = str(est.get("id", "")).strip()
                    est_nombre = str(est.get("name", "")).strip()
                    if est_id and est_id not in vistos:
                        vistos.add(est_id)
                        item = QListWidgetItem(f"{est_id} - {est_nombre}")
                        item.setData(Qt.UserRole, est_id)
                        self.list_students.addItem(item)

            # 2. Consultar archivos .zip disponibles en server/labs
            res_labs = client.listProfessorsLabs(self.SERVER_URL, self.user_id)
            if res_labs and res_labs != "error":
                labs = json.loads(res_labs)
                for lab_file in labs:
                    if lab_file.endswith(".zip"):
                        nombre_amigable = obtener_nombre_amigable(lab_file)
                        item = QListWidgetItem(f"{nombre_amigable}\n({lab_file})")
                        item.setData(Qt.UserRole, lab_file)
                        self.list_labs.addItem(item)

            # 3. Limpiar o actualizar marcas visuales de asignación
            self.actualizar_vista_asignados()
        except Exception as e:
            QMessageBox.critical(self, "Error de Conexión", f"No se pudieron cargar las listas desde el servidor: {e}")

    def actualizar_vista_asignados(self):
        """Resalta en la columna derecha los laboratorios que ya tiene asignados el estudiante elegido."""
        selected_students = self.list_students.selectedItems()
        asignados = set()

        # Si hay un estudiante seleccionado, consulta sus asignaciones actuales en el servidor
        if selected_students:
            est_id = selected_students[0].data(Qt.UserRole)
            try:
                res = client.assignLab(self.SERVER_URL, self.user_id, "LIST_ASSIGNED", est_id)
                if res and res != "error":
                    asignados = set(json.loads(res))
            except Exception:
                asignados = set()

        # Adapta el tono de verde según si el sistema usa tema oscuro o claro
        es_oscuro = self.list_labs.palette().base().color().lightness() < 128
        color_asignado = QColor("#a6e3a1") if es_oscuro else QColor("#1b5e20")

        for i in range(self.list_labs.count()):
            item = self.list_labs.item(i)
            lab_file = item.data(Qt.UserRole)
            nombre_amigable = obtener_nombre_amigable(lab_file)
            if lab_file in asignados:
                item.setText(f"✔ {nombre_amigable} [ASIGNADO]\n({lab_file})")
                item.setForeground(color_asignado)
            else:
                item.setText(f"{nombre_amigable}\n({lab_file})")
                item.setData(Qt.ForegroundRole, None)

    def asignar_laboratorio(self):
        """Asigna uno o varios laboratorios seleccionados al estudiante elegido."""
        selected_students = self.list_students.selectedItems()
        if not selected_students:
            QMessageBox.warning(self, "Selección Incompleta", "Selecciona un estudiante en la columna izquierda.")
            return

        selected_labs = self.list_labs.selectedItems()
        if not selected_labs:
            QMessageBox.warning(self, "Selección Incompleta", "Selecciona uno o más laboratorios en la columna derecha.")
            return

        student_item = selected_students[0]
        est_id = student_item.data(Qt.UserRole)
        est_label = student_item.text()

        asignados_ok = []
        ya_asignados = []
        errores = []

        try:
            for lab_item in selected_labs:
                lab_file = lab_item.data(Qt.UserRole)
                res = client.assignLab(self.SERVER_URL, self.user_id, lab_file, est_id)
                if res == "error":
                    errores.append(lab_file)
                elif "already assigned" in str(res).lower():
                    ya_asignados.append(lab_file)
                else:
                    asignados_ok.append(lab_file)

            self.list_labs.clearSelection()
            self.actualizar_vista_asignados()

            # Caso 1: Todos los seleccionados ya estaban asignados previamente
            if ya_asignados and not asignados_ok and not errores:
                lista_ya = "\n".join(f"• {l}" for l in ya_asignados)
                QMessageBox.warning(
                    self,
                    "Laboratorio Ya Asignado",
                    f"El/los laboratorio(s) seleccionado(s) ya está(n) asignado(s) a {est_label}:\n\n{lista_ya}"
                )
            # Caso 2: Algunos son nuevos y otros ya estaban asignados (o hubo error)
            elif asignados_ok and (ya_asignados or errores):
                partes = [f"Nuevos asignados a {est_label}:\n" + "\n".join(f"• {l}" for l in asignados_ok)]
                if ya_asignados:
                    partes.append("Ya estaban asignados (no se duplicaron):\n" + "\n".join(f"• {l}" for l in ya_asignados))
                if errores:
                    partes.append("Con error:\n" + "\n".join(f"• {l}" for l in errores))
                QMessageBox.information(self, "Resultado de Asignación", "\n\n".join(partes))
            # Caso 3: Todos se asignaron por primera vez con éxito
            elif asignados_ok:
                lista_txt = "\n".join(f"• {l}" for l in asignados_ok)
                QMessageBox.information(
                    self,
                    "Asignación Exitosa",
                    f"Se asignaron {len(asignados_ok)} laboratorio(s) a {est_label}:\n\n{lista_txt}"
                )
            # Caso 4: Falló la asignación por error de sesión o archivo inexistente
            else:
                QMessageBox.warning(
                    self,
                    "Error de Asignación",
                    "No se pudieron asignar los laboratorios seleccionados. Verifica que los archivos existan en server/labs."
                )
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo conectar con el servidor: {e}")

    def eliminar_asignacion(self):
        """Quita uno o varios laboratorios asignados por error al estudiante seleccionado."""
        selected_students = self.list_students.selectedItems()
        if not selected_students:
            QMessageBox.warning(self, "Selección Incompleta", "Selecciona un estudiante en la columna izquierda.")
            return

        selected_labs = self.list_labs.selectedItems()
        if not selected_labs:
            QMessageBox.warning(self, "Selección Incompleta", "Selecciona uno o más laboratorios en la columna derecha.")
            return

        student_item = selected_students[0]
        est_id = student_item.data(Qt.UserRole)
        est_label = student_item.text()

        quitados_ok = []
        no_asignados = []
        errores = []

        try:
            for lab_item in selected_labs:
                lab_file = lab_item.data(Qt.UserRole)
                # Se envía el prefijo 'UNASSIGN_' reutilizando el endpoint /assign_lab
                res = client.assignLab(self.SERVER_URL, self.user_id, f"UNASSIGN_{lab_file}", est_id)
                if res == "error":
                    errores.append(lab_file)
                elif "not assigned" in str(res).lower():
                    no_asignados.append(lab_file)
                else:
                    quitados_ok.append(lab_file)

            self.list_labs.clearSelection()
            self.actualizar_vista_asignados()

            # Caso 1: Todos los seleccionados se quitaron correctamente
            if quitados_ok and not no_asignados and not errores:
                lista_txt = "\n".join(f"• {l}" for l in quitados_ok)
                QMessageBox.information(
                    self,
                    "Asignación Eliminada",
                    f"Se quitó {len(quitados_ok)} laboratorio(s) a {est_label}:\n\n{lista_txt}"
                )
            # Caso 2: Algunos se quitaron y otros no estaban asignados (o hubo error)
            elif quitados_ok and (no_asignados or errores):
                partes = [f"Quitados a {est_label}:\n" + "\n".join(f"• {l}" for l in quitados_ok)]
                if no_asignados:
                    partes.append("No estaban asignados:\n" + "\n".join(f"• {l}" for l in no_asignados))
                if errores:
                    partes.append("Con error:\n" + "\n".join(f"• {l}" for l in errores))
                QMessageBox.information(self, "Resultado", "\n\n".join(partes))
            # Caso 3: Ninguno de los seleccionados estaba asignado previamente al estudiante
            elif no_asignados and not errores:
                lista_no = "\n".join(f"• {l}" for l in no_asignados)
                QMessageBox.warning(
                    self,
                    "Sin Asignación Previa",
                    f"El/los laboratorio(s) seleccionado(s) no estaban asignados a {est_label}:\n\n{lista_no}"
                )
            # Caso 4: Falló la operación por sesión inválida o error en el servidor
            else:
                QMessageBox.warning(
                    self,
                    "Error",
                    "No se pudo quitar la asignación. Verifica tu sesión con el servidor."
                )
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo conectar con el servidor: {e}")

    def previsualizar_profesor(self):
        """Abre el diálogo interactivo para que el profesor pruebe el circuito seleccionado."""
        selected_labs = self.list_labs.selectedItems()
        item = selected_labs[0] if selected_labs else self.list_labs.currentItem()
        if not item:
            QMessageBox.warning(self, "Selecciona un Laboratorio", "Selecciona un laboratorio de la columna derecha para previsualizarlo.")
            return

        lab_filename = item.data(Qt.UserRole)
        dlg = InteractiveLabDialog(title="Previsualización del Profesor", lab_filename=lab_filename, parent=self)
        dlg.exec()

    def solicitar_laboratorio(self, silencioso=False):
        """Consulta al servidor la lista de prácticas asignadas al estudiante actual."""
        self.list_student_labs.clear()
        self.btn_run_lab.setEnabled(False)

        try:
            res_labs = client.listStudentLabs(self.SERVER_URL, self.user_id)
            if res_labs == "error" or not res_labs:
                if not silencioso:
                    QMessageBox.warning(self, "Sin Asignación", "No tienes laboratorios asignados o tu sesión no es válida.")
                return

            labs = json.loads(res_labs)
            if not labs:
                if not silencioso:
                    QMessageBox.information(self, "Sin Asignación", "Aún no tienes laboratorios asignados.")
                return

            for lab_file in labs:
                nombre_amigable = obtener_nombre_amigable(lab_file)
                item = QListWidgetItem(f"{nombre_amigable} ({lab_file})")
                item.setData(Qt.UserRole, lab_file)
                self.list_student_labs.addItem(item)

            self.list_student_labs.setCurrentRow(0)
            self.btn_run_lab.setEnabled(True)

            if not silencioso:
                QMessageBox.information(
                    self,
                    "Laboratorios Actualizados",
                    f"Tienes {len(labs)} laboratorio(s) asignado(s). Selecciona uno de la lista y presiona simular."
                )
        except Exception as e:
            if not silencioso:
                QMessageBox.critical(self, "Error", f"Error en la comunicación con el servidor: {e}")

    def correr_laboratorio(self):
        """Descarga el .zip desde el servidor y abre el simulador interactivo."""
        item = self.list_student_labs.currentItem()
        if not item:
            QMessageBox.warning(self, "Selecciona un Laboratorio", "Selecciona uno de tus laboratorios asignados.")
            return

        lab_filename = item.data(Qt.UserRole)
        try:
            # Verifica descarga real desde el servidor antes de abrir el circuito
            res_dl = client.downloadLab(self.SERVER_URL, self.user_id, lab_filename)
            if "downloaded to" not in str(res_dl):
                QMessageBox.warning(self, "Error de Descarga", f"No se pudo descargar '{lab_filename}' desde el servidor.")
                return

            dlg = InteractiveLabDialog(
                title=f"Simulación Estudiante (ID: {self.user_id})",
                lab_filename=lab_filename,
                parent=self
            )
            dlg.exec()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al descargar o ejecutar el laboratorio: {e}")

    def cerrar_sesion(self):
        """Cierra la sesión en el servidor y regresa a la ventana de inicio."""
        try:
            client.closeSession(self.SERVER_URL, self.user_id)
        except Exception:
            pass

        # Importación local para evitar importación circular con main_gui.py
        from main_gui import MainWindow
        self.main_window = MainWindow()
        self.main_window.show()
        self.close()
