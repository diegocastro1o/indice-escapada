import argparse
import json
import statistics
import sys
from datetime import date, timedelta
from pathlib import Path

try:
    from .cache import cargar_json, guardar_json
    from .holidays import detectar_fines_de_semana_largos, obtener_feriados
    from .weather import DAILY_VARIABLES, validar_datos_diarios
except ImportError:
    from cache import cargar_json, guardar_json
    from holidays import detectar_fines_de_semana_largos, obtener_feriados
    from weather import DAILY_VARIABLES, validar_datos_diarios

PROJECT_ROOT = Path(__file__).resolve().parent.parent
ANIOS_HISTORICOS = [*range(2015, 2025)]

PESOS_CLIMA = {
    "apparent_temperature_max": 0.30,
    "apparent_temperature_min": 0.20,
    "precipitation_sum": 0.35,
    "precipitation_hours": 0.15,
}
PESO_CLIMA_FINAL = 0.80
PESO_ACCESO_FINAL = 0.15
PESO_DURACION_FINAL = 0.05


def cargar_configuracion(config_path: Path) -> dict:
    with config_path.open(encoding="utf-8") as archivo:
        return json.load(archivo)


def cargar_historico_destino(
    destino_id: str,
    anios: list[int],
    weather_dir: Path,
) -> dict[str, dict]:
    historico = {}
    faltantes = []

    for anio in anios:
        ruta = weather_dir / destino_id / f"{anio}.json"
        try:
            datos = cargar_json(ruta)
            if datos is None:
                faltantes.append(str(ruta))
                continue
            validar_datos_diarios(datos, anio)
        except (json.JSONDecodeError, ValueError):
            faltantes.append(str(ruta))
            continue

        diarios = datos["daily"]
        for posicion, fecha in enumerate(diarios["time"]):
            historico[fecha] = {
                variable: diarios[variable][posicion]
                for variable in DAILY_VARIABLES
            }

    if faltantes:
        raise ValueError(
            f"Faltan {len(faltantes)} archivos climáticos válidos para "
            f"'{destino_id}'. Ejecutá primero la recolección completa."
        )

    return historico


def fechas_entre(inicio: date, fin: date) -> list[date]:
    cantidad = (fin - inicio).days + 1
    return [inicio + timedelta(days=desplazamiento) for desplazamiento in range(cantidad)]


def promedios_historicos(
    historico: dict[str, dict],
    finde: dict,
    anios: list[int],
) -> dict[str, float]:
    inicio = date.fromisoformat(finde["inicio"])
    fin = date.fromisoformat(finde["fin"])
    fechas_objetivo = fechas_entre(inicio, fin)
    valores = {variable: [] for variable in DAILY_VARIABLES}

    for anio in anios:
        for fecha_objetivo in fechas_objetivo:
            try:
                fecha_historica = date(
                    anio,
                    fecha_objetivo.month,
                    fecha_objetivo.day,
                ).isoformat()
            except ValueError:
                continue

            dia = historico.get(fecha_historica)
            if dia is None:
                continue

            for variable in DAILY_VARIABLES:
                valor = dia.get(variable)
                if isinstance(valor, (int, float)):
                    valores[variable].append(float(valor))

    promedios = {}
    for variable, observaciones in valores.items():
        if not observaciones:
            raise ValueError(
                f"No hay observaciones históricas para '{variable}' en {finde['id']}."
            )
        promedios[variable] = statistics.fmean(observaciones)

    return promedios


def puntuar_rango_comodo(
    valor: float,
    minimo_comodo: float,
    maximo_comodo: float,
    minimo_tolerable: float,
    maximo_tolerable: float,
) -> float:
    if minimo_comodo <= valor <= maximo_comodo:
        return 100.0
    if valor <= minimo_tolerable or valor >= maximo_tolerable:
        return 0.0
    if valor < minimo_comodo:
        return 100 * (valor - minimo_tolerable) / (minimo_comodo - minimo_tolerable)
    return 100 * (maximo_tolerable - valor) / (maximo_tolerable - maximo_comodo)


def puntuar_clima(promedios: dict[str, float]) -> tuple[float, dict[str, float]]:
    componentes = {
        "apparent_temperature_max": puntuar_rango_comodo(
            promedios["apparent_temperature_max"], 20, 28, 5, 40
        ),
        "apparent_temperature_min": puntuar_rango_comodo(
            promedios["apparent_temperature_min"], 12, 20, 0, 30
        ),
        "precipitation_sum": max(
            0.0,
            100 - promedios["precipitation_sum"] * 10,
        ),
        "precipitation_hours": max(
            0.0,
            100 - promedios["precipitation_hours"] * (100 / 12),
        ),
    }
    puntaje = sum(
        componentes[variable] * peso
        for variable, peso in PESOS_CLIMA.items()
    )
    return puntaje, componentes


def puntuar_acceso(duracion_minutos: float) -> float:
    if duracion_minutos <= 60:
        return 100.0
    if duracion_minutos >= 480:
        return 0.0
    return 100 * (480 - duracion_minutos) / 420


def puntuar_duracion(cantidad_dias: int) -> float:
    return min(100.0, cantidad_dias * 25.0)


def construir_ranking(
    anio_objetivo: int,
    config_path: Path,
    weather_dir: Path,
    holidays_dir: Path,
    routes_path: Path,
    processed_dir: Path,
    anios_historicos: list[int] = ANIOS_HISTORICOS,
) -> dict:
    configuracion = cargar_configuracion(config_path)
    rutas = cargar_json(routes_path)
    if not isinstance(rutas, dict):
        raise ValueError("Falta data/raw/routes.json. Ejecutá primero routes.py.")

    feriados = obtener_feriados(anio_objetivo, holidays_dir)
    fines_largos = detectar_fines_de_semana_largos(feriados, anio_objetivo)
    if not fines_largos:
        raise ValueError(f"No se detectaron fines de semana largos en {anio_objetivo}.")

    resultados = []
    for destino in configuracion["destinos"]:
        destino_id = destino["id"]
        if destino_id not in rutas:
            raise ValueError(f"Falta la ruta cacheada para '{destino_id}'.")

        historico = cargar_historico_destino(
            destino_id,
            anios_historicos,
            weather_dir,
        )
        ruta = rutas[destino_id]
        puntaje_acceso = puntuar_acceso(ruta["duracion_minutos"])

        for finde in fines_largos:
            promedios = promedios_historicos(historico, finde, anios_historicos)
            puntaje_clima, componentes = puntuar_clima(promedios)
            puntaje_duracion = puntuar_duracion(finde["cantidad_dias"])
            puntaje_final = (
                puntaje_clima * PESO_CLIMA_FINAL
                + puntaje_acceso * PESO_ACCESO_FINAL
                + puntaje_duracion * PESO_DURACION_FINAL
            )
            resultados.append(
                {
                    "finde_id": finde["id"],
                    "inicio": finde["inicio"],
                    "fin": finde["fin"],
                    "cantidad_dias": finde["cantidad_dias"],
                    "feriados": finde["feriados"],
                    "destino_id": destino_id,
                    "destino": destino["nombre"],
                    "puntaje_final": round(puntaje_final, 2),
                    "puntaje_clima": round(puntaje_clima, 2),
                    "puntaje_acceso": round(puntaje_acceso, 2),
                    "puntaje_duracion": round(puntaje_duracion, 2),
                    "promedios_climaticos": {
                        clave: round(valor, 2) for clave, valor in promedios.items()
                    },
                    "componentes_climaticos": {
                        clave: round(valor, 2) for clave, valor in componentes.items()
                    },
                    "distancia_km": ruta["distancia_km"],
                    "duracion_viaje_minutos": ruta["duracion_minutos"],
                }
            )

    resultados.sort(key=lambda fila: fila["puntaje_final"], reverse=True)
    for posicion, resultado in enumerate(resultados, start=1):
        resultado["posicion_general"] = posicion

    asignar_posiciones_por_finde(resultados)
    conclusiones = generar_conclusiones(resultados)
    salida = {
        "anio_objetivo": anio_objetivo,
        "anios_historicos": anios_historicos,
        "pesos_finales": {
            "clima": PESO_CLIMA_FINAL,
            "acceso": PESO_ACCESO_FINAL,
            "duracion": PESO_DURACION_FINAL,
        },
        "pesos_clima": PESOS_CLIMA,
        "cantidad_fines_largos": len(fines_largos),
        "cantidad_combinaciones": len(resultados),
        "conclusiones": conclusiones,
        "ranking": resultados,
    }
    guardar_json(salida, processed_dir / f"ranking_{anio_objetivo}.json")
    return salida


def asignar_posiciones_por_finde(resultados: list[dict]) -> None:
    ids_findes = {resultado["finde_id"] for resultado in resultados}
    for finde_id in ids_findes:
        filas = [fila for fila in resultados if fila["finde_id"] == finde_id]
        filas.sort(key=lambda fila: fila["puntaje_final"], reverse=True)
        for posicion, fila in enumerate(filas, start=1):
            fila["posicion_en_finde"] = posicion


def generar_conclusiones(resultados: list[dict]) -> list[str]:
    if not resultados:
        return []

    mejor = resultados[0]
    conclusiones = [
        f"La mejor combinación es {mejor['destino']} del {mejor['inicio']} "
        f"al {mejor['fin']}, con {mejor['puntaje_final']:.2f} puntos."
    ]

    mayor_cambio = None
    for finde_id in {fila["finde_id"] for fila in resultados}:
        filas = [fila for fila in resultados if fila["finde_id"] == finde_id]
        por_clima = sorted(filas, key=lambda fila: fila["puntaje_clima"], reverse=True)
        posiciones_clima = {
            fila["destino_id"]: posicion
            for posicion, fila in enumerate(por_clima, start=1)
        }
        for fila in filas:
            cambio = posiciones_clima[fila["destino_id"]] - fila["posicion_en_finde"]
            if mayor_cambio is None or abs(cambio) > abs(mayor_cambio[0]):
                mayor_cambio = (cambio, fila, posiciones_clima[fila["destino_id"]])

    if mayor_cambio and mayor_cambio[0] != 0:
        cambio, fila, posicion_clima = mayor_cambio
        direccion = "sube" if cambio > 0 else "baja"
        conclusiones.append(
            f"{fila['destino']} {direccion} {abs(cambio)} puestos para el finde "
            f"del {fila['inicio']} cuando se considera el tiempo de viaje: pasa "
            f"del puesto {posicion_clima} por clima al {fila['posicion_en_finde']} final."
        )

    return conclusiones


def mostrar_ranking(resultado: dict, limite: int = 10) -> None:
    print(f"\nÍndice de Escapada {resultado['anio_objetivo']}")
    print("=" * 72)
    for fila in resultado["ranking"][:limite]:
        print(
            f"{fila['posicion_general']:>2}. {fila['destino']:<24} "
            f"{fila['inicio']} → {fila['fin']}  {fila['puntaje_final']:>6.2f}"
        )

    print("\nConclusiones:")
    for conclusion in resultado["conclusiones"]:
        print(f"- {conclusion}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Construye el Índice de Escapada.")
    parser.add_argument("--year", type=int, default=date.today().year)
    parser.add_argument("--top", type=int, default=10)
    argumentos = parser.parse_args()

    try:
        resultado = construir_ranking(
            anio_objetivo=argumentos.year,
            config_path=PROJECT_ROOT / "config/ubicaciones.json",
            weather_dir=PROJECT_ROOT / "data/raw/weather",
            holidays_dir=PROJECT_ROOT / "data/raw/holidays",
            routes_path=PROJECT_ROOT / "data/raw/routes.json",
            processed_dir=PROJECT_ROOT / "data/processed",
        )
        mostrar_ranking(resultado, argumentos.top)
    except (OSError, ValueError) as error:
        print(f"[error] No se pudo construir el índice: {error}", file=sys.stderr)
        raise SystemExit(1)
