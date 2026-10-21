"""Cliente para validación de CFDI ante el Web Service SOAP oficial del SAT."""

from __future__ import annotations

import logging
import re
import xml.etree.ElementTree as ET
from typing import Any

import httpx

from .constants import SAT_CFDI_SOAP_ACTION, SAT_CFDI_SOAP_URL

logger = logging.getLogger(__name__)

RE_UUID = re.compile(
    r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$"
)


class SATCFDIError(Exception):
    """Excepción para errores al consultar el servicio de validación de CFDI del SAT."""


def normalizar_total(total: str | float) -> str:
    """Normaliza el importe total para la expresión impresa del SAT."""
    if isinstance(total, (int, float)):
        # Formato numérico con al menos 2 decimales sin notación científica
        return f"{float(total):.2f}"
    texto = str(total).strip()
    if not texto:
        raise ValueError("El importe total de la factura no puede estar vacío.")
    # Validar que sea un número válido
    try:
        float(texto)
    except ValueError as err:
        raise ValueError(f"El total '{total}' no tiene un formato numérico válido.") from err
    return texto


class CFDIClient:
    """Cliente HTTP asíncrono para el servicio de consulta de CFDI del SAT."""

    def __init__(self, timeout: float = 15.0):
        self.timeout = timeout

    async def consultar(
        self,
        rfc_emisor: str,
        rfc_receptor: str,
        total: str | float,
        uuid: str,
    ) -> dict[str, Any]:
        """Consulta el estatus oficial de una factura electrónica en los servidores del SAT.

        Args:
            rfc_emisor: RFC de quien emite el comprobante fiscal.
            rfc_receptor: RFC de quien recibe el comprobante fiscal.
            total: Monto total del comprobante (ej. '1234.50' o 1234.5).
            uuid: Folio fiscal UUID (ej. '9016A446-5A28-5425-8CBD-835F902F8D3C').

        Returns:
            Diccionario con estado (Vigente/Cancelado), cancelabilidad y estatus de EFOS.
        """
        re_limpio = (rfc_emisor or "").strip().upper()
        rr_limpio = (rfc_receptor or "").strip().upper()
        id_limpio = (uuid or "").strip().upper()

        if not re_limpio or not rr_limpio:
            raise SATCFDIError("Los RFCs del emisor y receptor son obligatorios.")

        if not RE_UUID.match(id_limpio):
            raise SATCFDIError(
                f"El UUID '{uuid}' no tiene el formato estándar (ej. 9016A446-5A28-5425-8CBD-835F902F8D3C)."
            )

        total_str = normalizar_total(total)

        expresion = f"?re={re_limpio}&rr={rr_limpio}&tt={total_str}&id={id_limpio}"

        soap_body = (
            '<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" '
            'xmlns:tem="http://tempuri.org/">\n'
            "   <soapenv:Header/>\n"
            "   <soapenv:Body>\n"
            "      <tem:Consulta>\n"
            f"         <tem:expresionImpresa><![CDATA[{expresion}]]></tem:expresionImpresa>\n"
            "      </tem:Consulta>\n"
            "   </soapenv:Body>\n"
            "</soapenv:Envelope>"
        )

        headers = {
            "Content-Type": "text/xml; charset=utf-8",
            "SOAPAction": SAT_CFDI_SOAP_ACTION,
        }

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    SAT_CFDI_SOAP_URL,
                    content=soap_body.encode("utf-8"),
                    headers=headers,
                )
                response.raise_for_status()
        except httpx.TimeoutException as err:
            raise SATCFDIError(f"Tiempo de espera agotado al conectar con el SAT: {err}") from err
        except httpx.HTTPError as err:
            raise SATCFDIError(f"Error HTTP al comunicar con el servicio del SAT: {err}") from err

        return self._parsear_xml(response.content, expresion, id_limpio, re_limpio, rr_limpio, total_str)

    def _parsear_xml(
        self,
        xml_bytes: bytes,
        expresion: str,
        uuid: str,
        rfc_emisor: str,
        rfc_receptor: str,
        total: str,
    ) -> dict[str, Any]:
        """Parsea el XML de respuesta del SAT."""
        try:
            root = ET.fromstring(xml_bytes)
        except ET.ParseError as err:
            raise SATCFDIError(f"Respuesta del SAT con XML no válido: {err}") from err

        namespaces = {
            "a": "http://schemas.datacontract.org/2004/07/Sat.Cfdi.Negocio.ConsultaCfdi.Servicio"
        }

        def obtener_texto(tag: str) -> str | None:
            elem = root.find(f".//a:{tag}", namespaces)
            if elem is not None and elem.text:
                texto = elem.text.strip()
                return texto if texto else None
            return None

        codigo_estatus = obtener_texto("CodigoEstatus")
        estado = obtener_texto("Estado")
        es_cancelable = obtener_texto("EsCancelable")
        estatus_cancelacion = obtener_texto("EstatusCancelacion")
        validacion_efos = obtener_texto("ValidacionEFOS")

        # Interpretación amigable de EFOS devuelto por el Web Service
        # '200' = Emisor sin coincidencia en listas de EFOS
        # '100' = Presunto / Definitivo
        efos_diagnostico = "No listado como EFOS"
        if validacion_efos == "100":
            efos_diagnostico = "ALERTA: El RFC emisor tiene presunción o sentencia en listas EFOS"
        elif validacion_efos == "200":
            efos_diagnostico = "Limpio (sin incidencias de EFOS reportadas en consulta directa)"

        return {
            "uuid": uuid,
            "rfc_emisor": rfc_emisor,
            "rfc_receptor": rfc_receptor,
            "total": total,
            "estado": estado or "Desconocido",
            "es_cancelable": es_cancelable or "No especificado",
            "estatus_cancelacion": estatus_cancelacion or "Ninguno",
            "codigo_estatus_sat": codigo_estatus,
            "validacion_efos_codigo": validacion_efos,
            "validacion_efos_diagnostico": efos_diagnostico,
            "expresion_impresa_sat": expresion,
        }
