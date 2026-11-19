import sys
import os
import math
import json
import shutil
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, 
    QMessageBox, QDialog, QComboBox, QLineEdit
)
from PySide6.QtGui import QPainter, QPen, QBrush, QColor, QFont, QPainterPath
from PySide6.QtCore import Qt, QRectF, QPointF
import virtuallab_client as client

class CircuitCanvasDC(QWidget):
    """Lienzo gráfico para laboratorio DC (Divisor de Voltaje)"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(500, 300)
        self.vin, self.r1, self.r2 = 12.0, 1000.0, 1000.0
        self.nodo_seleccionado, self.voltaje_medido = None, None
        self.pos_nodo_in, self.pos_nodo_out, self.pos_nodo_gnd = QPointF(100, 130), QPointF(250, 130), QPointF(400, 130)

    def mousePressEvent(self, event):
        pos = event.position()
        radio = 25.0
        if (pos - self.pos_nodo_in).manhattanLength() <= radio:
            self.nodo_seleccionado, self.voltaje_medido = "Vin (DC)", f"{self.vin:.2f} V"
        elif (pos - self.pos_nodo_out).manhattanLength() <= radio:
            vout = self.vin * (self.r2 / (self.r1 + self.r2))
            self.nodo_seleccionado, self.voltaje_medido = "Vout (DC)", f"{vout:.2f} V"
        elif (pos - self.pos_nodo_gnd).manhattanLength() <= radio:
            self.nodo_seleccionado, self.voltaje_medido = "GND", "0.00 V"
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.fillRect(self.rect(), QColor("#1e1e2e"))

        painter.setPen(QPen(QColor("#a6adc8"), 4))
        painter.drawLine(100, 130, 180, 130)
        painter.drawLine(220, 130, 330, 130)
        painter.drawLine(370, 130, 400, 130)

        painter.setPen(QPen(QColor("#f9e2af"), 3))
        painter.setBrush(QBrush(QColor("#313244")))
        painter.drawRect(180, 115, 40, 30)
        painter.drawRect(330, 115, 40, 30)

        painter.setPen(QColor("#cdd6f4"))
        painter.setFont(QFont("Arial", 9, QFont.Bold))
        painter.drawText(175, 105, "R1: 1kΩ")
        painter.drawText(325, 105, "R2: 1kΩ")

        for nombre, pos, col in [("Vin", self.pos_nodo_in, "#89b4fa"), ("Vout", self.pos_nodo_out, "#a6e3a1"), ("GND", self.pos_nodo_gnd, "#f38ba8")]:
            sel = (self.nodo_seleccionado and nombre in self.nodo_seleccionado)
            painter.setPen(QPen(QColor("#ffffff") if sel else QColor(col), 3 if sel else 2))
            painter.setBrush(QBrush(QColor(col)))
            painter.drawEllipse(pos, 14 if sel else 10, 14 if sel else 10)
            painter.setPen(QColor("#cdd6f4"))
            painter.drawText(int(pos.x() - 15), int(pos.y() - 20), nombre)

        painter.setPen(QPen(QColor("#89b4fa"), 2))
        painter.setBrush(QBrush(QColor("#181825")))
        painter.drawRoundedRect(120, 190, 260, 80, 10, 10)
        painter.setPen(QColor("#a6e3a1"))
        painter.setFont(QFont("Consolas", 11, QFont.Bold))
        txt = f"Nodo: {self.nodo_seleccionado}\nVoltaje: {self.voltaje_medido}" if self.nodo_seleccionado else "Haz clic en un nodo..."
        painter.drawText(QRectF(120, 190, 260, 80), Qt.AlignCenter, txt)


class CircuitCanvasAC(QWidget):
    """Lienzo para laboratorio AC con gráfica dinámica de Carga y Descarga"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(500, 340)
        self.v_peak = 12.0
        self.nodo_seleccionado = None
        self.voltaje_medido = None
        self.pos_nodo_in, self.pos_nodo_out, self.pos_nodo_gnd = QPointF(100, 100), QPointF(250, 100), QPointF(400, 100)

    def mousePressEvent(self, event):
        pos = event.position()
        radio = 25.0
        if (pos - self.pos_nodo_in).manhattanLength() <= radio:
            self.nodo_seleccionado = "Vac (Entrada)"
            self.voltaje_medido = "12.0 Vp (Onda Cuadrada / Seno)"
        elif (pos - self.pos_nodo_out).manhattanLength() <= radio:
            self.nodo_seleccionado = "Vc (Capacitor)"
            self.voltaje_medido = "Carga t=RC / Descarga t=3RC"
        elif (pos - self.pos_nodo_gnd).manhattanLength() <= radio:
            self.nodo_seleccionado = "GND / Masa"
            self.voltaje_medido = "0.00 V"
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.fillRect(self.rect(), QColor("#1e1e2e"))

        painter.setPen(QPen(QColor("#a6adc8"), 4))
        painter.drawLine(100, 100, 180, 100)
        painter.drawLine(220, 100, 330, 100)
        painter.drawLine(370, 100, 400, 100)

        painter.setPen(QPen(QColor("#fab387"), 3))
        painter.setBrush(QBrush(QColor("#313244")))
        painter.drawRect(180, 85, 40, 30)

        painter.setPen(QPen(QColor("#89b4fa"), 4))
        painter.drawLine(345, 85, 345, 115)
        painter.drawLine(355, 85, 355, 115)

        painter.setPen(QColor("#cdd6f4"))
        painter.setFont(QFont("Arial", 9, QFont.Bold))
        painter.drawText(175, 75, "R: 1kΩ")
        painter.drawText(335, 75, "C: 10µF")

        for nombre, pos, col in [("Vac", self.pos_nodo_in, "#cba6f7"), ("Vc", self.pos_nodo_out, "#a6e3a1"), ("GND", self.pos_nodo_gnd, "#f38ba8")]:
            sel = (self.nodo_seleccionado and nombre in self.nodo_seleccionado)
            painter.setPen(QPen(QColor("#ffffff") if sel else QColor(col), 3 if sel else 2))
            painter.setBrush(QBrush(QColor(col)))
            painter.drawEllipse(pos, 14 if sel else 10, 14 if sel else 10)
            painter.setPen(QColor("#cdd6f4"))
            painter.drawText(int(pos.x() - 15), int(pos.y() - 15), nombre)

        gx, gy, gw, gh = 60, 150, 380, 150
        painter.setPen(QPen(QColor("#89b4fa"), 2))
        painter.setBrush(QBrush(QColor("#11111b")))
        painter.drawRoundedRect(gx, gy, gw, gh, 8, 8)

        painter.setPen(QPen(QColor("#313244"), 1, Qt.DashLine))
        painter.drawLine(gx, gy + gh//2, gx + gw, gy + gh//2)
        painter.drawLine(gx + gw//2, gy, gx + gw//2, gy + gh)

        if not self.nodo_seleccionado:
            painter.setPen(QColor("#a6e3a1"))
            painter.setFont(QFont("Consolas", 11, QFont.Bold))
            painter.drawText(QRectF(gx, gy, gw, gh), Qt.AlignCenter, "Haz clic en un nodo para graficar la onda...")
        else:
            path = QPainterPath()
            
            if "Vac" in self.nodo_seleccionado:
                painter.setPen(QPen(QColor("#cba6f7"), 2))
                path.moveTo(gx + 10, gy + gh - 20)
                for i in range(3):
                    x_start = gx + 10 + i * 110
                    path.lineTo(x_start, gy + 20)
                    path.lineTo(x_start + 55, gy + 20)
                    path.lineTo(x_start + 55, gy + gh - 20)
                    path.lineTo(x_start + 110, gy + gh - 20)
                painter.drawPath(path)

            elif "Vc" in self.nodo_seleccionado:
                painter.setPen(QPen(QColor("#a6e3a1"), 3))
                start_x = gx + 10
                path.moveTo(start_x, gy + gh - 20)
                
                num_puntos = 350
                dx = (gw - 20) / num_puntos
                for step in range(num_puntos):
                    x = start_x + step * dx
                    t = (step % 100) / 20.0
                    
                    if (step // 100) % 2 == 0:
                        val = 1.0 - math.exp(-t)
                    else:
                        val = math.exp(-t)
                    
                    y = (gy + gh - 20) - val * (gh - 40)
                    path.lineTo(x, y)
                
                painter.drawPath(path)

            elif "GND" in self.nodo_seleccionado:
                painter.setPen(QPen(QColor("#f38ba8"), 2))
                painter.drawLine(gx + 10, gy + gh - 20, gx + gw - 10, gy + gh - 20)

            painter.setPen(QColor("#e2e8f7"))
            painter.setFont(QFont("Arial", 9, QFont.Bold))
            painter.drawText(gx + 10, gy + 20, f"Medición: {self.nodo_seleccionado} -> {self.voltaje_medido}")


class InteractiveLabDialog(QDialog):
    """Diálogo emergente con botón de cerrar estándar activo"""
    def __init__(self, title, es_ac=False, parent=None):
        super().__init__(parent)
        tipo_str = "Corriente Alterna (AC - Carga y Descarga RC)" if es_ac else "Corriente Directa (DC - Divisor)"
        self.setWindowTitle(f"{title} - [{tipo_str}]")
        
        self.setFixedSize(540, 430)

        layout = QVBoxLayout()
        lbl = QLabel(f"<b>Modo: {tipo_str}</b><br>Haz clic en los nodos para visualizar la gráfica en el osciloscopio.")
        lbl.setWordWrap(True)
        layout.addWidget(lbl)

        self.circuit_canvas = CircuitCanvasAC(self) if es_ac else CircuitCanvasDC(self)
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
        self.lab_filename = "voltage_divider.zip"
        self.es_laboratorio_ac = False

        self.setWindowTitle(f"VirtualLab - Panel de ({self.role.capitalize()})")
        self.setFixedSize(380, 260 if self.role == "student" else 360)

        layout = QVBoxLayout()
        self.lbl_info = QLabel(f"<b>Usuario:</b> {self.user_id} | <b>Rol:</b> <font color='#89b4fa'>{self.role.capitalize()}</font>")
        layout.addWidget(self.lbl_info)

        if self.role == "professor":
            prof_layout = QVBoxLayout()
            prof_layout.addWidget(QLabel("<b> Panel de Gestión y Previsualización</b>"))

            lbl_target = QLabel("ID del estudiante a asignar:")
            self.txt_estudiante_id = QLineEdit()
            self.txt_estudiante_id.setPlaceholderText("Ej: 123")
            
            lbl_tipo = QLabel("Seleccionar Laboratorio:")
            self.combo_lab = QComboBox()
            self.combo_lab.addItems(["Divisor de Voltaje (DC)", "Circuito AC (Carga/Descarga RC)"])

            self.btn_guardar_asignacion = QPushButton("Guardar Asignación")
            self.btn_guardar_asignacion.clicked.connect(self.asignar_laboratorio)

            self.btn_probar_simulacion = QPushButton(" Previsualizar Simulación Seleccionada")
            self.btn_probar_simulacion.clicked.connect(self.previsualizar_profesor)

            prof_layout.addWidget(lbl_target)
            prof_layout.addWidget(self.txt_estudiante_id)
            prof_layout.addWidget(lbl_tipo)
            prof_layout.addWidget(self.combo_lab)
            prof_layout.addWidget(self.btn_guardar_asignacion)
            prof_layout.addWidget(self.btn_probar_simulacion)
            
            layout.addLayout(prof_layout)
        else:
            est_layout = QVBoxLayout()
            est_layout.addWidget(QLabel("<b> Mi Laboratorio Asignado</b>"))

            self.btn_request_lab = QPushButton("Solicitar mi laboratorio")
            self.btn_request_lab.clicked.connect(self.solicitar_laboratorio)
            est_layout.addWidget(self.btn_request_lab)

            self.btn_run_lab = QPushButton("Simular Laboratorio")
            self.btn_run_lab.setEnabled(False)
            self.btn_run_lab.clicked.connect(self.correr_laboratorio)
            est_layout.addWidget(self.btn_run_lab)

            layout.addLayout(est_layout)

        self.setLayout(layout)

    def asignar_laboratorio(self):
        est_id = self.txt_estudiante_id.text().strip()
        if not est_id:
            QMessageBox.warning(self, "Error", "Ingresa el ID del estudiante para realizar la asignación.")
            return

        opcion = self.combo_lab.currentText()
        # Nombre exacto del paquete zip en el servidor
        lab_archivo = "rc.zip" if "AC" in opcion else "voltage_divider.zip"

        try:
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            server_dir = os.path.join(base_dir, "server")
            labs_dir = os.path.join(server_dir, "labs")
            os.makedirs(labs_dir, exist_ok=True)

            # Verificar y copiar el archivo zip a server/labs si aún no existe allí
            target_lab = os.path.join(labs_dir, lab_archivo)
            if not os.path.exists(target_lab):
                client_lab = os.path.join(base_dir, "client", lab_archivo)
                if os.path.exists(client_lab):
                    shutil.copy(client_lab, target_lab)

            assign_file = os.path.join(server_dir, "assignments.txt")

            lineas = []
            encontrado = False

            if os.path.exists(assign_file):
                with open(assign_file, "r", encoding="utf-8") as f:
                    for linea in f:
                        if linea.startswith(f"{est_id}:"):
                            lineas.append(f"{est_id}:{lab_archivo}\n")
                            encontrado = True
                        else:
                            lineas.append(linea)

            if not encontrado:
                lineas.append(f"{est_id}:{lab_archivo}\n")

            with open(assign_file, "w", encoding="utf-8") as f:
                f.writelines(lineas)

            QMessageBox.information(self, "Éxito", f"Laboratorio '{lab_archivo}' asignado al estudiante ID: {est_id}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo guardar la asignación: {e}")

    def previsualizar_profesor(self):
        opcion = self.combo_lab.currentText()
        es_ac = ("AC" in opcion)
        dlg = InteractiveLabDialog(title="Previsualización del Profesor", es_ac=es_ac, parent=self)
        dlg.exec()

    def solicitar_laboratorio(self):
        assigned_lab = None

        # 1. Intentar consultar listStudentLabs del servidor
        try:
            res_labs = client.listStudentLabs(self.SERVER_URL, self.user_id)
            if res_labs and res_labs != "error":
                labs = json.loads(res_labs)
                if labs:
                    assigned_lab = labs[-1]
        except Exception:
            pass

        # 2. Leer assignments.txt de forma local si falla la API
        if not assigned_lab:
            try:
                base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                assign_file = os.path.join(base_dir, "server", "assignments.txt")

                if os.path.exists(assign_file):
                    with open(assign_file, "r", encoding="utf-8") as f:
                        for linea in f:
                            if linea.startswith(f"{self.user_id}:"):
                                assigned_lab = linea.split(":")[1].strip()
            except Exception:
                pass

        if not assigned_lab:
            QMessageBox.warning(self, "Sin Asignación", "No tienes ningún laboratorio asignado actualmente.")
            return

        self.lab_filename = assigned_lab
        self.es_laboratorio_ac = ("rc" in self.lab_filename.lower() or "ac" in self.lab_filename.lower())

        # 3. Solicitar descarga al servidor
        try:
            res_dl = client.downloadLab(self.SERVER_URL, self.user_id, self.lab_filename)
            if "downloaded to" not in str(res_dl):
                QMessageBox.warning(self, "Error de Descarga", f"No se pudo descargar el archivo '{self.lab_filename}'. Verifique el servidor.")
                return
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error en la petición de descarga: {e}")
            return

        self.btn_run_lab.setEnabled(True)
        tipo = "Circuito AC (Carga/Descarga RC)" if self.es_laboratorio_ac else "Divisor de Voltaje (DC)"
        QMessageBox.information(self, "Laboratorio Asignado", f"Tu laboratorio asignado es:\n- Archivo: {self.lab_filename}\n- Tipo: {tipo}")

    def correr_laboratorio(self):
        dlg = InteractiveLabDialog(title=f"Simulación Estudiante (ID: {self.user_id})", es_ac=self.es_laboratorio_ac, parent=self)
        dlg.exec()
        self.btn_run_lab.setEnabled(False)