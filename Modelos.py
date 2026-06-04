from sqlmodel import SQLModel, Field, Relationship
from modelo_type import *
from typing import Optional





class CombinadaBase(SQLModel):
      """Apuesta combinada: varios picks. Gana solo si todas las piernas aciertan."""      
      stake: float = 1.0                  # unidades apostadas
      cuota_total: float | None = Field(default=None,ge=1) # Π de las cuotas de las piernas ej 1.80
      prob_combinada: float | None = Field(default=None,ge=0,le=1)  # Π de las probs del modelo ej 0.23
      estado: CombinadaType | None = Field(default=None)  # pendiente | ganada | perdida
      activo: bool = True
      imagen_url: str | None = Field(default=None)  # URL publica de la imagen IA (en Supabase)

class CombinadaID(CombinadaBase, table=True):
      id: int | None = Field(default=None, primary_key=True, gt=0)
      


class PiernaBase(SQLModel,):
      """Cada pierna de una combinada."""
      # None = pierna "libre" (todavia no pertenece a ninguna combinada, esta en el pool)
      combinada_id: int | None = Field(default=None, foreign_key="combinadaid.id")
      partido: str                        # "Brasil vs Camerún"
      mercado: str                        # "1X2 Brasil", "Corners U12.5", "BTTS No"...
      cuota: float                        # cuota de esta pierna
      prob: float                         # prob del modelo (0–1)
      resultado: PiernaType | None = Field(default=None)       # pendiente | acierto | fallo
      activo: bool = True
      
class PiernaID(PiernaBase, table=True):
      id: int | None = Field(default=None, primary_key=True, gt=0)
      