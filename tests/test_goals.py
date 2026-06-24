import unittest

from utils.goals import calcular_status_meta


class GoalsTests(unittest.TestCase):
    def test_status_meta_sob_controle(self):
        pct, cor, texto = calcular_status_meta(50.0, 100.0)

        self.assertEqual(pct, 0.5)
        self.assertEqual(cor, "green")
        self.assertIn("Sob Controle", texto)
        self.assertIn("R$ 50,00", texto)

    def test_status_meta_em_alerta(self):
        pct, cor, texto = calcular_status_meta(85.0, 100.0)

        self.assertEqual(pct, 0.85)
        self.assertEqual(cor, "orange")
        self.assertIn("Atenção", texto)
        self.assertIn("85.0%", texto)
        self.assertIn("R$ 15,00", texto)

    def test_status_meta_estourada(self):
        pct, cor, texto = calcular_status_meta(125.0, 100.0)

        self.assertEqual(pct, 1.25)
        self.assertEqual(cor, "red")
        self.assertIn("Orçamento Estourado", texto)
        self.assertIn("R$ 25,00", texto)


if __name__ == "__main__":
    unittest.main()
