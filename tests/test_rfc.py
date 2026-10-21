"""Pruebas unitarias para validación de RFC del SAT."""

from mcp_sat.rfc import calcular_digito_verificador, validar_rfc


def test_calcular_digito_verificador_moral():
    # EKU9003173C9 es un RFC oficial de pruebas del SAT para persona moral
    assert calcular_digito_verificador("EKU9003173C") == "9"
    # AAA080808HL8
    assert calcular_digito_verificador("AAA080808HL") == "8"


def test_validar_rfc_moral_valido():
    res = validar_rfc("EKU9003173C9")
    assert res["es_valido"] is True
    assert res["tipo_persona"] == "MORAL"
    assert res["digito_verificador_correcto"] is True
    assert res["fecha_asociada"] == "1990-03-17"


def test_validar_rfc_genericos():
    res_nac = validar_rfc("XAXX010101000")
    assert res_nac["es_valido"] is True
    assert res_nac["tipo_persona"] == "GENERICO_NACIONAL"

    res_ext = validar_rfc("XEXX010101000")
    assert res_ext["es_valido"] is True
    assert res_ext["tipo_persona"] == "GENERICO_EXTRANJERO"


def test_validar_rfc_invalido_longitud():
    res = validar_rfc("ABC123")
    assert res["es_valido"] is False
    assert res["tipo_persona"] == "INVALIDO"
    assert "Longitud inválida" in res["motivo_invalido"]


def test_validar_rfc_invalido_digito():
    # Alteramos el dígito verificador de EKU9003173C9 por 1
    res = validar_rfc("EKU9003173C1")
    assert res["es_valido"] is False
    assert res["digito_verificador_correcto"] is False
    assert res["digito_verificador_esperado"] == "9"
    assert res["digito_verificador_recibido"] == "1"


def test_validar_rfc_vacio_o_tipo_erroneo():
    assert validar_rfc("")["es_valido"] is False
    assert validar_rfc(None)["es_valido"] is False


def test_validar_rfc_fecha_invalida():
    # Febrero 30 es fecha inválida de calendario
    res = validar_rfc("EKU9002303C9")
    assert res["es_valido"] is False
    assert "no es una fecha de calendario válida" in res["motivo_invalido"]
