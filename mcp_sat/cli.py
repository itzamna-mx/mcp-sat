"""Interfaz de línea de comandos para mcp-sat."""

from __future__ import annotations

import argparse
import asyncio
import sqlite3
import sys

import httpx

from . import __version__
from .cfdi import CFDIClient, SATCFDIError
from .lista69 import Lista69Manager
from .server import create_server


def build_transport_security(allowed_hosts: list[str] | None):
    """Arma la configuración anti DNS-rebinding para los transportes HTTP."""
    if not allowed_hosts:
        return None

    from mcp.server.transport_security import TransportSecuritySettings

    hosts: list[str] = []
    origins: list[str] = []
    for nombre in allowed_hosts:
        for entrada in (nombre, f"{nombre}:*"):
            if entrada not in hosts:
                hosts.append(entrada)
        for entrada in (f"https://{nombre}", f"http://{nombre}"):
            if entrada not in origins:
                origins.append(entrada)

    for entrada in ("127.0.0.1:*", "localhost:*", "[::1]:*"):
        if entrada not in hosts:
            hosts.append(entrada)
    for entrada in ("http://127.0.0.1:*", "http://localhost:*", "http://[::1]:*"):
        if entrada not in origins:
            origins.append(entrada)

    return TransportSecuritySettings(
        enable_dns_rebinding_protection=True,
        allowed_hosts=hosts,
        allowed_origins=origins,
    )


def test_connection() -> int:
    """Prueba la conexión al servicio SOAP del SAT consultando el estatus de un comprobante de prueba."""
    print("=" * 60)
    print(f"mcp-sat v{__version__} - Verificación de conexión con el SAT")
    print("=" * 60)
    print("Conectando con el Web Service oficial de validación de CFDI...")

    client = CFDIClient(timeout=10.0)

    async def _run():
        try:
            # Consulta con RFCs de prueba estándar del SAT
            res = await client.consultar(
                rfc_emisor="EKU9003173C9",
                rfc_receptor="XAXX010101000",
                total="100.00",
                uuid="00000000-0000-0000-0000-000000000000",
            )
            print("-> Respuesta recibida del SAT:")
            print(f"   Código de estatus: {res['codigo_estatus_sat']}")
            print(f"   Estado del CFDI:   {res['estado']}")
            print("-> Conectividad con el SAT verificada correctamente (100% gratuita y sin credenciales).")
            return 0
        except SATCFDIError as err:
            print(f"[ERROR] Falló la conexión con el SAT: {err}")
            return 1

    return asyncio.run(_run())


def actualizar_listas_cli() -> int:
    """Descarga el padrón oficial del Artículo 69-B del SAT."""
    print("=" * 60)
    print(f"mcp-sat v{__version__} - Descarga de Lista 69-B (EFOS)")
    print("=" * 60)
    print("Descargando archivo oficial desde el portal del SAT...")

    manager = Lista69Manager()

    async def _run():
        try:
            resumen = await manager.actualizar_listas()
            print("-> Base de datos actualizada con éxito:")
            print(f"   Total contribuyentes importados: {resumen['total_importados']}")
            print(f"   Fecha de actualización:          {resumen['actualizado_en']}")
            print(f"   Ubicación:                       {manager.db_path}")
            return 0
        except (httpx.HTTPError, sqlite3.Error, OSError) as err:
            print(f"[ERROR] No se pudo descargar la lista: {err}")
            return 1

    return asyncio.run(_run())


def mostrar_info() -> int:
    """Muestra información sobre el estado de la base de datos local del SAT."""
    manager = Lista69Manager()
    estado = manager.obtener_estado_bd()
    print("=" * 60)
    print(f"mcp-sat v{__version__} - Información local de datos SAT")
    print("=" * 60)
    print(f"Base de datos SQLite:       {estado['ruta_bd']}")
    print(f"¿Existe archivo local?:     {'Sí' if estado['existe'] else 'No'}")
    print(f"Total registros 69-B:       {estado['total_registros']}")
    print(f"Última actualización:       {estado['ultima_actualizacion'] or 'Nunca'}")
    return 0


def main() -> None:
    """Punto de entrada principal para el comando mcp-sat."""
    parser = argparse.ArgumentParser(
        prog="mcp-sat",
        description=(
            "Servidor MCP para consultas oficiales y gratuitas del SAT (México). "
            "Parte de la suite Itzamná; proyecto independiente y de código abierto."
        ),
    )
    parser.add_argument("--version", action="version", version=f"mcp-sat {__version__}")
    parser.add_argument(
        "--test",
        action="store_true",
        help="Verifica la conectividad en vivo con el Web Service de validación del SAT",
    )
    parser.add_argument(
        "--actualizar-listas",
        action="store_true",
        help="Descarga e indexa en SQLite el listado oficial completo del Artículo 69-B (EFOS)",
    )
    parser.add_argument(
        "--info",
        action="store_true",
        help="Muestra información sobre la base de datos local y listas del SAT",
    )
    parser.add_argument(
        "--transport",
        choices=["stdio", "sse", "streamable-http"],
        default="stdio",
        help="Tipo de transporte MCP (por defecto: stdio)",
    )
    parser.add_argument(
        "--host",
        default="127.0.0.1",
        help="Host de escucha para transportes HTTP (por defecto: 127.0.0.1)",
    )
    parser.add_argument(
        "--allowed-host",
        action="append",
        default=[],
        metavar="HOST",
        help="Host permitido detrás de proxy inverso para evitar DNS-rebinding",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Puerto de escucha para transportes HTTP (por defecto: 8000)",
    )

    args = parser.parse_args()

    if args.test:
        sys.exit(test_connection())

    if args.actualizar_listas:
        sys.exit(actualizar_listas_cli())

    if args.info:
        sys.exit(mostrar_info())

    server = create_server()

    if args.transport == "stdio":
        server.run(transport="stdio")
    else:
        server.run(
            transport=args.transport,
            host=args.host,
            port=args.port,
            transport_security=build_transport_security(args.allowed_host),
        )


if __name__ == "__main__":
    main()
