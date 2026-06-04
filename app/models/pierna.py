from sqlmodel import SQLModel, Field

from app.models.enums import PiernaType


class PiernaBase(SQLModel):
    """Cada pierna de una combinada."""
    # None = pierna "libre" (todavia no pertenece a ninguna combinada, esta en el pool).
    # El foreign_key apunta por NOMBRE de tabla ("combinadaid.id"), por eso no hace falta
    # importar el modelo Combinada aqui (evita imports circulares).
    combinada_id: int | None = Field(default=None, foreign_key="combinadaid.id")
    partido: str                        # "Brasil vs Camerún"
    mercado: str                        # "1X2 Brasil", "Corners U12.5", "BTTS No"...
    cuota: float                        # cuota de esta pierna
    prob: float                         # prob del modelo (0–1)
    resultado: PiernaType | None = Field(default=None)   # pendiente | acierto | fallo
    activo: bool = True


class PiernaID(PiernaBase, table=True):
    id: int | None = Field(default=None, primary_key=True, gt=0)
