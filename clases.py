# Clase que representa una tarea
class Tarea:
    def __init__(self, id, origen, destino, prioridad, distancia):
        # Identificador único de la tarea
        self.id = id
        # Punto de origen de la tarea
        self.origen = origen
        # Punto de destino de la tarea
        self.destino = destino
        # Nivel de prioridad de la tarea
        self.prioridad = prioridad
        # Distancia entre el origen y el destino
        self.distancia = distancia
        # Número de reintentos permitidos para completar la tarea
        self.reintentos = 3

# Clase que representa un dron
class Dron:
    def __init__(self, id, velocidad):
        # Identificador único del dron
        self.id = id
        # Velocidad del dron
        self.velocidad = velocidad
