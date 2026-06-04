import os
import requests
from dotenv import load_dotenv
from fastapi import HTTPException

load_dotenv()


def subir_bytes_supabase(contenido: bytes, nombre: str, content_type: str = "image/png") -> str:
    """Sube BYTES a Supabase Storage usando la API REST (sin el SDK) y devuelve la URL publica.
    El bucket debe estar marcado como Public para que la URL se pueda ver.
    Requiere SUPABASE_URL, SUPABASE_KEY (service_role) y SUPABASE_BUCKET en el .env.
    """
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY")
    bucket = os.getenv("SUPABASE_BUCKET")
    if not url or not key or not bucket:
        raise HTTPException(status_code=500, detail="Faltan credenciales de Supabase en el .env")

    endpoint = f"{url}/storage/v1/object/{bucket}/{nombre}"
    headers = {
        "Authorization": f"Bearer {key}",
        "apikey": key,
        "Content-Type": content_type,
        "x-upsert": "true",   # si ya existe un archivo con ese nombre, lo reemplaza
    }
    resp = requests.post(endpoint, headers=headers, data=contenido, timeout=60)
    if resp.status_code not in (200, 201):
        raise HTTPException(status_code=502, detail=f"Error subiendo a Supabase: {resp.text}")

    # URL publica final (requiere bucket Public)
    return f"{url}/storage/v1/object/public/{bucket}/{nombre}"
