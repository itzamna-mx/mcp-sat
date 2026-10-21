"""Constantes y URLs oficiales para los servicios del SAT."""

from __future__ import annotations

import os
from pathlib import Path

PACKAGE_VERSION = "0.1.0"

# Endpoint oficial de validación de CFDI mediante Web Service SOAP (ConsultaCFDIService)
SAT_CFDI_SOAP_URL = "https://consultaqr.facturaelectronica.sat.gob.mx/ConsultaCFDIService.svc"
SAT_CFDI_SOAP_ACTION = "http://tempuri.org/IConsultaCFDIService/Consulta"

# URL oficial de descarga del Listado Completo del Artículo 69-B del CFF (EFOS)
SAT_LISTA_69B_URL = "http://omawww.sat.gob.mx/cifras_sat/Documents/Listado_Completo_69-B.csv"

# Directorio de caché local para bases de datos SQLite
CACHE_DIR = Path(os.environ.get("MCP_SAT_CACHE_DIR", Path.home() / ".cache" / "mcp-sat"))
DB_PATH = CACHE_DIR / "lista_69b.sqlite3"

# RFCs genéricos oficiales del SAT
RFC_GENERICO_NACIONAL = "XAXX010101000"
RFC_GENERICO_EXTRANJERO = "XEXX010101000"

# Mapeo de caracteres para cálculo de dígito verificador del RFC según el SAT
RFC_TABLA_VALORES = {
    "0": 0, "1": 1, "2": 2, "3": 3, "4": 4, "5": 5, "6": 6, "7": 7, "8": 8, "9": 9,
    "A": 10, "B": 11, "C": 12, "D": 13, "E": 14, "F": 15, "G": 16, "H": 17, "I": 18,
    "J": 19, "K": 20, "L": 21, "M": 22, "N": 23, "&": 24, "O": 25, "P": 26, "Q": 27,
    "R": 28, "S": 29, "T": 30, "U": 31, "V": 32, "W": 33, "X": 34, "Y": 35, "Z": 36,
    " ": 37, "Ñ": 38,
}
