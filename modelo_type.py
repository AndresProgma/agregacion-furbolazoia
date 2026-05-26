from enum import Enum


class Semaforo(str, Enum):
    ALTO = "alto"        # 🟢 HIGH VALUE
    MEDIO = "medio"      # 🟡 MEDIUM VALUE
    EVITAR = "evitar"    # 🔴 AVOID


class Efecto(str, Enum):
    ZOOM = "zoom"
    GLITCH = "glitch"
    BARRA_PROB = "barra_prob"
    CONTADOR = "contador"
    RED_NEURONAL = "red_neuronal"
    CODIGO = "codigo"
    ALERTA = "alerta"


class TipoSegmento(str, Enum):
    HOOK = "hook"
    DASHBOARD = "dashboard"
    CEREBRO = "cerebro"
    PREDICCION = "prediccion"
    SEMAFORO = "semaforo"
    STORYTELLING = "storytelling"
    CTA = "cta"

class EstadoGuion(str, Enum):
    BORRADOR = "borrador"
    LISTO = "listo"
    PUBLICADO = "publicado"


class TipoFondo(str, Enum):
    ESTADIO = "estadio"
    EQUIPO = "equipo"
    GRAFICO = "grafico"
    CEREBRO = "cerebro"
    MUNECO = "muneco"
