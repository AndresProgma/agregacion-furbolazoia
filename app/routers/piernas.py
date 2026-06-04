from fastapi import APIRouter, HTTPException, Request, Form, Depends
from typing import Optional
from sqlmodel import Session
from fastapi.responses import HTMLResponse, RedirectResponse

from app.core.database import get_session
from app.core.templates import templates
from app.models import *
from app.services.crud import *
from app.services.futbolaza_api import recomendadas   # apuestas recomendadas de futbolaza (servicio aparte)

router = APIRouter()


# ===================== ELIMINAR PIERNA =====================
# POST (no DELETE) para que el boton del HTML pueda llamarlo (los forms solo hacen GET/POST)
@router.post("/Pierna/{id}/eliminar", response_class=HTMLResponse)
async def eliminar_una_pierna(id: int, session: Session = Depends(get_session)):
    borrada = eliminar_pierna(id, session)
    if not borrada:
        raise HTTPException(status_code=404, detail=f"{id} pierna not found")
    return RedirectResponse("/combinadas/", status_code=302)   # volvemos a la lista


# ===================== MOSTRAR PIERNAS (con buscador por id) =====================
@router.get("/piernas/", response_class=HTMLResponse)
async def mostrar_todas_piernas(request: Request, id: Optional[int] = None, session: Session = Depends(get_session)):
    # Si la URL trae ?id=, buscamos SOLO esa pierna; si no, mostramos todas
    if id is not None:
        p = Mostrar_Pierna_bd(id, session)
        piernas = [p] if (p and p.activo) else []   # solo si existe y está activa
    else:
        piernas = Mostrar_Piernas_bd(session)
    return templates.TemplateResponse(request, "all_piernas.html", {"piernas_lista": piernas, "busqueda": id})


# ===================== CREAR PIERNA =====================
@router.get("/Pierna/Crear/", response_class=HTMLResponse)
async def crear_pierna_vista(request: Request, session: Session = Depends(get_session)):
    # Pasamos las combinadas para llenar el <select> del formulario
    combinadas = Mostrar_Combinadas_bd(session)
    # Apuestas recomendadas de futbolaza: autocompletan partido + mercado + prob
    recos = recomendadas()
    return templates.TemplateResponse(request, "crear_pierna.html",
        {"combinadas_lista": combinadas, "recomendadas": recos})


@router.post("/Pierna/Crear/", response_class=HTMLResponse)
async def crear_pierna_post(
        request: Request,
        combinada_id: Optional[str] = Form(None),   # vacio "" = pierna libre (sin combinada)
        partido: str = Form(""),
        mercado: str = Form(""),
        cuota: str = Form(""),
        prob: str = Form(""),
        resultado: Optional[PiernaType] = Form(None),
        activo: bool = Form(True),   # una pierna nueva queda activa por defecto
        session: Session = Depends(get_session)):

    # Re-muestra el MISMO formulario con un mensaje de error y lo que ya se escribio.
    # Cada vez que renderizas una plantilla, le tienes que dar TODOS los datos.
    def volver_con_error(msg):
        combinadas = Mostrar_Combinadas_bd(session)   # el <select> necesita la lista otra vez
        return templates.TemplateResponse(request, "crear_pierna.html", {
            "combinadas_lista": combinadas,
            "error": msg,
            "valores": {"partido": partido, "mercado": mercado, "cuota": cuota, "prob": prob},
        })

    # --- validacion manual con mensajes amables (segunda capa, por si saltan el front) ---
    if not partido.strip():
        return volver_con_error("El partido es obligatorio.")
    if not mercado.strip():
        return volver_con_error("El mercado es obligatorio.")
    try:
        cuota_f = float(cuota)
    except ValueError:
        return volver_con_error("La cuota debe ser un número (ej. 1.85).")
    if cuota_f <= 1:
        return volver_con_error("La cuota debe ser mayor a 1.")
    try:
        prob_f = float(prob)
    except ValueError:
        return volver_con_error("La probabilidad debe ser un número entre 0 y 1.")
    if not (0 <= prob_f <= 1):
        return volver_con_error("La probabilidad debe estar entre 0 y 1.")

    # Si el <select> mando "" (libre), guardamos None; si mando un id, lo pasamos a int
    cid = int(combinada_id) if combinada_id else None

    nueva_pierna = PiernaBase(
        combinada_id=cid, partido=partido, mercado=mercado,
        cuota=cuota_f, prob=prob_f, resultado=resultado, activo=activo)

    creada = Crear_Pierna_bd(nueva_pierna, session)
    if creada is None:                       # la combinada seleccionada no existía
        return volver_con_error("La combinada seleccionada no existe.")

    return RedirectResponse("/piernas/", status_code=302)


# ===================== EDITAR PIERNA =====================
@router.get("/Pierna/{id}/editar", response_class=HTMLResponse)
async def editar_pierna_vista(id: int, request: Request, session: Session = Depends(get_session)):
    # Muestra el formulario YA LLENO con los datos actuales de la pierna
    pierna = Mostrar_Pierna_bd(id, session)
    if pierna is None:
        raise HTTPException(status_code=404, detail="Pierna no existe")
    # Pasamos las combinadas para llenar el <select> de "a cuál pertenece"
    combinadas = Mostrar_Combinadas_bd(session)
    return templates.TemplateResponse(request, "editar_pierna.html",
        {"pierna": pierna, "combinadas_lista": combinadas})


@router.post("/Pierna/{id}/editar", response_class=HTMLResponse)
async def editar_pierna_post(
        id: int,
        request: Request,
        partido: str = Form(""),
        mercado: str = Form(""),
        cuota: str = Form(""),
        prob: str = Form(""),
        resultado: Optional[PiernaType] = Form(None),
        combinada_id: Optional[str] = Form(None),   # vacio "" = pierna libre (sin combinada)
        session: Session = Depends(get_session)):

    pierna = Mostrar_Pierna_bd(id, session)
    if pierna is None:
        raise HTTPException(status_code=404, detail="Pierna no existe")

    def volver_con_error(msg):
        combinadas = Mostrar_Combinadas_bd(session)   # el <select> necesita la lista otra vez
        return templates.TemplateResponse(request, "editar_pierna.html", {
            "pierna": pierna, "combinadas_lista": combinadas, "error": msg,
            "valores": {"partido": partido, "mercado": mercado, "cuota": cuota,
                        "prob": prob, "combinada_id": combinada_id},
        })

    # --- misma validacion que al crear ---
    if not partido.strip():
        return volver_con_error("El partido es obligatorio.")
    if not mercado.strip():
        return volver_con_error("El mercado es obligatorio.")
    try:
        cuota_f = float(cuota)
    except ValueError:
        return volver_con_error("La cuota debe ser un número (ej. 1.85).")
    if cuota_f <= 1:
        return volver_con_error("La cuota debe ser mayor a 1.")
    try:
        prob_f = float(prob)
    except ValueError:
        return volver_con_error("La probabilidad debe ser un número entre 0 y 1.")
    if not (0 <= prob_f <= 1):
        return volver_con_error("La probabilidad debe estar entre 0 y 1.")

    # El <select> manda "" (libre) -> None; o un id -> int. Si manda un id, debe existir
    cid = int(combinada_id) if combinada_id else None
    if cid is not None and Mostrar_Combinada_bd(cid, session) is None:
        return volver_con_error("La combinada seleccionada no existe.")

    Editar_Pierna_bd(id, partido, mercado, cuota_f, prob_f, resultado, cid, session)
    return RedirectResponse("/piernas/", status_code=302)
