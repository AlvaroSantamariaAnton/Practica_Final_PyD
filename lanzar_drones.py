import subprocess
import signal
import os
import time

# Nombre del archivo que almacenará los PIDs de los drones activos
PID_FILE = "drones_activos.txt"

# Función para detener drones que se hayan lanzado previamente
def detener_drones_anteriores():
    if os.path.exists(PID_FILE):  # Verifica si el archivo de PIDs existe
        with open(PID_FILE) as f:  # Abre el archivo de PIDs
            for line in f:
                try:
                    os.kill(int(line.strip()), signal.SIGTERM)  # Envía la señal SIGTERM para detener el proceso
                except Exception:  # Ignora errores si el proceso ya no existe
                    pass
        os.remove(PID_FILE)  # Elimina el archivo de PIDs
        print("Drones anteriores detenidos.")

# Función para lanzar una cantidad específica de drones
def lanzar_drones(n):
    procesos = []  # Lista para almacenar los procesos de los drones
    with open(PID_FILE, "w") as f:  # Abre el archivo de PIDs en modo escritura
        for i in range(1, n + 1):  # Itera desde 1 hasta n
            dron_id = f"D{str(i).zfill(2)}"  # Genera un ID único para cada dron (e.g., D01, D02)
            proceso = subprocess.Popen(["python", "drones.py", dron_id])  # Lanza el script `drones.py` con el ID del dron
            procesos.append(proceso)  # Agrega el proceso a la lista
            f.write(str(proceso.pid) + "\n")  # Escribe el PID del proceso en el archivo
    return procesos  # Retorna la lista de procesos

# Punto de entrada del programa
if __name__ == "__main__":
    try:
        detener_drones_anteriores()  # Detiene drones lanzados previamente
        n = int(input("¿Cuántos drones quieres lanzar? "))  # Solicita al usuario la cantidad de drones a lanzar
        print(f"Lanzando {n} drones...")
        procesos = lanzar_drones(n)  # Lanza los drones
        print("Todos los drones fueron lanzados.")
        print("Presiona Ctrl+C para finalizar todos los drones y cerrar esta sesion...")
        while True:
            time.sleep(1)  # Mantiene el programa en ejecución hasta que se interrumpa manualmente
    except KeyboardInterrupt:  # Maneja la interrupción manual (Ctrl+C)
        print("\n\nFinalizando drones actuales...")
        for p in procesos:  # Itera sobre los procesos lanzados
            try:
                p.terminate()  # Termina cada proceso
            except:
                pass
        if os.path.exists(PID_FILE):  # Elimina el archivo de PIDs si existe
            os.remove(PID_FILE)
        print("Sesion de drones finalizada correctamente.")
