from sqlmodel import Session, select
from Modelos import *
from sqlalchemy.exc import NoResultFound

def Crear_Personaje(personaje: PersonajeBase,session: Session ):
    new = PersonajeID.model_validate(personaje)
    session.add(new)
    session.commit()
    session.refresh(new)
    return new

def encontrar_personaje(personaje_id: int, session:Session):
    try:
        return session.get_one(PersonajeID,personaje_id)

    except NoResultFound:
        return None 
    
def mostrar_personajes(session:Session):
    return session.exec(select(PersonajeID))



def actualizar_personaje(personaje_id:int,nuevo_personaje: PersonajeUpdate, session:Session):
    personaje = encontrar_personaje(personaje_id,session)
    if personaje is None:
        return None
    personaje_nuevo = nuevo_personaje.model_dump(exclude_unset=True)


    personaje.sqlmodel_update(personaje_nuevo)
    session.add(personaje)
    session.commit()
    session.refresh(personaje)
    return personaje






def Crear_Prediccion(prediccion: PrediccionBase,session: Session):
    new = PrediccionID.model_validate(prediccion)
    session.add(new)
    session.commit()
    session.refresh(new)
    return new


