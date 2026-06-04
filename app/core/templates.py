from pathlib import Path
from fastapi.templating import Jinja2Templates

# Ruta a la carpeta de plantillas calculada A PARTIR de este archivo, no del
# directorio desde donde se ejecuta el server. Asi las plantillas SIEMPRE se
# encuentran, sin importar si corres  uvicorn main:app  o  uvicorn app.main:app.
#   __file__              -> .../app/core/templates.py
#   .parents[1]           -> .../app
#   / "templates"         -> .../app/templates
TEMPLATES_DIR = Path(__file__).resolve().parents[1] / "templates"

# Un unico objeto 'templates' que comparten TODOS los routers.
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))
