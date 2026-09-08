import argparse
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
RETRY_DELAY_SECONDS = 5
PROJECT_ROOT = Path(__file__).resolve().parent.parent
MUESTRA_DESTINOS = [
    "colonia_del_sacramento",
    "carmelo",
    "piriapolis",
]
MUESTRA_ANIOS = [2015, 2016, 2017]


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
        except requests.HTTPError as error:
            if intento == MAX_RETRIES:
                raise
            retry_after = (
                error.response.headers.get("Retry-After")
                if error.response is not None
                else None
            )
            espera = float(retry_after) if retry_after else RETRY_DELAY_SECONDS * (intento + 1)
            estado = error.response.status_code if error.response is not None else "HTTP"
            print(f"[reintento] Open-Meteo respondió {estado}; esperando {espera:g}s.")
            time.sleep(espera)
        except requests.RequestException:
            if intento == MAX_RETRIES:
                raise
            espera = RETRY_DELAY_SECONDS * (intento + 1)
            print(f"[reintento] Error de red; esperando {espera:g}s.")
            time.sleep(espera)

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
    force: bool = False,
) -> dict:
    cache_path = ruta_cache(destino_id, anio, weather_dir)
    cache = cargar_cache(cache_path)
    if cache is not None and not force:
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


def recolectar_sincrono(
    destinos: list[str],
    anios: list[int],
    geocoding_path: Path,
    weather_dir: Path,
    force: bool = False,
) -> None:
    tareas = [(destino_id, anio) for destino_id in destinos for anio in anios]
    inicio = time.perf_counter()
    registros = 0

    print(f"[inicio] Recolectando {len(tareas)} tareas en modo síncrono.")
    for posicion, (destino_id, anio) in enumerate(tareas, start=1):
        print(f"[progreso] {posicion}/{len(tareas)}")
        datos = obtener_clima(
            destino_id=destino_id,
            anio=anio,
            geocoding_path=geocoding_path,
            weather_dir=weather_dir,
            force=force,
        )
        registros += len(datos["daily"]["time"])

    duracion = time.perf_counter() - inicio
    print(
        f"[finalizado] {len(tareas)} tareas, {registros} registros diarios, "
        f"{duracion:.2f} segundos."
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Recolecta una muestra síncrona de clima para el hito 2."
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Vuelve a descargar incluso los archivos que ya están en caché.",
    )
    argumentos = parser.parse_args()

    try:
        recolectar_sincrono(
            destinos=MUESTRA_DESTINOS,
            anios=MUESTRA_ANIOS,
            geocoding_path=PROJECT_ROOT / "data/raw/geocoding.json",
            weather_dir=PROJECT_ROOT / "data/raw/weather",
            force=argumentos.force,
        )
    except (OSError, ValueError, requests.RequestException) as error:
        print(f"[error] No se pudo obtener el clima: {error}", file=sys.stderr)
        raise SystemExit(1)
