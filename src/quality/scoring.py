"""
Motor de cálculo y puntuación pura para ISO/IEC 25010 y GQM (Calabrese et al., 2018).
Funciones puras sin efectos secundarios ni I/O.
"""
from typing import Any, Callable, Dict, List, Optional, Tuple

from src.quality.catalog import (
    ALL_CRITERIA,
    CATALOG,
    CRITERIA_SEG,
    SUBCHARS_SEG,
    CriterionExpr,
)

# Pesos oficiales recomendados para el Índice Global de Salud (IQ-Salud)
DEFAULT_WEIGHTS: Dict[str, float] = {
    "Adecuación funcional": 0.25,
    "Eficiencia de desempeño": 0.15,
    "Fiabilidad": 0.20,
    "Seguridad": 0.15,
    "Mantenibilidad": 0.15,
    "Usabilidad": 0.10,
}

CODE_TO_CHAR_NAME: Dict[str, str] = {
    "AF": "Adecuación funcional",
    "ED": "Eficiencia de desempeño",
    "FI": "Fiabilidad",
    "SEG": "Seguridad",
    "MA": "Mantenibilidad",
    "US": "Usabilidad",
}


def _eval_single(answers: Dict[str, Optional[bool]], qids: Tuple[str, ...]) -> float:
    return 1.0 if answers.get(qids[0]) is True else 0.0


def _eval_and(answers: Dict[str, Optional[bool]], qids: Tuple[str, ...]) -> float:
    return 1.0 if all(answers.get(q) is True for q in qids) else 0.0


def _eval_or(answers: Dict[str, Optional[bool]], qids: Tuple[str, ...]) -> float:
    return 1.0 if any(answers.get(q) is True for q in qids) else 0.0


def _eval_not_any(answers: Dict[str, Optional[bool]], qids: Tuple[str, ...]) -> float:
    return 0.0 if any(answers.get(q) is True for q in qids) else 1.0


def _eval_c1(answers: Dict[str, Optional[bool]], _qids: Tuple[str, ...]) -> float:
    return 1.0 if (answers.get("Q5") is True and not (answers.get("Q12") is True)) else 0.0


def _eval_pwd_level(answers: Dict[str, Optional[bool]], qids: Tuple[str, ...]) -> float:
    q_vals = [answers.get(qid) for qid in qids]
    cnt = sum(1 for v in q_vals if v is True)
    if cnt == len(qids):
        return 1.0
    return 0.5 if cnt > 0 else 0.0


_OP_DISPATCH: Dict[str, Callable[[Dict[str, Optional[bool]], Tuple[str, ...]], float]] = {
    "single": _eval_single,
    "and": _eval_and,
    "or": _eval_or,
    "not_any": _eval_not_any,
    "c1": _eval_c1,
    "pwd_level": _eval_pwd_level,
}


def evaluate_criterion(
    answers: Dict[str, Optional[bool]],
    expr: CriterionExpr,
) -> Optional[float]:
    """
    Evalúa un Criterio de Evaluación (EC) según las respuestas a sus preguntas.
    Retorna float (1.0, 0.5, 0.0) o None si todas las preguntas son NO_APLICA.
    """
    if all(answers.get(qid) is None for qid in expr.questions):
        return None

    handler = _OP_DISPATCH.get(expr.op)
    if handler is None:
        raise ValueError(f"Operador de criterio desconocido: {expr.op}")
    return handler(answers, expr.questions)


def score_subcharacteristic(
    criteria_scores: List[Optional[float]],
    strict: bool = True,
) -> Optional[float]:
    """
    Calcula el puntaje porcentual (0-100) de una subcaracterística.
    - strict=True: denominador fijo len(criteria_scores); criterios None valen 0.0.
    - strict=False: excluye criterios None del denominador. Retorna None si no hay aplicables.
    """
    if not criteria_scores:
        return 0.0

    if strict:
        points = sum(s for s in criteria_scores if s is not None)
        return (points / len(criteria_scores)) * 100.0

    applicable = [s for s in criteria_scores if s is not None]
    if not applicable:
        return None
    return (sum(applicable) / len(applicable)) * 100.0


def score_security_subcharacteristics(
    answers: Dict[str, Optional[bool]],
    strict: bool = True,
) -> Dict[str, Optional[float]]:
    """Calcula las 5 subcaracterísticas de Seguridad del modelo UNLP."""
    scores: Dict[str, Optional[float]] = {}
    for sub in SUBCHARS_SEG:
        crit_scores = [evaluate_criterion(answers, c.expr) for c in sub.criteria]
        scores[sub.name] = score_subcharacteristic(crit_scores, strict=strict)
    return scores


def classify(score: float) -> str:
    """Clasificación de aceptabilidad según Calabrese et al. (2018) §4.2."""
    if score < 40.0:
        return "No aceptable"
    if score < 60.0:
        return "Mínimamente aceptable"
    if score < 90.0:
        return "Objetivo"
    return "Supera"


def global_index(
    scores: Dict[str, float],
    weights: Optional[Dict[str, float]] = None,
) -> float:
    """Calcula el Índice Global ponderado (0-100)."""
    w_map = DEFAULT_WEIGHTS if weights is None else weights
    normalized: Dict[str, float] = {
        CODE_TO_CHAR_NAME.get(k, k): float(w) for k, w in w_map.items()
    }

    total_w = sum(normalized.values())
    if abs(total_w - 1.0) > 1e-4:
        raise ValueError(f"Los pesos deben sumar 1.0 (suma actual: {total_w:.6f})")

    return sum(scores.get(c, 0.0) * w for c, w in normalized.items())


def weak_link_status(
    sub_scores: Dict[str, Optional[float]],
    applicable_mask: Optional[Dict[str, bool]] = None,
) -> Tuple[bool, str]:
    """Aplica la Regla de la Cadena Débil (Calabrese et al., §4.2)."""
    for name, score in sub_scores.items():
        if score is None:
            continue
        if applicable_mask is not None and not applicable_mask.get(name, True):
            continue
        if score < 40.0:
            return False, f"No cumple: '{name}' en No aceptable ({score:.1f} %)"
    return True, "Cumple la regla de la cadena débil"


def _eval_single_char(
    char: Any,
    criteria_results: Dict[str, Optional[float]],
    sub_results: Dict[str, Optional[float]],
    strict: bool,
) -> float:
    """Calcula el puntaje agregado de una característica."""
    sub_scores: List[float] = []
    for sub in char.subcharacteristics:
        scs = [criteria_results[c.id] for c in sub.criteria]
        score_sub = score_subcharacteristic(scs, strict=strict)
        sub_results[sub.name] = score_sub
        if score_sub is not None:
            sub_scores.append(score_sub)
    return (sum(sub_scores) / len(sub_scores)) if sub_scores else 0.0


def evaluate_catalog(
    answers: Dict[str, Optional[bool]],
    strict: bool = True,
) -> Dict[str, Any]:
    """Evalúa el catálogo completo de 6 características."""
    crit_res = {c.id: evaluate_criterion(answers, c.expr) for c in ALL_CRITERIA}
    sub_res: Dict[str, Optional[float]] = {}
    char_res = {
        ch.name: _eval_single_char(ch, crit_res, sub_res, strict)
        for ch in CATALOG
    }

    idx_weighted = global_index(char_res, DEFAULT_WEIGHTS)
    equal_w = {k: 1.0 / len(CATALOG) for k in DEFAULT_WEIGHTS}
    idx_equal = global_index(char_res, equal_w)

    seg_ids = [c.id for c in CRITERIA_SEG]
    seg_app = sum(1 for cid in seg_ids if crit_res[cid] is not None)
    weak_ok, weak_msg = weak_link_status(sub_res)

    return {
        "criteria": crit_res,
        "subcharacteristics": sub_res,
        "characteristics": char_res,
        "global_index": idx_weighted,
        "global_index_equal_weights": idx_equal,
        "weak_link_passed": weak_ok,
        "weak_link_message": weak_msg,
        "security_applicability_coverage": f"{seg_app}/15",
        "security_applicable_count": seg_app,
        "total_criteria_count": len(ALL_CRITERIA),
        "total_applicable_count": sum(1 for s in crit_res.values() if s is not None),
    }
