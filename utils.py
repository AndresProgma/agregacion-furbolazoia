import os
import base64
import requests
from dotenv import load_dotenv
from pathlib import Path
import shutil
from fastapi import File, UploadFile, HTTPException

load_dotenv()

IMG_DIR = Path("files/img")
SUPABASE_BUCKET=os.getenv("SUPABASE_BUCKET")

# API de generacion de imagenes de Google (Gemini / Google AI Studio)
GEMINI_MODEL = "gemini-2.0-flash-preview-image-generation"
GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/models"


def generar_imagen_ia(prompt: str) -> bytes:
    """Genera una imagen con la API de Gemini (Google AI Studio) y devuelve los BYTES.
    Necesita GEMINI_API_KEY en el .env. El prompt es el texto que describe la imagen.
    """
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="Falta GEMINI_API_KEY en el .env")

    endpoint = f"{GEMINI_URL}/{GEMINI_MODEL}:generateContent?key={api_key}"
    body = {
        "contents": [{"parts": [{"text": prompt}]}],
        # le pedimos explicitamente que la respuesta incluya una IMAGEN
        "generationConfig": {"responseModalities": ["TEXT", "IMAGE"]},
    }
    resp = requests.post(endpoint, json=body, timeout=120)
    if resp.status_code != 200:
        raise HTTPException(status_code=502, detail=f"Error generando imagen con Gemini: {resp.text}")

    data = resp.json()
    # La imagen viene en base64 dentro de una "parte" de la respuesta (inlineData)
    try:
        partes = data["candidates"][0]["content"]["parts"]
    except (KeyError, IndexError):
        raise HTTPException(status_code=502, detail="Gemini no devolvió imagen")
    for parte in partes:
        inline = parte.get("inlineData") or parte.get("inline_data")
        if inline and inline.get("data"):
            return base64.b64decode(inline["data"])   # base64 -> bytes
    raise HTTPException(status_code=502, detail="Gemini no devolvió imagen en la respuesta")


def subir_bytes_supabase(contenido: bytes, nombre: str, content_type: str = "image/png") -> str:
    """Sube BYTES a Supabase Storage usando la API REST (sin el SDK) y devuelve la URL publica.
    El bucket debe estar marcado como Public para que la URL se pueda ver.
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


def save_img_local(file:UploadFile):
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Archivo Invalido")

    IMG_DIR.mkdir(parents=True, exist_ok=True)
    dest = IMG_DIR/file.filename

    with dest.open("wb") as store:
        shutil.copyfileobj(file.file, store)

    return dest

## SUPABASE
def supabase_client():
    from supabase import create_client
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY")

    if not url or not key:
        raise RuntimeError("No credentials")
    return create_client(url, key)

def save_img_remote(file:UploadFile):
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Archivo Invalido")

    contents = file.file.read()
    path = file.filename

    supa_client = supabase_client()

    response = supa_client.storage.from_(SUPABASE_BUCKET).upload(
        path=path,
        file=contents,
        file_options={"content-type":file.content_type},
    )
    stored_url_bucket=(supa_client.
                       storage.
                       from_(SUPABASE_BUCKET).
                       get_public_url(path))

    return stored_url_bucket






