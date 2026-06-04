from sqlmodel import SQLModel, Field

from app.models.enums import CombinadaType


class CombinadaBase(SQLModel):
    """Apuesta combinada: varios picks. Gana solo si todas las piernas aciertan."""
    stake: float = 1.0                  # unidades apostadas
    cuota_total: float | None = Field(default=None, ge=1)         # Π de las cuotas de las piernas ej 1.80
    prob_combinada: float | None = Field(default=None, ge=0, le=1)  # Π de las probs del modelo ej 0.23
    estado: CombinadaType | None = Field(default=None)           # pendiente | acierto | fallo
    activo: bool = True
    imagen_url: str | None = Field(default=None)                 # URL publica de la imagen (en Supabase)


class CombinadaID(CombinadaBase, table=True):
    id: int | None = Field(default=None, primary_key=True, gt=0)
