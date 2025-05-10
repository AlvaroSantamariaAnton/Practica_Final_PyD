import socket
import json
import time
import random
import sys
from datetime import datetime
from provincias import provincias

def enviar_json(sock, mensaje):
    data = (json.dumps(mensaje) + "\n").encode()
    sock.sendall(data)

def recibir_json(sock):
    data = b""
    while not data.endswith(b"\n"):
        parte = sock.recv(1024)
        if not parte:
            break
        data += parte
    if not data:
        return None
    return json.loads(data.decode())

def now():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def simular_entrega(tarea, dron_id):
    velocidad = 5
    provincia = tarea['destino'].split()[-1]
    distancia = provincias.get(provincia, 300)

    tiempo_ida = distancia / velocidad
    if tarea['prioridad'] == 'URGENTE':
        tiempo_ida /= 2
    tiempo_vuelta = distancia / (velocidad * 3)

    print(f"[{now()}] [DRON {dron_id}] Enviando paquete {tarea['id']} a {tarea['destino']} | Prioridad: {tarea['prioridad']} | Distancia: {distancia} km | Tiempo estimado: {tiempo_ida:.2f}s", flush=True)
    time.sleep(tiempo_ida)

    if random.random() < 0.2:
        print(f"[{now()}] [DRON {dron_id}] FALLO entrega {tarea['id']} -> regreso a base...", flush=True)
        time.sleep(tiempo_vuelta)
        return 'fallo'

    print(f"[{now()}] [DRON {dron_id}] Entregado {tarea['id']} con EXITO. Regresando a base...", flush=True)
    time.sleep(tiempo_vuelta)
    return 'entrega_exitosa'

def main(dron_id):
    sock = None
    tarea_actual = None

    try:
        sock = socket.create_connection(('127.0.0.1', 8888))
        enviar_json(sock, {'id': dron_id, 'velocidad': 5})

        while True:
            respuesta = recibir_json(sock)
            if respuesta is None:
                print(f"[{now()}] [DRON {dron_id}] Servidor desconectado. Vuelta a la base.", flush=True)
                break

            if respuesta.get('accion') == 'nueva_tarea':
                tarea_actual = respuesta['tarea']
                estado = simular_entrega(tarea_actual, dron_id)
                if estado == 'entrega_exitosa':
                    mensaje_log = f"Entregado paquete {tarea_actual['id']} con EXITO en {tarea_actual['destino']}"
                elif estado == 'fallo':
                    mensaje_log = f"FALLO entrega {tarea_actual['id']} hacia {tarea_actual['destino']}"
                enviar_json(sock, {
                    'estado': estado,
                    'log_event': f"[{now()}] [DRON {dron_id}] {mensaje_log}"
                })
                tarea_actual = None

    except ConnectionRefusedError:
        print(f"[{now()}] [DRON {dron_id}] No se pudo conectar al servidor.", flush=True)
    except KeyboardInterrupt:
        print(f"[{now()}] [DRON {dron_id}] Interrupcion manual.", flush=True)
        if sock and tarea_actual:
            print(f"[{now()}] [DRON {dron_id}] Interrupcion durante tarea {tarea_actual['id']}, enviando fallo al servidor...", flush=True)
            try:
                enviar_json(sock, {'estado': 'fallo'})
            except:
                pass
    finally:
        if sock:
            try:
                sock.close()
            except:
                pass
            print(f"[{now()}] [DRON {dron_id}] Desconectado.", flush=True)

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print("Uso: python drones.py <dron_id>", flush=True)
        sys.exit(1)

    dron_id = sys.argv[1]
    main(dron_id)
