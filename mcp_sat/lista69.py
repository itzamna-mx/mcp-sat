"""Gestor de listas negras del SAT (Artículo 69-B del CFF - EFOS / EDOS)."""

from __future__ import annotations

import csv
import io
import logging
import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import httpx

from .constants import DB_PATH, SAT_LISTA_69B_URL

logger = logging.getLogger(__name__)


class Lista69Manager:
    """Administrador y motor de búsqueda en SQLite para las listas del Artículo 69-B del SAT."""

    def __init__(self, db_path: Path | None = None):
        self.db_path = db_path or DB_PATH

    @contextmanager
    def _conectar(self) -> Iterator[sqlite3.Connection]:
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()

    def inicializar_bd(self) -> None:
        """Crea las tablas e índices si no existen."""
        with self._conectar() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS lista_69b (
                    rfc TEXT PRIMARY KEY,
                    razon_social TEXT,
                    situacion TEXT,
                    oficio_presuncion TEXT,
                    fecha_sat_presuncion TEXT,
                    fecha_dof_presuncion TEXT,
                    oficio_desvirtuado TEXT,
                    fecha_sat_desvirtuado TEXT,
                    fecha_dof_desvirtuado TEXT,
                    oficio_definitivo TEXT,
                    fecha_sat_definitivo TEXT,
                    fecha_dof_definitivo TEXT,
                    oficio_sentencia TEXT,
                    fecha_sat_sentencia TEXT,
                    fecha_dof_sentencia TEXT,
                    actualizado_en TEXT
                );
            """)
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_69b_razon ON lista_69b(razon_social);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_69b_situacion ON lista_69b(situacion);")
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS metadata (
                    clave TEXT PRIMARY KEY,
                    valor TEXT
                );
            """)
            conn.commit()

    def obtener_estado_bd(self) -> dict[str, Any]:
        """Devuelve información sobre la base de datos local y su última actualización."""
        if not self.db_path.exists():
            return {
                "existe": False,
                "total_registros": 0,
                "ultima_actualizacion": None,
                "ruta_bd": str(self.db_path),
            }

        try:
            with self._conectar() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM lista_69b")
                total = cursor.fetchone()[0]

                cursor.execute("SELECT valor FROM metadata WHERE clave = 'ultima_actualizacion'")
                fila_meta = cursor.fetchone()
                ultima_act = fila_meta[0] if fila_meta else None

                return {
                    "existe": True,
                    "total_registros": total,
                    "ultima_actualizacion": ultima_act,
                    "ruta_bd": str(self.db_path),
                }
        except (sqlite3.Error, OSError):
            return {
                "existe": False,
                "total_registros": 0,
                "ultima_actualizacion": None,
                "ruta_bd": str(self.db_path),
            }

    async def actualizar_listas(self, timeout: float = 60.0) -> dict[str, Any]:
        """Descarga el listado completo oficial del SAT y actualiza la base de datos local.

        Args:
            timeout: Tiempo máximo de espera para la descarga del CSV del SAT.

        Returns:
            Resumen con el total de registros importados y fecha de actualización.
        """
        self.inicializar_bd()

        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            )
        }

        async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
            resp = await client.get(SAT_LISTA_69B_URL, headers=headers)
            resp.raise_for_status()
            contenido = resp.content

        # El archivo del SAT viene en codificación Windows-1252 / ISO-8859-1 (Latin-1)
        texto_csv = contenido.decode("latin1", errors="replace")
        lector = csv.reader(io.StringIO(texto_csv))

        registros = []
        ahora_iso = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

        # Saltar líneas de encabezado informativas hasta encontrar la cabecera real
        en_cabecera = False
        for fila in lector:
            if not fila or len(fila) < 4:
                continue

            primer_campo = fila[0].strip().lower()
            if "no" in primer_campo and "rfc" in fila[1].strip().lower():
                en_cabecera = True
                continue

            if not en_cabecera:
                # Comprobar si ya es un registro numérico
                if not fila[0].strip().isdigit():
                    continue
                en_cabecera = True

            rfc = fila[1].strip().upper()
            if not rfc:
                continue

            razon_social = fila[2].strip() if len(fila) > 2 else ""
            situacion = fila[3].strip() if len(fila) > 3 else "Desconocido"

            oficio_presuncion = fila[4].strip() if len(fila) > 4 else ""
            fecha_sat_presuncion = fila[5].strip() if len(fila) > 5 else ""
            fecha_dof_presuncion = fila[7].strip() if len(fila) > 7 else ""

            oficio_desvirtuado = fila[8].strip() if len(fila) > 8 else ""
            fecha_sat_desvirtuado = fila[9].strip() if len(fila) > 9 else ""
            fecha_dof_desvirtuado = fila[11].strip() if len(fila) > 11 else ""

            oficio_definitivo = fila[12].strip() if len(fila) > 12 else ""
            fecha_sat_definitivo = fila[13].strip() if len(fila) > 13 else ""
            fecha_dof_definitivo = fila[15].strip() if len(fila) > 15 else ""

            oficio_sentencia = fila[16].strip() if len(fila) > 16 else ""
            fecha_sat_sentencia = fila[17].strip() if len(fila) > 17 else ""
            fecha_dof_sentencia = fila[19].strip() if len(fila) > 19 else ""

            registros.append((
                rfc,
                razon_social,
                situacion,
                oficio_presuncion,
                fecha_sat_presuncion,
                fecha_dof_presuncion,
                oficio_desvirtuado,
                fecha_sat_desvirtuado,
                fecha_dof_desvirtuado,
                oficio_definitivo,
                fecha_sat_definitivo,
                fecha_dof_definitivo,
                oficio_sentencia,
                fecha_sat_sentencia,
                fecha_dof_sentencia,
                ahora_iso,
            ))

        with self._conectar() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM lista_69b")
            cursor.executemany("""
                INSERT OR REPLACE INTO lista_69b VALUES (
                    ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
                )
            """, registros)
            cursor.execute(
                "INSERT OR REPLACE INTO metadata (clave, valor) VALUES ('ultima_actualizacion', ?)",
                (ahora_iso,),
            )
            cursor.execute(
                "INSERT OR REPLACE INTO metadata (clave, valor) VALUES ('total_registros', ?)",
                (str(len(registros)),),
            )
            conn.commit()

        return {
            "estado": "actualizado",
            "total_importados": len(registros),
            "actualizado_en": ahora_iso,
            "fuente": SAT_LISTA_69B_URL,
        }

    def buscar_rfc(self, rfc: str) -> dict[str, Any]:
        """Busca si un RFC está registrado en la lista negra del Artículo 69-B."""
        estado = self.obtener_estado_bd()
        if not estado["existe"]:
            return {
                "rfc": rfc.upper().strip(),
                "en_lista_negra": None,
                "mensaje": (
                    "La base de datos local de la lista 69-B del SAT aún no ha sido descargada. "
                    "Ejecuta la herramienta 'actualizar_lista_sat' para descargar el padrón oficial."
                ),
                "base_datos_inicializada": False,
            }

        rfc_limpio = rfc.upper().strip()
        with self._conectar() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM lista_69b WHERE rfc = ?", (rfc_limpio,))
            fila = cursor.fetchone()

        if not fila:
            return {
                "rfc": rfc_limpio,
                "en_lista_negra": False,
                "situacion": "Limpio / No listado",
                "mensaje": (
                    f"El RFC '{rfc_limpio}' no se encuentra en el listado del Artículo 69-B "
                    "(sin presunción ni definitivos de EFOS)."
                ),
                "ultima_actualizacion_padron": estado["ultima_actualizacion"],
            }

        situacion = fila["situacion"]
        es_riesgo = situacion in ("Presunto", "Definitivo")

        return {
            "rfc": rfc_limpio,
            "en_lista_negra": True,
            "es_riesgo_fiscal": es_riesgo,
            "razon_social": fila["razon_social"],
            "situacion": situacion,
            "detalle": {
                "oficio_presuncion": fila["oficio_presuncion"] or None,
                "fecha_publicacion_sat_presuncion": fila["fecha_sat_presuncion"] or None,
                "fecha_publicacion_dof_presuncion": fila["fecha_dof_presuncion"] or None,
                "oficio_definitivo": fila["oficio_definitivo"] or None,
                "fecha_publicacion_sat_definitivo": fila["fecha_sat_definitivo"] or None,
                "fecha_publicacion_dof_definitivo": fila["fecha_dof_definitivo"] or None,
                "oficio_desvirtuado": fila["oficio_desvirtuado"] or None,
                "oficio_sentencia": fila["oficio_sentencia"] or None,
            },
            "ultima_actualizacion_padron": estado["ultima_actualizacion"],
        }

    def buscar_por_nombre(self, nombre: str, limite: int = 10) -> list[dict[str, Any]]:
        """Busca contribuyentes en la lista 69-B por coincidencia en su razón social."""
        estado = self.obtener_estado_bd()
        if not estado["existe"] or estado["total_registros"] == 0:
            return []

        patron = f"%{nombre.strip()}%"
        with self._conectar() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT rfc, razon_social, situacion FROM lista_69b WHERE razon_social LIKE ? LIMIT ?",
                (patron, limite),
            )
            filas = cursor.fetchall()

        return [
            {
                "rfc": f["rfc"],
                "razon_social": f["razon_social"],
                "situacion": f["situacion"],
            }
            for f in filas
        ]
