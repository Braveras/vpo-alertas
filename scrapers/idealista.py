import requests
import logging
from bs4 import BeautifulSoup
from datetime import datetime
from models import Listing

logger = logging.getLogger(__name__)

BASE_URL = "https://www.idealista.com"
URLS = [
    f"{BASE_URL}/venta-viviendas/madrid-provincia/vpo/?ordenado-por=fecha-publicacion-desc",
    f"{BASE_URL}/alquiler-viviendas/madrid-provincia/con-opcion-a-compra/?ordenado-por=fecha-publicacion-desc",
]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept-Language": "es-ES,es;q=0.9",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Referer": "https://www.idealista.com/",
}


def _parse_listings(html: str) -> list:
    soup = BeautifulSoup(html, "html.parser")
    results = []
    for article in soup.find_all("article", class_="item"):
        a = article.find("a", class_="item-link")
        if not a:
            continue
        href = a.get("href", "")
        url = href if href.startswith("http") else BASE_URL + href
        title_tag = a.find("span", class_="item-title") or a
        title = title_tag.get_text(strip=True)
        if not title:
            continue
        results.append(Listing(
            titulo=title,
            url=url,
            fuente="Idealista",
            fecha=datetime.today().strftime("%Y-%m-%d"),
        ))
    return results


def scrape() -> list:
    all_results = []
    seen_urls = set()
    try:
        for url in URLS:
            resp = requests.get(url, headers=HEADERS, timeout=15)
            resp.raise_for_status()
            for listing in _parse_listings(resp.text):
                if listing.url not in seen_urls:
                    seen_urls.add(listing.url)
                    all_results.append(listing)
        return all_results
    except Exception as e:
        logger.warning(f"Idealista scraper failed: {e}")
        return []
