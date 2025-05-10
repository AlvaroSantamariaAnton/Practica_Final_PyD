import subprocess
import threading
import time

def leer_salida(nombre, proceso):
    for linea in iter(proceso.stdout.readline, b''):
        print(f"[{nombre}] {linea.decode().rstrip()}")
    proceso.stdout.close()

def lanzar_servidor():
    print("Lanzando servidor...")
    servidor = subprocess.Popen(
        ["python", "servidor.py"],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT
    )
    hilo = threading.Thread(target=leer_salida, args=("SERVIDOR", servidor))
    hilo.start()
    threads.append(hilo)
    return servidor

def lanzar_drones(n):
    procesos = []
    for i in range(1, n + 1):
        dron_id = f"D{str(i).zfill(2)}"
        print(f"Lanzando Dron {dron_id}...")
        p = subprocess.Popen(
            ["python", "drones.py", dron_id],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT
        )
        hilo = threading.Thread(target=leer_salida, args=(f"DRON {dron_id}", p))
        hilo.start()
        threads.append(hilo)
        procesos.append(p)
        time.sleep(0.2)
    return procesos

def main():
    global threads
    threads = []

    n = int(input("¿Cuántos drones quieres lanzar? "))
    print("\nSistema en marcha. Presiona Ctrl+C para detener todo.")
    servidor = lanzar_servidor()
    time.sleep(1)
    drones = lanzar_drones(n)
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nDeteniendo drones y servidor...")
        for p in drones:
            try:
                p.terminate()
            except:
                pass
        try:
            servidor.terminate()
        except:
            pass

        print("Esperando cierre de procesos...")
        for hilo in threads:
            hilo.join(timeout=2)
        print("Todo detenido correctamente.")

if __name__ == "__main__":
    main()
