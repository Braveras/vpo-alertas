import requests
import logging
from bs4 import BeautifulSoup
from datetime import datetime
from models import Listing
from scrapers.keywords import KEYWORDS

logger = logging.getLogger(__name__)

BASE_URL = "https://www.fotocasa.es"
URLS = [
    f"{BASE_URL}/es/comprar/viviendas/madrid-provincia/vpo/l",
    f"{BASE_URL}/es/alquiler/viviendas/madrid-provincia/alquiler-con-opcion-a-compra/l",
]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept-Language": "es-ES,es;q=0.9",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Referer": "https://www.fotocasa.es/",
}


def _matches(text: str) -> bool:
    text_lower = text.lower()
    return any(kw in text_lower for kw in KEYWORDS)


def _parse_listings(html: str) -> list:
    soup = BeautifulSoup(html, "html.parser")
    results = []
    seen_urls = set()
    for article in soup.find_all("article"):
        a = article.find("a", href=True)
        if not a:
            continue
        href = a.get("href", "")
        url = href if href.startswith("http") else BASE_URL + href
        title = a.get_text(strip=True)
        if not title or url in seen_urls:
            continue
        if not _matches(title):
            continue
        seen_urls.add(url)
        results.append(Listing(
            titulo=title,
            url=url,
            fuente="Fotocasa",
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
        logger.warning(f"Fotocasa scraper failed: {e}")
        return []
