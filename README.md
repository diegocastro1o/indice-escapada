uv run python src/weather.py --mode sync --force
uv run python src/weather.py --mode async --force

Ejemplo de log de reintento en `weather.py`, `descargar_clima_async()`:
[reintento] Carmelo (2016): Open-Meteo respondió 429; esperando 5s.
[reintento] Piriápolis (2017): error de conexión (...); esperando 10s.
