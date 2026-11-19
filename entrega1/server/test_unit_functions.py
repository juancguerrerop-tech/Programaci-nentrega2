import os
import tempfile
import unittest
from unittest.mock import patch
import virtuallab_functions as vf


class TestVirtualLabFunctions(unittest.TestCase):
    def setUp(self):
        # 1. Crear un directorio temporal aislado para cada prueba
        self.temp_dir = tempfile.TemporaryDirectory()
        self.test_users = os.path.join(self.temp_dir.name, "users.txt")
        self.test_assignments = os.path.join(self.temp_dir.name, "assignments.txt")
        self.test_labs = os.path.join(self.temp_dir.name, "labs")
        os.makedirs(self.test_labs, exist_ok=True)

        # 2. Redirigir las rutas globales del módulo al entorno temporal
        self.patches = [
            patch.object(vf, "usersFile", self.test_users),
            patch.object(vf, "assignmentsFile", self.test_assignments),
            patch.object(vf, "labsDir", self.test_labs),
        ]
        for p in self.patches:
            p.start()

        # 3. Limpiar las sesiones activas en memoria
        vf.openSessions.clear()

    def tearDown(self):
        for p in self.patches:
            p.stop()
        vf.openSessions.clear()
        self.temp_dir.cleanup()

    def test_lab_file_name_agrega_extension(self):
        self.assertEqual(vf.labFileName("rc"), "rc.zip")
        self.assertEqual(vf.labFileName("rc.zip"), "rc.zip")

    def test_registro_y_duplicados(self):
        res1 = vf.registerUser("Ana", "101", "professor", "1234")
        self.assertEqual(res1, "User Ana with role professor registered")

        res2 = vf.registerUser("Otra", "101", "student", "9999")
        self.assertEqual(res2, "User already registered")

    def test_flujo_sesion_y_validacion_contrasena(self):
        vf.registerUser("Eva", "202", "student", "clave_ok")

        # Contraseña incorrecta
        self.assertEqual(vf.openSession("202", "mala"), "error")
        self.assertNotIn("202", vf.openSessions)

        # Contraseña correcta
        self.assertEqual(vf.openSession("202", "clave_ok"), "Session was succesfully opened")
        self.assertIn("202", vf.openSessions)

        # Cierre de sesión
        self.assertEqual(vf.closeSession("202"), "Session was succesfully closed")
        self.assertNotIn("202", vf.openSessions)

    def test_asignar_laboratorio_evita_duplicados(self):
        vf.registerUser("Prof", "1", "professor", "p1")
        vf.registerUser("Est", "2", "student", "s1")
        vf.openSession("1", "p1")

        # Simular un .zip existente en el directorio temporal
        with open(os.path.join(self.test_labs, "rc.zip"), "wb") as f:
            f.write(b"PK_fake_zip")

        # Primera asignación exitosa (sin extensión .zip)
        res_ok = vf.assignLab("1", "rc", "2")
        self.assertEqual(res_ok, "Lab rc.zip was succesfully assigned to student 2")

        # Segunda asignación del mismo laboratorio debe avisar que ya existe
        res_dup = vf.assignLab("1", "rc.zip", "2")
        self.assertEqual(res_dup, "Lab rc.zip is already assigned to student 2")

def test_read_assignments_formato_plano(self):
        with open(self.test_assignments, "w", encoding="utf-8") as f:
            f.write("202:rc.zip\n")
            f.write("303:voltage_divider.zip\n")

        asignaciones = vf.readAssignments()
        self.assertEqual(len(asignaciones), 2)
        self.assertEqual(asignaciones[0], {"student_id": "202", "lab": "rc.zip"})
        self.assertEqual(asignaciones[1], {"student_id": "303", "lab": "voltage_divider.zip"})
