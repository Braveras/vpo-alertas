import requests
import logging
from bs4 import BeautifulSoup
from datetime import datetime
from models import Listing

logger = logging.getLogger(__name__)

BASE_URL = "https://www.agenciavivienda.comunidad.madrid"
URL = f"{BASE_URL}/convocatorias-y-actuaciones"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept-Language": "es-ES,es;q=0.9",
}

KEYWORDS = [
    "vpo", "vpp", "vppl",
    "vivienda protección oficial",
    "vivienda precio tasado",
    "vivienda protección pública",
    "vivienda protegida",
    "alquiler con opción a compra",
    "alquiler opción compra",
    "protección oficial",
]


def _matches(text: str) -> bool:
    text_lower = text.lower()
    return any(kw in text_lower for kw in KEYWORDS)


def scrape() -> list:
    try:
        resp = requests.get(URL, headers=HEADERS, timeout=15)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
        results = []
        for a in soup.find_all("a", href=True):
            title = a.get_text(strip=True)
            if not title or not _matches(title):
                continue
            href = a["href"]
            url = href if href.startswith("http") else BASE_URL + href
            parent = a.find_parent()
            fecha_tag = parent.find("span", class_="fecha") if parent else None
            fecha = fecha_tag.get_text(strip=True) if fecha_tag else datetime.today().strftime("%Y-%m-%d")
            results.append(Listing(titulo=title, url=url, fuente="AVS", fecha=fecha))
        return results
    except Exception as e:
        logger.warning(f"AVS scraper failed: {e}")
        return []
