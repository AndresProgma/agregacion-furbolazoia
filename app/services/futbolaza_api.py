"""Cliente HTTP de futbolaza (servicio APARTE: https://futbolazoia.live).

Combinadas NO comparte código ni base de datos con futbolaza: solo le pide datos
por su API REST. Aquí traemos las "apuestas recomendadas" (los `valores` que
futbolaza calcula con su modelo) para autocompletar las piernas:
    partido  <- "Equipo1 vs Equipo2"
    mercado  <- valor.nombre        (ej. "1X2 Brasil", "Corners U")
    prob     <- valor.porcentaje/100 (ej. 65 -> 0.65)
La cuota NO la da el modelo (es de la casa de apuestas), se sigue poniendo a mano.
"""
import os
import requests

# URL del servicio de futbolaza. Configurable por env var por si cambia el dominio.
FUTBOLAZA_URL = os.getenv("FUTBOLAZA_URL", "https://futbolazoia.live").rstrip("/")

# El plan free de Render duerme el servicio: el primer request puede tardar.
_TIMEOUT = 25


def _valores_de_partido(p: dict) -> list[dict]:
    """Convierte un partido de futbolaza en filas listas para una pierna."""
    e1 = (p.get("equipo1") or "").strip()
    e2 = (p.get("equipo2") or "").strip()
    if not e1 or not e2:
        return []
    partido = f"{e1} vs {e2}"
    filas = []
    for v in (p.get("valores") or []):
        nombre = (v.get("nombre") or "").strip()
        if not nombre:
            continue
        try:
            prob = round(float(v.get("porcentaje", 0)) / 100, 2)
        except (TypeError, ValueError):
            prob = 0.0
        filas.append({
            "partido": partido,
            "mercado": nombre,
            "prob": prob,
            "descripcion": (v.get("descripcion") or "").strip(),
        })
    return filas


def recomendadas() -> list[dict]:
    """Trae las apuestas recomendadas de futbolaza (partidos de hoy + pick del día).

    Devuelve una lista de {partido, mercado, prob, descripcion}. Si futbolaza está
    caído o dormido, devuelve [] y el formulario sigue funcionando a mano.
    """
    filas: list[dict] = []
    # 1) Partidos de hoy (lista curada por el admin, cada uno con sus valores)
    try:
        r = requests.get(f"{FUTBOLAZA_URL}/api/partidos-hoy", timeout=_TIMEOUT)
        r.raise_for_status()
        for p in (r.json() or []):
            filas.extend(_valores_de_partido(p))
    except requests.RequestException:
        pass
    # 2) Pick del día (un solo partido destacado), por si no está en la lista
    try:
        r = requests.get(f"{FUTBOLAZA_URL}/api/featured-pick", timeout=_TIMEOUT)
        r.raise_for_status()
        pick = r.json() or {}
        if pick:
            filas.extend(_valores_de_partido(pick))
    except requests.RequestException:
        pass

    # Quitamos duplicados (mismo partido + mercado) conservando el primero
    vistos = set()
    unicas = []
    for f in filas:
        clave = (f["partido"], f["mercado"])
        if clave not in vistos:
            vistos.add(clave)
            unicas.append(f)
    return unicas
