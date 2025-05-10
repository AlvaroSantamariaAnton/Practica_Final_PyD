class Tarea:
    def __init__(self, id, origen, destino, prioridad, distancia):
        self.id = id
        self.origen = origen
        self.destino = destino
        self.prioridad = prioridad
        self.distancia = distancia
        self.reintentos = 3

class Dron:
    def __init__(self, id, velocidad):
        self.id = id
        self.velocidad = velocidad
