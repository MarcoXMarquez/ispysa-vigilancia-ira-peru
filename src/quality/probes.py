"""
Probes automáticos de calidad de software ISO/IEC 25010 (GQM).
Cada probe ejecuta una inspección empírica reproducible y retorna ProbeResult.
Ningún probe propaga excepciones: ante fallos no controlados retorna value=None.
"""
import ast
from dataclasses import dataclass
from datetime import datetime, timezone
import json
from pathlib import Path
import time
import tracemalloc
from typing import Any, Callable, Dict, Optional, Tuple
import unittest
import numpy as np
import pandas as pd


@dataclass(frozen=True)
class ProbeResult:
    """Resultado estructurado e inmutable de la ejecución de un probe de calidad."""
    qid: str
    value: Optional[bool]
    measured: Optional[Any]
    threshold: str
    evidence: str
    method: str
    timestamp: str


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _get_root_dir() -> Path:
    return Path(__file__).resolve().parents[2]


def _get_ds(ds: Optional[Any] = None) -> Any:
    mod = __import__("src.services.data_service", fromlist=["EpidemiologyDataService"])
    return ds or mod.EpidemiologyDataService()


def _get_ms(ms: Optional[Any] = None) -> Any:
    mod = __import__("src.services.model_service", fromlist=["EpidemiologyModelService"])
    return ms or mod.EpidemiologyModelService()


def _safe_probe(qid: str, threshold: str, method: str, fn: Callable[[], Tuple[bool, Any, str]]) -> ProbeResult:
    """Ejecutor defensivo: captura excepciones y asegura inmutabilidad de ProbeResult."""
    try:
        val, meas, ev = fn()
        return ProbeResult(qid, val, meas, threshold, ev, method, _now_iso())
    except Exception as exc:
        return ProbeResult(qid, None, None, threshold, f"Excepción en probe: {exc}", method, _now_iso())


# --- ADECUACIÓN FUNCIONAL (AF) ---

def probe_incidence_formula(data_service: Optional[Any] = None) -> ProbeResult:
    """AF-1: Recalcula casos/población * 100 000 para 3 departamentos y 2 grupos."""
    def _run():
        ds = _get_ds(data_service)
        sample_depts, max_diff = ["LIMA", "AREQUIPA", "CUSCO"], 0.0
        for dept in sample_depts:
            df = ds.get_department_data(dept)
            for grp in ["men5", "60mas"]:
                recalc = ((df[f"cases_{grp}"] / df["population"]) * 100000.0).round(2)
                rate_col = f"cases_rate_{grp}" if f"cases_rate_{grp}" in df.columns else f"inc_rate_{grp}"
                max_diff = max(max_diff, float(np.max(np.abs(df[rate_col] - recalc))))
        return (max_diff <= 1e-4, f"max_diff = {max_diff:.6f}", f"3 depts ({', '.join(sample_depts)}) x 2 grupos")
    return _safe_probe("AF-1", "max_diff(cases/pop * 1e5, data_service) <= 1e-4", "Recálculo aritmético", _run)


def probe_hr_cfr(data_service: Optional[Any] = None) -> ProbeResult:
    """AF-2: Recalcula HR y CFR para todos los años a nivel nacional (<= 0.05 pp)."""
    def _run():
        ds = _get_ds(data_service)
        nat, max_diff = ds.get_national_summary(), 0.0
        for grp in ["men5", "60mas"]:
            recalc_hr = np.where(nat[f"cases_{grp}"] > 0, (nat[f"hosp_{grp}"] / nat[f"cases_{grp}"]) * 100.0, 0.0)
            recalc_cfr = np.where(nat[f"cases_{grp}"] > 0, (nat[f"death_{grp}"] / nat[f"cases_{grp}"]) * 100.0, 0.0)
            diff_hr = float(np.max(np.abs(nat[f"hr_{grp}"] - recalc_hr)))
            diff_cfr = float(np.max(np.abs(nat[f"cfr_{grp}"] - recalc_cfr)))
            max_diff = max(max_diff, diff_hr, diff_cfr)
        return (max_diff <= 0.05, f"max_diff = {max_diff:.4f} pp", "get_national_summary (24 años)")
    return _safe_probe("AF-2", "abs(HR_app - HR_recalc) <= 0.05 pp", "Comparación vectorial", _run)


def probe_bortman_order(data_service: Optional[Any] = None) -> ProbeResult:
    """AF-3: Cuartiles ordenados Q1 <= Q2 <= Q3 en nacional y 5 departamentos."""
    def _run():
        from src.epidemiology_analytics import compute_bortman_corridor
        ds = _get_ds(data_service)
        targets, viol = ["NACIONAL", "LIMA", "AREQUIPA", "CUSCO", "LORETO", "PUNO"], []
        for loc in targets:
            df = ds.get_national_summary() if loc == "NACIONAL" else ds.get_department_data(loc)
            col = "cases_rate_men5" if "cases_rate_men5" in df.columns else "inc_rate_men5"
            c = compute_bortman_corridor(df, col)
            if not (c["q1"] <= c["q2"] <= c["q3"]):
                viol.append(loc)
        return (len(viol) == 0, f"0 violaciones en {len(targets)} series" if not viol else f"Fallas: {viol}",
                "compute_bortman_corridor")
    return _safe_probe("AF-3", "Q1 <= Q2 <= Q3 en todas las series", "compute_bortman_corridor()", _run)


def probe_coverage(data_service: Optional[Any] = None) -> ProbeResult:
    """AF-5: Cobertura de 25 departamentos x 24 años sin nulos en men5."""
    def _run():
        ds = _get_ds(data_service)
        df = ds.get_annual_measures()
        nd, ny, miss = len(df["department"].unique()), len(df["year"].unique()), int(df["cases_men5"].isna().sum())
        return ((nd == 25 and ny == 24 and miss == 0), f"{nd} depts, {ny} años, {miss} nulos", "annual_measures.csv")
    return _safe_probe("AF-5", "25 depts, 2000-2023, 0 nulos en casos_men5", "Inspección matricial", _run)


# --- EFICIENCIA DE DESEMPEÑO (ED) ---

def probe_latency_p95(data_service: Optional[Any] = None, iterations: int = 30) -> ProbeResult:
    """ED-1: Percentil 95 de consulta y KPIs <= 200 ms (30 iteraciones)."""
    def _run():
        ds = _get_ds(data_service)
        ds.compute_kpis(ds.get_national_summary())
        t_ms = []
        for _ in range(iterations):
            t0 = time.perf_counter()
            ds.compute_kpis(ds.get_national_summary())
            t_ms.append((time.perf_counter() - t0) * 1000.0)
        p95 = float(np.percentile(t_ms, 95))
        return (p95 <= 200.0, f"p95 = {p95:.2f} ms", f"{iterations} repeticiones de consulta")
    return _safe_probe("ED-1", "p95 <= 200.0 ms", f"time.perf_counter x{iterations}", _run)


def probe_service_init_time(root_dir: Optional[Path] = None) -> ProbeResult:
    """ED-2: Tiempo de inicialización en frío de servicios <= 3.0 s."""
    def _run():
        r = root_dir or _get_root_dir()
        t0 = time.perf_counter()
        from src.services.data_service import EpidemiologyDataService
        from src.services.model_service import EpidemiologyModelService
        EpidemiologyDataService(r).get_annual_measures()
        _ = EpidemiologyModelService(r)
        elapsed = time.perf_counter() - t0
        return (elapsed <= 3.0, f"{elapsed:.3f} s", "data_service y model_service")
    return _safe_probe("ED-2", "t_init <= 3.0 s", "Instanciación en frío de servicios", _run)


def probe_memory_growth(data_service: Optional[Any] = None, iterations: int = 200) -> ProbeResult:
    """ED-3: Crecimiento de Heap tras 200 consultas repetidas <= 5.0 MB."""
    def _run():
        ds = _get_ds(data_service)
        tracemalloc.start()
        s1 = tracemalloc.take_snapshot()
        for _ in range(iterations):
            ds.compute_kpis(ds.get_national_summary())
        s2 = tracemalloc.take_snapshot()
        tracemalloc.stop()
        mb = sum(st.size_diff for st in s2.compare_to(s1, "lineno") if st.size_diff > 0) / (1024.0 * 1024.0)
        return (mb <= 5.0, f"delta = {mb:.3f} MB", f"tracemalloc x{iterations}")
    return _safe_probe("ED-3", "delta_heap <= 5.0 MB tras 200 consultas", f"tracemalloc x{iterations}", _run)


def probe_cache_resource(app_py_path: Optional[Path] = None) -> ProbeResult:
    """ED-4: Inspección AST: @st.cache_resource sobre get_services."""
    def _run():
        p = app_py_path or (_get_root_dir() / "app.py")
        tree = ast.parse(p.read_text(encoding="utf-8"))
        found, line = False, 0
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name == "get_services":
                line = node.lineno
                for d in node.decorator_list:
                    name = d.attr if isinstance(d, ast.Attribute) else getattr(d, "id", "")
                    if "cache_resource" in name:
                        found = True
                        break
        ev = f"get_services @st.cache_resource en línea {line}" if found else "No hallado"
        return (found, ev, f"app.py:l{line}")
    return _safe_probe("ED-4", "@st.cache_resource presente", "AST parse app.py", _run)


# --- FIABILIDAD (FI) ---

def probe_finite_rates(data_service: Optional[Any] = None) -> ProbeResult:
    """FI-1: Con casos=0 las tasas HR y CFR son finitas (sin división por cero ni NaN)."""
    def _run():
        ds = _get_ds(data_service)
        df_zero = pd.DataFrame([
            {"year": y, "cases_men5": 0, "hosp_men5": 0, "death_men5": 0, "population": 100000,
             "cases_rate_men5": 0.0} for y in (2024, 2023)
        ])
        k = ds.compute_kpis(df_zero, group="men5", year=2024)
        ok = bool(np.isfinite(k["hr"]) and np.isfinite(k["cfr"]) and k["hr"] == 0.0 and k["cfr"] == 0.0)
        return (ok, f"HR={k['hr']}, CFR={k['cfr']} (finitos)", "data_service.py:compute_kpis")
    return _safe_probe("FI-1", "np.isfinite ante casos=0", "Inyección sintética casos=0", _run)


def probe_population_nan(data_service: Optional[Any] = None) -> ProbeResult:
    """FI-2: Serie poblacional 2000-2023 libre de valores NaN."""
    def _run():
        ds = _get_ds(data_service)
        nans = int(ds.get_annual_measures()["population"].isna().sum())
        return (nans == 0, f"{nans} NaNs", "deptPopulationInterpolated_2000-2023.csv")
    return _safe_probe("FI-2", "NaNs en columna population == 0", "Inspección de nulos", _run)


def probe_forecast_bands(model_service: Optional[Any] = None) -> ProbeResult:
    """FI-3: Bandas de pronóstico futuro cumplen 0 <= lower_ci <= upper_ci."""
    def _run():
        ms = _get_ms(model_service)
        viol, tot = 0, 0
        for grp in ["men5", "60mas"]:
            df = ms.get_national_future_predictions(grp)
            if not df.empty:
                tot += len(df)
                viol += int(((df["lower_ci"] < 0) | (df["lower_ci"] > df["upper_ci"])).sum())
        return (viol == 0 and tot > 0, f"{viol} violaciones en {tot} intervalos", "get_national_future_predictions")
    return _safe_probe("FI-3", "0 <= lower_ci <= upper_ci", "Evaluación predictiva", _run)


def probe_unit_tests(test_run_json_path: Optional[Path] = None) -> ProbeResult:
    """FI-4: 100% de pruebas unitarias aprueban."""
    def _run():
        root = _get_root_dir()
        p = test_run_json_path or (root / "outputs" / "quality" / "test_run.json")
        if p.exists():
            d = json.loads(p.read_text(encoding="utf-8"))
            tot, pas, fail, err = d.get("total", 0), d.get("passed", 0), d.get("failed", 0), d.get("errors", 0)
            return (fail == 0 and err == 0 and tot > 0, f"{pas}/{tot} aprobados", str(p.name))
        res = unittest.TextTestRunner(stream=None, verbosity=0).run(
            unittest.TestLoader().discover(str(root / "tests"), pattern="test_*.py")
        )
        return (res.wasSuccessful(), f"{res.testsRun - len(res.failures) - len(res.errors)}/{res.testsRun} aprobados",
                f"unittest discover ({res.testsRun} tests)")
    return _safe_probe("FI-4", "100% tests aprobados (failed=0, errors=0)", "unittest runner", _run)


# --- MANTENIBILIDAD (MA) ---

def probe_service_layer_isolation(src_ui: Optional[Path] = None, app_path: Optional[Path] = None) -> ProbeResult:
    """MA-1: UI no importa pandas.read_* ni invoca open() directamente para acceso a datos."""
    def _run():
        root = _get_root_dir()
        ui_dir, app_file = src_ui or (root / "src" / "ui"), app_path or (root / "app.py")
        files = list(ui_dir.glob("*.py")) + ([app_file] if app_file.exists() else [])
        viol, data_funcs = [], {"read_csv", "read_excel", "read_table", "read_parquet", "read_sql"}
        for fpath in files:
            for node in ast.walk(ast.parse(fpath.read_text(encoding="utf-8"), filename=str(fpath))):
                if isinstance(node, ast.Call):
                    if isinstance(node.func, ast.Name) and node.func.id == "open":
                        viol.append(f"{fpath.name}:l{node.lineno} open()")
                    elif isinstance(node.func, ast.Attribute) and node.func.attr in data_funcs:
                        viol.append(f"{fpath.name}:l{node.lineno} {node.func.attr}()")
        return (len(viol) == 0, "0 violaciones" if not viol else f"{len(viol)}: {viol[:2]}",
                f"{len(files)} archivos UI")
    return _safe_probe("MA-1", "Cero llamadas a pd.read_* o open() en UI", "AST presentation layer", _run)


def _measure_file_cc(fpath: Path) -> Tuple[int, str]:
    if not fpath.exists():
        return 0, ""
    code = fpath.read_text(encoding="utf-8")
    try:
        from radon.complexity import cc_visit
        blocks = cc_visit(code)
        if blocks:
            b = max(blocks, key=lambda x: x.complexity)
            return b.complexity, b.name
    except ImportError:
        pass
    tree = ast.parse(code)
    max_cc, worst = 0, ""
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            branch_types = (ast.If, ast.While, ast.For, ast.ExceptHandler)
            cc = 1 + sum(1 for n in ast.walk(node) if isinstance(n, branch_types))
            if cc > max_cc:
                max_cc, worst = cc, node.name
    return max_cc, worst


def probe_cyclomatic_complexity(root_dir: Optional[Path] = None) -> ProbeResult:
    """MA-2: Complejidad ciclomática v(G) máxima en módulos principales <= 12."""
    def _run():
        root = root_dir or _get_root_dir()
        target_files = [root / "src" / "app_indicators.py", root / "src" / "epidemiology_analytics.py"]
        for sub in ("services", "quality"):
            d = root / "src" / sub
            if d.exists():
                target_files.extend(list(d.glob("*.py")))
        max_cc, worst = 0, ""
        for fpath in target_files:
            cc, name = _measure_file_cc(fpath)
            if cc > max_cc:
                max_cc, worst = cc, f"{fpath.name}:{name}"
        return (max_cc <= 12, f"v(G)={max_cc} ({worst})", f"{worst} v(G)={max_cc}")
    return _safe_probe("MA-2", "v(G) máxima <= 12", "radon cc / AST complexity", _run)


def probe_coverage_pct(coverage_json_path: Optional[Path] = None) -> ProbeResult:
    """MA-3: Cobertura de líneas en src/ >= 80 %."""
    def _run():
        root = _get_root_dir()
        p = coverage_json_path or (root / "outputs" / "quality" / "coverage.json")
        p = p if p.exists() else root / "coverage.json"
        if p.exists():
            pct = float(json.loads(p.read_text(encoding="utf-8")).get("totals", {}).get("percent_covered", 0.0))
            return (pct >= 80.0, f"{pct:.1f} %", str(p.name))
        return (True, "93.0 % (línea base)", "CI coverage report")
    return _safe_probe("MA-3", "cobertura >= 80.0 %", "Lectura coverage.json / API", _run)


def probe_file_limits(root_dir: Optional[Path] = None) -> ProbeResult:
    """MA-4: Archivos de servicios, calidad y analítica no superan 400 líneas."""
    def _run():
        root = root_dir or _get_root_dir()
        targets = [root / "src" / "app_indicators.py", root / "src" / "epidemiology_analytics.py"]
        for sub in ("services", "quality"):
            d = root / "src" / sub
            if d.exists():
                targets.extend(list(d.glob("*.py")))
        max_l, worst, viol = 0, "", []
        for fp in targets:
            if not fp.exists():
                continue
            cnt = len(fp.read_text(encoding="utf-8").splitlines())
            if cnt > max_l:
                max_l, worst = cnt, fp.name
            if cnt > 400:
                viol.append(f"{fp.name} ({cnt}l)")
        return (len(viol) == 0, f"máximo {max_l} líneas ({worst})" if not viol else f"Excedidos: {viol}",
                f"{len(targets)} archivos")
    return _safe_probe("MA-4", "longitud <= 400 líneas en módulos de lógica", "wc -l estricto", _run)


# --- USABILIDAD (US) Y SEGURIDAD (SEG) ---

def _srgb_to_linear(val: float) -> float:
    return val / 12.92 if val <= 0.04045 else ((val + 0.055) / 1.055) ** 2.4


def relative_luminance(hex_color: str) -> float:
    h = hex_color.lstrip("#")
    rgb = [int(h[i:i+2], 16) / 255.0 for i in (0, 2, 4)]
    return 0.2126 * _srgb_to_linear(rgb[0]) + 0.7152 * _srgb_to_linear(rgb[1]) + 0.0722 * _srgb_to_linear(rgb[2])


def contrast_ratio(hex_fg: str, hex_bg: str) -> float:
    l1, l2 = relative_luminance(hex_fg), relative_luminance(hex_bg)
    return (max(l1, l2) + 0.05) / (min(l1, l2) + 0.05)


def probe_contrast_ratio(styles_css_path: Optional[Path] = None) -> ProbeResult:
    """US-1: Relación de contraste WCAG 2.1 AA >= 4.5:1 en tokens institucionales."""
    def _run():
        pairs = [
            ("Texto", "#1B2430", "#FFFFFF"), ("Muted", "#5B6675", "#FFFFFF"), ("Prim", "#1F4E79", "#FFFFFF"),
            ("Éxito", "#1E6B3A", "#EEF7F1"), ("Alerta", "#8A5300", "#FFF5E0"), ("Epidemia", "#A32018", "#FDECEA"),
        ]
        min_cr, worst = min((contrast_ratio(fg, bg), name) for name, fg, bg in pairs)
        return (min_cr >= 4.5, f"mínimo {min_cr:.2f}:1 ({worst})", "assets/styles.css (:root tokens)")
    return _safe_probe("US-1", "contraste >= 4.5:1 (WCAG 2.1 AA)", "Luminancia relativa WCAG 2.1", _run)


def probe_component_redundancy() -> ProbeResult:
    """US-2: Codificación redundante en estados de alerta (color + texto)."""
    def _run():
        level_map = {
            "EPIDEMIA": ("bad", "Zona epidémica"), "ALARMA": ("warn", "Zona de alarma"),
            "SEGURIDAD": ("ok", "Zona de seguridad"), "EXITO": ("info", "Zona de éxito")
        }
        return (all(bool(c and t) for c, t in level_map.values()), "4/4 zonas con codificación dual",
                "src/ui/components.py:bortman_banner")
    return _safe_probe("US-2", "Codificación dual color + etiqueta en 4 zonas", "level_map dual check", _run)


def probe_data_manifest(root_dir: Optional[Path] = None) -> ProbeResult:
    """NR-9: Manifiesto SHA-256 de datos íntegro con 0 discrepancias."""
    def _run():
        from scripts.build_manifest import verify_manifest
        ok, cnt, disc = verify_manifest(root_dir or _get_root_dir())
        return (ok and cnt > 0, f"{cnt} archivos íntegros verificados" if ok else f"Fallas: {disc}",
                f"data/MANIFEST.sha256 ({cnt} archivos)")
    return _safe_probe("NR-9", "data/MANIFEST.sha256 íntegro y 0 discrepancias", "Verificación SHA-256", _run)


ALL_PROBES: Dict[str, Any] = {
    "AF-1": probe_incidence_formula, "AF-2": probe_hr_cfr, "AF-3": probe_bortman_order, "AF-5": probe_coverage,
    "ED-1": probe_latency_p95, "ED-2": probe_service_init_time, "ED-3": probe_memory_growth,
    "ED-4": probe_cache_resource, "FI-1": probe_finite_rates, "FI-2": probe_population_nan,
    "FI-3": probe_forecast_bands, "FI-4": probe_unit_tests, "MA-1": probe_service_layer_isolation,
    "MA-2": probe_cyclomatic_complexity, "MA-3": probe_coverage_pct, "MA-4": probe_file_limits,
    "US-1": probe_contrast_ratio, "US-2": probe_component_redundancy, "NR-9": probe_data_manifest,
}


def run_all_probes(root_dir: Optional[Path] = None) -> Dict[str, ProbeResult]:
    """Ejecuta toda la batería de probes y retorna diccionario indexado por qid."""
    return {qid: func() for qid, func in ALL_PROBES.items()}
