import feedparser
import requests
import logging
from bs4 import BeautifulSoup
from datetime import datetime
from models import Listing
from scrapers.keywords import KEYWORDS

logger = logging.getLogger(__name__)

FEED_URL = "https://www.bocm.es/sumarios.rss"
BASE_URL = "https://www.bocm.es"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept-Language": "es-ES,es;q=0.9",
}


def _matches(text: str) -> bool:
    return any(kw in text.lower() for kw in KEYWORDS)


def _scrape_bulletin(bulletin_url: str, date: str) -> list:
    resp = requests.get(bulletin_url, headers=HEADERS, timeout=15)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")
    results = []
    for heading in soup.find_all(["h3", "h4"]):
        title = heading.get_text(strip=True)
        if not title or not _matches(title):
            continue
        a = heading.find("a", href=True) or heading.find_next("a", href=True)
        href = a["href"] if a else bulletin_url
        url = href if href.startswith("http") else BASE_URL + href
        results.append(Listing(titulo=title, url=url, fuente="BOCM", fecha=date))
    return results


def scrape() -> list:
    try:
        feed = feedparser.parse(FEED_URL)
        entries = feed.get("entries", [])
        if not entries:
            return []
        entry = entries[0]
        bulletin_url = entry.get("link", "")
        published = entry.get("published", datetime.today().strftime("%Y-%m-%d"))
        date = str(published)[:10]
        if not bulletin_url:
            return []
        return _scrape_bulletin(bulletin_url, date)
    except Exception as e:
        logger.warning(f"BOCM scraper failed: {e}")
        return []
