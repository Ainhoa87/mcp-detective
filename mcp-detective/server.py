"""
Servidor MCP – Detective de Incidentes de Seguridad
====================================================
Expone tres tools para inspeccionar casos de seguridad cargados desde
casos.json.  La lógica de negocio vive en funciones puras (prefijo
``logica_``) para que pytest pueda ejercerlas sin levantar el servidor.
"""

from __future__ import annotations

import asyncio
import json
import pathlib
from typing import Any

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import TextContent, Tool

# ---------------------------------------------------------------------------
# Carga de datos
# ---------------------------------------------------------------------------

_CASOS_PATH = pathlib.Path(__file__).parent / "casos.json"


def _cargar_casos() -> dict[str, Any]:
    """Lee casos.json desde el mismo directorio que este módulo."""
    with _CASOS_PATH.open(encoding="utf-8") as f:
        return json.load(f)


# Estado global del proceso: casos en disco, alertas solo en memoria.
CASOS: dict[str, Any] = _cargar_casos()
_alertas: dict[str, dict] = {}

# ---------------------------------------------------------------------------
# Lógica de negocio – funciones puras, sin efectos de red ni I/O extra
# ---------------------------------------------------------------------------

_NIVELES_VALIDOS: frozenset[str] = frozenset({"bajo", "medio", "alto"})


def logica_listar_casos(casos: dict[str, Any]) -> list[dict]:
    """
    Construye un resumen de cada caso.

    Devuelve una lista con un dict por caso que contiene únicamente
    ``id``, ``sistema`` y ``num_eventos``.  No expone eventos individuales
    ni conclusiones.

    Args:
        casos: Diccionario completo de casos tal como viene de casos.json.

    Returns:
        Lista de dicts ``{"id", "sistema", "num_eventos"}``, uno por caso.
    """
    return [
        {
            "id": caso_id,
            "sistema": datos["sistema"],
            "num_eventos": len(datos["eventos"]),
        }
        for caso_id, datos in casos.items()
    ]


def logica_consultar_eventos(casos: dict[str, Any], caso_id: str) -> list[dict]:
    """
    Recupera los eventos exactos de un caso por su identificador.

    Args:
        casos:   Diccionario completo de casos.
        caso_id: Identificador del caso a consultar (p. ej. ``"INC-001"``).

    Returns:
        Lista de dicts de eventos tal como están almacenados en casos.json.

    Raises:
        ValueError: Si ``caso_id`` no corresponde a ningún caso existente.
    """
    if caso_id not in casos:
        disponibles = ", ".join(casos.keys())
        raise ValueError(
            f"El caso '{caso_id}' no existe. "
            f"Casos disponibles: {disponibles}."
        )
    return casos[caso_id]["eventos"]


def logica_registrar_alerta(
    casos: dict[str, Any],
    alertas: dict[str, dict],
    caso_id: str,
    nivel: str,
    motivo: str,
) -> dict:
    """
    Valida los parámetros y guarda una alerta en el diccionario ``alertas``.

    Restricciones aplicadas (en orden):
    - El caso debe existir en ``casos``.
    - ``nivel`` debe ser ``"bajo"``, ``"medio"`` o ``"alto"``.
    - ``motivo`` debe contener al menos un carácter que no sea espacio en blanco.
    - Solo se permite una alerta por caso; los duplicados se rechazan con error.

    Args:
        casos:   Diccionario completo de casos (solo lectura aquí).
        alertas: Diccionario en memoria donde se persisten las alertas.
        caso_id: Identificador del caso al que pertenece la alerta.
        nivel:   Criticidad de la alerta: ``"bajo"``, ``"medio"`` o ``"alto"``.
        motivo:  Texto explicativo; no puede ser vacío ni solo espacios.

    Returns:
        Dict ``{"caso_id", "nivel", "motivo", "estado": "registrada"}``.

    Raises:
        ValueError: Si alguna validación falla o ya existe una alerta para el caso.
    """
    if caso_id not in casos:
        disponibles = ", ".join(casos.keys())
        raise ValueError(
            f"El caso '{caso_id}' no existe. "
            f"Casos disponibles: {disponibles}."
        )

    if nivel not in _NIVELES_VALIDOS:
        raise ValueError(
            f"Nivel '{nivel}' no válido. "
            f"Los valores aceptados son: bajo, medio, alto."
        )

    if not motivo or not motivo.strip():
        raise ValueError(
            "El motivo no puede estar vacío ni contener solo espacios en blanco."
        )

    if caso_id in alertas:
        raise ValueError(
            f"Ya existe una alerta registrada para el caso '{caso_id}'. "
            "Solo se permite una alerta por caso."
        )

    alerta: dict = {
        "caso_id": caso_id,
        "nivel": nivel,
        "motivo": motivo.strip(),
        "estado": "registrada",
    }
    alertas[caso_id] = alerta
    return alerta


# ---------------------------------------------------------------------------
# Servidor MCP
# ---------------------------------------------------------------------------

server = Server("mcp-detective")


@server.list_tools()
async def _listar_tools() -> list[Tool]:
    """Declara las tres tools que el servidor expone al cliente MCP."""
    return [
        Tool(
            name="listar_casos",
            description=(
                "Lista todos los casos de seguridad disponibles. "
                "Devuelve id, sistema y número de eventos de cada caso. "
                "No incluye eventos detallados ni conclusiones."
            ),
            inputSchema={
                "type": "object",
                "properties": {},
                "required": [],
            },
        ),
        Tool(
            name="consultar_eventos",
            description=(
                "Devuelve los eventos exactos registrados en un caso "
                "identificado por su ID (p. ej. INC-001). "
                "Lanza un error claro si el caso no existe."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "caso_id": {
                        "type": "string",
                        "description": "Identificador del caso, p. ej. 'INC-001'.",
                    },
                },
                "required": ["caso_id"],
            },
        ),
        Tool(
            name="registrar_alerta",
            description=(
                "Registra una alerta de seguridad para un caso existente. "
                "El nivel debe ser bajo, medio o alto. "
                "El motivo no puede estar vacío. "
                "Solo se acepta una alerta por caso."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "caso_id": {
                        "type": "string",
                        "description": "Identificador del caso al que pertenece la alerta.",
                    },
                    "nivel": {
                        "type": "string",
                        "enum": ["bajo", "medio", "alto"],
                        "description": "Criticidad de la alerta.",
                    },
                    "motivo": {
                        "type": "string",
                        "description": "Descripción del motivo. No puede estar vacío.",
                    },
                },
                "required": ["caso_id", "nivel", "motivo"],
            },
        ),
    ]


@server.call_tool()
async def _llamar_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
    """Despacha la llamada a la función de lógica correspondiente."""

    def _json(obj: Any) -> str:
        return json.dumps(obj, ensure_ascii=False, indent=2)

    if name == "listar_casos":
        resultado = logica_listar_casos(CASOS)
        return [TextContent(type="text", text=_json(resultado))]

    if name == "consultar_eventos":
        caso_id: str = arguments["caso_id"]
        resultado = logica_consultar_eventos(CASOS, caso_id)
        return [TextContent(type="text", text=_json(resultado))]

    if name == "registrar_alerta":
        resultado = logica_registrar_alerta(
            CASOS,
            _alertas,
            caso_id=arguments["caso_id"],
            nivel=arguments["nivel"],
            motivo=arguments["motivo"],
        )
        return [TextContent(type="text", text=_json(resultado))]

    raise ValueError(f"Tool desconocida: '{name}'.")


# ---------------------------------------------------------------------------
# Punto de entrada – transporte stdio
# ---------------------------------------------------------------------------

async def _main() -> None:
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options(),
        )


if __name__ == "__main__":
    asyncio.run(_main())
