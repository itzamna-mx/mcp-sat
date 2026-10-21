"""Servidor MCP oficial para validación de CFDI y listas del SAT."""

from __future__ import annotations

import json
from typing import Any

import httpx

try:
    from mcp.server.mcpserver import MCPServer
except ImportError:  # pragma: no cover
    from mcp.server.fastmcp import FastMCP as MCPServer

from .cfdi import CFDIClient, SATCFDIError
from .constants import PACKAGE_VERSION
from .lista69 import Lista69Manager
from .rfc import validar_rfc as validar_rfc_fn


def _json(datos: Any) -> str:
    return json.dumps(datos, ensure_ascii=False, indent=2)


def create_server() -> MCPServer:
    """Crea y configura el servidor MCP para servicios y consultas oficiales del SAT."""
    server = MCPServer(
        name="mcp-sat",
        version=PACKAGE_VERSION,
        instructions=(
            "Servidor MCP para consultas oficiales y gratuitas del SAT (Servicio de Administración "
            "Tributaria de México). Permite verificar el estatus en vivo de facturas electrónicas (CFDI), "
            "revisar el padrón del Artículo 69-B del CFF (empresas fantasma / EFOS) y validar "
            "la estructura y dígito verificador de RFCs. No requiere tokens privados ni e.firma."
        ),
    )

    cfdi_client = CFDIClient()
    lista_manager = Lista69Manager()

    @server.tool()
    async def validar_rfc(rfc: str) -> str:
        """Valida la sintaxis, tipo de persona, fecha y dígito verificador de un RFC ante el SAT.

        Args:
            rfc: Clave del RFC a validar (ej. 'XAXX010101000' o 'EKU9003173C9').
        """
        resultado = validar_rfc_fn(rfc)
        return _json(resultado)

    @server.tool()
    async def consultar_cfdi(
        rfc_emisor: str,
        rfc_receptor: str,
        total: str,
        uuid: str,
    ) -> str:
        """Consulta en vivo ante el Web Service del SAT si una factura (CFDI) está Vigente o Cancelada.

        Args:
            rfc_emisor: RFC del emisor del comprobante fiscal.
            rfc_receptor: RFC del receptor del comprobante fiscal.
            total: Monto total exacto del CFDI (ej. '1500.00' o '1500').
            uuid: Folio fiscal UUID de 36 caracteres (ej. '9016A446-5A28-5425-8CBD-835F902F8D3C').
        """
        try:
            resultado = await cfdi_client.consultar(
                rfc_emisor=rfc_emisor,
                rfc_receptor=rfc_receptor,
                total=total,
                uuid=uuid,
            )
            return _json(resultado)
        except SATCFDIError as err:
            return _json({
                "error": str(err),
                "estado": "Error en consulta SAT",
                "uuid": uuid,
            })

    @server.tool()
    async def buscar_lista_negra(rfc: str) -> str:
        """Verifica al instante si un RFC está en la lista negra del SAT (Art. 69-B del CFF - EFOS).

        Permite detectar si un proveedor está catalogado como Presunto, Definitivo, Desvirtuado
        o con Sentencia Favorable.

        Args:
            rfc: RFC de la persona física o moral a consultar.
        """
        resultado = lista_manager.buscar_rfc(rfc)
        return _json(resultado)

    @server.tool()
    async def buscar_proveedor_lista_negra(razon_social: str, limite: int = 10) -> str:
        """Busca empresas o contribuyentes en la lista 69-B por coincidencia en su razón social.

        Args:
            razon_social: Nombre o razón social a buscar (ej. 'CONSTRUCCIONES', 'ASESORES').
            limite: Número máximo de resultados a devolver (por defecto 10).
        """
        coincidencias = lista_manager.buscar_por_nombre(razon_social, limite=limite)
        return _json({
            "busqueda": razon_social,
            "total_coincidencias": len(coincidencias),
            "resultados": coincidencias,
        })

    @server.tool()
    async def actualizar_lista_sat() -> str:
        """Descarga y sincroniza la última versión del listado completo del Art. 69-B publicado por el SAT."""
        try:
            resumen = await lista_manager.actualizar_listas()
            return _json(resumen)
        except (httpx.HTTPError, OSError) as err:
            return _json({
                "error": f"No se pudo actualizar la lista del SAT: {err}",
                "estado": "fallido",
            })

    return server
