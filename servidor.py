import asyncio
import json
import logging
import random
import time
import datetime
from queue import PriorityQueue
from clases import Tarea, Dron
from time import perf_counter
from provincias import provincias

with open("eventos_servidor.log", "a") as f:
    f.write("\n=== Nueva sesion iniciada ===\n")

logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(message)s',
    handlers=[
        logging.FileHandler("eventos_servidor.log"),
        logging.StreamHandler()
    ]
)

cola_tareas = PriorityQueue()
drones = {}
servidor_activo = True
conexiones = []
tareas_entregadas = 0
tiempos_entrega = []

async def recibir_json(reader):
    data = await reader.readline()
    if not data:
        return None
    try:
        return json.loads(data.decode())
    except json.JSONDecodeError:
        return None

async def enviar_json(writer, mensaje):
    data = (json.dumps(mensaje) + "\n").encode()
    writer.write(data)
    await writer.drain()

async def manejar_dron(reader, writer):
    global tareas_entregadas, tiempos_entrega

    datos = await recibir_json(reader)
    if not datos:
        writer.close()
        try:
            await writer.wait_closed()
        except Exception:
            pass
        return

    dron_id = datos['id']
    velocidad = datos['velocidad']
    drones[dron_id] = Dron(dron_id, velocidad)
    logging.info(f"Dron {dron_id} conectado (velocidad: {velocidad})")

    tarea = None

    try:
        while servidor_activo:
            if cola_tareas.empty():
                await asyncio.sleep(1)
                continue

            _, _, tarea = cola_tareas.get()
            inicio = perf_counter()
            logging.info(f"Asignando tarea {tarea.id} ({tarea.prioridad}) a Dron {dron_id} -> {tarea.destino}")
            await enviar_json(writer, {
                'accion': 'nueva_tarea',
                'tarea': {
                    'id': tarea.id,
                    'origen': tarea.origen,
                    'destino': tarea.destino,
                    'prioridad': tarea.prioridad
                }
            })

            respuesta = await recibir_json(reader)
            if not respuesta:
                tarea.reintentos -= 1
                if tarea.reintentos > 0:
                    if tarea.prioridad == 'NORMAL':
                        tarea.prioridad = 'URGENTE'
                    timestamp = time.time()
                    prioridad_valor = 0 if tarea.prioridad == 'URGENTE' else 1
                    cola_tareas.put((prioridad_valor, timestamp, tarea))
                    logging.warning(f"Tarea {tarea.id} devuelta por desconexion de Dron {dron_id}")
                else:
                    logging.error(f"Tarea {tarea.id} eliminada tras desconexion y sin reintentos restantes")
                break

            estado = respuesta.get('estado')
            log_extra = respuesta.get('log_event')
            if log_extra:
                logging.info(log_extra)

            if estado == 'entrega_exitosa':
                duracion = perf_counter() - inicio
                tareas_entregadas += 1
                tiempos_entrega.append(duracion)
                logging.info(f"Tarea {tarea.id} completada por Dron {dron_id} -> {tarea.destino}")

            elif estado == 'fallo':
                tarea.reintentos -= 1
                if tarea.reintentos > 0:
                    if tarea.prioridad == 'NORMAL':
                        tarea.prioridad = 'URGENTE'
                        logging.warning(f"Tarea {tarea.id} fallida por Dron {dron_id}. Se convierte en URGENTE ({tarea.reintentos} intentos restantes)")
                    else:
                        logging.warning(f"Tarea {tarea.id} fallida por Dron {dron_id}. Reintentando ({tarea.reintentos} intentos restantes)")
                    timestamp = time.time()
                    prioridad_valor = 0 if tarea.prioridad == 'URGENTE' else 1
                    cola_tareas.put((prioridad_valor, timestamp, tarea))
                else:
                    logging.error(f"Tarea {tarea.id} eliminada del sistema tras 3 fallos consecutivos")

            tarea = None

    except asyncio.CancelledError:
        logging.info(f"Dron {dron_id} desconectado por cierre del servidor")
    finally:
        writer.close()
        try:
            await writer.wait_closed()
        except Exception:
            logging.warning(f"Error al cerrar conexion con Dron {dron_id}. Puede haberse desconectado abruptamente.")
        drones.pop(dron_id, None)

async def generar_tareas_periodicamente():
    tarea_id = 1
    primera = True
    while servidor_activo:
        if not primera:
            await asyncio.sleep(random.randint(5, 10))
        else:
            primera = False

        prioridad = random.choices(['URGENTE', 'NORMAL'], weights=[1, 4])[0]
        provincia = random.choice(list(provincias.keys()))
        distancia = provincias[provincia]
        nueva_tarea = Tarea(
            id=f"T{tarea_id}",
            origen="Almacen Central",
            destino=f"Almacen provincial de {provincia}",
            prioridad=prioridad,
            distancia=distancia
        )
        timestamp = time.time()
        prioridad_valor = 0 if prioridad == 'URGENTE' else 1
        cola_tareas.put((prioridad_valor, timestamp, nueva_tarea))
        logging.info(f"Nueva tarea generada: {nueva_tarea.id} ({prioridad}) -> {nueva_tarea.destino}")
        tarea_id += 1

async def mostrar_estadisticas():
    inicio = datetime.datetime.now()
    while servidor_activo:
        ahora = datetime.datetime.now()
        objetivo = inicio + datetime.timedelta(seconds=30)
        while ahora < objetivo:
            await asyncio.sleep(1)
            ahora = datetime.datetime.now()
        inicio = datetime.datetime.now()
        if tareas_entregadas:
            media = sum(tiempos_entrega) / len(tiempos_entrega)
            logging.info(f"[RENDIMIENTO] Tareas entregadas: {tareas_entregadas} | Tiempo medio por entrega: {media:.2f} s")

async def cerrar_servidor(server, tareas_gen_task, estadisticas_task, conexiones):
    global servidor_activo
    servidor_activo = False
    tareas_gen_task.cancel()
    estadisticas_task.cancel()
    await asyncio.gather(tareas_gen_task, estadisticas_task, return_exceptions=True)
    logging.info("Esperando a que los drones finalicen las tareas en curso...")
    await asyncio.sleep(5)
    for writer in conexiones:
        writer.close()
        try:
            await writer.wait_closed()
        except Exception:
            pass
    server.close()
    await server.wait_closed()
    logging.info("Servidor finalizado correctamente. Todas las conexiones han sido cerradas.")

async def manejador_conexion(reader, writer):
    conexiones.append(writer)
    try:
        await manejar_dron(reader, writer)
    except ConnectionResetError:
        logging.warning("Conexion reseteada por el cliente.")
    except Exception as e:
        logging.error(f"Excepcion inesperada en conexion con dron: {e}")

async def main():
    server = await asyncio.start_server(manejador_conexion, '127.0.0.1', 8888)
    logging.info("Servidor iniciado en 127.0.0.1:8888")
    tareas_gen_task = asyncio.create_task(generar_tareas_periodicamente())
    estadisticas_task = asyncio.create_task(mostrar_estadisticas())
    try:
        async with server:
            await server.serve_forever()
    except KeyboardInterrupt:
        await cerrar_servidor(server, tareas_gen_task, estadisticas_task, conexiones)

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, asyncio.CancelledError):
        print("Servidor interrumpido manualmente. Cerrado con exito.")
