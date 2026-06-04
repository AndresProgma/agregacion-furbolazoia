from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse

from app.core.database import create_all_tables
from app.core.templates import templates
from app.routers import combinadas, piernas, dashboard

# Creamos la app. 'lifespan=create_all_tables' hace que al arrancar se creen
# las tablas en la base de datos si todavia no existen.
app = FastAPI(lifespan=create_all_tables)

# Conectamos los routers (cada uno agrupa un conjunto de URLs por tema).
app.include_router(combinadas.router)
app.include_router(piernas.router)
app.include_router(dashboard.router)


# ----------------- pagina principal (home) -----------------
@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse(request, "base.html")
