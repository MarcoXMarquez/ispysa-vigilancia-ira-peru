"""
Módulo de registro rotativo de uso y eventos sin datos personales (Fase 5-bis).
Soporta las preguntas Q17 (historial de acciones) y Q24 (marca de tiempo).
Privacidad por diseño (ISO 25010): no registra direcciones IP ni identificadores personales.
"""
from datetime import datetime, timezone
import json
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Any, Dict, Optional

_LOGGER: Optional[logging.Logger] = None


def get_usage_logger(root_dir: Optional[Path] = None) -> logging.Logger:
    """Configura y retorna el logger rotativo para logs/usage.jsonl."""
    global _LOGGER
    if _LOGGER is not None:
        return _LOGGER

    if root_dir is None:
        root = Path(__file__).resolve().parents[2]
    else:
        root = Path(root_dir)

    logs_dir = root / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)
    log_file = logs_dir / "usage.jsonl"

    logger = logging.getLogger("ispysa_usage")
    logger.setLevel(logging.INFO)
    logger.propagate = False

    if not logger.handlers:
        # Rotación: 1 MB por archivo, máximo 3 backups
        handler = RotatingFileHandler(
            log_file,
            maxBytes=1_048_576,
            backupCount=3,
            encoding="utf-8",
        )
        formatter = logging.Formatter("%(message)s")
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    _LOGGER = logger
    return _LOGGER


def log_usage_event(
    event_type: str,
    params: Optional[Dict[str, Any]] = None,
    root_dir: Optional[Path] = None,
) -> Dict[str, Any]:
    """
    Registra un evento de telemetría de uso anónima en logs/usage.jsonl.
    Campos registrados: timestamp UTC, evento, parámetros de consulta.
    """
    record = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "event": str(event_type),
        "params": params or {},
    }
    logger = get_usage_logger(root_dir)
    logger.info(json.dumps(record, ensure_ascii=False))
    return record
