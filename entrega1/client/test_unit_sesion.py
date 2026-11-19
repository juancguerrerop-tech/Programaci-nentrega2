import unittest
from session_window import identificar_tipo_lab, obtener_nombre_amigable


class TestSessionHelpers(unittest.TestCase):
    def test_identificar_tipo_lab(self):
        # Verificar orden de prioridad (rlc antes que rl, dc_mesh antes que default)
        self.assertEqual(identificar_tipo_lab("practica_rlc_final.zip"), "rlc_circuit")
        self.assertEqual(identificar_tipo_lab("circuito_rl.zip"), "rl_circuit")
        self.assertEqual(identificar_tipo_lab("rc.zip"), "rc")
        self.assertEqual(identificar_tipo_lab("malla_dc.zip"), "dc_mesh")
        self.assertEqual(identificar_tipo_lab("voltage_divider.zip"), "voltage_divider")

    def test_obtener_nombre_amigable(self):
        self.assertEqual(
            obtener_nombre_amigable("rc.zip"),
            "Circuito RC (AC - Carga y Descarga)"
        )
