import argparse
import asyncio
import os
import sys
from datetime import date
from pathlib import Path

import aiohttp
import requests
from dotenv import load_dotenv

try:
    from .geocoding import geocodificar_todo
    from .holidays import detectar_fines_de_semana_largos, obtener_feriados
    from .index import construir_ranking, mostrar_ranking
    from .routes import obtener_rutas
    from .weather import (
        MUESTRA_ANIOS,
        MUESTRA_DESTINOS,
        cargar_ids_destinos,
        recolectar_async,
        recolectar_sincrono,
    )
except ImportError:
    from geocoding import geocodificar_todo
    from holidays import detectar_fines_de_semana_largos, obtener_feriados
    from index import construir_ranking, mostrar_ranking
    from routes import obtener_rutas
    from weather import (
        MUESTRA_ANIOS,
        MUESTRA_DESTINOS,
        cargar_ids_destinos,
        recolectar_async,
        recolectar_sincrono,
    )

PROJECT_ROOT = Path(__file__).resolve().parent.parent
CONFIG_PATH = PROJECT_ROOT / "config/ubicaciones.json"
GEOCODING_PATH = PROJECT_ROOT / "data/raw/geocoding.json"
WEATHER_DIR = PROJECT_ROOT / "data/raw/weather"
HOLIDAYS_DIR = PROJECT_ROOT / "data/raw/holidays"
ROUTES_PATH = PROJECT_ROOT / "data/raw/routes.json"
PROCESSED_DIR = PROJECT_ROOT / "data/processed"
ANIOS_COMPLETOS = [*range(2015, 2025)]


def seleccionar_alcance(scope: str) -> tuple[list[str], list[int]]:
    if scope == "full":
        return cargar_ids_destinos(CONFIG_PATH), ANIOS_COMPLETOS
    return MUESTRA_DESTINOS, MUESTRA_ANIOS


def ejecutar_clima(mode: str, scope: str, force: bool) -> None:
    destinos, anios = seleccionar_alcance(scope)
    if mode == "sync":
        recolectar_sincrono(
            destinos,
            anios,
            GEOCODING_PATH,
            WEATHER_DIR,
            force,
        )
        return

    asyncio.run(
        recolectar_async(
            destinos,
            anios,
            GEOCODING_PATH,
            WEATHER_DIR,
            force,
        )
    )


def ejecutar_feriados(anio: int, force: bool) -> list[dict]:
    feriados = obtener_feriados(anio, HOLIDAYS_DIR, force)
    fines_largos = detectar_fines_de_semana_largos(feriados, anio)
    print(f"[resultado] {len(fines_largos)} fines de semana largos en {anio}.")
    return fines_largos


def ejecutar_rutas(force: bool) -> dict:
    load_dotenv(PROJECT_ROOT / ".env")
    return obtener_rutas(
        CONFIG_PATH,
        GEOCODING_PATH,
        ROUTES_PATH,
        os.getenv("ORS_API_KEY", ""),
        force,
    )


def ejecutar_ranking(anio: int, top: int) -> dict:
    resultado = construir_ranking(
        anio,
        CONFIG_PATH,
        WEATHER_DIR,
        HOLIDAYS_DIR,
        ROUTES_PATH,
        PROCESSED_DIR,
    )
    mostrar_ranking(resultado, top)
    return resultado


def crear_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Proyecto Índice de Escapada.")
    subparsers = parser.add_subparsers(dest="comando", required=True)

    subparsers.add_parser("geocoding", help="Geocodifica origen y destinos.")

    parser_clima = subparsers.add_parser("clima", help="Recolecta clima histórico.")
    parser_clima.add_argument("--mode", choices=["sync", "async"], default="async")
    parser_clima.add_argument("--scope", choices=["sample", "full"], default="full")
    parser_clima.add_argument("--force", action="store_true")

    parser_feriados = subparsers.add_parser("feriados", help="Obtiene feriados.")
    parser_feriados.add_argument("--year", type=int, default=date.today().year)
    parser_feriados.add_argument("--force", action="store_true")

    parser_rutas = subparsers.add_parser("rutas", help="Obtiene rutas desde Montevideo.")
    parser_rutas.add_argument("--force", action="store_true")

    parser_ranking = subparsers.add_parser("ranking", help="Construye el ranking final.")
    parser_ranking.add_argument("--year", type=int, default=date.today().year)
    parser_ranking.add_argument("--top", type=int, default=10)

    parser_pipeline = subparsers.add_parser("pipeline", help="Ejecuta el proyecto completo.")
    parser_pipeline.add_argument("--year", type=int, default=date.today().year)
    parser_pipeline.add_argument("--top", type=int, default=10)

    return parser


def main() -> None:
    argumentos = crear_parser().parse_args()

    if argumentos.comando == "geocoding":
        geocodificar_todo(CONFIG_PATH, GEOCODING_PATH)
    elif argumentos.comando == "clima":
        ejecutar_clima(argumentos.mode, argumentos.scope, argumentos.force)
    elif argumentos.comando == "feriados":
        ejecutar_feriados(argumentos.year, argumentos.force)
    elif argumentos.comando == "rutas":
        ejecutar_rutas(argumentos.force)
    elif argumentos.comando == "ranking":
        ejecutar_ranking(argumentos.year, argumentos.top)
    elif argumentos.comando == "pipeline":
        geocodificar_todo(CONFIG_PATH, GEOCODING_PATH)
        ejecutar_clima("async", "full", False)
        ejecutar_feriados(argumentos.year, False)
        ejecutar_rutas(False)
        ejecutar_ranking(argumentos.year, argumentos.top)


if __name__ == "__main__":
    try:
        main()
    except (
        OSError,
        ValueError,
        RuntimeError,
        requests.RequestException,
        aiohttp.ClientError,
        asyncio.TimeoutError,
    ) as error:
        print(f"[error] {error}", file=sys.stderr)
        raise SystemExit(1)
