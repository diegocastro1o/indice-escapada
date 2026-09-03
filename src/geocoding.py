import json
import time
from pathlib import Path

import requests

NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
USER_AGENT = "indice-escapada/1.0 (contacto: diegoandres.castro@correo.ucu.edu.uy)"
REQUEST_INTERVAL_SECONDS = 1
MAX_RETRIES = 2
PROJECT_ROOT = Path(__file__).resolve().parent.parent


def cargar_ubicaciones(ruta_config: Path) -> list[dict]:
    with ruta_config.open(encoding="utf-8") as archivo:
        configuracion = json.load(archivo)

    return [configuracion["origen"], *configuracion["destinos"]]


def cargar_cache(ruta_cache: Path) -> dict:
    if not ruta_cache.exists():
        return {}
    with ruta_cache.open(encoding="utf-8") as archivo:
        return json.load(archivo)


def guardar_cache(cache: dict, cache_path: Path) -> None:
    cache_path.parent.mkdir(parents=True, exist_ok=True)

    ruta_temporal = cache_path.with_suffix(f"{cache_path.suffix}.tmp")
    with ruta_temporal.open("w", encoding="utf-8") as archivo:
        json.dump(cache, archivo, ensure_ascii=False, indent=2)
    ruta_temporal.replace(cache_path)


def buscar_coordenadas(ubicacion: dict) -> dict:
    params = {
        "q": ubicacion["consulta_nominatim"],
        "format": "jsonv2",
        "limit": 1,
        "addressdetails": 1,
        "countrycodes": "uy",
    }

    respuesta = requests.get(
        NOMINATIM_URL,
        params=params,
        headers={"User-Agent": USER_AGENT},
        timeout=10,
    )

    respuesta.raise_for_status()

    resultados = respuesta.json()

    if not resultados:
        raise ValueError(
            f"No se encontró la ubicación: {ubicacion['consulta_nominatim']}"
        )

    resultado = resultados[0]
    pais = resultado.get("address", {}).get("country_code")
    if pais != "uy":
        raise ValueError(
            f"Nominatim devolvió una ubicación fuera de Uruguay: "
            f"{resultado['display_name']}"
        )

    latitud = float(resultado["lat"])
    longitud = float(resultado["lon"])
    if not -90 <= latitud <= 90 or not -180 <= longitud <= 180:
        raise ValueError(f"Coordenadas inválidas para {ubicacion['nombre']}")

    return {
        "nombre": ubicacion["nombre"],
        "consulta_nominatim": ubicacion["consulta_nominatim"],
        "latitud": latitud,
        "longitud": longitud,
        "display_name": resultado["display_name"],
        "osm_type": resultado["osm_type"],
        "osm_id": resultado["osm_id"],
    }


def geocodificar_todo(config_path: Path, cache_path: Path) -> dict:
    ubicaciones = cargar_ubicaciones(config_path)
    cache = cargar_cache(cache_path)

    ultimo_pedido = None

    for ubicacion in ubicaciones:
        ubicacion_id = ubicacion["id"]

        if ubicacion_id in cache:
            print(f"[cache] {ubicacion['nombre']}")
            continue

        for intento in range(MAX_RETRIES + 1):
            if ultimo_pedido is not None:
                tiempo_transcurrido = time.monotonic() - ultimo_pedido
                espera = max(0, REQUEST_INTERVAL_SECONDS - tiempo_transcurrido)
                time.sleep(espera)

            print(f"[Nominatim] Buscando {ubicacion['nombre']}...")
            ultimo_pedido = time.monotonic()

            try:
                cache[ubicacion_id] = buscar_coordenadas(ubicacion)
            except requests.RequestException as error:
                if intento == MAX_RETRIES:
                    print(
                        f"[error] No se pudo geocodificar {ubicacion['nombre']}: "
                        f"{error}"
                    )
                    break
                print(
                    f"[reintento] {ubicacion['nombre']} falló "
                    f"({intento + 1}/{MAX_RETRIES})."
                )
            except ValueError as error:
                print(f"[error] {error}")
                break
            else:
                # Guarda después de cada éxito: permite reanudar si se corta la corrida.
                guardar_cache(cache, cache_path)
                break

    return cache


if __name__ == "__main__":
    geocodificar_todo(
        config_path=PROJECT_ROOT / "config/ubicaciones.json",
        cache_path=PROJECT_ROOT / "data/raw/geocoding.json",
    )
