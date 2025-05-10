import socket
import json
import time
import random
import sys
from datetime import datetime
from provincias import provincias

# Función para enviar datos en formato JSON a través de un socket
def enviar_json(sock, mensaje):
    data = (json.dumps(mensaje) + "\n").encode()  # Convierte el mensaje a JSON y lo codifica
    sock.sendall(data)  # Envía los datos al servidor

# Función para recibir datos en formato JSON desde un socket
def recibir_json(sock):
    data = b""  # Inicializa un buffer vacío
    while not data.endswith(b"\n"):  # Lee hasta encontrar un salto de línea
        parte = sock.recv(1024)  # Recibe datos en bloques de 1024 bytes
        if not parte:  # Si no hay más datos, termina
            break
        data += parte
    if not data:  # Si no se recibió nada, retorna None
        return None
    return json.loads(data.decode())  # Decodifica y convierte los datos a JSON

# Función para obtener la hora actual en formato legible
def now():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

# Función para simular la entrega de un paquete por parte de un dron
def simular_entrega(tarea, dron_id):
    velocidad = 5  # Velocidad base del dron en km/h
    provincia = tarea['destino'].split()[-1]  # Extrae la provincia del destino
    distancia = provincias.get(provincia, 300)  # Obtiene la distancia desde el diccionario de provincias

    # Calcula el tiempo de ida en función de la distancia y la velocidad
    tiempo_ida = distancia / velocidad
    if tarea['prioridad'] == 'URGENTE':  # Si la tarea es urgente, reduce el tiempo de ida a la mitad
        tiempo_ida /= 2
    tiempo_vuelta = distancia / (velocidad * 3)  # Calcula el tiempo de vuelta (más lento)

    # Imprime información sobre la entrega
    print(f"[{now()}] [DRON {dron_id}] Enviando paquete {tarea['id']} a {tarea['destino']} | Prioridad: {tarea['prioridad']} | Distancia: {distancia} km | Tiempo estimado: {tiempo_ida:.2f}s", flush=True)
    time.sleep(tiempo_ida)  # Simula el tiempo de ida

    # Simula un fallo en la entrega con una probabilidad del 20%
    if random.random() < 0.2:
        print(f"[{now()}] [DRON {dron_id}] FALLO entrega {tarea['id']} -> regreso a base...", flush=True)
        time.sleep(tiempo_vuelta)  # Simula el tiempo de vuelta
        return 'fallo'

    # Si la entrega es exitosa
    print(f"[{now()}] [DRON {dron_id}] Entregado {tarea['id']} con EXITO. Regresando a base...", flush=True)
    time.sleep(tiempo_vuelta)  # Simula el tiempo de vuelta
    return 'entrega_exitosa'

# Función principal que gestiona el comportamiento del dron
def main(dron_id):
    sock = None  # Inicializa el socket
    tarea_actual = None  # Variable para almacenar la tarea actual

    try:
        # Conecta el dron al servidor
        sock = socket.create_connection(('127.0.0.1', 8888))
        enviar_json(sock, {'id': dron_id, 'velocidad': 5})  # Envía los datos iniciales del dron

        while True:
            respuesta = recibir_json(sock)  # Espera una respuesta del servidor
            if respuesta is None:  # Si el servidor se desconecta, termina
                print(f"[{now()}] [DRON {dron_id}] Servidor desconectado. Vuelta a la base.", flush=True)
                break

            # Si el servidor asigna una nueva tarea
            if respuesta.get('accion') == 'nueva_tarea':
                tarea_actual = respuesta['tarea']  # Almacena la tarea actual
                estado = simular_entrega(tarea_actual, dron_id)  # Simula la entrega
                if estado == 'entrega_exitosa':  # Si la entrega fue exitosa
                    mensaje_log = f"Entregado paquete {tarea_actual['id']} con EXITO en {tarea_actual['destino']}"
                elif estado == 'fallo':  # Si la entrega falló
                    mensaje_log = f"FALLO entrega {tarea_actual['id']} hacia {tarea_actual['destino']}"
                # Envía el estado de la tarea al servidor
                enviar_json(sock, {
                    'estado': estado,
                    'log_event': f"[{now()}] [DRON {dron_id}] {mensaje_log}"
                })
                tarea_actual = None  # Limpia la tarea actual

    except ConnectionRefusedError:  # Maneja errores de conexión
        print(f"[{now()}] [DRON {dron_id}] No se pudo conectar al servidor.", flush=True)
    except KeyboardInterrupt:  # Maneja interrupciones manuales
        print(f"[{now()}] [DRON {dron_id}] Interrupcion manual.", flush=True)
        if sock and tarea_actual:  # Si hay una tarea en curso, informa al servidor
            print(f"[{now()}] [DRON {dron_id}] Interrupcion durante tarea {tarea_actual['id']}, enviando fallo al servidor...", flush=True)
            try:
                enviar_json(sock, {'estado': 'fallo'})
            except:
                pass
    finally:
        if sock:  # Cierra el socket al finalizar
            try:
                sock.close()
            except:
                pass
            print(f"[{now()}] [DRON {dron_id}] Desconectado.", flush=True)

# Punto de entrada del programa
if __name__ == '__main__':
    if len(sys.argv) != 2:  # Verifica que se pase el ID del dron como argumento
        print("Uso: python drones.py <dron_id>", flush=True)
        sys.exit(1)

    dron_id = sys.argv[1]  # Obtiene el ID del dron desde los argumentos
    main(dron_id)  # Llama a la función principal
