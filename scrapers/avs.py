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

# Only take external action links (resolutions in BOCM, tramitación portal)
ALLOWED_HREF_PREFIXES = ("https://www.bocm.es", "https://sede.comunidad.madrid")


def _matches(text: str) -> bool:
    return any(kw in text.lower() for kw in KEYWORDS)


def _context_matches(a_tag) -> bool:
    """Check if the surrounding block text contains VPO keywords."""
    container = a_tag.find_parent(["p", "li", "div", "section", "article"])
    if container:
        return _matches(container.get_text())
    return False


def scrape() -> list:
    try:
        resp = requests.get(URL, headers=HEADERS, timeout=15)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
        results = []
        seen_urls = set()
        for a in soup.find_all("a", href=True):
            href = a["href"]
            if not any(href.startswith(p) for p in ALLOWED_HREF_PREFIXES):
                continue
            if href in seen_urls:
                continue
            link_text = a.get_text(strip=True)
            # use parent block text as title if link text is not informative
            container = a.find_parent(["p", "li", "div"])
            context = container.get_text(" ", strip=True) if container else link_text
            title = context if len(context) > len(link_text) else link_text
            if not title:
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
