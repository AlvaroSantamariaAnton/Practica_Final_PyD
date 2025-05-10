import subprocess
import threading
import time

# Función para leer y mostrar la salida de un proceso en tiempo real
def leer_salida(nombre, proceso):
    for linea in iter(proceso.stdout.readline, b''):  # Itera sobre las líneas de salida del proceso
        print(f"[{nombre}] {linea.decode().rstrip()}")  # Imprime la línea con el nombre del proceso
    proceso.stdout.close()  # Cierra el flujo de salida estándar

# Función para lanzar el servidor
def lanzar_servidor():
    print("Lanzando servidor...")
    servidor = subprocess.Popen(  # Lanza el script `servidor.py` como un proceso
        ["python", "servidor.py"],
        stdout=subprocess.PIPE,  # Redirige la salida estándar
        stderr=subprocess.STDOUT  # Redirige la salida de error estándar a la salida estándar
    )
    # Crea un hilo para leer la salida del servidor en tiempo real
    hilo = threading.Thread(target=leer_salida, args=("SERVIDOR", servidor))
    hilo.start()  # Inicia el hilo
    threads.append(hilo)  # Agrega el hilo a la lista global de hilos
    return servidor  # Retorna el proceso del servidor

# Función para lanzar múltiples drones
def lanzar_drones(n):
    procesos = []  # Lista para almacenar los procesos de los drones
    for i in range(1, n + 1):  # Itera desde 1 hasta n
        dron_id = f"D{str(i).zfill(2)}"  # Genera un ID único para cada dron (e.g., D01, D02)
        print(f"Lanzando Dron {dron_id}...")
        p = subprocess.Popen(  # Lanza el script `drones.py` con el ID del dron
            ["python", "drones.py", dron_id],
            stdout=subprocess.PIPE,  # Redirige la salida estándar
            stderr=subprocess.STDOUT  # Redirige la salida de error estándar a la salida estándar
        )
        # Crea un hilo para leer la salida del dron en tiempo real
        hilo = threading.Thread(target=leer_salida, args=(f"DRON {dron_id}", p))
        hilo.start()  # Inicia el hilo
        threads.append(hilo)  # Agrega el hilo a la lista global de hilos
        procesos.append(p)  # Agrega el proceso del dron a la lista
        time.sleep(0.2)  # Espera un breve momento antes de lanzar el siguiente dron
    return procesos  # Retorna la lista de procesos de los drones

# Función principal del programa
def main():
    global threads
    threads = []  # Lista global para almacenar los hilos activos

    # Solicita al usuario la cantidad de drones a lanzar
    n = int(input("¿Cuántos drones quieres lanzar? "))
    print("\nSistema en marcha. Presiona Ctrl+C para detener todo.")
    servidor = lanzar_servidor()  # Lanza el servidor
    time.sleep(1)  # Espera un momento para asegurarse de que el servidor esté en marcha
    drones = lanzar_drones(n)  # Lanza los drones
    
    try:
        while True:
            time.sleep(1)  # Mantiene el programa en ejecución hasta que se interrumpa manualmente
    except KeyboardInterrupt:  # Maneja la interrupción manual (Ctrl+C)
        print("\nDeteniendo drones y servidor...")
        for p in drones:  # Itera sobre los procesos de los drones
            try:
                p.terminate()  # Termina cada proceso de dron
            except:
                pass
        try:
            servidor.terminate()  # Termina el proceso del servidor
        except:
            pass

        print("Esperando cierre de procesos...")
        for hilo in threads:  # Espera a que todos los hilos finalicen
            hilo.join(timeout=2)
        print("Todo detenido correctamente.")

# Punto de entrada del programa
if __name__ == "__main__":
    main()  # Llama a la función principal
