#!/usr/bin/env python3
"""
Script de Auditoría Automatizada de Calidad de Producto Software (ISO/IEC 25010 y GQM).
Ejecuta la suite de pruebas unitarias, recolecta cobertura, corre todos los probes,
fusiona con data/quality/respuestas.csv, calcula métricas (estricto y por aplicabilidad),
aplica la regla de la cadena débil y genera data/quality/last_audit.json y outputs/quality/test_run.json.
"""
import csv
from datetime import datetime, timezone
import json
from pathlib import Path
import re
import subprocess
import sys
import time
from typing import Any, Dict, List, Optional
import unittest

# Asegurar path de importación
ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from src.quality.catalog import (  # noqa: E402
    CRITERIA_SEG,
    QUESTIONS_BY_ID,
)
from src.quality.probes import ProbeResult, run_all_probes  # noqa: E402
from src.quality.scoring import (  # noqa: E402
    classify,
    evaluate_catalog,
    score_security_subcharacteristics,
    weak_link_status,
)


def get_git_commit(root_dir: Path) -> str:
    """Obtiene el hash corto del commit actual de git."""
    try:
        res = subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=str(root_dir),
            stderr=subprocess.DEVNULL,
        ).decode("utf-8").strip()
        return res
    except Exception:
        return "desconocido"


def run_unit_tests(root_dir: Path) -> Dict[str, Any]:
    """
    Ejecuta las pruebas unitarias y genera outputs/quality/test_run.json
    y coverage.json si coverage está disponible.
    """
    outputs_dir = root_dir / "outputs" / "quality"
    outputs_dir.mkdir(parents=True, exist_ok=True)
    test_run_file = outputs_dir / "test_run.json"
    coverage_file = outputs_dir / "coverage.json"

    t0 = time.perf_counter()
    # Ejecutar suite con unittest programático
    loader = unittest.TestLoader()
    suite = loader.discover(str(root_dir / "tests"), pattern="test_*.py")
    runner = unittest.TextTestRunner(stream=None, verbosity=0)
    result = runner.run(suite)
    duration = time.perf_counter() - t0

    total = result.testsRun
    failed = len(result.failures)
    errors = len(result.errors)
    passed = total - failed - errors
    is_success = result.wasSuccessful()

    test_run_data = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "total": total,
        "passed": passed,
        "failed": failed,
        "errors": errors,
        "skipped": len(result.skipped),
        "success": is_success,
        "duration_s": round(duration, 3),
    }

    test_run_file.write_text(json.dumps(test_run_data, indent=2, ensure_ascii=False), encoding="utf-8")

    # Intentar generar reporte de cobertura en JSON si coverage está instalado
    try:
        subprocess.run(
            [sys.executable, "-m", "coverage", "json", "-o", str(coverage_file)],
            cwd=str(root_dir),
            capture_output=True,
            check=False,
        )
    except Exception:
        pass

    return test_run_data


def load_and_validate_respuestas_csv(csv_path: Path) -> List[Dict[str, str]]:
    """Carga y valida rigurosamente data/quality/respuestas.csv."""
    if not csv_path.exists():
        raise FileNotFoundError(f"Archivo de respuestas no encontrado: {csv_path}")

    rows: List[Dict[str, str]] = []
    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(row)

    ids_seen = set()
    errors: List[str] = []

    for r in rows:
        qid = r.get("id", "").strip()
        if not qid:
            errors.append("Fila con ID vacío.")
            continue
        if qid in ids_seen:
            errors.append(f"ID duplicado: {qid}")
        ids_seen.add(qid)

        origen = r.get("origen", "").strip()
        resp = r.get("respuesta", "").strip()
        ev = r.get("evidencia", "").strip()
        just = r.get("justificacion", "").strip()

        if resp == "NA" and not just:
            errors.append(f"Pregunta {qid} con respuesta NA requiere 'justificacion'.")
        if origen == "DOCUMENTAL" and resp in ("SI", "NO") and not ev:
            errors.append(f"Pregunta {qid} DOCUMENTAL con {resp} requiere 'evidencia'.")
        if resp == "SI" and re.search(r"\b(TODO|PENDIENTE)\b", ev, re.IGNORECASE):
            errors.append(f"Pregunta {qid} marcada como SI contiene TODO/pendiente en evidencia.")

    cat_ids = set(QUESTIONS_BY_ID.keys())
    missing_in_csv = cat_ids - ids_seen
    extra_in_csv = ids_seen - cat_ids
    if missing_in_csv:
        errors.append(f"Preguntas del catálogo faltantes en CSV: {missing_in_csv}")
    if extra_in_csv:
        errors.append(f"Preguntas no reconocidas en CSV: {extra_in_csv}")

    if errors:
        raise ValueError(f"Errores de validación en {csv_path.name}:\n" + "\n".join(errors))

    return rows


def update_respuestas_with_probes(
    rows: List[Dict[str, str]],
    probe_results: Dict[str, ProbeResult],
    csv_path: Path,
) -> None:
    """Actualiza las filas AUTOMATICA con los resultados reales de los probes y reescribe el CSV."""
    probe_map = dict(probe_results)
    if "NR-9" in probe_map:
        probe_map["Q19"] = probe_map["NR-9"]

    for r in rows:
        qid = r["id"]
        if r.get("origen") == "AUTOMATICA" and qid in probe_map:
            p = probe_map[qid]
            if p.value is True:
                r["respuesta"] = "SI"
            elif p.value is False:
                r["respuesta"] = "NO"
            else:
                r["respuesta"] = "SIN_EVIDENCIA"
            r["evidencia"] = f"{p.method}: {p.measured} (umbral: {p.threshold})"

    # Guardar CSV actualizado
    fieldnames = [
        "id", "caracteristica", "subcaracteristica", "pregunta", "respuesta",
        "origen", "evidencia", "justificacion", "verificado_por", "fecha"
    ]
    with open(csv_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore", quoting=csv.QUOTE_MINIMAL)
        writer.writeheader()
        writer.writerows(rows)


def build_answers_dict(rows: List[Dict[str, str]]) -> Dict[str, Optional[bool]]:
    """Convierte las respuestas textuales (SI, NO, NA, '') a dict[str, bool | None]."""
    answers: Dict[str, Optional[bool]] = {}
    for r in rows:
        qid = r["id"]
        resp = r.get("respuesta", "").strip().upper()
        if resp == "SI":
            answers[qid] = True
        elif resp == "NO":
            answers[qid] = False
        elif resp == "NA":
            answers[qid] = None
        else:
            # Vacío o SIN_EVIDENCIA -> False conservador (no cumple)
            answers[qid] = False
    return answers


def run_audit(root_dir: Optional[Path] = None) -> Dict[str, Any]:
    """Ejecuta la auditoría integral y persiste el archivo last_audit.json."""
    root = root_dir or ROOT_DIR
    git_commit = get_git_commit(root)
    audit_timestamp = datetime.now(timezone.utc).isoformat()

    # 1. Pruebas unitarias
    test_run = run_unit_tests(root)

    # 2. Ejecutar probes automáticos
    probe_results = run_all_probes(root)

    # 3. Leer y validar respuestas.csv
    csv_path = root / "data" / "quality" / "respuestas.csv"
    rows = load_and_validate_respuestas_csv(csv_path)

    # 4. Actualizar respuestas.csv con resultados de probes
    update_respuestas_with_probes(rows, probe_results, csv_path)

    # 5. Transformar a diccionario de respuestas lógicas
    answers = build_answers_dict(rows)

    # 6. Evaluar catálogo en ambos modos (estricto y por aplicabilidad)
    eval_strict = evaluate_catalog(answers, strict=True)
    eval_app = evaluate_catalog(answers, strict=False)

    # 7. Subcaracterísticas de Seguridad (modelo UNLP)
    sec_strict = score_security_subcharacteristics(answers, strict=True)
    sec_app = score_security_subcharacteristics(answers, strict=False)

    # Identificar criterios de seguridad excluidos (todas sus preguntas NA)
    excluded_sec_criteria: List[Dict[str, str]] = []
    for crit in CRITERIA_SEG:
        all_na = all(answers.get(q) is None for q in crit.expr.questions)
        if all_na:
            excluded_sec_criteria.append({
                "id": crit.id,
                "name": crit.name,
                "subcharacteristic": crit.subcharacteristic,
                "reason": f"Todas las preguntas ({', '.join(crit.expr.questions)}) marcadas como NO_APLICA",
            })

    # Regla de la cadena débil sobre subcaracterísticas aplicables
    weak_ok, weak_msg = weak_link_status(eval_app["subcharacteristics"])

    # Estado global de conformidad
    global_idx = eval_app["global_index"]
    is_conforming = weak_ok and (global_idx >= 60.0)
    estado_evaluacion = "APROBADO" if is_conforming else "REPROBADO"

    # Preparar objeto final de auditoría
    audit_record: Dict[str, Any] = {
        "generated_at": audit_timestamp,
        "git_commit": git_commit,
        "python_version": sys.version.split()[0],
        "status": estado_evaluacion,
        "global_index": round(global_idx, 2),
        "global_index_equal_weights": round(eval_app["global_index_equal_weights"], 2),
        "global_index_strict": round(eval_strict["global_index"], 2),
        "weak_link": {
            "passed": weak_ok,
            "message": weak_msg,
        },
        "scores": {k: round(v, 2) for k, v in eval_app["characteristics"].items()},
        "scores_strict": {k: round(v, 2) for k, v in eval_strict["characteristics"].items()},
        "subcharacteristics_applicable": {
            k: (round(v, 2) if v is not None else None)
            for k, v in eval_app["subcharacteristics"].items()
        },
        "subcharacteristics_strict": {
            k: (round(v, 2) if v is not None else 0.0)
            for k, v in eval_strict["subcharacteristics"].items()
        },
        "security": {
            "strict_scores": {k: round(v, 2) for k, v in sec_strict.items()},
            "applicable_scores": {k: (round(v, 2) if v is not None else None) for k, v in sec_app.items()},
            "applicability_coverage": eval_strict["security_applicability_coverage"],
            "applicable_criteria_count": eval_strict["security_applicable_count"],
            "total_security_criteria": len(CRITERIA_SEG),
            "excluded_criteria": excluded_sec_criteria,
        },
        "thresholds": {
            "no_aceptable": "< 40 %",
            "minimamente_aceptable": "40 - < 60 %",
            "objetivo": "60 - < 90 %",
            "supera": ">= 90 %",
        },
        "unit_tests": test_run,
        "questions_count": len(rows),
        "questions": rows,
        "probes": {
            qid: {
                "value": p.value,
                "measured": p.measured,
                "threshold": p.threshold,
                "evidence": p.evidence,
                "method": p.method,
                "timestamp": p.timestamp,
            }
            for qid, p in probe_results.items()
        },
    }

    # Guardar data/quality/last_audit.json
    audit_file = root / "data" / "quality" / "last_audit.json"
    audit_file.parent.mkdir(parents=True, exist_ok=True)
    audit_file.write_text(json.dumps(audit_record, indent=2, ensure_ascii=False), encoding="utf-8")

    return audit_record


def main():
    root = ROOT_DIR
    print(f"=== Iniciando Auditoría de Calidad ISO/IEC 25010 en {root.name} ===")
    audit = run_audit(root)

    print("\n" + "=" * 65)
    print(f"AUDITORÍA COMPLETADA · Commit: {audit['git_commit']} · {audit['generated_at'][:19]}")
    print("=" * 65)
    print(f"Estado de Evaluación:          {audit['status']}")
    print(f"Índice Global Ponderado:       {audit['global_index']:.1f} % ({classify(audit['global_index'])})")
    print(f"Índice Pesos Iguales (1/6):    {audit['global_index_equal_weights']:.1f} %")
    print(f"Índice Denominador Estricto:   {audit['global_index_strict']:.1f} %")
    weak_stat = 'Aprobada' if audit['weak_link']['passed'] else 'Reprobada'
    print(f"Regla de la Cadena Débil:      {weak_stat} ({audit['weak_link']['message']})")
    print(f"Cobertura Aplicabilidad SEG:   {audit['security']['applicability_coverage']}")

    print("\n--- Desglose por Característica ---")
    for name, score in audit["scores"].items():
        score_strict = audit["scores_strict"].get(name, 0.0)
        print(f"  • {name:<26} Aplicable: {score:5.1f} % | Estricto: {score_strict:5.1f} % [{classify(score)}]")

    print("\n--- Seguridad (Modelo UNLP, Calabrese et al., 2018) ---")
    for sub, sc in audit["security"]["applicable_scores"].items():
        sc_str = f"{sc:5.1f} %" if sc is not None else "  N/A  "
        sc_st = audit["security"]["strict_scores"].get(sub, 0.0)
        print(f"  • {sub:<22} Aplicable: {sc_str} | Estricto: {sc_st:5.1f} %")

    print(f"\nArchivo generado: data/quality/last_audit.json ({len(audit['questions'])} preguntas auditadas)")


if __name__ == "__main__":
    main()
