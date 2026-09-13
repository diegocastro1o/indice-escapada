import json
from pathlib import Path
from typing import Any


def cargar_json(ruta: Path, valor_por_defecto: Any = None) -> Any:
    if not ruta.exists():
        return valor_por_defecto

    with ruta.open(encoding="utf-8") as archivo:
        return json.load(archivo)


def guardar_json(datos: Any, ruta: Path) -> None:
    ruta.parent.mkdir(parents=True, exist_ok=True)
    ruta_temporal = ruta.with_suffix(f"{ruta.suffix}.tmp")

    with ruta_temporal.open("w", encoding="utf-8") as archivo:
        json.dump(datos, archivo, ensure_ascii=False, indent=2)

    ruta_temporal.replace(ruta)
