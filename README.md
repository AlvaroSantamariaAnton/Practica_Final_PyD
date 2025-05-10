# Simulador de Red de Drones con Entregas Distribuidas (Python + asyncio)

Este proyecto simula una red de drones que realizan entregas de paquetes desde un almacen central en Madrid a distintas provincias de España (excluyendo Madrid). Las entregas varían en tiempo según la distancia, la prioridad y el retorno a la base. El sistema es distribuido, concurrente y asincrónico, y maneja reintentos, métricas de rendimiento y errores de red de forma robusta.

---

## 📦 Estructura del proyecto

```
├── servidor.py             # Servidor central (asyncio)
├── drones.py               # Cliente simulado (proceso dron)
├── clases.py               # Clases base: Tarea y Dron
├── provincias.py           # Diccionario de provincias y distancias
├── lanzar_drones.py        # Script para lanzar múltiples drones
├── gestor.py               # Consola unificada (modo terminal)
├── monitor_gui.py          # Visualización básica del sistema en tiempo real
├── eventos_servidor.log    # Registro detallado del sistema
├── README.md               # Este archivo
```

---

## ▶️ Requisitos

- Python 3.8+

---

## 🚀 Cómo ejecutar el sistema

### Opción recomendada: TODO desde una sola consola (modo terminal)

```bash
python gestor.py
```

Esto lanzará el servidor y luego te preguntará cuántos drones quieres lanzar. Unificará todas las salidas (servidor + drones) en una única consola.

**Importante:** al usar `gestor.py`, cuando finalizas la sesión con `Ctrl+C`, **se detienen tanto el servidor como todos los drones**, por lo que **la próxima vez que lo inicies, todo empezará desde cero.**

---

### Opción alternativa: monitor gráfico en paralelo

```bash
python monitor_gui.py
```

Esto abrirá una ventana de visualización **en tiempo real** con los mensajes del log del servidor y drones, imitando la consola original. Solo contiene un botón para **finalizar la visualización** y es útil cuando usas `gestor.py`.

---

### Opción manual (por separado)

#### 1. Ejecutar el servidor

```bash
python servidor.py
```

#### 2. En otra terminal, lanzar drones:

```bash
python lanzar_drones.py
```

**Ventaja:** puedes cerrar solo el proceso de los drones y volver a ejecutarlo más tarde, mientras el servidor **nunca se ha detenido** y sigue generando tareas. Al reconectar, los nuevos drones retomarán desde donde se quedó la última sesión. **El sistema solo se reinicia completamente cuando cierras el servidor manualmente.**

---

## 📒 Lógica del sistema

- El servidor genera tareas desde el almacén central (Madrid) a cualquier provincia **excepto Madrid**.
- Cada tarea tiene un destino, una distancia y una prioridad (`NORMAL` o `URGENTE`).
- Los drones:
  - Recogen tareas en orden de prioridad y antigüedad.
  - Simulan la entrega según la distancia y prioridad.
  - Regresan a la base tras cada entrega o fallo.
  - Reintentan entregas fallidas hasta 3 veces.
  - Si fallan 3 veces, la tarea es eliminada del sistema.
- Todas las acciones quedan registradas en el log del servidor.

---

## 📊 Métricas de rendimiento

Cada 30 segundos exactos el servidor imprime en consola y log:

- Cantidad de tareas completadas.
- Tiempo medio de entrega (ida + vuelta).

Ejemplo:
```
[RENDIMIENTO] Tareas entregadas: 10 | Tiempo medio por entrega: 95.12 s
```

---

## 📝 Log de eventos

Toda la actividad se registra en `eventos_servidor.log`, incluyendo:

```
[2025-05-10 21:00:00] Nueva tarea generada: T5 (NORMAL) -> Almacen provincial de Zaragoza
[2025-05-10 21:00:03] Asignando tarea T5 a Dron D01 -> Almacen provincial de Zaragoza
[2025-05-10 21:00:18] [DRON D01] Entregado paquete T5 con EXITO en Almacen provincial de Zaragoza
[2025-05-10 21:00:30] [RENDIMIENTO] Tareas entregadas: 1 | Tiempo medio por entrega: 14.56 s
```

También incluye los fallos, reintentos y reconexiones de los drones de forma automática.

---

## Link al repositorio

https://github.com/AlvaroSantamariaAnton/Practica_Final_PyD.git
