from enum import Enum


class CombinadaType(str, Enum):
    PENDIENTE = "pendiente"
    ACIERTO = "acierto"
    FALLO = "fallo"


class PiernaType(str, Enum):
    PENDIENTE = "pendiente"
    ACIERTO = "acierto"
    FALLO = "fallo"
