import argparse
import json
import os
import sys
import time
from pathlib import Path

import requests
from dotenv import load_dotenv

try:
    from .cache import cargar_json, guardar_json
except ImportError:
    from cache import cargar_json, guardar_json

OPENROUTESERVICE_URL = (
    "https://api.openrouteservice.org/v2/directions/driving-car/json"
)
MAX_RETRIES = 2
RETRY_DELAY_SECONDS = 3
PROJECT_ROOT = Path(__file__).resolve().parent.parent


def cargar_configuracion(config_path: Path) -> dict:
    with config_path.open(encoding="utf-8") as archivo:
        return json.load(archivo)


def cargar_geocoding(geocoding_path: Path) -> dict:
    datos = cargar_json(geocoding_path)
    if not isinstance(datos, dict):
        raise ValueError("No se encontró una caché de geocoding válida.")
    return datos


def validar_ruta(ruta: object, destino_id: str) -> dict:
    if not isinstance(ruta, dict):
        raise ValueError(f"La ruta de '{destino_id}' no es válida.")

    distancia = ruta.get("distancia_km")
    duracion = ruta.get("duracion_minutos")
    if not isinstance(distancia, (int, float)) or distancia <= 0:
        raise ValueError(f"La distancia de '{destino_id}' no es válida.")
    if not isinstance(duracion, (int, float)) or duracion <= 0:
        raise ValueError(f"La duración de '{destino_id}' no es válida.")

    return ruta


def descargar_ruta(
    origen: dict,
    destino: dict,
    destino_id: str,
    api_key: str,
) -> dict:
    cuerpo = {
        "coordinates": [
            [origen["longitud"], origen["latitud"]],
            [destino["longitud"], destino["latitud"]],
        ],
        "instructions": False,
    }
    headers = {
        "Authorization": api_key,
        "Accept": "application/json",
        "Content-Type": "application/json",
    }

    for intento in range(MAX_RETRIES + 1):
        try:
            respuesta = requests.post(
                OPENROUTESERVICE_URL,
                json=cuerpo,
                headers=headers,
                timeout=30,
            )
            respuesta.raise_for_status()
            datos = respuesta.json()
            resumen = datos["routes"][0]["summary"]
            return validar_ruta(
                {
                    "destino_id": destino_id,
                    "distancia_km": round(resumen["distance"] / 1000, 2),
                    "duracion_minutos": round(resumen["duration"] / 60, 2),
                    "fuente": "OpenRouteService",
                },
                destino_id,
            )
        except (KeyError, IndexError, TypeError) as error:
            raise ValueError(
                f"OpenRouteService devolvió una respuesta inesperada para '{destino_id}'."
            ) from error
        except requests.RequestException:
            if intento == MAX_RETRIES:
                raise
            time.sleep(RETRY_DELAY_SECONDS * (intento + 1))

    raise RuntimeError("No se pudo descargar la ruta.")


def obtener_rutas(
    config_path: Path,
    geocoding_path: Path,
    cache_path: Path,
    api_key: str,
    force: bool = False,
) -> dict:
    if not api_key:
        raise ValueError(
            "Falta ORS_API_KEY. Creá una clave de OpenRouteService y guardala en .env."
        )

    configuracion = cargar_configuracion(config_path)
    geocoding = cargar_geocoding(geocoding_path)
    origen_id = configuracion["origen"]["id"]
    if origen_id not in geocoding:
        raise ValueError(f"No hay coordenadas cacheadas para el origen '{origen_id}'.")

    cache = {} if force else cargar_json(cache_path, {})
    if not isinstance(cache, dict):
        print("[cache inválida] Las rutas se descargarán nuevamente.")
        cache = {}

    origen = geocoding[origen_id]
    errores = []

    for destino_config in configuracion["destinos"]:
        destino_id = destino_config["id"]
        if destino_id not in geocoding:
            errores.append(destino_id)
            print(f"[error] No hay coordenadas para {destino_id}.")
            continue

        if not force and destino_id in cache:
            try:
                validar_ruta(cache[destino_id], destino_id)
                print(f"[cache] Ruta Montevideo → {destino_config['nombre']}")
                continue
            except ValueError:
                print(f"[cache inválida] Ruta a {destino_config['nombre']}.")

        print(f"[OpenRouteService] Calculando ruta a {destino_config['nombre']}...")
        try:
            cache[destino_id] = descargar_ruta(
                origen,
                geocoding[destino_id],
                destino_id,
                api_key,
            )
        except (ValueError, requests.RequestException) as error:
            errores.append(destino_id)
            print(f"[error] {destino_config['nombre']}: {error}")
            continue

        guardar_json(cache, cache_path)

    if errores:
        raise RuntimeError(f"No se pudieron obtener {len(errores)} rutas.")

    return cache


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Obtiene distancia y duración desde Montevideo."
    )
    parser.add_argument("--force", action="store_true")
    argumentos = parser.parse_args()

    load_dotenv(PROJECT_ROOT / ".env")
    try:
        rutas = obtener_rutas(
            config_path=PROJECT_ROOT / "config/ubicaciones.json",
            geocoding_path=PROJECT_ROOT / "data/raw/geocoding.json",
            cache_path=PROJECT_ROOT / "data/raw/routes.json",
            api_key=os.getenv("ORS_API_KEY", ""),
            force=argumentos.force,
        )
        print(f"[resultado] {len(rutas)} rutas disponibles.")
    except (OSError, ValueError, RuntimeError) as error:
        print(f"[error] No se pudieron obtener las rutas: {error}", file=sys.stderr)
        raise SystemExit(1)
