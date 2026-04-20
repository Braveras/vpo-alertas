import requests
import logging
from bs4 import BeautifulSoup
from datetime import datetime
from models import Listing
from scrapers.keywords import KEYWORDS

logger = logging.getLogger(__name__)

BASE_URL = "https://www.comunidad.madrid"
URL = f"{BASE_URL}/servicios/vivienda/adjudicacion-viviendas-agencia-vivienda-social-sorteo"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept-Language": "es-ES,es;q=0.9",
}


def _matches(text: str) -> bool:
    return any(kw in text.lower() for kw in KEYWORDS)


def scrape() -> list:
    try:
        resp = requests.get(URL, headers=HEADERS, timeout=15)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
        results = []
        seen_urls = set()
        for a in soup.find_all("a", href=True):
            title = a.get_text(strip=True)
            if not title or not _matches(title):
                continue
            href = a["href"]
            url = href if href.startswith("http") else BASE_URL + href
            if url in seen_urls:
                continue
            seen_urls.add(url)
            results.append(Listing(
                titulo=title,
                url=url,
                fuente="AVS",
                fecha=datetime.today().strftime("%Y-%m-%d"),
            ))
        return results
    except Exception as e:
        logger.warning(f"AVS scraper failed: {e}")
        return []
