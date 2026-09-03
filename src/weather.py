import json
import sys
import time
from datetime import date
from pathlib import Path

import requests

OPEN_METEO_ARCHIVE_URL = "https://archive-api.open-meteo.com/v1/archive"
DAILY_VARIABLES = [
    "temperature_2m_max",
    "temperature_2m_min",
    "precipitation_sum",
    "wind_speed_10m_max",
]
MAX_RETRIES = 2
RETRY_DELAY_SECONDS = 2
PROJECT_ROOT = Path(__file__).resolve().parent.parent


def cargar_ubicacion(destino_id: str, geocoding_path: Path) -> dict:
    with geocoding_path.open(encoding="utf-8") as archivo:
        ubicaciones = json.load(archivo)

    if destino_id not in ubicaciones:
        raise ValueError(
            f"No hay coordenadas cacheadas para '{destino_id}'. "
            "Ejecutá primero geocoding.py."
        )

    return ubicaciones[destino_id]


def ruta_cache(destino_id: str, anio: int, weather_dir: Path) -> Path:
    return weather_dir / destino_id / f"{anio}.json"


def cargar_cache(cache_path: Path) -> dict | None:
    if not cache_path.exists():
        return None
    with cache_path.open(encoding="utf-8") as archivo:
        return json.load(archivo)


def guardar_cache(datos: dict, cache_path: Path) -> None:
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    ruta_temporal = cache_path.with_suffix(f"{cache_path.suffix}.tmp")
    with ruta_temporal.open("w", encoding="utf-8") as archivo:
        json.dump(datos, archivo, ensure_ascii=False, indent=2)
    ruta_temporal.replace(cache_path)


def descargar_clima(ubicacion: dict, anio: int) -> dict:
    params = {
        "latitude": ubicacion["latitud"],
        "longitude": ubicacion["longitud"],
        "start_date": f"{anio}-01-01",
        "end_date": f"{anio}-12-31",
        "daily": ",".join(DAILY_VARIABLES),
        "timezone": "America/Montevideo",
    }

    for intento in range(MAX_RETRIES + 1):
        try:
            respuesta = requests.get(OPEN_METEO_ARCHIVE_URL, params=params, timeout=30)
            respuesta.raise_for_status()
            return respuesta.json()
        except requests.RequestException:
            if intento == MAX_RETRIES:
                raise
            time.sleep(RETRY_DELAY_SECONDS)

    raise RuntimeError("No se pudo descargar el clima")


def validar_datos_diarios(datos: dict, anio: int) -> int:
    diarios = datos.get("daily")
    if not isinstance(diarios, dict):
        raise ValueError("La respuesta de Open-Meteo no contiene datos diarios.")

    cantidad_esperada = (date(anio + 1, 1, 1) - date(anio, 1, 1)).days
    for variable in ["time", *DAILY_VARIABLES]:
        valores = diarios.get(variable)
        if not isinstance(valores, list) or len(valores) != cantidad_esperada:
            raise ValueError(
                f"Open-Meteo devolvió datos incompletos para '{variable}': "
                f"se esperaban {cantidad_esperada} días."
            )

    return cantidad_esperada


def obtener_clima(
    destino_id: str,
    anio: int,
    geocoding_path: Path,
    weather_dir: Path,
) -> dict:
    cache_path = ruta_cache(destino_id, anio, weather_dir)
    cache = cargar_cache(cache_path)
    if cache is not None:
        cantidad_dias = validar_datos_diarios(cache, anio)
        print(f"[cache] {destino_id} {anio}: {cantidad_dias} días")
        return cache

    ubicacion = cargar_ubicacion(destino_id, geocoding_path)
    print(f"[Open-Meteo] Descargando {ubicacion['nombre']} ({anio})...")
    datos = descargar_clima(ubicacion, anio)
    cantidad_dias = validar_datos_diarios(datos, anio)
    guardar_cache(datos, cache_path)
    print(f"[guardado] {destino_id} {anio}: {cantidad_dias} días")
    return datos


if __name__ == "__main__":
    try:
        obtener_clima(
            destino_id="colonia_del_sacramento",
            anio=2015,
            geocoding_path=PROJECT_ROOT / "data/raw/geocoding.json",
            weather_dir=PROJECT_ROOT / "data/raw/weather",
        )
    except (OSError, ValueError, requests.RequestException) as error:
        print(f"[error] No se pudo obtener el clima: {error}", file=sys.stderr)
        raise SystemExit(1)
