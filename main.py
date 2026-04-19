import os
import logging
from pathlib import Path
from scrapers import bocm, avs, emvs, idealista, fotocasa
from storage import load_seen, save_seen, filter_new
from notifier import send_listing, send_warning

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger(__name__)


def run(seen_file: Path = Path(__file__).parent / "seen.json") -> None:
    phone = os.environ["CALLMEBOT_PHONE"]
    apikey = os.environ["CALLMEBOT_APIKEY"]

    all_listings = []
    for scraper in [bocm, avs, emvs, idealista, fotocasa]:
        results = scraper.scrape()
        logger.info(f"{scraper.__name__}: {len(results)} listings found")
        all_listings.extend(results)

    if not all_listings:
        logger.error("All scrapers returned empty — possible failures")
        send_warning("⚠️ Error scrapers VPO Madrid — revisar logs GitHub Actions", phone=phone, apikey=apikey)
        return

    seen = load_seen(seen_file)
    new_listings = filter_new(all_listings, seen)
    logger.info(f"New listings: {len(new_listings)}")

    for listing in new_listings:
        send_listing(listing, phone=phone, apikey=apikey)
        seen.add(listing.id)

    save_seen(seen, seen_file)


if __name__ == "__main__":
    run()
