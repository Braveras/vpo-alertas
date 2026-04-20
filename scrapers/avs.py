import requests
import logging
from bs4 import BeautifulSoup
from datetime import datetime
from models import Listing

logger = logging.getLogger(__name__)

BASE_URL = "https://www.comunidad.madrid"
URL = f"{BASE_URL}/servicios/vivienda/adjudicacion-viviendas-agencia-vivienda-social-sorteo"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept-Language": "es-ES,es;q=0.9",
}

# Only BOCM article PDFs (not bocm.es root or other pages)
BOCM_ARTICLE_PREFIX = "https://www.bocm.es/boletin/CM_Orden_BOCM/"

# Skip status updates and button links — not new convocatorias
SKIP_KEYWORDS = [
    "relación provisional", "admitidos y excluidos", "lista provisional",
    "admitidos", "excluidos", "accede a", "tramitación",
]


def _is_skippable(text: str) -> bool:
    t = text.lower()
    return any(kw in t for kw in SKIP_KEYWORDS)


def scrape() -> list:
    try:
        resp = requests.get(URL, headers=HEADERS, timeout=15)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
        results = []
        seen_urls = set()
        for a in soup.find_all("a", href=True):
            href = a["href"]
            if not href.startswith(BOCM_ARTICLE_PREFIX):
                continue
            if href in seen_urls:
                continue
            # Build title from link text + nearest heading context
            link_text = a.get_text(strip=True)
            heading = a.find_previous(["h2", "h3", "h4"])
            heading_text = heading.get_text(strip=True) if heading else ""
            title = f"{heading_text} — {link_text}" if heading_text else link_text
            # Check parent block context for skip keywords (e.g. provisional list)
            container = a.find_parent(["p", "li", "div"])
            context_text = container.get_text() if container else ""
            if not title or _is_skippable(title) or _is_skippable(context_text):
                continue
            seen_urls.add(href)
            results.append(Listing(
                titulo=title,
                url=href,
                fuente="AVS",
                fecha=datetime.today().strftime("%Y-%m-%d"),
            ))
        return results
    except Exception as e:
        logger.warning(f"AVS scraper failed: {e}")
        return []
