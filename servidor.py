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

# Abre el archivo de log y escribe un mensaje indicando el inicio de una nueva sesión
with open("eventos_servidor.log", "a") as f:
    f.write("\n=== Nueva sesion iniciada ===\n")

# Configuración del sistema de logging para registrar eventos en un archivo y en la consola
logging.basicConfig(
    level=logging.INFO,  # Nivel de registro: INFO
    format='[%(asctime)s] %(message)s',  # Formato del mensaje de log
    handlers=[
        logging.FileHandler("eventos_servidor.log"),  # Archivo de log
        logging.StreamHandler()  # Consola
    ]
)

# Cola de prioridad para gestionar las tareas pendientes
cola_tareas = PriorityQueue()
# Diccionario para almacenar los drones conectados
drones = {}
# Variable que indica si el servidor está activo
servidor_activo = True
# Lista para almacenar las conexiones activas
conexiones = []
# Contador de tareas entregadas
tareas_entregadas = 0
# Lista para registrar los tiempos de entrega de las tareas
tiempos_entrega = []

# Función asíncrona para recibir datos en formato JSON desde un cliente
async def recibir_json(reader):
    data = await reader.readline()  # Lee una línea de datos
    if not data:  # Si no hay datos, retorna None
        return None
    try:
        return json.loads(data.decode())  # Decodifica y convierte los datos a JSON
    except json.JSONDecodeError:  # Maneja errores de decodificación
        return None

# Función asíncrona para enviar datos en formato JSON a un cliente
async def enviar_json(writer, mensaje):
    data = (json.dumps(mensaje) + "\n").encode()  # Convierte el mensaje a JSON y lo codifica
    writer.write(data)  # Envía los datos al cliente
    await writer.drain()  # Espera a que se complete el envío

# Función asíncrona para manejar la conexión con un dron
async def manejar_dron(reader, writer):
    global tareas_entregadas, tiempos_entrega

    # Recibe los datos iniciales del dron
    datos = await recibir_json(reader)
    if not datos:  # Si no hay datos, cierra la conexión
        writer.close()
        try:
            await writer.wait_closed()
        except Exception:
            pass
        return

    # Registra el dron en el sistema
    dron_id = datos['id']
    velocidad = datos['velocidad']
    drones[dron_id] = Dron(dron_id, velocidad)
    logging.info(f"Dron {dron_id} conectado (velocidad: {velocidad})")

    tarea = None

    try:
        while servidor_activo:  # Bucle principal mientras el servidor esté activo
            if cola_tareas.empty():  # Si no hay tareas, espera un momento
                await asyncio.sleep(1)
                continue

            # Asigna una tarea al dron
            _, _, tarea = cola_tareas.get()
            inicio = perf_counter()  # Registra el tiempo de inicio
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

            # Espera la respuesta del dron
            respuesta = await recibir_json(reader)
            if not respuesta:  # Si no hay respuesta, maneja la desconexión
                tarea.reintentos -= 1
                if tarea.reintentos > 0:
                    if tarea.prioridad == 'NORMAL':
                        tarea.prioridad = 'URGENTE'  # Escala la prioridad si es necesario
                    timestamp = time.time()
                    prioridad_valor = 0 if tarea.prioridad == 'URGENTE' else 1
                    cola_tareas.put((prioridad_valor, timestamp, tarea))  # Reagrega la tarea a la cola
                    logging.warning(f"Tarea {tarea.id} devuelta por desconexion de Dron {dron_id}")
                else:
                    logging.error(f"Tarea {tarea.id} eliminada tras desconexion y sin reintentos restantes")
                break

            # Procesa el estado de la tarea según la respuesta del dron
            estado = respuesta.get('estado')
            log_extra = respuesta.get('log_event')
            if log_extra:
                logging.info(log_extra)

            if estado == 'entrega_exitosa':  # Si la entrega fue exitosa
                duracion = perf_counter() - inicio
                tareas_entregadas += 1
                tiempos_entrega.append(duracion)
                logging.info(f"Tarea {tarea.id} completada por Dron {dron_id} -> {tarea.destino}")

            elif estado == 'fallo':  # Si la entrega falló
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

    except asyncio.CancelledError:  # Maneja la desconexión del dron
        logging.info(f"Dron {dron_id} desconectado por cierre del servidor")
    finally:
        writer.close()
        try:
            await writer.wait_closed()
        except Exception:
            logging.warning(f"Error al cerrar conexion con Dron {dron_id}. Puede haberse desconectado abruptamente.")
        drones.pop(dron_id, None)

# Función asíncrona para generar tareas periódicamente
async def generar_tareas_periodicamente():
    tarea_id = 1
    primera = True
    while servidor_activo:
        if not primera:
            await asyncio.sleep(random.randint(5, 10))  # Espera un tiempo aleatorio entre tareas
        else:
            primera = False

        # Genera una nueva tarea con prioridad y destino aleatorios
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
        cola_tareas.put((prioridad_valor, timestamp, nueva_tarea))  # Agrega la tarea a la cola
        logging.info(f"Nueva tarea generada: {nueva_tarea.id} ({prioridad}) -> {nueva_tarea.destino}")
        tarea_id += 1

# Función asíncrona para mostrar estadísticas del servidor periódicamente
async def mostrar_estadisticas():
    inicio = datetime.datetime.now()
    while servidor_activo:
        ahora = datetime.datetime.now()
        objetivo = inicio + datetime.timedelta(seconds=30)  # Intervalo de 30 segundos
        while ahora < objetivo:
            await asyncio.sleep(1)
            ahora = datetime.datetime.now()
        inicio = datetime.datetime.now()
        if tareas_entregadas:
            media = sum(tiempos_entrega) / len(tiempos_entrega)  # Calcula el tiempo promedio de entrega
            logging.info(f"[RENDIMIENTO] Tareas entregadas: {tareas_entregadas} | Tiempo medio por entrega: {media:.2f} s")

# Función para cerrar el servidor y limpiar recursos
async def cerrar_servidor(server, tareas_gen_task, estadisticas_task, conexiones):
    global servidor_activo
    servidor_activo = False
    tareas_gen_task.cancel()  # Cancela la tarea de generación de tareas
    estadisticas_task.cancel()  # Cancela la tarea de estadísticas
    await asyncio.gather(tareas_gen_task, estadisticas_task, return_exceptions=True)
    logging.info("Esperando a que los drones finalicen las tareas en curso...")
    await asyncio.sleep(5)
    for writer in conexiones:  # Cierra todas las conexiones activas
        writer.close()
        try:
            await writer.wait_closed()
        except Exception:
            pass
    server.close()
    await server.wait_closed()
    logging.info("Servidor finalizado correctamente. Todas las conexiones han sido cerradas.")

# Función para manejar nuevas conexiones al servidor
async def manejador_conexion(reader, writer):
    conexiones.append(writer)  # Agrega la conexión a la lista
    try:
        await manejar_dron(reader, writer)  # Maneja la conexión con el dron
    except ConnectionResetError:
        logging.warning("Conexion reseteada por el cliente.")
    except Exception as e:
        logging.error(f"Excepcion inesperada en conexion con dron: {e}")

# Función principal del servidor
async def main():
    server = await asyncio.start_server(manejador_conexion, '127.0.0.1', 8888)  # Inicia el servidor en el puerto 8888
    logging.info("Servidor iniciado en 127.0.0.1:8888")
    tareas_gen_task = asyncio.create_task(generar_tareas_periodicamente())  # Tarea para generar tareas
    estadisticas_task = asyncio.create_task(mostrar_estadisticas())  # Tarea para mostrar estadísticas
    try:
        async with server:
            await server.serve_forever()  # Mantiene el servidor en ejecución
    except KeyboardInterrupt:
        await cerrar_servidor(server, tareas_gen_task, estadisticas_task, conexiones)  # Cierra el servidor al interrumpir

# Punto de entrada del programa
if __name__ == '__main__':
    try:
        asyncio.run(main())  # Ejecuta la función principal
    except (KeyboardInterrupt, asyncio.CancelledError):
        print("Servidor interrumpido manualmente. Cerrado con exito.")
