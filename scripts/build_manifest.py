#!/usr/bin/env python3
"""
Fase 5-bis: Constructor del Manifiesto Criptográfico de Integridad de Datos (SHA-256).
Genera data/MANIFEST.sha256 con los hashes de los datasets en data/processed y outputs/tables.
Cumple con los requisitos de Integridad (Q19/NR-9) y reproducibilidad técnica.
"""
import hashlib
from pathlib import Path
from typing import List, Tuple


def compute_sha256(file_path: Path) -> str:
    """Calcula el hash SHA-256 en bloques de 64 KB para evitar consumo de memoria."""
    hasher = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def generate_manifest(root_dir: Path) -> List[Tuple[str, str]]:
    """
    Escanea data/processed y outputs/tables, calcula los hashes y genera
    la lista de tuplas (sha256, ruta_relativa).
    """
    target_dirs = [
        root_dir / "data" / "processed",
        root_dir / "outputs" / "tables",
    ]

    manifest_entries: List[Tuple[str, str]] = []

    for d in target_dirs:
        if not d.exists():
            continue
        for file_path in sorted(d.rglob("*")):
            if file_path.is_file() and not file_path.name.startswith("."):
                rel_path = file_path.relative_to(root_dir).as_posix()
                sha = compute_sha256(file_path)
                manifest_entries.append((sha, rel_path))

    return manifest_entries


def write_manifest(root_dir: Path, manifest_entries: List[Tuple[str, str]]) -> Path:
    """Escribe data/MANIFEST.sha256 con formato estándar sha256sum."""
    manifest_file = root_dir / "data" / "MANIFEST.sha256"
    manifest_file.parent.mkdir(parents=True, exist_ok=True)

    lines = [f"{sha}  {rel_path}\n" for sha, rel_path in manifest_entries]
    with open(manifest_file, "w", encoding="utf-8") as f:
        f.writelines(lines)

    return manifest_file


def verify_manifest(root_dir: Path) -> Tuple[bool, int, List[str]]:
    """
    Verifica que todos los archivos listados en data/MANIFEST.sha256 existan
    y que su hash SHA-256 coincida exactamente.
    Retorna (es_valido, total_archivos, lista_de_discrepancias).
    """
    manifest_file = root_dir / "data" / "MANIFEST.sha256"
    if not manifest_file.exists():
        return False, 0, ["El archivo data/MANIFEST.sha256 no existe."]

    discrepancies: List[str] = []
    total = 0

    with open(manifest_file, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            parts = line.split(maxsplit=1)
            if len(parts) != 2:
                continue
            expected_sha, rel_path = parts[0].strip(), parts[1].strip()
            file_path = root_dir / rel_path
            total += 1

            if not file_path.exists():
                discrepancies.append(f"Archivo faltante: {rel_path}")
                continue

            actual_sha = compute_sha256(file_path)
            if actual_sha != expected_sha:
                discrepancies.append(
                    f"Hash corrupto en {rel_path}: esperado {expected_sha[:8]}..., obtenido {actual_sha[:8]}..."
                )

    is_valid = len(discrepancies) == 0 and total > 0
    return is_valid, total, discrepancies


def main():
    root_dir = Path(__file__).resolve().parents[1]
    entries = generate_manifest(root_dir)
    manifest_path = write_manifest(root_dir, entries)
    print(f"Manifiesto generado exitosamente: {manifest_path} ({len(entries)} archivos)")

    # Auto-verificación
    ok, count, errors = verify_manifest(root_dir)
    if ok:
        print(f"Verificación inmediata exitosa: {count} archivos íntegros.")
    else:
        print(f"Error en verificación: {errors}")


if __name__ == "__main__":
    main()
