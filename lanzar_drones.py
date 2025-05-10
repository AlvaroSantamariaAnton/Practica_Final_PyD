import subprocess
import signal
import os
import time

PID_FILE = "drones_activos.txt"

def detener_drones_anteriores():
    if os.path.exists(PID_FILE):
        with open(PID_FILE) as f:
            for line in f:
                try:
                    os.kill(int(line.strip()), signal.SIGTERM)
                except Exception:
                    pass
        os.remove(PID_FILE)
        print("Drones anteriores detenidos.")

def lanzar_drones(n):
    procesos = []
    with open(PID_FILE, "w") as f:
        for i in range(1, n + 1):
            dron_id = f"D{str(i).zfill(2)}"
            proceso = subprocess.Popen(["python", "drones.py", dron_id])
            procesos.append(proceso)
            f.write(str(proceso.pid) + "\n")
    return procesos

if __name__ == "__main__":
    try:
        detener_drones_anteriores()
        n = int(input("¿Cuántos drones quieres lanzar? "))
        print(f"Lanzando {n} drones...")
        procesos = lanzar_drones(n)
        print("Todos los drones fueron lanzados.")
        print("Presiona Ctrl+C para finalizar todos los drones y cerrar esta sesion...")
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n\nFinalizando drones actuales...")
        for p in procesos:
            try:
                p.terminate()
            except:
                pass
        if os.path.exists(PID_FILE):
            os.remove(PID_FILE)
        print("Sesion de drones finalizada correctamente.")
