from pathlib import Path

index_path = Path("html-slide-viewer/index.html")
content = index_path.read_text(encoding="utf-8")

is_crlf = "\r\n" in content
content = content.replace("\r\n", "\n")

target = """          <optgroup label="Diapositivas del Proyecto">
            <option value="../slides/trabajo_enunciado_solucion_tp5/enunciado_solucion.html">"""

replacement = """          <optgroup label="Diapositivas del Proyecto">
            <option value="../slides/trabajo_6_iso29119/diapositivas_iso29119.html" selected>TP6 - Automatización E2E ISO 29119 (Grupo 02)</option>
            <option value="../slides/trabajo_enunciado_solucion_tp5/enunciado_solucion.html">"""

assert target in content, "Target not found in index.html"
content = content.replace(target, replacement, 1)

if is_crlf:
    content = content.replace("\n", "\r\n")

index_path.write_text(content, encoding="utf-8")
print("Successfully registered TP6 in html-slide-viewer/index.html!")
