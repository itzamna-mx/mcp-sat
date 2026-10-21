"""Módulo para validación sintáctica y verificación de dígito del RFC."""

from __future__ import annotations

import re
from datetime import datetime
from typing import Any

from .constants import (
    RFC_GENERICO_EXTRANJERO,
    RFC_GENERICO_NACIONAL,
    RFC_TABLA_VALORES,
)

# Expresiones regulares para estructura oficial del RFC
RE_RFC_MORAL = re.compile(r"^[A-ZÑ&]{3}[0-9]{2}(0[1-9]|1[0-2])(0[1-9]|[12][0-9]|3[01])[A-Z0-9]{3}$")
RE_RFC_FISICA = re.compile(r"^[A-ZÑ&]{4}[0-9]{2}(0[1-9]|1[0-2])(0[1-9]|[12][0-9]|3[01])[A-Z0-9]{3}$")


def calcular_digito_verificador(rfc: str) -> str:
    """Calcula el dígito verificador oficial del SAT para un RFC.

    Acepta tanto el RFC completo (12 o 13 caracteres) como la cadena base
    sin el dígito verificador (11 o 12 caracteres).
    """
    rfc_limpio = rfc.upper().strip()
    if len(rfc_limpio) in (12, 13):
        rfc_base = rfc_limpio[:-1]
    else:
        rfc_base = rfc_limpio

    # Persona moral tiene 11 caracteres base -> se prefija con espacio para tener 12 posiciones
    if len(rfc_base) == 11:
        rfc_trabajo = " " + rfc_base
    else:
        rfc_trabajo = rfc_base

    suma = sum(RFC_TABLA_VALORES.get(c, 0) * (14 - i) for i, c in enumerate(rfc_trabajo, 1))
    resto = suma % 11
    if resto == 0:
        return "0"
    if resto == 1:
        return "A"
    return str(11 - resto)


def validar_rfc(rfc: str) -> dict[str, Any]:
    """Valida la estructura, fecha y dígito verificador de un RFC ante el estándar del SAT.

    Args:
        rfc: Cadena del RFC (con o sin guiones/espacios).

    Returns:
        Diccionario con el diagnóstico de validez, tipo de persona, fecha y dígito verificador.
    """
    if not rfc or not isinstance(rfc, str):
        return {
            "rfc": "",
            "es_valido": False,
            "tipo_persona": "INVALIDO",
            "motivo_invalido": "El RFC proporcionado está vacío o no es una cadena válida.",
        }

    rfc_limpio = re.sub(r"[\s\-_]+", "", rfc).upper()

    # Manejo de RFCs genéricos oficiales
    if rfc_limpio == RFC_GENERICO_NACIONAL:
        return {
            "rfc": rfc_limpio,
            "es_valido": True,
            "tipo_persona": "GENERICO_NACIONAL",
            "descripcion": "RFC genérico para operaciones con público en general",
            "digito_verificador_correcto": True,
        }

    if rfc_limpio == RFC_GENERICO_EXTRANJERO:
        return {
            "rfc": rfc_limpio,
            "es_valido": True,
            "tipo_persona": "GENERICO_EXTRANJERO",
            "descripcion": "RFC genérico para operaciones con residentes en el extranjero",
            "digito_verificador_correcto": True,
        }

    longitud = len(rfc_limpio)
    if longitud not in (12, 13):
        return {
            "rfc": rfc_limpio,
            "es_valido": False,
            "tipo_persona": "INVALIDO",
            "motivo_invalido": (
                f"Longitud inválida ({longitud} caracteres). Debe tener 12 (persona moral) "
                "o 13 (persona física)."
            ),
        }

    tipo_persona = "MORAL" if longitud == 12 else "FISICA"
    regex = RE_RFC_MORAL if tipo_persona == "MORAL" else RE_RFC_FISICA

    if not regex.match(rfc_limpio):
        return {
            "rfc": rfc_limpio,
            "es_valido": False,
            "tipo_persona": tipo_persona,
            "motivo_invalido": "No cumple con el patrón alfanumérico reglamentario del SAT.",
        }

    # Validar coherencia de la fecha (YYMMDD)
    idx_fecha = 3 if tipo_persona == "MORAL" else 4
    sub_fecha = rfc_limpio[idx_fecha : idx_fecha + 6]
    aa = int(sub_fecha[0:2])
    mm = int(sub_fecha[2:4])
    dd = int(sub_fecha[4:6])

    # Aproximación de siglo para personas físicas/morales
    # Años 00-49 -> 2000-2049; Años 50-99 -> 1950-1999
    anio_completo = 2000 + aa if aa <= 49 else 1900 + aa
    try:
        fecha_dt = datetime(anio_completo, mm, dd)
        fecha_iso = fecha_dt.strftime("%Y-%m-%d")
    except ValueError:
        return {
            "rfc": rfc_limpio,
            "es_valido": False,
            "tipo_persona": tipo_persona,
            "motivo_invalido": f"La fecha contenida en el RFC ({sub_fecha}) no es una fecha de calendario válida.",
        }

    # Validación del dígito verificador
    digito_esperado = calcular_digito_verificador(rfc_limpio)
    digito_real = rfc_limpio[-1]
    digito_correcto = digito_esperado == digito_real

    return {
        "rfc": rfc_limpio,
        "es_valido": digito_correcto,
        "tipo_persona": tipo_persona,
        "fecha_asociada": fecha_iso,
        "digito_verificador_esperado": digito_esperado,
        "digito_verificador_recibido": digito_real,
        "digito_verificador_correcto": digito_correcto,
        "motivo_invalido": None if digito_correcto else (
            f"El dígito verificador recibido ('{digito_real}') no coincide con el calculado ('{digito_esperado}')."
        ),
    }
