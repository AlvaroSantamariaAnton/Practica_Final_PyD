import tkinter as tk
from tkinter import scrolledtext
import threading
import time
import os

LOG_FILE = "eventos_servidor.log"

class MonitorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Monitor del Sistema de Drones")
        self.root.geometry("1200x800")

        self.text_area = scrolledtext.ScrolledText(root, wrap=tk.WORD, font=("Courier", 10), width=140, height=40)
        self.text_area.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

        self.btn_finalizar = tk.Button(root, text="Finalizar visualización", command=self.salir, font=("Arial", 12))
        self.btn_finalizar.pack(pady=10)

        self.stop = False
        self.last_size = 0
        self.hilo = threading.Thread(target=self.actualizar_log, daemon=True)
        self.hilo.start()

    def actualizar_log(self):
        while not self.stop:
            try:
                if os.path.exists(LOG_FILE):
                    with open(LOG_FILE, "r", encoding="utf-8") as f:
                        f.seek(self.last_size)
                        nuevas = f.read()
                        self.last_size = f.tell()
                        if nuevas:
                            self.text_area.insert(tk.END, nuevas)
                            self.text_area.see(tk.END)
            except Exception as e:
                pass
            time.sleep(1)

    def salir(self):
        self.stop = True
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = MonitorApp(root)
    root.mainloop()
