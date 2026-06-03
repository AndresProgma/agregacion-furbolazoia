from fastapi import FastAPI, HTTPException, UploadFile, File, Request, Form, Depends
from typing import Optional
from fastapi.params import Depends
from sqlmodel import Session
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from Modelos import *
from modelo_type import *
from db import SessionDep, create_all_tables, get_session
from operaciones_db import *

app = FastAPI(lifespan=create_all_tables)

templates = Jinja2Templates(directory="templates")

#-----------------pagina principal home---------------------
@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse({"request": request}, "base.html")


##--------------------------crear combinada -------------------
@app.post("/Combinada", response_model=CombinadaID)
async def crear_combinada_api(pokemon: CombinadaBase, session: SessionDep):
    
    return Crear_Combinada_bd(pokemon, session)

#---------------------borrar combinada-------------------------

@app.delete("/pokemon/{id}", response_model=CombinadaBase)
async def delete_one_combinada(id: int, session: SessionDep):
    deleted = eliminar_combinada(id, session)
    if not (deleted):
        raise HTTPException(status_code=404, detail=f"{id} combinada not found")
    return deleted


# Version POST para el boton del HTML (los forms no pueden mandar DELETE)
@app.post("/Combinada/{id}/eliminar", response_class=HTMLResponse)
async def eliminar_una_combinada(id: int, session: Session = Depends(get_session)):
    borrada = eliminar_combinada(id, session)   # soft delete de la combinada + sus piernas
    if not borrada:
        raise HTTPException(status_code=404, detail=f"{id} combinada not found")
    return RedirectResponse("/combinadas/", status_code=302)


#---------------------borrar pierna-------------------------
# POST (no DELETE) para que el boton del HTML pueda llamarlo (los forms solo hacen GET/POST)
@app.post("/Pierna/{id}/eliminar", response_class=HTMLResponse)
async def eliminar_una_pierna(id: int, session: Session = Depends(get_session)):
    borrada = eliminar_pierna(id, session)
    if not borrada:
        raise HTTPException(status_code=404, detail=f"{id} pierna not found")
    return RedirectResponse("/combinadas/", status_code=302)   # volvemos a la lista





#-------------------------mostrar todo combinadas (con buscador por id)------------------------
@app.get("/combinadas/", response_class=HTMLResponse)
async def mostrar_todas_combinadas(request: Request, id: Optional[int] = None, session: Session = Depends(get_session)):
    # Si la URL trae ?id=, buscamos SOLO esa combinada; si no, mostramos todas
    if id is not None:
        c = Mostrar_Combinada_bd(id, session)
        combinadas = [c] if (c and c.activo) else []   # solo si existe y está activa
    else:
        combinadas = Mostrar_Combinadas_bd(session)

    # Por cada combinada armamos un par {combinada, sus piernas} para mostrarlas juntas
    datos = []
    for c in combinadas:
        piernas = Piernas_de_combinada_bd(c.id, session)
        datos.append({"combinada": c, "piernas": piernas})
    return templates.TemplateResponse(request, "all_combinadas.html", {"datos": datos, "busqueda": id})




#-------------------------mostrar todas piernas (con buscador por id)------------------------
@app.get("/piernas/", response_class=HTMLResponse)
async def mostrar_todas_piernas(request: Request, id: Optional[int] = None, session: Session = Depends(get_session)):
    # Si la URL trae ?id=, buscamos SOLO esa pierna; si no, mostramos todas
    if id is not None:
        p = Mostrar_Pierna_bd(id, session)
        piernas = [p] if (p and p.activo) else []   # solo si existe y está activa
    else:
        piernas = Mostrar_Piernas_bd(session)
    return templates.TemplateResponse(request, "all_piernas.html", {"piernas_lista": piernas, "busqueda": id})



@app.get("/Combinada/Crear/", response_class=HTMLResponse)
async def Crear_Combinada_vista(request: Request):
    return templates.TemplateResponse(request, "crear.html")


@app.post("/Combinada/Crear/", response_class=HTMLResponse)
async def pokemon_catched(
        stake: str = Form(),
        cuota_total: Optional[float] = Form(None),
        prob_combinada: Optional[float] = Form(None),
        estado: PiernaType = Form(None),
        activo: Optional[bool] = Form(None),
        session: Session = Depends(get_session)):
    nueva_combinada = CombinadaBase(stake=stake, cuota_total=cuota_total, prob_combinada=prob_combinada, estado= estado,activo=activo)
    catched = Crear_Combinada_bd(nueva_combinada, session)

    return RedirectResponse("/combinadas/", status_code=302)


@app.get("/Pierna/Crear/", response_class=HTMLResponse)
async def crear_pierna_vista(request: Request, session: Session = Depends(get_session)):
    # Pasamos las combinadas para llenar el <select> del formulario
    combinadas = Mostrar_Combinadas_bd(session)
    return templates.TemplateResponse(request, "crear_pierna.html", {"pierna_lista": combinadas})


@app.post("/Pierna/Crear/", response_class=HTMLResponse)
async def crear_pierna_post(
        combinada_id: Optional[str] = Form(None),   # vacio "" = pierna libre (sin combinada)
        partido: str = Form(),
        mercado: str = Form(),
        cuota: float = Form(),
        prob: float = Form(),
        resultado: Optional[PiernaType] = Form(None),
        activo: bool = Form(True),   # una pierna nueva queda activa por defecto
        session: Session = Depends(get_session)):

    # Si el <select> mando "" (libre), guardamos None; si mando un id, lo pasamos a int
    cid = int(combinada_id) if combinada_id else None

    nueva_pierna = PiernaBase(
        combinada_id=cid, partido=partido, mercado=mercado,
        cuota=cuota, prob=prob, resultado=resultado, activo=activo)

    creada = Crear_Pierna_bd(nueva_pierna, session)
    if creada is None:                       # la combinada no existía
        raise HTTPException(status_code=404, detail="La combinada no existe")

    return RedirectResponse("/piernas/", status_code=302)


# ===================== COMBINADA COMPLETA (armar arrastrando) =====================

@app.get("/Combinada/Completa/", response_class=HTMLResponse)
async def combinada_completa_inicio(request: Request):
    # Pagina con el boton "Crear combinada"
    return templates.TemplateResponse(request, "combinada_completa_inicio.html")


@app.post("/Combinada/Completa/", response_class=HTMLResponse)
async def combinada_completa_crear(session: Session = Depends(get_session)):
    # Crea la combinada VACIA y lleva al armador de esa combinada
    nueva = Crear_Combinada_vacia_bd(session)
    return RedirectResponse(f"/Combinada/Completa/{nueva.id}", status_code=302)


@app.get("/Combinada/Completa/{combinada_id}", response_class=HTMLResponse)
async def combinada_completa_builder(combinada_id: int, request: Request, session: Session = Depends(get_session)):
    combinada = Mostrar_Combinada_bd(combinada_id, session)
    if combinada is None:
        raise HTTPException(status_code=404, detail="Combinada no existe")
    asignadas = Piernas_de_combinada_bd(combinada_id, session)  # ya estan dentro
    libres = Piernas_libres_bd(session)                         # el pool de la derecha
    return templates.TemplateResponse(request, "combinada_completa.html",
        {"combinada": combinada, "asignadas": asignadas, "libres": libres})


@app.post("/api/combinada/{combinada_id}/agregar/{pierna_id}")
async def api_agregar_pierna(combinada_id: int, pierna_id: int, session: Session = Depends(get_session)):
    # Lo llama el JavaScript al soltar una pierna. Asigna y devuelve los totales nuevos.
    combinada = Asignar_Pierna_bd(pierna_id, combinada_id, session)
    if combinada is None:
        raise HTTPException(status_code=404, detail="Pierna o combinada no existe")
    return {"cuota_total": combinada.cuota_total, "prob_combinada": combinada.prob_combinada}


@app.post("/Combinada/Completa/{combinada_id}/finalizar", response_class=HTMLResponse)
async def combinada_completa_finalizar(combinada_id: int, stake: float = Form(), session: Session = Depends(get_session)):
    # Guarda el stake que escribio el usuario y termina -> va a la lista
    combinada = Mostrar_Combinada_bd(combinada_id, session)
    if combinada is None:
        raise HTTPException(status_code=404, detail="Combinada no existe")
    combinada.stake = stake
    session.add(combinada)
    session.commit()
    return RedirectResponse("/combinadas/", status_code=302)
