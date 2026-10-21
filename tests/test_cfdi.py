"""Pruebas unitarias para el cliente de validación de CFDI ante el SAT."""


import pytest

from mcp_sat.cfdi import CFDIClient, SATCFDIError, normalizar_total


def test_normalizar_total():
    assert normalizar_total(1500) == "1500.00"
    assert normalizar_total(1500.5) == "1500.50"
    assert normalizar_total("250.75") == "250.75"
    with pytest.raises(ValueError):
        normalizar_total("no_es_numero")
    with pytest.raises(ValueError):
        normalizar_total("")


def test_cfdi_validaciones_entrada():
    client = CFDIClient()

    with pytest.raises(SATCFDIError, match="son obligatorios"):
        import asyncio
        asyncio.run(client.consultar("", "XAXX010101000", "100.00", "00000000-0000-0000-0000-000000000000"))

    with pytest.raises(SATCFDIError, match="no tiene el formato estándar"):
        import asyncio
        asyncio.run(client.consultar("EKU9003173C9", "XAXX010101000", "100.00", "uuid-invalido"))


def test_parsear_xml_vigente():
    client = CFDIClient()
    xml_mock = b"""<s:Envelope xmlns:s="http://schemas.xmlsoap.org/soap/envelope/">
      <s:Body>
        <ConsultaResponse xmlns="http://tempuri.org/">
          <ConsultaResult xmlns:a="http://schemas.datacontract.org/2004/07/Sat.Cfdi.Negocio.ConsultaCfdi.Servicio" xmlns:i="http://www.w3.org/2001/XMLSchema-instance">
            <a:CodigoEstatus>S - Comprobante obtenido satisfactoriamente.</a:CodigoEstatus>
            <a:EsCancelable>Cancelable sin acepci\xc3\xb3n</a:EsCancelable>
            <a:Estado>Vigente</a:Estado>
            <a:EstatusCancelacion/>
            <a:ValidacionEFOS>200</a:ValidacionEFOS>
          </ConsultaResult>
        </ConsultaResponse>
      </s:Body>
    </s:Envelope>"""

    resultado = client._parsear_xml(
        xml_bytes=xml_mock,
        expresion="?re=A&rr=B&tt=100.00&id=123",
        uuid="9016A446-5A28-5425-8CBD-835F902F8D3C",
        rfc_emisor="EKU9003173C9",
        rfc_receptor="XAXX010101000",
        total="100.00",
    )

    assert resultado["estado"] == "Vigente"
    assert "Cancelable sin" in resultado["es_cancelable"]
    assert resultado["validacion_efos_codigo"] == "200"
    assert "Limpio" in resultado["validacion_efos_diagnostico"]


def test_parsear_xml_alerta_efos():
    client = CFDIClient()
    xml_mock = b"""<s:Envelope xmlns:s="http://schemas.xmlsoap.org/soap/envelope/">
      <s:Body>
        <ConsultaResponse xmlns="http://tempuri.org/">
          <ConsultaResult xmlns:a="http://schemas.datacontract.org/2004/07/Sat.Cfdi.Negocio.ConsultaCfdi.Servicio">
            <a:CodigoEstatus>S - Comprobante obtenido satisfactoriamente.</a:CodigoEstatus>
            <a:EsCancelable>No cancelable</a:EsCancelable>
            <a:Estado>Vigente</a:Estado>
            <a:EstatusCancelacion/>
            <a:ValidacionEFOS>100</a:ValidacionEFOS>
          </ConsultaResult>
        </ConsultaResponse>
      </s:Body>
    </s:Envelope>"""

    resultado = client._parsear_xml(
        xml_bytes=xml_mock,
        expresion="?test",
        uuid="9016A446-5A28-5425-8CBD-835F902F8D3C",
        rfc_emisor="AAA010101AAA",
        rfc_receptor="XAXX010101000",
        total="500.00",
    )

    assert resultado["validacion_efos_codigo"] == "100"
    assert "ALERTA" in resultado["validacion_efos_diagnostico"]
