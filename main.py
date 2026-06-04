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
from utils import subir_bytes_supabase

app = FastAPI(lifespan=create_all_tables)

templates = Jinja2Templates(directory="templates")

#-----------------pagina principal home---------------------
@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse({"request": request}, "base.html")


##--------------------------crear combinada -------------------
@app.post("/Combinada", response_model=CombinadaID)
async def crear_combinada_api(combinada: CombinadaBase, session: SessionDep):
    creada = Crear_Combinada_bd(combinada, session)
    if creada is None:                       # por si la BD no la pudo crear
        raise HTTPException(status_code=400, detail="No se pudo crear la combinada")
    return creada

#---------------------borrar combinada-------------------------

@app.delete("/pokemon/{id}", response_model=CombinadaBase)
async def delete_one_combinada(id: int, session: SessionDep):
    deleted = eliminar_combinada(id, session)#soft delete a combinada y a piernas


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
        request: Request,
        stake: str = Form(""),
        cuota_total: Optional[str] = Form(None),
        prob_combinada: Optional[str] = Form(None),
        estado: PiernaType = Form(None),
        activo: Optional[bool] = Form(None),
        session: Session = Depends(get_session)):

    # Re-muestra el MISMO formulario con un mensaje de error y lo que ya se escribio
    def volver_con_error(msg):
        return templates.TemplateResponse(request, "crear.html", {
            "error": msg,
            "valores": {"stake": stake, "cuota_total": cuota_total, "prob_combinada": prob_combinada},
        })

    # --- validacion manual con mensajes amables (segunda capa, por si saltan el front) ---
    try:
        stake_f = float(stake)
    except ValueError:
        return volver_con_error("El stake debe ser un número (ej. 1.5).")
    if stake_f <= 0:
        return volver_con_error("El stake debe ser mayor a 0.")

    # cuota_total es opcional: si viene vacia la dejamos en None
    cuota_f = None
    if cuota_total:
        try:
            cuota_f = float(cuota_total)
        except ValueError:
            return volver_con_error("La cuota total debe ser un número.")
        if cuota_f < 1:
            return volver_con_error("La cuota total no puede ser menor a 1.")

    # prob_combinada tambien es opcional, y va entre 0 y 1
    prob_f = None
    if prob_combinada:
        try:
            prob_f = float(prob_combinada)
        except ValueError:
            return volver_con_error("La probabilidad debe ser un número.")
        if not (0 <= prob_f <= 1):
            return volver_con_error("La probabilidad debe estar entre 0 y 1.")

    nueva_combinada = CombinadaBase(stake=stake_f, cuota_total=cuota_f, prob_combinada=prob_f, estado=estado, activo=activo)
    catched = Crear_Combinada_bd(nueva_combinada, session)
    if catched is None:                      # si no se pudo crear, avisamos en vez de seguir
        return volver_con_error("No se pudo crear la combinada. Intenta de nuevo.")

    return RedirectResponse("/combinadas/", status_code=302)


@app.get("/Pierna/Crear/", response_class=HTMLResponse)
async def crear_pierna_vista(request: Request, session: Session = Depends(get_session)):
    # Pasamos las combinadas para llenar el <select> del formulario
    combinadas = Mostrar_Combinadas_bd(session)
    return templates.TemplateResponse(request, "crear_pierna.html", {"combinadas_lista": combinadas})


@app.post("/Pierna/Crear/", response_class=HTMLResponse)
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
#-----------------------------------------------------------------------------------------------------------------------------
    # Re-muestra el MISMO formulario con un mensaje de error y lo que ya se escribio
    # Cada vez que renderizas una plantilla, le tienes que dar TODOS los datos
    def volver_con_error(msg):
        combinadas = Mostrar_Combinadas_bd(session)   # el <select> necesita la lista otra vez
        return templates.TemplateResponse(request, "crear_pierna.html", {
            "combinadas_lista": combinadas,
            "error": msg,
            "valores": {"partido": partido, "mercado": mercado, "cuota": cuota, "prob": prob},
        })

    # ------------------------ validacion manual con mensajes amables (segunda capa, por si saltan el front) --------------------------
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
#------------------------------------------------------------------------------------------------------
    # Si el <select> mando "" (libre), guardamos None; si mando un id, lo pasamos a int
    #combinada_id es "3" (string)
    cid = int(combinada_id) if combinada_id else None

    nueva_pierna = PiernaBase(
        combinada_id=cid, partido=partido, mercado=mercado,
        cuota=cuota_f, prob=prob_f, resultado=resultado, activo=activo)

    creada = Crear_Pierna_bd(nueva_pierna, session)
    if creada is None:                       # la combinada seleccionada no existía
        return volver_con_error("La combinada seleccionada no existe.")

    return RedirectResponse("/piernas/", status_code=302)


# ===================== EDITAR COMBINADA =====================

@app.get("/Combinada/{id}/editar", response_class=HTMLResponse)
async def editar_combinada_vista(id: int, request: Request, session: Session = Depends(get_session)):
    # Muestra el formulario YA LLENO con los datos actuales de la combinada
    combinada = Mostrar_Combinada_bd(id, session)
    if combinada is None:
        raise HTTPException(status_code=404, detail="Combinada no existe")
    return templates.TemplateResponse(request, "editar_combinada.html", {"combinada": combinada})


@app.post("/Combinada/{id}/editar", response_class=HTMLResponse)
async def editar_combinada_post(
        id: int,
        request: Request,
        stake: str = Form(""),
        cuota_total: Optional[str] = Form(None),
        prob_combinada: Optional[str] = Form(None),
        estado: CombinadaType = Form(None),
        activo: bool = Form(False),
        session: Session = Depends(get_session)):

    combinada = Mostrar_Combinada_bd(id, session)
    if combinada is None:
        raise HTTPException(status_code=404, detail="Combinada no existe")

    # Re-muestra el formulario de edicion con el error y lo que se escribio
    def volver_con_error(msg):
        return templates.TemplateResponse(request, "editar_combinada.html", {
            "combinada": combinada, "error": msg,
            "valores": {"stake": stake, "cuota_total": cuota_total, "prob_combinada": prob_combinada},
        })

    # --- misma validacion que al crear ---
    try:
        stake_f = float(stake)
    except ValueError:
        return volver_con_error("El stake debe ser un número (ej. 1.5).")
    if stake_f <= 0:
        return volver_con_error("El stake debe ser mayor a 0.")

    cuota_f = None
    if cuota_total:
        try:
            cuota_f = float(cuota_total)
        except ValueError:
            return volver_con_error("La cuota total debe ser un número.")
        if cuota_f < 1:
            return volver_con_error("La cuota total no puede ser menor a 1.")

    prob_f = None
    if prob_combinada:
        try:
            prob_f = float(prob_combinada)
        except ValueError:
            return volver_con_error("La probabilidad debe ser un número.")
        if not (0 <= prob_f <= 1):
            return volver_con_error("La probabilidad debe estar entre 0 y 1.")

    Editar_Combinada_bd(id, stake_f, cuota_f, prob_f, estado, activo, session)
    return RedirectResponse("/combinadas/", status_code=302)


# ===================== EDITAR PIERNA =====================

@app.get("/Pierna/{id}/editar", response_class=HTMLResponse)
async def editar_pierna_vista(id: int, request: Request, session: Session = Depends(get_session)):
    # Muestra el formulario YA LLENO con los datos actuales de la pierna
    pierna = Mostrar_Pierna_bd(id, session)
    if pierna is None:
        raise HTTPException(status_code=404, detail="Pierna no existe")
    # Pasamos las combinadas para llenar el <select> de "a cuál pertenece"
    combinadas = Mostrar_Combinadas_bd(session)
    return templates.TemplateResponse(request, "editar_pierna.html",
        {"pierna": pierna, "combinadas_lista": combinadas})


@app.post("/Pierna/{id}/editar", response_class=HTMLResponse)
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


# ===================== COMBINADA DEL DIA (grafica riesgo vs recompensa) =====================

@app.get("/Combinada/Dia/", response_class=HTMLResponse)
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


# ===================== COMBINADA COMPLETA (armar arrastrando) =====================

@app.get("/Combinada/Completa/", response_class=HTMLResponse)
async def combinada_completa_inicio(request: Request):
    # Pagina con el boton "Crear combinada"
    return templates.TemplateResponse(request, "combinada_completa_inicio.html")


@app.post("/Combinada/Completa/", response_class=HTMLResponse)
async def combinada_completa_crear(session: Session = Depends(get_session)):
    # Crea la combinada VACIA y lleva al armador de esa combinada
    nueva = Crear_Combinada_vacia_bd(session)
    if nueva is None:                        # si no se pudo crear la vacia, no podemos seguir al armador
        raise HTTPException(status_code=400, detail="No se pudo crear la combinada")
    return RedirectResponse(f"/Combinada/Completa/{nueva.id}", status_code=302)# se manda nueva id, porque hay valores sin nada pero id es autoincremental


@app.get("/Combinada/Completa/{combinada_id}", response_class=HTMLResponse)
async def combinada_completa_builder(combinada_id: int, request: Request, session: Session = Depends(get_session)):
    combinada = Mostrar_Combinada_bd(combinada_id, session)
    if combinada is None:
        raise HTTPException(status_code=404, detail="Combinada no existe")
    asignadas = Piernas_de_combinada_bd(combinada_id, session)  # ya estan dentro
    libres = Piernas_libres_bd(session)                         # el pool de la derecha
    return templates.TemplateResponse(request, "combinada_completa.html",
        {"combinada": combinada, "asignadas": asignadas, "libres": libres})


#hasta aca se podria decir que es todo lo base, de aca en adelante es la parte de la afiliacion de soltar

@app.post("/api/combinada/{combinada_id}/agregar/{pierna_id}")
async def api_agregar_pierna(combinada_id: int, pierna_id: int, session: Session = Depends(get_session)):
    # Lo llama el JavaScript al soltar una pierna. Asigna y devuelve los totales nuevos.
    combinada = Asignar_Pierna_bd(pierna_id, combinada_id, session)
    if combinada is None:
        raise HTTPException(status_code=404, detail="Pierna o combinada no existe")
    return {"cuota_total": combinada.cuota_total, "prob_combinada": combinada.prob_combinada}


# ===================== MULTIMEDIA: subir imagen de la combinada =====================

@app.post("/Combinada/{id}/subir-imagen", response_class=HTMLResponse)
async def subir_imagen_combinada(id: int, imagen: UploadFile = File(...), session: Session = Depends(get_session)):
    # 1. Buscamos la combinada
    combinada = Mostrar_Combinada_bd(id, session)
    if combinada is None:
        raise HTTPException(status_code=404, detail="Combinada no existe")

    # 2. Validamos que el archivo subido sea realmente una imagen
    if not imagen.content_type or not imagen.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="El archivo debe ser una imagen")

    # 3. Leemos los bytes y los subimos a Supabase
    contenido = await imagen.read()
    extension = imagen.filename.rsplit(".", 1)[-1] if "." in imagen.filename else "png"
    nombre = f"combinada_{id}.{extension}"
    url_publica = subir_bytes_supabase(contenido, nombre, imagen.content_type)

    # 4. Guardamos la URL en la combinada
    combinada.imagen_url = url_publica
    session.add(combinada)
    session.commit()
    return RedirectResponse("/combinadas/", status_code=302)


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
