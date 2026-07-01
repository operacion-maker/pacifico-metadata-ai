"""
Governance Pillars — derived from lineamiento_gobierno_metadatos.md

Defines the 4 pillars of functional metadata quality and the evaluation
criteria the LLM judge uses to score each draft.
"""

from typing import TypedDict

# ── Pillar Weights (must sum to 1.0) ──────────────────────────────────

PILLAR_WEIGHTS: dict[str, float] = {
    "clarity": 0.25,
    "purpose": 0.25,
    "detail": 0.25,
    "context": 0.25,
}


class PillarSpec(TypedDict):
    name_es: str
    description: str
    table_questions: list[str]
    column_questions: list[str]


GOVERNANCE_PILLARS: dict[str, PillarSpec] = {
    "clarity": {
        "name_es": "Claridad y Comprensión",
        "description": (
            "Las definiciones deben ser claras, precisas y comprensibles, "
            "evitando ambigüedades. Todo término técnico debe ser explicado "
            "para asegurar una correcta interpretación del dato."
        ),
        "table_questions": [
            "¿Qué representa esta tabla en términos de negocio?",
            "¿Qué tipo de tabla es? (hechos, dimensión, maestro, data entry, etc.)",
            "¿Existen términos técnicos que deban aclararse?",
            "¿Con qué frecuencia se actualiza la información?",
        ],
        "column_questions": [
            "¿Qué permite identificar, clasificar o medir?",
            "¿Qué reglas de negocio aplica?",
        ],
    },
    "purpose": {
        "name_es": "Propósito del Dato",
        "description": (
            "Los metadatos deben proporcionar el contexto de negocio del dato, "
            "describiendo para qué se utiliza dentro de la organización y "
            "cuál es su valor, permitiendo comprender claramente su uso esperado."
        ),
        "table_questions": [
            "¿Para qué se usa esta tabla en el negocio?",
            "¿Qué proceso(s) de negocio habilita o impacta?",
            "¿Quién(es) la utilizan?",
        ],
        "column_questions": [
            "¿Para qué sirve este dato dentro del negocio?",
            "¿Qué decisiones se apoyan en este dato?",
        ],
    },
    "detail": {
        "name_es": "Nivel de Detalle",
        "description": (
            "El nivel de detalle describe el contenido, alcance y condiciones "
            "del dato, incluyendo escenarios de uso, excepciones y "
            "particularidades relevantes."
        ),
        "table_questions": [
            "¿Qué productos de datos, modelos analíticos o soluciones la utilizan?",
            "¿Incluye información histórica o solo estado actual?",
            "¿Existen reglas relevantes que definan su alcance o interpretación?",
        ],
        "column_questions": [
            "¿Cuál es el dominio de valores esperado y qué significa cada uno?",
            "¿Es un valor único por entidad o puede haber múltiples?",
            "¿El dato es obligatorio o puede estar vacío?",
            "¿El dato es calculado o derivado?",
            "¿Qué campos o fuentes participan en su cálculo?",
        ],
    },
    "context": {
        "name_es": "Contexto y Relacionamiento",
        "description": (
            "Los metadatos deben describir el contexto del dato, sus "
            "relaciones y su rol dentro del ecosistema de información "
            "de la organización."
        ),
        "table_questions": [
            "¿De qué fuentes o sistemas proviene la información?",
            "¿Con qué otras tablas o activos de datos se relaciona?",
            "¿Cómo se integra dentro del ecosistema de datos?",
        ],
        "column_questions": [
            "¿Está basado en algún estándar o clasificación externa?",
            "¿Se utiliza para segmentación, scoring o reporting?",
            "¿Está alineado con definiciones corporativas?",
        ],
    },
}


# ── Governance Principles (7 mandatory) ───────────────────────────────

GOVERNANCE_PRINCIPLES: list[dict[str, str]] = [
    {
        "id": "P1",
        "name": "Unicidad",
        "rule": (
            "Cada activo de datos debe tener una única definición canónica, "
            "validada y publicada. No se permiten definiciones paralelas "
            "o informales."
        ),
    },
    {
        "id": "P2",
        "name": "Colaboración obligatoria con el negocio",
        "rule": (
            "Toda definición de metadatos funcionales debe construirse "
            "en conjunto con las áreas de negocio responsables del activo."
        ),
    },
    {
        "id": "P3",
        "name": "Trazabilidad del proceso",
        "rule": (
            "Toda definición o actualización de metadatos debe seguir el "
            "flujo establecido con sus entregables correspondientes."
        ),
    },
    {
        "id": "P4",
        "name": "Aprobación formal",
        "rule": (
            "Ningún metadato puede considerarse oficial sin el Visto Bueno "
            "del Domain Owner correspondiente."
        ),
    },
    {
        "id": "P5",
        "name": "Actualización continua",
        "rule": (
            "Los metadatos deben actualizarse cada vez que el activo sufra "
            "cambios estructurales, funcionales o de uso."
        ),
    },
    {
        "id": "P6",
        "name": "Clasificación correcta",
        "rule": (
            "Metadatos técnicos y funcionales no son intercambiables. Deben "
            "documentarse de forma separada y complementaria."
        ),
    },
    {
        "id": "P7",
        "name": "Publicación centralizada",
        "rule": (
            "El repositorio oficial de metadatos debe ser el sistema "
            "centralizado de gobierno (Unity Catalog / MS Purview)."
        ),
    },
]
