"""Fixtures compartidos para tests de mcp-sat."""

from pathlib import Path

import pytest

from mcp_sat.lista69 import Lista69Manager


@pytest.fixture
def tmp_db_path(tmp_path: Path) -> Path:
    return tmp_path / "test_lista69.sqlite3"


@pytest.fixture
def lista_manager_test(tmp_db_path: Path) -> Lista69Manager:
    manager = Lista69Manager(db_path=tmp_db_path)
    manager.inicializar_bd()
    return manager
