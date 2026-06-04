# Puente de compatibilidad.
# El código real ahora vive en el paquete  app/  (app/main.py).
# Este archivo solo reexporta la app para que siga funcionando el arranque
# clásico  uvicorn main:app  (por ejemplo, en el deploy ya configurado).
# Lo recomendado de aquí en adelante es:  uvicorn app.main:app --reload
from app.main import app

__all__ = ["app"]
