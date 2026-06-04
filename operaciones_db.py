from sqlmodel import Session, select
from Modelos import *
from sqlalchemy.exc import NoResultFound

def Crear_Combinada_bd(personaje: CombinadaBase,session: Session ):
    new = CombinadaID.model_validate(personaje)
    session.add(new)
    session.commit()
    session.refresh(new)
    return new


def Mostrar_Combinada_bd(id:int,session:Session):
    try:
        return session.get_one(CombinadaID,id)
    except NoResultFound:
        return None

def Mostrar_Combinadas_bd(session:Session):
    # activo == True para que las combinadas "eliminadas" (soft delete) no aparezcan
    return session.exec(select(CombinadaID).where(CombinadaID.activo == True))

def Crear_Pierna_bd(pierna:PiernaBase,session:Session):
    # Si la pierna trae combinada, verificamos que esa combinada exista.
    # Si combinada_id es None, es una pierna "libre" (va al pool) -> no validamos nada.
    if pierna.combinada_id is not None:
        combinada = session.get(CombinadaID, pierna.combinada_id)
        if combinada is None:
            return None  # la combinada no existe -> el endpoint decide el error 404

    new = PiernaID.model_validate(pierna)
    session.add(new)
    session.commit()
    session.refresh(new)
    return new



def Mostrar_Pierna_bd(id:int,session:Session):
    try:
        return session.get_one(PiernaID,id)
    except NoResultFound:
        return None

def Mostrar_Piernas_bd(session:Session):
    # activo == True para que las piernas "eliminadas" (soft delete) no aparezcan
    return session.exec(select(PiernaID).where(PiernaID.activo == True))



#-------------buscar por id-------------------
async def encontrar_combinada_id(id: int, session: Session):
    try:
        return session.get_one(CombinadaID, id)
    except NoResultFound:
        return None
    

    
def eliminar_combinada(id: int, session: Session):
    """Soft delete de la combinada Y de todas sus piernas (la 'elimina completa').
    Marca activo=False en vez de borrar; nada se pierde de la base.
    """
    try:
        combinada = session.get_one(CombinadaID, id)
        combinada.activo = False          # apagamos la combinada
        session.add(combinada)

        # EN CASCADA: apagamos tambien todas las piernas de esa combinada
        piernas = session.exec(select(PiernaID).where(PiernaID.combinada_id == id)).all()
        for p in piernas:
            p.activo = False
            session.add(p)

        session.commit()
        return combinada
    except NoResultFound:
        return None


def eliminar_pierna(id: int, session: Session):
    """'Eliminar' = borrado LOGICO (soft delete): marca activo=False en vez de borrar la fila.
    Asi el dato no se pierde y se podria recuperar. Las consultas ignoran las inactivas.
    """
    try:
        pierna = session.get_one(PiernaID, id)
        pierna.activo = False        # NO la borramos: solo la "apagamos"
        session.add(pierna)
        session.commit()
        # Recalculamos la combinada: esta pierna ya no cuenta (quedo inactiva)
        if pierna.combinada_id is not None:
            Recalcular_Combinada_bd(pierna.combinada_id, session)
        return pierna
    except NoResultFound:
        return None


# ---------- EDITAR (UPDATE del CRUD) ----------

def Editar_Combinada_bd(id, stake, cuota_total, prob_combinada, estado, activo, session: Session):
    """Actualiza los campos de una combinada. Devuelve None si no existe."""
    try:
        combinada = session.get_one(CombinadaID, id)
    except NoResultFound:
        return None
    combinada.stake = stake
    combinada.cuota_total = cuota_total
    combinada.prob_combinada = prob_combinada
    combinada.estado = estado
    combinada.activo = activo
    session.add(combinada)
    session.commit()
    session.refresh(combinada)
    return combinada


def Editar_Pierna_bd(id, partido, mercado, cuota, prob, resultado, combinada_id, session: Session):
    """Actualiza los campos de una pierna, INCLUIDA la combinada a la que pertenece.
    Devuelve None si la pierna no existe.

    'combinada_id' nuevo puede ser:
      - un id  -> la pierna pasa a esa combinada
      - None    -> la pierna queda "libre" (vuelve al pool)

    Como la pierna puede MOVERSE de una combinada a otra, recalculamos los totales
    de AMBAS: la combinada de la que sale (ya no la cuenta) y a la que entra.
    """
    try:
        pierna = session.get_one(PiernaID, id)
    except NoResultFound:
        return None

    combinada_vieja = pierna.combinada_id   # de donde venia (puede ser None)

    pierna.partido = partido
    pierna.mercado = mercado
    pierna.cuota = cuota
    pierna.prob = prob
    pierna.resultado = resultado
    pierna.combinada_id = combinada_id      # la mudamos (o la dejamos libre con None)
    session.add(pierna)
    session.commit()
    session.refresh(pierna)

    # Recalculamos las combinadas afectadas (sin repetir si es la misma)
    afectadas = {combinada_vieja, combinada_id}   # un set evita recalcular dos veces
    for cid in afectadas:
        if cid is not None:
            Recalcular_Combinada_bd(cid, session)
    return pierna


# ---------- COMBINADA COMPLETA (armar arrastrando piernas) ----------

def Crear_Combinada_vacia_bd(session:Session):
    """Crea una combinada SIN datos: estado pendiente, activa, sin cuota/prob todavia."""
    nueva = CombinadaID(estado=CombinadaType.PENDIENTE, activo=True)
    session.add(nueva)
    session.commit()
    session.refresh(nueva)
    return nueva

def Piernas_libres_bd(session:Session):
    """Piernas ACTIVAS que todavia NO pertenecen a ninguna combinada (el 'pool' de la derecha)."""
    # activo == True para que las "eliminadas" (soft delete) no aparezcan en el pool
    return session.exec(
        select(PiernaID).where(PiernaID.combinada_id == None, PiernaID.activo == True)
    ).all()

def Piernas_de_combinada_bd(combinada_id:int, session:Session):
    """Piernas ACTIVAS que YA pertenecen a esta combinada (las inactivas no cuentan ni se muestran)."""
    return session.exec(
        select(PiernaID).where(PiernaID.combinada_id == combinada_id, PiernaID.activo == True)
    ).all()

def Recalcular_Combinada_bd(combinada_id:int, session:Session):
    """Recalcula cuota_total (Π cuotas) y prob_combinada (Π probs) de la combinada.

    'Π' (pi) significa MULTIPLICAR todas. Ej: cuotas 1.85, 2.0 -> 1.85*2.0 = 3.70
    """
    combinada = session.get(CombinadaID, combinada_id)
    if combinada is None:
        return None

    piernas = Piernas_de_combinada_bd(combinada_id, session)  # todas las piernas de esta combinada
    if piernas:
        # Arrancamos en 1.0 porque vamos a MULTIPLICAR (1 es el "neutro" del producto:
        # cualquier numero por 1 sigue igual). Si arrancaramos en 0, todo daria 0.
        cuota = 1.0
        prob = 1.0
        for p in piernas:          # recorremos pierna por pierna
            cuota *= p.cuota       # cuota = cuota * p.cuota  (acumula el producto)
            prob *= p.prob         # prob  = prob  * p.prob
        combinada.cuota_total = cuota
        combinada.prob_combinada = prob
    else:
        # Si la combinada se quedo sin piernas, no hay totales que mostrar.
        combinada.cuota_total = None
        combinada.prob_combinada = None

    session.add(combinada)      # marcamos los cambios
    session.commit()            # los guardamos en la base
    session.refresh(combinada)  # traemos la version actualizada
    return combinada

def Asignar_Pierna_bd(pierna_id:int, combinada_id:int, session:Session):
    """Mete una pierna libre dentro de una combinada y recalcula los totales.

    Es lo que pasa "por detras" cada vez que sueltas una pierna en el armador.
    """
    # Buscamos las dos cosas en la base de datos.
    pierna = session.get(PiernaID, pierna_id)
    combinada = session.get(CombinadaID, combinada_id)
    if pierna is None or combinada is None:
        return None  # alguna no existe -> el endpoint responde 404

    # El cambio clave: apuntamos la pierna a esta combinada (deja de estar "libre").
    pierna.combinada_id = combinada_id
    session.add(pierna)
    session.commit()

    # Como ya hay una pierna mas, recalculamos cuota_total y prob_combinada.
    return Recalcular_Combinada_bd(combinada_id, session)


