import argparse
import json
import sys
import time
from datetime import date, timedelta
from pathlib import Path

import requests

try:
    from .cache import cargar_json, guardar_json
except ImportError:
    from cache import cargar_json, guardar_json

NAGER_URL = "https://date.nager.at/api/v3/PublicHolidays/{anio}/UY"
MAX_RETRIES = 2
RETRY_DELAY_SECONDS = 3
PROJECT_ROOT = Path(__file__).resolve().parent.parent


def validar_feriados(feriados: object, anio: int) -> list[dict]:
    if not isinstance(feriados, list) or not feriados:
        raise ValueError(f"Nager.Date no devolvió feriados para {anio}.")

    for feriado in feriados:
        if not isinstance(feriado, dict) or "date" not in feriado:
            raise ValueError("La respuesta de Nager.Date tiene un formato inesperado.")
        fecha = date.fromisoformat(feriado["date"])
        if fecha.year != anio:
            raise ValueError(f"Nager.Date devolvió un feriado fuera de {anio}.")

    return feriados


def descargar_feriados(anio: int) -> list[dict]:
    url = NAGER_URL.format(anio=anio)

    for intento in range(MAX_RETRIES + 1):
        try:
            respuesta = requests.get(url, timeout=15)
            respuesta.raise_for_status()
            return validar_feriados(respuesta.json(), anio)
        except requests.RequestException:
            if intento == MAX_RETRIES:
                raise
            time.sleep(RETRY_DELAY_SECONDS * (intento + 1))

    raise RuntimeError("No se pudieron descargar los feriados.")


def obtener_feriados(anio: int, cache_dir: Path, force: bool = False) -> list[dict]:
    cache_path = cache_dir / f"{anio}.json"

    if not force:
        try:
            cache = cargar_json(cache_path)
            if cache is not None:
                feriados = validar_feriados(cache, anio)
                print(f"[cache] Feriados {anio}: {len(feriados)}")
                return feriados
        except (json.JSONDecodeError, ValueError):
            print(f"[cache inválida] Feriados {anio}: se descargarán nuevamente.")

    print(f"[Nager.Date] Descargando feriados de Uruguay para {anio}...")
    feriados = descargar_feriados(anio)
    guardar_json(feriados, cache_path)
    print(f"[guardado] Feriados {anio}: {len(feriados)}")
    return feriados


def detectar_fines_de_semana_largos(feriados: list[dict], anio: int) -> list[dict]:
    nombres_por_fecha: dict[date, list[str]] = {}
    for feriado in feriados:
        fecha = date.fromisoformat(feriado["date"])
        nombre = feriado.get("localName") or feriado.get("name") or "Feriado"
        nombres_por_fecha.setdefault(fecha, []).append(nombre)

    dias_no_laborables = set(nombres_por_fecha)
    cursor = date(anio, 1, 1)
    fin_anio = date(anio, 12, 31)
    while cursor <= fin_anio:
        if cursor.weekday() >= 5:
            dias_no_laborables.add(cursor)
        cursor += timedelta(days=1)

    fines_largos = []
    visitados: set[date] = set()

    for fecha_feriado in sorted(nombres_por_fecha):
        if fecha_feriado in visitados:
            continue

        inicio = fecha_feriado
        while inicio - timedelta(days=1) in dias_no_laborables:
            inicio -= timedelta(days=1)

        fin = fecha_feriado
        while fin + timedelta(days=1) in dias_no_laborables:
            fin += timedelta(days=1)

        cantidad_dias = (fin - inicio).days + 1
        bloque = {
            inicio + timedelta(days=desplazamiento)
            for desplazamiento in range(cantidad_dias)
        }
        visitados.update(bloque)

        if cantidad_dias < 3:
            continue

        nombres = sorted(
            {
                nombre
                for fecha in bloque
                for nombre in nombres_por_fecha.get(fecha, [])
            }
        )
        fines_largos.append(
            {
                "id": inicio.isoformat(),
                "inicio": inicio.isoformat(),
                "fin": fin.isoformat(),
                "cantidad_dias": cantidad_dias,
                "feriados": nombres,
            }
        )

    return fines_largos


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Descarga feriados y detecta findes largos.")
    parser.add_argument("--year", type=int, default=date.today().year)
    parser.add_argument("--force", action="store_true")
    argumentos = parser.parse_args()

    try:
        datos = obtener_feriados(
            argumentos.year,
            PROJECT_ROOT / "data/raw/holidays",
            argumentos.force,
        )
        fines_largos = detectar_fines_de_semana_largos(datos, argumentos.year)
        print(f"[resultado] {len(fines_largos)} fines de semana largos:")
        for finde in fines_largos:
            print(
                f"- {finde['inicio']} a {finde['fin']} "
                f"({finde['cantidad_dias']} días): {', '.join(finde['feriados'])}"
            )
    except (OSError, ValueError, requests.RequestException) as error:
        print(f"[error] No se pudieron obtener los feriados: {error}", file=sys.stderr)
        raise SystemExit(1)
