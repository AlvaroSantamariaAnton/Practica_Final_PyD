import tkinter as tk
from tkinter import scrolledtext
import threading
import time
import os

# Nombre del archivo de log que se va a monitorear
LOG_FILE = "eventos_servidor.log"

# Clase principal de la aplicación de monitoreo
class MonitorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Monitor del Sistema de Drones")  # Título de la ventana
        self.root.geometry("1200x800")  # Tamaño de la ventana

        # Área de texto con scroll para mostrar el contenido del archivo de log
        self.text_area = scrolledtext.ScrolledText(root, wrap=tk.WORD, font=("Courier", 10), width=140, height=40)
        self.text_area.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)  # Empaqueta el área de texto en la ventana

        # Botón para finalizar la visualización
        self.btn_finalizar = tk.Button(root, text="Finalizar visualización", command=self.salir, font=("Arial", 12))
        self.btn_finalizar.pack(pady=10)  # Empaqueta el botón en la ventana

        self.stop = False  # Variable para controlar el estado del hilo
        self.last_size = 0  # Tamaño del archivo leído hasta el momento
        self.hilo = threading.Thread(target=self.actualizar_log, daemon=True)  # Hilo para actualizar el log en tiempo real
        self.hilo.start()  # Inicia el hilo

    # Método para actualizar el contenido del área de texto con nuevas líneas del archivo de log
    def actualizar_log(self):
        while not self.stop:  # Mientras no se haya solicitado detener el hilo
            try:
                if os.path.exists(LOG_FILE):  # Verifica si el archivo de log existe
                    with open(LOG_FILE, "r", encoding="utf-8") as f:  # Abre el archivo en modo lectura
                        f.seek(self.last_size)  # Mueve el puntero al último tamaño leído
                        nuevas = f.read()  # Lee las nuevas líneas
                        self.last_size = f.tell()  # Actualiza el tamaño leído
                        if nuevas:  # Si hay nuevas líneas
                            self.text_area.insert(tk.END, nuevas)  # Inserta las nuevas líneas en el área de texto
                            self.text_area.see(tk.END)  # Desplaza el scroll al final
            except Exception as e:  # Maneja cualquier excepción
                pass
            time.sleep(1)  # Espera 1 segundo antes de volver a verificar

    # Método para finalizar la aplicación
    def salir(self):
        self.stop = True  # Detiene el hilo
        self.root.destroy()  # Cierra la ventana principal

# Punto de entrada del programa
if __name__ == "__main__":
    root = tk.Tk()  # Crea la ventana principal de Tkinter
    app = MonitorApp(root)  # Instancia la aplicación de monitoreo
    root.mainloop()  # Inicia el bucle principal de la interfaz gráfica
