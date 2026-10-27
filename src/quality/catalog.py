"""
Catálogo formal de Características, Subcaracterísticas, Preguntas y Criterios
de Evaluación (EC) bajo el modelo ISO/IEC 25010 y GQM (Calabrese et al., 2018).
"""
from dataclasses import dataclass
from typing import Dict, Tuple


@dataclass(frozen=True)
class CriterionExpr:
    """Expresión lógica de un Criterio de Evaluación (EC)."""
    op: str
    questions: Tuple[str, ...]
    description: str = ""


@dataclass(frozen=True)
class Question:
    """Pregunta operacional (GQM) con metadatos de recolección."""
    id: str
    characteristic: str
    subcharacteristic: str
    question: str
    origin: str  # 'AUTOMATICA', 'DOCUMENTAL', 'NO_APLICA', 'SIN_EVIDENCIA'
    criterion_id: str
    evidence_ref: str = ""
    justification: str = ""


@dataclass(frozen=True)
class Criterion:
    """Criterio de Evaluación (EC) que agrega preguntas mediante lógica."""
    id: str
    name: str
    subcharacteristic: str
    characteristic: str
    expr: CriterionExpr
    weight: float = 1.0


@dataclass(frozen=True)
class Subcharacteristic:
    """Subcaracterística de calidad ISO/IEC 25010."""
    id: str
    name: str
    characteristic: str
    criteria: Tuple[Criterion, ...]


@dataclass(frozen=True)
class Characteristic:
    """Característica ISO/IEC 25010 con Meta GQM (Goal)."""
    id: str
    name: str
    goal: str
    subcharacteristics: Tuple[Subcharacteristic, ...]
    default_weight: float


# ==============================================================================
# 1. ADECUACIÓN FUNCIONAL (AF) — Meta G1
# ==============================================================================
CRITERIA_AF = (
    Criterion("EC_AF1", "Completitud y precisión de cálculo de tasas", "Completitud funcional", "Adecuación funcional",
              CriterionExpr("and", ("AF-1", "AF-2"), "Incidencia recalculada x 100k y tasas HR/CFR coinciden")),
    Criterion("EC_AF2", "Corrección de canal endémico", "Corrección funcional", "Adecuación funcional",
              CriterionExpr("single", ("AF-3",), "Canal endémico Bortman con cuartiles Q1 <= Q2 <= Q3")),
    Criterion("EC_AF3", "Pertinencia y cobertura espacial/temporal", "Pertinencia funcional", "Adecuación funcional",
              CriterionExpr("and", ("AF-4", "AF-5"), "Parámetros UCI documentados y 25 depts x 24 años")),
)

SUBCHARS_AF = (
    Subcharacteristic("AF_COMPLETITUD", "Completitud funcional", "Adecuación funcional", (CRITERIA_AF[0],)),
    Subcharacteristic("AF_CORRECCION", "Corrección funcional", "Adecuación funcional", (CRITERIA_AF[1],)),
    Subcharacteristic("AF_PERTINENCIA", "Pertinencia funcional", "Adecuación funcional", (CRITERIA_AF[2],)),
)

QUESTIONS_AF = (
    Question("AF-1", "Adecuación funcional", "Completitud funcional", "¿Calcula la incidencia por 100 000 hab. para ambos grupos?", "AUTOMATICA", "EC_AF1"),
    Question("AF-2", "Adecuación funcional", "Completitud funcional", "¿Tasas HR y CFR coinciden con el recálculo desde conteos?", "AUTOMATICA", "EC_AF1"),
    Question("AF-3", "Adecuación funcional", "Corrección funcional", "¿Existe canal endémico con cuartiles ordenados Q1 <= Q2 <= Q3?", "AUTOMATICA", "EC_AF2"),
    Question("AF-4", "Adecuación funcional", "Pertinencia funcional", "¿Estima demanda UCI y oxígeno con parámetros documentados?", "DOCUMENTAL", "EC_AF3", evidence_ref="Ficha técnica de triaje; Plan 04 §7; UCI 5.0%, Oxígeno 15.0 L/min"),
    Question("AF-5", "Adecuación funcional", "Pertinencia funcional", "¿Cubre los 25 departamentos y 24 años 2000-2023 para men5?", "AUTOMATICA", "EC_AF3"),
)

# ==============================================================================
# 2. EFICIENCIA DE DESEMPEÑO (ED) — Meta G2
# ==============================================================================
CRITERIA_ED = (
    Criterion("EC_ED1", "Latencia interactiva y memoización", "Comportamiento temporal", "Eficiencia de desempeño",
              CriterionExpr("and", ("ED-1", "ED-4"), "p95 <= 200 ms y uso de @st.cache_resource")),
    Criterion("EC_ED2", "Inicialización en frío de servicios", "Comportamiento temporal", "Eficiencia de desempeño",
              CriterionExpr("single", ("ED-2",), "Carga e inicialización de servicios <= 3.0 s")),
    Criterion("EC_ED3", "Estabilidad de consumo de memoria", "Uso de recursos", "Eficiencia de desempeño",
              CriterionExpr("single", ("ED-3",), "Crecimiento de memoria Heap <= 5.0 MB")),
)

SUBCHARS_ED = (
    Subcharacteristic("ED_TIEMPO", "Comportamiento temporal", "Eficiencia de desempeño", (CRITERIA_ED[0], CRITERIA_ED[1])),
    Subcharacteristic("ED_RECURSOS", "Uso de recursos", "Eficiencia de desempeño", (CRITERIA_ED[2],)),
)

QUESTIONS_ED = (
    Question("ED-1", "Eficiencia de desempeño", "Comportamiento temporal", "¿p95 de consulta y cálculo de KPIs es <= 200 ms?", "AUTOMATICA", "EC_ED1"),
    Question("ED-2", "Eficiencia de desempeño", "Comportamiento temporal", "¿Inicialización en frío de ambos servicios es <= 3.0 s?", "AUTOMATICA", "EC_ED2"),
    Question("ED-3", "Eficiencia de desempeño", "Uso de recursos", "¿Crecimiento de memoria tras 200 consultas repetidas <= 5 MB?", "AUTOMATICA", "EC_ED3"),
    Question("ED-4", "Eficiencia de desempeño", "Comportamiento temporal", "¿La app usa caché de recursos (@st.cache_resource) para servicios?", "AUTOMATICA", "EC_ED1"),
)

# ==============================================================================
# 3. FIABILIDAD (FI) — Meta G3
# ==============================================================================
CRITERIA_FI = (
    Criterion("EC_FI1", "Robustez ante datos límite y continuidad", "Tolerancia a fallos", "Fiabilidad",
              CriterionExpr("and", ("FI-1", "FI-2"), "Tasas finitas ante casos=0 y serie poblacional continua sin NaNs")),
    Criterion("EC_FI2", "Validez de intervalos predictivos", "Tolerancia a fallos", "Fiabilidad",
              CriterionExpr("single", ("FI-3",), "Bandas válidas: 0 <= lower_ci <= upper_ci")),
    Criterion("EC_FI3", "Madurez del código y pruebas unitarias", "Madurez", "Fiabilidad",
              CriterionExpr("single", ("FI-4",), "100% de la suite de pruebas unitarias aprobadas")),
)

SUBCHARS_FI = (
    Subcharacteristic("FI_TOLERANCIA", "Tolerancia a fallos", "Fiabilidad", (CRITERIA_FI[0], CRITERIA_FI[1])),
    Subcharacteristic("FI_MADUREZ", "Madurez", "Fiabilidad", (CRITERIA_FI[2],)),
)

QUESTIONS_FI = (
    Question("FI-1", "Fiabilidad", "Tolerancia a fallos", "¿Con casos=0 las tasas HR/CFR son finitas (sin NaN/inf)?", "AUTOMATICA", "EC_FI1"),
    Question("FI-2", "Fiabilidad", "Tolerancia a fallos", "¿La población interpolada no tiene NaN para 2000-2023?", "AUTOMATICA", "EC_FI1"),
    Question("FI-3", "Fiabilidad", "Tolerancia a fallos", "¿Bandas de pronóstico válidas: 0 <= lower <= upper?", "AUTOMATICA", "EC_FI2"),
    Question("FI-4", "Fiabilidad", "Madurez", "¿100% de pruebas unitarias aprueban?", "AUTOMATICA", "EC_FI3"),
)

# ==============================================================================
# 4. SEGURIDAD (SEG) — Meta G4 (Modelo UNLP, Calabrese et al., 2018)
# ==============================================================================
CRITERIA_SEG = (
    Criterion("EC_C1", "Conexiones Seguras", "Confidencialidad", "Seguridad", CriterionExpr("c1", ("Q5", "Q12"), "Q5 & ~Q12 = True")),
    Criterion("EC_C2", "Control de Acceso", "Confidencialidad", "Seguridad", CriterionExpr("not_any", ("Q7", "Q8", "Q9", "Q10", "Q11"), "~(Q7|Q8|Q9|Q10|Q11) = True")),
    Criterion("EC_C3", "Cifrado de Datos", "Confidencialidad", "Seguridad", CriterionExpr("single", ("Q6",), "Q6 = True")),
    Criterion("EC_C4", "Nivel de Complejidad de Contraseña", "Confidencialidad", "Seguridad", CriterionExpr("pwd_level", ("Q1", "Q2", "Q3", "Q4"), "Baja 0, Media 0.5, Alta 1.0")),
    Criterion("EC_I5", "Prevención de Acceso Indebido", "Integridad", "Seguridad", CriterionExpr("not_any", ("Q7", "Q8", "Q9", "Q16"), "~(Q7|Q8|Q9|Q16) = True")),
    Criterion("EC_I6", "Prevención de Modificación No Autorizada", "Integridad", "Seguridad", CriterionExpr("not_any", ("Q14", "Q15"), "~(Q14|Q15) = True")),
    Criterion("EC_I7", "Confirmación de Datos", "Integridad", "Seguridad", CriterionExpr("single", ("Q13",), "Q13 = True")),
    Criterion("EC_NR8", "Registro de Operaciones Efectuadas", "No repudio", "Seguridad", CriterionExpr("or", ("Q17", "Q23"), "Q17 | Q23 = True")),
    Criterion("EC_NR9", "Método de Criptografía Utilizado", "No repudio", "Seguridad", CriterionExpr("or", ("Q18", "Q19", "Q21"), "Q18 | Q19 | Q21 = True")),
    Criterion("EC_NR10", "Confirmación de Acciones", "No repudio", "Seguridad", CriterionExpr("single", ("Q20",), "Q20 = True")),
    Criterion("EC_NR11", "Registro de Ubicación Anómala", "No repudio", "Seguridad", CriterionExpr("single", ("Q22",), "Q22 = True")),
    Criterion("EC_R12", "Registro de Acciones y Telemetría de Acceso", "Responsabilidad", "Seguridad", CriterionExpr("or", ("Q17", "Q24", "Q25", "Q26"), "Q17|Q24|Q25|Q26 = True")),
    Criterion("EC_R13", "Control de Ubicación", "Responsabilidad", "Seguridad", CriterionExpr("single", ("Q22",), "Q22 = True")),
    Criterion("EC_A14", "Verificación de Identidad Primaria", "Autenticidad", "Seguridad", CriterionExpr("or", ("Q27", "Q30", "Q31", "Q32", "Q33"), "Q27|Q30|Q31|Q32|Q33 = True")),
    Criterion("EC_A15", "Verificación de Identidad Adicional", "Autenticidad", "Seguridad", CriterionExpr("or", ("Q28", "Q29", "Q13"), "Q28|Q29|Q13 = True")),
)

SUBCHARS_SEG = (
    Subcharacteristic("SEG_CONFIDENCIALIDAD", "Confidencialidad", "Seguridad", CRITERIA_SEG[0:4]),
    Subcharacteristic("SEG_INTEGRIDAD", "Integridad", "Seguridad", CRITERIA_SEG[4:7]),
    Subcharacteristic("SEG_NO_REPUDIO", "No repudio", "Seguridad", CRITERIA_SEG[7:11]),
    Subcharacteristic("SEG_RESPONSABILIDAD", "Responsabilidad", "Seguridad", CRITERIA_SEG[11:13]),
    Subcharacteristic("SEG_AUTENTICIDAD", "Autenticidad", "Seguridad", CRITERIA_SEG[13:15]),
)

_RAW_QUESTIONS_SEG = [
    ("Q1", "Confidencialidad", "¿Es un requisito que la contraseña tenga al menos 8 caracteres?", "NO_APLICA", "EC_C4", "", "No hay autenticación en la app."),
    ("Q2", "Confidencialidad", "¿Es un requisito que la contraseña incluya mayúsculas y minúsculas?", "NO_APLICA", "EC_C4", "", "No hay autenticación en la app."),
    ("Q3", "Confidencialidad", "¿Es un requisito que la contraseña incluya números y letras?", "NO_APLICA", "EC_C4", "", "No hay autenticación en la app."),
    ("Q4", "Confidencialidad", "¿Es un requisito que la contraseña incluya caracteres especiales?", "NO_APLICA", "EC_C4", "", "No hay autenticación en la app."),
    ("Q5", "Confidencialidad", "¿El sistema utiliza conexiones seguras a través de HTTPS?", "DOCUMENTAL", "EC_C1", "curl -sI https://ispysa-vigilancia-ira-peru.onrender.com/ | HTTP/2 200", ""),
    ("Q6", "Confidencialidad", "¿Los datos en la base de datos están cifrados?", "NO_APLICA", "EC_C3", "", "No hay base de datos; datasets públicos."),
    ("Q7", "Confidencialidad", "¿El sistema permite acceso a funcionalidades sin tener permisos asignados?", "NO_APLICA", "EC_C2", "", "Sin roles ni permisos; datos abiertos."),
    ("Q8", "Confidencialidad", "¿El sistema permite acceso a la base de datos a cualquier individuo?", "NO_APLICA", "EC_C2", "", "No hay servidor de base de datos."),
    ("Q9", "Confidencialidad", "¿El sistema permite acceso al código del servidor a cualquier individuo?", "DOCUMENTAL", "EC_C2", "Contenedor gestionado por Render; branch protection en GitHub", ""),
    ("Q10", "Confidencialidad", "¿El servidor físico es accesible por cualquier individuo?", "DOCUMENTAL", "EC_C2", "Infraestructura cloud Render con SOC 2 Type II", ""),
    ("Q11", "Confidencialidad", "¿El servidor remoto es accesible por cualquier individuo?", "DOCUMENTAL", "EC_C2", "Acceso SSH restringido a desarrolladores mediante claves públicas", ""),
    ("Q12", "Confidencialidad", "¿El sistema redirige a sitios no seguros?", "DOCUMENTAL", "EC_C1", "curl -sI http://ispysa-vigilancia-ira-peru.onrender.com redirige 301 a HTTPS", ""),
    ("Q13", "Integridad", "¿El sistema solicita confirmación de registro por correo electrónico?", "NO_APLICA", "EC_I7", "", "No hay registro de usuarios."),
    ("Q14", "Integridad", "¿El sistema permite que cualquier individuo modifique la base de datos?", "DOCUMENTAL", "EC_I6", "App de solo lectura; datos procesados inmutables en tiempo de ejecución", ""),
    ("Q15", "Integridad", "¿El sistema permite que cualquier individuo modifique el código del servidor?", "DOCUMENTAL", "EC_I6", "Contenedor inmutable en ejecución en Render; despliegue desde main", ""),
    ("Q16", "Integridad", "¿El sistema permite inyecciones SQL?", "NO_APLICA", "EC_I5", "", "No hay motor SQL (grep sqlite/psycopg en src = 0)."),
    ("Q17", "No repudio", "¿El sistema mantiene un historial de las acciones realizadas?", "DOCUMENTAL", "EC_NR8", "src/services/usage_logger.py: registro en logs/usage.jsonl", ""),
    ("Q18", "No repudio", "¿El sistema cuenta con algoritmos de cifrado de datos?", "DOCUMENTAL", "EC_NR9", "No aplica cifrado en reposo para datos epidemiológicos de acceso público", ""),
    ("Q19", "No repudio", "¿El sistema cuenta con un método criptográfico, tal como firma digital?", "DOCUMENTAL", "EC_NR9", "data/MANIFEST.sha256 con verificación criptográfica SHA-256", ""),
    ("Q20", "No repudio", "¿El sistema solicita confirmación cuando se realiza una acción crítica?", "NO_APLICA", "EC_NR10", "", "La aplicación es de solo lectura y no ejecuta acciones destructivas."),
    ("Q21", "No repudio", "¿El sistema está protegido con certificados SSL?", "DOCUMENTAL", "EC_NR9", "Certificado TLS emitido por Cloudflare / Render", ""),
    ("Q22", "No repudio", "¿El sistema emite una advertencia al acceder desde una ubicación desconocida?", "NO_APLICA", "EC_NR11", "", "Sin sesiones de usuario ni perfiles."),
    ("Q23", "No repudio", "¿El sistema envía un reporte por correo de las operaciones efectuadas?", "DOCUMENTAL", "EC_NR8", "No existe servicio SMTP ni envío de reportes", ""),
    ("Q24", "Responsabilidad", "¿El sistema registra fecha y hora de los inicios de sesión?", "DOCUMENTAL", "EC_R12", "src/services/usage_logger.py registra timestamps ISO de consultas", ""),
    ("Q25", "Responsabilidad", "¿El sistema registra el tipo de navegador y sistema operativo?", "DOCUMENTAL", "EC_R12", "Streamlit no expone User-Agent nativo; Render registra a nivel proxy", ""),
    ("Q26", "Responsabilidad", "¿El sistema registra la dirección IP desde donde se accede?", "DOCUMENTAL", "EC_R12", "No se persiste IP por privacidad de usuario", ""),
    ("Q27", "Autenticidad", "¿El sistema comprueba la identidad mediante certificado digital?", "NO_APLICA", "EC_A14", "", "Sin autenticación en la plataforma."),
    ("Q28", "Autenticidad", "¿El sistema cuenta con verificación en dos pasos (2FA)?", "NO_APLICA", "EC_A15", "", "Sin autenticación en la plataforma."),
    ("Q29", "Autenticidad", "¿Se requiere una clave de segundo nivel para ingresar al sistema?", "NO_APLICA", "EC_A15", "", "Sin autenticación en la plataforma."),
    ("Q30", "Autenticidad", "¿El sistema comprueba la identidad mediante datos biométricos?", "NO_APLICA", "EC_A14", "", "Sin autenticación en la plataforma."),
    ("Q31", "Autenticidad", "¿El sistema comprueba la identidad mediante tarjeta de coordenadas / código?", "NO_APLICA", "EC_A14", "", "Sin autenticación en la plataforma."),
    ("Q32", "Autenticidad", "¿El sistema comprueba la identidad mediante credenciales de usuario/clave?", "NO_APLICA", "EC_A14", "", "Sin autenticación en la plataforma."),
    ("Q33", "Autenticidad", "¿El sistema comprueba la identidad mediante firma digital?", "NO_APLICA", "EC_A14", "", "Sin autenticación en la plataforma."),
]

QUESTIONS_SEG = tuple(
    Question(qid, "Seguridad", sub, text, orig, ec, ev, just)
    for qid, sub, text, orig, ec, ev, just in _RAW_QUESTIONS_SEG
)

# ==============================================================================
# 5. MANTENIBILIDAD (MA) — Meta G5
# ==============================================================================
CRITERIA_MA = (
    Criterion("EC_MA1", "Aislamiento arquitectónico y modularidad", "Modularidad", "Mantenibilidad",
              CriterionExpr("and", ("MA-1", "MA-4"), "UI desacoplada de I/O de datos y archivos <= 400 líneas")),
    Criterion("EC_MA2", "Complejidad ciclomática acotada", "Analizabilidad", "Mantenibilidad",
              CriterionExpr("single", ("MA-2",), "Complejidad ciclomática máxima v(G) <= 12")),
    Criterion("EC_MA3", "Capacidad de ser probado y cobertura", "Capacidad de ser probado", "Mantenibilidad",
              CriterionExpr("single", ("MA-3",), "Cobertura de líneas en src/ >= 80 %")),
)

SUBCHARS_MA = (
    Subcharacteristic("MA_MODULARIDAD", "Modularidad", "Mantenibilidad", (CRITERIA_MA[0],)),
    Subcharacteristic("MA_ANALIZABILIDAD", "Analizabilidad", "Mantenibilidad", (CRITERIA_MA[1],)),
    Subcharacteristic("MA_TESTABILIDAD", "Capacidad de ser probado", "Mantenibilidad", (CRITERIA_MA[2],)),
)

QUESTIONS_MA = (
    Question("MA-1", "Mantenibilidad", "Modularidad", "¿Existe capa de servicios que aísla la UI del acceso a datos?", "AUTOMATICA", "EC_MA1"),
    Question("MA-2", "Mantenibilidad", "Analizabilidad", "¿Complejidad ciclomática máxima <= 12 en src/ y app.py?", "AUTOMATICA", "EC_MA2"),
    Question("MA-3", "Mantenibilidad", "Capacidad de ser probado", "¿Cobertura de líneas en src/ >= 80 %?", "AUTOMATICA", "EC_MA3"),
    Question("MA-4", "Mantenibilidad", "Modularidad", "¿Sin imports circulares y archivos <= 400 líneas?", "AUTOMATICA", "EC_MA1"),
)

# ==============================================================================
# 6. USABILIDAD (US) — Meta G6
# ==============================================================================
CRITERIA_US = (
    Criterion("EC_US1", "Accesibilidad cromática y contraste", "Accesibilidad", "Usabilidad",
              CriterionExpr("single", ("US-1",), "Contraste WCAG 2.1 AA >= 4.5:1 en tokens")),
    Criterion("EC_US2", "Protección frente a errores y redundancia", "Protección frente a errores de usuario", "Usabilidad",
              CriterionExpr("single", ("US-2",), "Codificación redundante (color + texto)")),
    Criterion("EC_US3", "Operabilidad y eficiencia ergonómica", "Operabilidad", "Usabilidad",
              CriterionExpr("and", ("US-3", "US-4"), "Navegación en <= 2 clics y auditoría libre de fallos graves")),
)

SUBCHARS_US = (
    Subcharacteristic("US_ACCESIBILIDAD", "Accesibilidad", "Usabilidad", (CRITERIA_US[0],)),
    Subcharacteristic("US_PROTECCION", "Protección frente a errores de usuario", "Usabilidad", (CRITERIA_US[1],)),
    Subcharacteristic("US_OPERABILIDAD", "Operabilidad", "Usabilidad", (CRITERIA_US[2],)),
)

QUESTIONS_US = (
    Question("US-1", "Usabilidad", "Accesibilidad", "¿Contraste >= 4.5:1 en todos los pares texto/fondo?", "AUTOMATICA", "EC_US1"),
    Question("US-2", "Usabilidad", "Protección frente a errores de usuario", "¿Estados con redundancia (texto + color)?", "AUTOMATICA", "EC_US2"),
    Question("US-3", "Usabilidad", "Operabilidad", "¿Llegar a cualquier departamento y grupo en <= 2 interacciones?", "DOCUMENTAL", "EC_US3", evidence_ref="Filtros en sidebar permiten conmutar depto y grupo en 2 clics"),
    Question("US-4", "Usabilidad", "Operabilidad", "¿Auditoría sin violaciones serious o critical?", "AUTOMATICA", "EC_US3"),
)

# ==============================================================================
# CATALOG: Tupla canónica inmutable
# ==============================================================================
CATALOG: Tuple[Characteristic, ...] = (
    Characteristic("AF", "Adecuación funcional", "G1: evaluar funciones epidemiológicas", SUBCHARS_AF, 0.25),
    Characteristic("ED", "Eficiencia de desempeño", "G2: evaluar tiempos de respuesta y memoria", SUBCHARS_ED, 0.15),
    Characteristic("FI", "Fiabilidad", "G3: evaluar robustez ante datos límite", SUBCHARS_FI, 0.20),
    Characteristic("SEG", "Seguridad", "G4: evaluar protección de datos y trazabilidad", SUBCHARS_SEG, 0.15),
    Characteristic("MA", "Mantenibilidad", "G5: evaluar modularidad, analizabilidad y pruebas", SUBCHARS_MA, 0.15),
    Characteristic("US", "Usabilidad", "G6: evaluar eficacia, satisfacción y accesibilidad", SUBCHARS_US, 0.10),
)

ALL_QUESTIONS: Tuple[Question, ...] = (
    QUESTIONS_AF + QUESTIONS_ED + QUESTIONS_FI + QUESTIONS_SEG + QUESTIONS_MA + QUESTIONS_US
)
QUESTIONS_BY_ID: Dict[str, Question] = {q.id: q for q in ALL_QUESTIONS}
ALL_CRITERIA: Tuple[Criterion, ...] = CRITERIA_AF + CRITERIA_ED + CRITERIA_FI + CRITERIA_SEG + CRITERIA_MA + CRITERIA_US
CRITERIA_BY_ID: Dict[str, Criterion] = {c.id: c for c in ALL_CRITERIA}
CHARACTERISTICS_BY_ID: Dict[str, Characteristic] = {c.id: c for c in CATALOG}
CHARACTERISTICS_BY_NAME: Dict[str, Characteristic] = {c.name: c for c in CATALOG}
