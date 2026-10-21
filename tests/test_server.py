"""Pruebas para el servidor MCP de SAT."""

import json
from unittest.mock import AsyncMock, patch

import pytest

from mcp_sat.server import create_server


def _texto(resultado) -> str:
    """Extrae el texto de un resultado de llamada a herramienta MCP."""
    if isinstance(resultado, tuple):
        resultado = resultado[0]
    if hasattr(resultado, "content"):
        resultado = resultado.content
    return resultado[0].text


@pytest.mark.asyncio
async def test_server_creation_and_tools():
    server = create_server()
    assert server.name == "mcp-sat"

    # Encontrar tools
    tools = await server.list_tools()
    tool_names = [t.name for t in tools]

    assert "validar_rfc" in tool_names
    assert "consultar_cfdi" in tool_names
    assert "buscar_lista_negra" in tool_names
    assert "buscar_proveedor_lista_negra" in tool_names
    assert "actualizar_lista_sat" in tool_names


@pytest.mark.asyncio
async def test_tool_validar_rfc():
    server = create_server()
    res = await server.call_tool("validar_rfc", {"rfc": "EKU9003173C9"})
    data = json.loads(_texto(res))
    assert data["es_valido"] is True
    assert data["tipo_persona"] == "MORAL"


@pytest.mark.asyncio
async def test_tool_consultar_cfdi_mock():
    server = create_server()

    mock_resp = {
        "uuid": "00000000-0000-0000-0000-000000000000",
        "rfc_emisor": "EKU9003173C9",
        "rfc_receptor": "XAXX010101000",
        "total": "1500.00",
        "estado": "Vigente",
        "es_cancelable": "Cancelable sin aceptación",
        "estatus_cancelacion": "Ninguno",
        "codigo_estatus_sat": "S - Comprobante obtenido satisfactoriamente.",
        "validacion_efos_codigo": "200",
        "validacion_efos_diagnostico": "Limpio",
        "expresion_impresa_sat": "?test",
    }

    with patch("mcp_sat.server.CFDIClient.consultar", new_callable=AsyncMock) as mock_consultar:
        mock_consultar.return_value = mock_resp

        res = await server.call_tool(
            "consultar_cfdi",
            {
                "rfc_emisor": "EKU9003173C9",
                "rfc_receptor": "XAXX010101000",
                "total": "1500.00",
                "uuid": "00000000-0000-0000-0000-000000000000",
            },
        )
        data = json.loads(_texto(res))
        assert data["estado"] == "Vigente"
        assert data["validacion_efos_codigo"] == "200"


@pytest.mark.asyncio
async def test_tool_buscar_lista_negra_limpio(lista_manager_test):
    with patch("mcp_sat.server.Lista69Manager", return_value=lista_manager_test):
        server = create_server()
        res = await server.call_tool("buscar_lista_negra", {"rfc": "EKU9003173C9"})
        data = json.loads(_texto(res))
        assert data["en_lista_negra"] is False


@pytest.mark.asyncio
async def test_tool_buscar_proveedor(lista_manager_test):
    with patch("mcp_sat.server.Lista69Manager", return_value=lista_manager_test):
        server = create_server()
        res = await server.call_tool("buscar_proveedor_lista_negra", {"razon_social": "TEST"})
        data = json.loads(_texto(res))
        assert "total_coincidencias" in data
