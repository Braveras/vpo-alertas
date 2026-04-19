import feedparser
import logging
from datetime import datetime
from models import Listing
from scrapers.keywords import KEYWORDS

logger = logging.getLogger(__name__)

FEED_URL = "https://www.bocm.es/boletin/boletin_hoy.rss"


def _matches(text: str) -> bool:
    text_lower = text.lower()
    return any(kw in text_lower for kw in KEYWORDS)


def scrape() -> list:
    try:
        feed = feedparser.parse(FEED_URL)
        results = []
        for entry in feed.get("entries", []):
            title = entry.get("title", "")
            url = entry.get("link", "")
            if not url or not _matches(title):
                continue
            published = entry.get("published", datetime.today().strftime("%Y-%m-%d"))
            results.append(Listing(
                titulo=title,
                url=url,
                fuente="BOCM",
                fecha=str(published)[:10],
            ))
        return results
    except Exception as e:
        logger.warning(f"BOCM scraper failed: {e}")
        return []
