import pytest
from server import listar_casos, consultar_eventos, registrar_alerta, _alertas

def setup_function():
    _alertas.clear()

def test_1_listar_casos():
    casos = listar_casos()
    ids = [c["id"] for c in casos]
    assert sorted(ids) == ["INC-001", "INC-002", "INC-003"]

def test_2_consultar_eventos_valido():
    eventos = consultar_eventos("INC-002")
    assert len(eventos) == 6

def test_3_consultar_caso_desconocido():
    with pytest.raises(ValueError):
        consultar_eventos("INC-999")

def test_4_registrar_alerta_valido():
    res = registrar_alerta("INC-003", "alto", "Cuatro fallos desde la misma IP")
    assert res["caso_id"] == "INC-003"
    assert res["estado"] == "registrada"

def test_5_registrar_alerta_duplicado():
    registrar_alerta("INC-003", "medio", "Primer aviso")
    with pytest.raises(ValueError):
        registrar_alerta("INC-003", "alto", "Intento duplicado")

def test_6_nivel_invalido():
    with pytest.raises(ValueError):
        registrar_alerta("INC-002", "critico", "Intentos repetidos")

def test_7_motivo_en_blanco():
    with pytest.raises(ValueError):
        registrar_alerta("INC-002", "medio", "   ")