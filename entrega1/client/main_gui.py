import sys
import os
import json
from PySide6.QtWidgets import (
    QApplication, QWidget, QLabel, QLineEdit, 
    QComboBox, QPushButton, QVBoxLayout, QHBoxLayout, QMessageBox
)
from session_window import SessionWindow
import virtuallab_client as client

class MainWindow(QWidget):
    SERVER_URL = "http://localhost:80"

    def __init__(self):
        super().__init__()
        self.setWindowTitle("VirtualLab - Cliente")
        
        # Tamaño fijo (mantiene la X activa y deshabilita el maximizar)
        self.setFixedSize(350, 280)

        self.segunda_ventana = None

        layout = QVBoxLayout()

        # Campo Nombre
        layout.addWidget(QLabel("Nombre:"))
        self.txt_nombre = QLineEdit()
        layout.addWidget(self.txt_nombre)

        # Campo ID
        layout.addWidget(QLabel("ID:"))
        self.txt_id = QLineEdit()
        layout.addWidget(self.txt_id)

        # ComboBox Rol
        layout.addWidget(QLabel("Rol:"))
        self.combo_rol = QComboBox()
        self.combo_rol.addItems(["student", "professor"])
        layout.addWidget(self.combo_rol)

        # Campo Contraseña
        layout.addWidget(QLabel("Contraseña:"))
        self.txt_password = QLineEdit()
        self.txt_password.setEchoMode(QLineEdit.Password)
        layout.addWidget(self.txt_password)

        # Botones
        btn_layout = QHBoxLayout()
        self.btn_register = QPushButton("Registrarse")
        self.btn_login = QPushButton("Iniciar sesión")
        btn_layout.addWidget(self.btn_register)
        btn_layout.addWidget(self.btn_login)
        layout.addLayout(btn_layout)

        self.setLayout(layout)

        # Eventos
        self.btn_register.clicked.connect(self.registrarse)
        self.btn_login.clicked.connect(self.iniciar_sesion)

    def registrarse(self):
        nombre = self.txt_nombre.text().strip()
        user_id = self.txt_id.text().strip()
        rol = self.combo_rol.currentText().lower()
        password = self.txt_password.text().strip()

        if not user_id or not nombre or not password:
            QMessageBox.warning(self, "Error", "Completa todos los campos para registrarte.")
            return

        try:
            client.registerUser(self.SERVER_URL, nombre, user_id, rol, password)
        except Exception:
            pass

        try:
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            users_file_path = os.path.join(base_dir, "server", "users.txt")

            nuevo_usuario = {
                "name": nombre,
                "id": user_id,
                "role": rol,
                "password": password
            }

            with open(users_file_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(nuevo_usuario) + "\n")

            QMessageBox.information(self, "Registro Exitoso", f"Usuario '{nombre}' (ID: {user_id}) registrado correctamente.")
        except Exception as e:
            QMessageBox.information(self, "Registro", f"Usuario '{nombre}' registrado (Aviso: {e}).")

    def iniciar_sesion(self):
        user_id = self.txt_id.text().strip()
        password = self.txt_password.text().strip()
        rol_seleccionado = self.combo_rol.currentText().lower()

        if not user_id or not password:
            QMessageBox.warning(self, "Error", "Ingresa el ID y la contraseña para iniciar sesión.")
            return

        # 1. Validar la autenticación con el servidor
        try:
            respuesta = client.openSession(self.SERVER_URL, user_id, password)
            if respuesta != "Session was succesfully opened":
                QMessageBox.warning(self, "Error", "ID o contraseña incorrectos.")
                return
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo conectar con el servidor: {e}")
            return

        # 2. Consultar el rol real registrado en users.txt
        rol_real = None
        try:
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            users_file_path = os.path.join(base_dir, "server", "users.txt")

            if os.path.exists(users_file_path):
                with open(users_file_path, "r", encoding="utf-8") as f:
                    for linea in f:
                        if not linea.strip():
                            continue
                        try:
                            usuario = json.loads(linea.strip())
                            if str(usuario.get("id")) == user_id:
                                rol_real = usuario.get("role", "").lower()
                                break
                        except Exception:
                            continue
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Error al verificar información de usuario: {e}")
            return

        # 3. Bloquear el acceso si el rol no coincide
        if rol_real and rol_real != rol_seleccionado:
            QMessageBox.warning(
                self, 
                "Rol No Autorizado", 
                f"El usuario con ID '{user_id}' está registrado como '{rol_real.capitalize()}', "
                f"no como '{rol_seleccionado.capitalize()}'."
            )
            return

        # 4. Iniciar sesión con el rol verificado
        self.segunda_ventana = SessionWindow(user_id=user_id, role=rol_real if rol_real else rol_seleccionado)
        self.segunda_ventana.show()
        self.close()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())