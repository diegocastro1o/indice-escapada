import asyncio
import unittest

from src.weather import LimitadorSolicitudes


class LimitadorSolicitudesTest(unittest.IsolatedAsyncioTestCase):
    async def test_espacia_los_inicios_de_solicitud(self) -> None:
        limitador = LimitadorSolicitudes(0.05)
        inicios = []

        async def pedir_turno() -> None:
            await limitador.esperar_turno()
            inicios.append(asyncio.get_running_loop().time())

        await asyncio.gather(*(pedir_turno() for _ in range(4)))

        diferencias = [
            siguiente - anterior
            for anterior, siguiente in zip(inicios, inicios[1:])
        ]
        self.assertTrue(all(diferencia >= 0.04 for diferencia in diferencias))

    async def test_pausa_global_retrasa_el_siguiente_inicio(self) -> None:
        limitador = LimitadorSolicitudes(0.05)
        await limitador.esperar_turno()

        inicio_espera = asyncio.get_running_loop().time()
        siguiente_turno = asyncio.create_task(limitador.esperar_turno())
        await asyncio.sleep(0.01)
        await limitador.pausar(0.05)
        await siguiente_turno
        duracion_espera = asyncio.get_running_loop().time() - inicio_espera

        self.assertGreaterEqual(duracion_espera, 0.04)
