from fastapi import APIRouter, Request, Depends
from sqlmodel import Session
from fastapi.responses import HTMLResponse

from app.core.database import get_session
from app.core.templates import templates
from app.services.crud import Mostrar_Combinadas_bd, Piernas_de_combinada_bd

router = APIRouter()


# ===================== COMBINADA DEL DIA (grafica riesgo vs recompensa) =====================

@router.get("/Combinada/Dia/", response_class=HTMLResponse)
async def combinada_del_dia(request: Request, session: Session = Depends(get_session)):
    # Trae TODAS las combinadas activas. La grafica arranca vacia: el usuario
    # arrastra las cartas de abajo hacia la grafica para ir colocando puntos
    # (eje X = probabilidad de ganar, eje Y = cuota total = lo que paga).
    # Por cada combinada mandamos tambien la prob de cada una de sus piernas:
    # la tabla de al lado las multiplica una por una para mostrar como BAJA la
    # probabilidad combinada a medida que se suman piernas.
    combinadas = Mostrar_Combinadas_bd(session)
    datos = []
    for c in combinadas:
        piernas = Piernas_de_combinada_bd(c.id, session)
        piernas_info = [{"partido": p.partido, "prob": p.prob} for p in piernas]
        datos.append({"combinada": c, "piernas_info": piernas_info})
    return templates.TemplateResponse(request, "combinada_dia.html", {"datos": datos})
