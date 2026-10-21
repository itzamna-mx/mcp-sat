"""Pruebas unitarias para el gestor de listas del Artículo 69-B del CFF."""

from pathlib import Path

from mcp_sat.lista69 import Lista69Manager


def test_lista69_db_no_inicializada(tmp_path: Path):
    manager = Lista69Manager(db_path=tmp_path / "no_existe.sqlite3")
    res = manager.buscar_rfc("AAA010101AAA")
    assert res["en_lista_negra"] is None
    assert "aún no ha sido descargada" in res["mensaje"]


def test_lista69_busqueda_rfc_no_encontrado(lista_manager_test: Lista69Manager):
    res = lista_manager_test.buscar_rfc("LIMPIO010101")
    assert res["en_lista_negra"] is False
    assert "no se encuentra en el listado" in res["mensaje"]


def test_lista69_insercion_y_busqueda(lista_manager_test: Lista69Manager):
    # Simulamos inserción de un registro presunto y uno desvirtuado
    with lista_manager_test._conectar() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO lista_69b (
                rfc, razon_social, situacion, oficio_presuncion, fecha_sat_presuncion, actualizado_en
            ) VALUES (
                'FANTASMA999', 'EMPRESA FANTASMA S.A. DE C.V.', 'Definitivo',
                'OFICIO-1234', '2025-01-10', '2026-10-21 12:00:00'
            )
        """)
        cursor.execute("INSERT INTO metadata (clave, valor) VALUES ('total_registros', '1')")
        conn.commit()

    res = lista_manager_test.buscar_rfc("FANTASMA999")
    assert res["en_lista_negra"] is True
    assert res["es_riesgo_fiscal"] is True
    assert res["situacion"] == "Definitivo"
    assert res["razon_social"] == "EMPRESA FANTASMA S.A. DE C.V."
    assert res["detalle"]["oficio_presuncion"] == "OFICIO-1234"

    # Búsqueda por nombre
    busqueda = lista_manager_test.buscar_por_nombre("FANTASMA")
    assert len(busqueda) == 1
    assert busqueda[0]["rfc"] == "FANTASMA999"


def test_obtener_estado_bd(lista_manager_test: Lista69Manager):
    estado = lista_manager_test.obtener_estado_bd()
    assert estado["existe"] is True
    assert estado["total_registros"] == 0
