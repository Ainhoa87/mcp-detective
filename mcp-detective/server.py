from mcp.server import MCPServer
import json
import pathlib
from typing import Any

# Instancia del servidor MCP oficial para el SDK v2
mcp = MCPServer("MCP Detective")

# Carga de datos resolviendo la ruta de forma segura con __file__
_CASOS_PATH = pathlib.Path(__file__).parent / "casos.json"

def _cargar_casos() -> dict[str, Any]:
    with _CASOS_PATH.open(encoding="utf-8") as f:
        return json.load(f)

CASOS: dict[str, Any] = _cargar_casos()
_alertas: dict[str, dict] = {}
_NIVELES_VALIDOS: frozenset[str] = frozenset({"bajo", "medio", "alto"})

@mcp.tool()
def listar_casos() -> list[dict]:
    """
    Lista los casos disponibles para investigar.
    Devuelve id, sistema y número de eventos de cada caso. No incluye conclusiones.
    """
    return [
        {
            "id": caso_id,
            "sistema": datos["sistema"],
            "num_eventos": len(datos["eventos"]),
        }
        for caso_id, datos in CASOS.items()
    ]

@mcp.tool()
def consultar_eventos(caso_id: str) -> list[dict]:
    """
    Devuelve los eventos exactos registrados en un caso por su identificador.
    Lanza un ValueError claro si el caso no existe.
    """
    if caso_id not in CASOS:
        disponibles = ", ".join(CASOS.keys())
        raise ValueError(
            f"El caso '{caso_id}' no existe. Casos disponibles: {disponibles}."
        )
    return CASOS[caso_id]["eventos"]

@mcp.tool()
def registrar_alerta(caso_id: str, nivel: str, motivo: str) -> dict:
    """
    Registra una alerta de seguridad en memoria para un caso existente.
    El nivel debe ser bajo, medio o alto. El motivo no puede estar vacío.
    Solo se acepta una alerta por caso.
    """
    if caso_id not in CASOS:
        disponibles = ", ".join(CASOS.keys())
        raise ValueError(
            f"El caso '{caso_id}' no existe. Casos disponibles: {disponibles}."
        )

    if nivel not in _NIVELES_VALIDOS:
        raise ValueError(
            f"Nivel '{nivel}' no válido. Los valores aceptados son: bajo, medio, alto."
        )

    if not motivo or not motivo.strip():
        raise ValueError("El motivo no puede estar vacío ni contener solo espacios en blanco.")

    if caso_id in _alertas:
        raise ValueError(f"Ya existe una alerta registrada para el caso '{caso_id}'.")

    alerta = {
        "caso_id": caso_id,
        "nivel": nivel,
        "motivo": motivo.strip(),
        "estado": "registrada",
    }
    _alertas[caso_id] = alerta
    return alerta

if __name__ == "__main__":
    mcp.run(transport="stdio")