"""
Módulo de Calidad de Producto Software ISO/IEC 25010 (GQM).
Exporta el catálogo de características, motor de puntuación y probes automáticos.
"""
from src.quality.catalog import (
    ALL_CRITERIA,
    ALL_QUESTIONS,
    CATALOG,
    CHARACTERISTICS_BY_ID,
    CHARACTERISTICS_BY_NAME,
    CRITERIA_BY_ID,
    QUESTIONS_BY_ID,
    Characteristic,
    Criterion,
    CriterionExpr,
    Question,
    Subcharacteristic,
)
from src.quality.scoring import (
    DEFAULT_WEIGHTS,
    classify,
    evaluate_catalog,
    evaluate_criterion,
    global_index,
    score_security_subcharacteristics,
    score_subcharacteristic,
    weak_link_status,
)
from src.quality.probes import (
    ALL_PROBES,
    ProbeResult,
    contrast_ratio,
    relative_luminance,
    run_all_probes,
)

__all__ = [
    "ALL_CRITERIA",
    "ALL_QUESTIONS",
    "CATALOG",
    "CHARACTERISTICS_BY_ID",
    "CHARACTERISTICS_BY_NAME",
    "CRITERIA_BY_ID",
    "QUESTIONS_BY_ID",
    "Characteristic",
    "Criterion",
    "CriterionExpr",
    "Question",
    "Subcharacteristic",
    "DEFAULT_WEIGHTS",
    "classify",
    "evaluate_catalog",
    "evaluate_criterion",
    "global_index",
    "score_security_subcharacteristics",
    "score_subcharacteristic",
    "weak_link_status",
    "ALL_PROBES",
    "ProbeResult",
    "contrast_ratio",
    "relative_luminance",
    "run_all_probes",
]
