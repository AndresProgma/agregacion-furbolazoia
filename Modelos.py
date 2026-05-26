from sqlmodel import SQLModel, Field, Relationship
from modelo_type import (
    Semaforo,
    Efecto,
    TipoSegmento,
    EstadoGuion,
    TipoFondo,
)


# ---------------- PERSONAJE (la mascota = una imagen) ----------------
class PersonajeBase(SQLModel):
    nombre: str                      # nombre de la mascota, ej: "Zoia" (obligatorio)
    imagen_url: str | None = None    # URL de la imagen del muñeco (subida a Supabase); puede ir vacío
    descripcion: str | None = None   # texto opcional, ej: "mascota analista"


class PersonajeID(PersonajeBase, table=True):           # table=True -> esta clase SÍ es tabla en la BD
    id: int | None = Field(default=None, primary_key=True)   # clave primaria; la BD la autogenera
    guiones: list["GuionID"] = Relationship(back_populates="personaje")


class PersonajeUpdate(PersonajeBase):
    nombre: str | None = None 
    imagen_url: str | None = None        # en el Update TODO es opcional (PATCH parcial)
    descripcion: str | None = None

# ---------------- PREDICCION (datos del modelo de futbol) ----------------
class PrediccionBase(SQLModel):
    equipo_local: str                # equipo de casa, ej: "Real Madrid" (obligatorio)
    equipo_visitante: str            # equipo visitante, ej: "Sevilla" (obligatorio)
    liga: str | None = None          # competición, ej: "LaLiga J30" (opcional)

    # Probabilidades del modelo (0-1) -> opcionales: solo las que tu modelo dé
    prob_local: float | None = None      # prob. de que gane el local, ej: 0.62
    prob_empate: float | None = None     # prob. de empate, ej: 0.21
    prob_visitante: float | None = None  # prob. de que gane el visitante, ej: 0.17
    prob_goles: float | None = None      # prob. de más goles (over), ej: 0.78
    prob_corners: float | None = None    # prob. relacionada a córners
    prob_amarillas: float | None = None  # prob. relacionada a tarjetas amarillas
    # Mercado / valor
    cuota_mercado: float | None = None   # cuota de la casa de apuestas, ej: 1.95
    semaforo: Semaforo = Semaforo.MEDIO  # decisión visual: ALTO 🟢 / MEDIO 🟡 / EVITAR 🔴


class PrediccionID(PrediccionBase, table=True):
    id: int | None = Field(default=None, primary_key=True)
    guiones: list["GuionID"] = Relationship(back_populates="prediccion")  # guiones creados desde esta predicción


# ---------------- FONDO (imagen reutilizable) ----------------
class FondoBase(SQLModel):
    imagen_url: str                       # URL de la imagen de fondo (Supabase); aquí SÍ obligatorio
    descripcion: str | None = None        # para reconocerlo/buscarlo, ej: "Bernabéu noche"
    tipo: TipoFondo = TipoFondo.GRAFICO   # categoría del fondo: ESTADIO / EQUIPO / GRAFICO / ...


class FondoID(FondoBase, table=True):
    id: int | None = Field(default=None, primary_key=True)
    segmentos: list["SegmentoID"] = Relationship(back_populates="fondo")  # segmentos que usan este fondo


# ---------------- GUION (el video) ----------------
class GuionBase(SQLModel):
    titulo: str                              # nombre del video, ej: "Madrid vs Sevilla — Over 2.5"
    hook_texto: str | None = None            # frase gancho del primer segundo, ej: "⚠ MODELO DETECTA VALOR"
    hook_efecto: Efecto = Efecto.GLITCH      # efecto del gancho: GLITCH / ZOOM / ALERTA / ...
    estado: EstadoGuion = EstadoGuion.BORRADOR   # en qué punto está: BORRADOR / LISTO / PUBLICADO


class GuionID(GuionBase, table=True):
    id: int | None = Field(default=None, primary_key=True)
    # FKs: "tabla.columna". Sin __tablename__, la tabla se llama "prediccionid"/"personajeid"
    prediccion_id: int | None = Field(default=None, foreign_key="prediccionid.id")
    personaje_id: int | None = Field(default=None, foreign_key="personajeid.id")

    # Relationships: back_populates = nombre de la variable en la otra clase
    prediccion: PrediccionID | None = Relationship(back_populates="guiones")  # la predicción de este guion
    personaje: PersonajeID | None = Relationship(back_populates="guiones")    # el personaje que narra
    segmentos: list["SegmentoID"] = Relationship(back_populates="guion")      # las escenas del video, en orden


# ---------------- SEGMENTO (cada parte cronometrada del loop) ----------------
class SegmentoBase(SQLModel):
    orden: int                            # posición en el video: 1, 2, 3... (define la secuencia)
    tipo: TipoSegmento                    # qué escena es: HOOK / DASHBOARD / PREDICCION / CTA / ...
    texto_muneco: str | None = None       # lo que DICE el muñeco en esta escena
    texto_overlay: str | None = None      # el texto que SALE en pantalla, ej: "OVER 2.5 → 78%"
    descripcion_visual: str | None = None # qué debe DIBUJAR la IA de video, ej: "fondo terminal oscuro, neón verde, zoom lento"
    duracion_seg: float = 3.0             # cuántos segundos dura la escena
    efecto_visual: Efecto = Efecto.ZOOM   # animación: ZOOM / BARRA_PROB / CONTADOR / ...


class SegmentoID(SegmentoBase, table=True):
    id: int | None = Field(default=None, primary_key=True)
    guion_id: int | None = Field(default=None, foreign_key="guionid.id")   # a qué guion pertenece esta escena
    fondo_id: int | None = Field(default=None, foreign_key="fondoid.id")   # qué imagen de fondo usa

    guion: GuionID | None = Relationship(back_populates="segmentos")  # atajo al guion dueño
    fondo: FondoID | None = Relationship(back_populates="segmentos")  # atajo al fondo de esta escena
