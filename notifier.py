import requests
import logging
import time
from urllib.parse import quote
from models import Listing

logger = logging.getLogger(__name__)

CALLMEBOT_URL = "https://api.callmebot.com/whatsapp.php"


def _format_message(listing: Listing) -> str:
    return (
        f"🏠 NUEVA VPO/VPP MADRID\n"
        f"Fuente: {listing.fuente}\n"
        f"Titulo: {listing.titulo}\n"
        f"URL: {listing.url}"
    )


def _call_api(message: str, phone: str, apikey: str, retries: int = 2) -> bool:
    encoded = quote(message)
    url = f"{CALLMEBOT_URL}?phone={phone}&text={encoded}&apikey={apikey}"
    for attempt in range(retries):
        try:
            resp = requests.get(url, timeout=10)
            if resp.status_code == 200:
                return True
            logger.warning(f"CallMeBot returned {resp.status_code}, attempt {attempt + 1}")
            if attempt < retries - 1:
                time.sleep(2)
        except Exception as e:
            logger.warning(f"CallMeBot request failed: {e}, attempt {attempt + 1}")
            if attempt < retries - 1:
                time.sleep(2)
    return False


def send_listing(listing: Listing, phone: str, apikey: str) -> bool:
    message = _format_message(listing)
    return _call_api(message, phone, apikey)


def send_warning(message: str, phone: str, apikey: str) -> bool:
    return _call_api(message, phone, apikey)
