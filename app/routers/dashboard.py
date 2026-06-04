from fastapi import APIRouter, Request, Depends, Form, HTTPException
from sqlmodel import Session
from fastapi.responses import HTMLResponse, RedirectResponse

from app.core.database import get_session
from app.core.templates import templates
from app.models import CombinadaID, PiernaID
from app.services.crud import (
    Mostrar_Combinadas_bd,
    Piernas_de_combinada_bd,
    Piernas_libres_bd,
    Recalcular_Combinada_bd,
)

router = APIRouter()


def _pierna_info(p: PiernaID) -> dict:
    """Datos de una pierna que necesita el editor (tabla + gráfica)."""
    return {
        "id": p.id,
        "partido": p.partido,
        "mercado": p.mercado,
        "prob": p.prob,
        "cuota": p.cuota,
    }


# ===================== COMBINADA DEL DIA (editor + gráfica idea #1) =====================

@router.get("/Combinada/Dia/", response_class=HTMLResponse)
async def combinada_del_dia(request: Request, session: Session = Depends(get_session)):
    # Arrastra una combinada (abajo) a la zona de edición. A la derecha ves su tabla
    # de piernas (editable) y un POOL de piernas libres para AGREGAR. La gráfica
    # (idea #1) muestra en tiempo real cómo CAE la probabilidad combinada y SUBE
    # el pago a medida que agregas/quitas piernas. El botón Guardar persiste los
    # cambios; Descartar los revierte a como estaba.
    combinadas = list(Mostrar_Combinadas_bd(session))
    datos = []
    for c in combinadas:
        piernas = Piernas_de_combinada_bd(c.id, session)
        datos.append({
            "combinada": c,
            "piernas_info": [_pierna_info(p) for p in piernas],
        })

    # Pool de piernas LIBRES (no pertenecen a ninguna combinada): se pueden agregar.
    piernas_pool = [_pierna_info(p) for p in Piernas_libres_bd(session)]

    return templates.TemplateResponse(request, "combinada_dia.html",
        {"datos": datos, "piernas_pool": piernas_pool})


@router.post("/Combinada/Dia/{id}/guardar", response_class=HTMLResponse)
async def guardar_combinada_dia(
        id: int,
        pierna_ids: str = Form(""),   # ids finales que deben quedar en la combinada, ej "3,5,7"
        session: Session = Depends(get_session)):
    """Guarda la combinada con las piernas que quedaron tras agregar/quitar.

    SEGURO: solo libera piernas que ya eran de ESTA combinada y solo agrega
    piernas que estén LIBRES. Nunca le roba piernas a otra combinada.
    """
    combinada = session.get(CombinadaID, id)
    if combinada is None or not combinada.activo:
        raise HTTPException(status_code=404, detail=f"Combinada #{id} no existe")

    # ids deseados (limpiamos lo que no sea número)
    deseados = {int(x) for x in pierna_ids.split(",") if x.strip().isdigit()}
    actuales = {p.id for p in Piernas_de_combinada_bd(id, session)}

    # QUITAR: las que estaban y ya no se quieren -> quedan libres (combinada_id = None)
    for pid in actuales - deseados:
        p = session.get(PiernaID, pid)
        if p is not None:
            p.combinada_id = None
            session.add(p)

    # AGREGAR: las nuevas, solo si están activas y LIBRES (no le quitamos a otra combinada)
    for pid in deseados - actuales:
        p = session.get(PiernaID, pid)
        if p is not None and p.activo and p.combinada_id is None:
            p.combinada_id = id
            session.add(p)

    session.commit()
    Recalcular_Combinada_bd(id, session)   # recalcula cuota_total y prob_combinada
    return RedirectResponse("/Combinada/Dia/", status_code=302)
