import unittest
from pathlib import Path


class PortugueseCopyTests(unittest.TestCase):
    def test_textos_visiveis_nao_tem_mojibake(self):
        arquivos = list(Path("views").glob("*.py")) + list(Path("utils").glob("*.py"))
        marcadores_mojibake = ("Ã", "�", "ðŸ")
        ocorrencias = []

        for caminho in arquivos:
            texto = caminho.read_text(encoding="utf-8")
            for marcador in marcadores_mojibake:
                if marcador in texto:
                    ocorrencias.append(f"{caminho}: contem {marcador!r}")

        self.assertEqual([], ocorrencias)


if __name__ == "__main__":
    unittest.main()
