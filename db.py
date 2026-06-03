import os

from sqlmodel import Session, create_engine, SQLModel
from typing import Annotated
from fastapi import Depends, FastAPI
from dotenv import load_dotenv

load_dotenv()

neon_url_db = os.getenv("url_basededatos")


# pool_pre_ping: antes de usar una conexion, comprueba que siga viva (si Neon la cerro,
#                la reemplaza por una nueva). Evita el error "SSL connection closed".
# pool_recycle: recicla conexiones que lleven mas de 5 min (300 s) para que no se queden viejas.
engine = create_engine(neon_url_db, pool_pre_ping=True, pool_recycle=300)

def create_all_tables(app: FastAPI):
    SQLModel.metadata.create_all(engine)
    yield


def get_session():
    with Session(engine) as session:
        yield session

SessionDep = Annotated[Session, Depends(get_session)]