"""Pruebas unitarias para tokens visuales, contraste WCAG 2.1 AA y plantillas Plotly."""

import re
import unittest
import plotly.io as pio

from src.ui.theme import FONT, PALETTE, get_css_path, register_plotly_template


def _relative_luminance(hex_color: str) -> float:
    """Calcula la luminancia relativa conforme al estándar W3C WCAG 2.1."""
    hex_color = hex_color.lstrip("#")
    r, g, b = [int(hex_color[i:i + 2], 16) / 255.0 for i in (0, 2, 4)]

    def _channel_lum(c: float) -> float:
        return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4

    return 0.2126 * _channel_lum(r) + 0.7152 * _channel_lum(g) + 0.0722 * _channel_lum(b)


def _contrast_ratio(hex1: str, hex2: str) -> float:
    """Calcula el ratio de contraste entre dos colores hex."""
    l1 = _relative_luminance(hex1)
    l2 = _relative_luminance(hex2)
    lighter = max(l1, l2)
    darker = min(l1, l2)
    return (lighter + 0.05) / (darker + 0.05)


class TestTheme(unittest.TestCase):
    def setUp(self):
        self.css_path = get_css_path()
        self.assertTrue(self.css_path.exists(), f"El archivo {self.css_path} no existe.")
        self.css_content = self.css_path.read_text(encoding="utf-8")

    def test_wcag_contrast_text_tokens(self):
        """Verifica que los colores de texto superen el umbral WCAG AA (>= 4.5:1) sobre blanco."""
        white = "#FFFFFF"
        tokens_to_test = {
            "--c-text": "#1B2430",
            "--c-primary": "#1F4E79",
            "--c-muted": "#5B6675",
            "--c-ok-text": "#1E6B3A",
            "--c-warn-text": "#8A5300",
            "--c-bad-text": "#A32018",
        }

        for token, hex_code in tokens_to_test.items():
            ratio = _contrast_ratio(hex_code, white)
            self.assertGreaterEqual(
                ratio,
                4.5,
                f"El token {token} ({hex_code}) no cumple contraste WCAG AA: ratio={ratio:.2f} < 4.5",
            )

    def test_palette_colors_in_styles_css(self):
        """Verifica que cada color hex de PALETTE esté presente en assets/styles.css."""
        for key, val in PALETTE.items():
            if val.startswith("#"):
                self.assertIn(
                    val.lower(),
                    self.css_content.lower(),
                    f"El color {val} de PALETTE['{key}'] no aparece en styles.css",
                )

    def test_spacing_tokens_grid(self):
        """Verifica que los tokens de espaciado --sp-* sigan la rejilla matemática de 4/8 px."""
        spacing_pattern = re.compile(r"--sp-(\d+):\s*(\d+)px;")
        matches = spacing_pattern.findall(self.css_content)
        self.assertGreaterEqual(len(matches), 5, "Deben existir al menos 5 tokens de espaciado")

        for idx_str, px_str in matches:
            px_val = int(px_str)
            # Todos múltiplos de 4 (rejilla estándar de 8 px con microajuste de 4 px)
            self.assertEqual(
                px_val % 4,
                0,
                f"--sp-{idx_str} = {px_val}px no es múltiplo de 4 px",
            )

    def test_register_plotly_template(self):
        """Verifica que el template 'ispysa' quede registrado y activo en Plotly."""
        register_plotly_template()
        self.assertIn("ispysa", pio.templates)
        self.assertEqual(pio.templates.default, "ispysa")

        tmpl = pio.templates["ispysa"]
        self.assertEqual(tmpl.layout.font.family, FONT)
        self.assertEqual(tmpl.layout.font.color, PALETTE["text"])
        self.assertIsNone(tmpl.layout.title.text)

    def test_apply_and_load_css(self):
        """Verifica que theme.apply() cargue CSS e inicialice la plantilla."""
        from unittest.mock import patch
        from src.ui import theme

        with patch("src.ui.components.inject_css") as mock_inject:
            theme.apply()
            mock_inject.assert_called_once()
            css_arg = mock_inject.call_args[0][0]
            self.assertIn("--sp-1", css_arg)
            self.assertIn("--c-primary", css_arg)


if __name__ == "__main__":
    unittest.main()
