# VPO Alertas Madrid — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Daily scraper that monitors 5 sources for new VPO/VPP/alquiler-opción-compra listings in Madrid and sends WhatsApp notifications via CallMeBot.

**Architecture:** GitHub Actions cron (daily 08:00 Madrid) runs `main.py`, which calls all scrapers, compares results against `seen.json` persisted in the repo, and sends WhatsApp via CallMeBot for any new listings. State is committed back to the repo automatically.

**Tech Stack:** Python 3.11, requests, beautifulsoup4, feedparser, pytest, GitHub Actions

---

## File Map

| File | Responsibility |
|------|---------------|
| `models.py` | `Listing` dataclass |
| `storage.py` | Load/save `seen.json`, filter new listings |
| `scrapers/bocm.py` | BOCM RSS scraper |
| `scrapers/avs.py` | AVS Madrid HTML scraper |
| `scrapers/emvs.py` | EMVS HTML scraper |
| `scrapers/idealista.py` | Idealista HTML scraper (VPO + alquiler opción) |
| `scrapers/fotocasa.py` | Fotocasa HTML scraper (VPO + alquiler opción) |
| `notifier.py` | CallMeBot WhatsApp sender |
| `main.py` | Orchestrator |
| `seen.json` | Persisted set of seen listing IDs |
| `.github/workflows/check.yml` | Cron job |
| `requirements.txt` | Dependencies |
| `tests/` | One test file per module |

---

### Task 1: Project skeleton

**Files:**
- Create: `requirements.txt`
- Create: `seen.json`
- Create: `scrapers/__init__.py`
- Create: `tests/__init__.py`

- [ ] **Step 1: Create requirements.txt**

```
requests==2.31.0
beautifulsoup4==4.12.3
feedparser==6.0.11
pytest==8.1.1
pytest-mock==3.14.0
```

- [ ] **Step 2: Create seen.json**

```json
[]
```

- [ ] **Step 3: Create empty init files**

```bash
mkdir -p scrapers tests
touch scrapers/__init__.py tests/__init__.py
```

- [ ] **Step 4: Install dependencies**

```bash
pip install -r requirements.txt
```

Expected: all packages install without error.

- [ ] **Step 5: Commit**

```bash
git init
git add requirements.txt seen.json scrapers/__init__.py tests/__init__.py
git commit -m "chore: project skeleton"
```

---

### Task 2: Listing model and storage

**Files:**
- Create: `models.py`
- Create: `storage.py`
- Create: `tests/test_storage.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/test_storage.py
import json
import pytest
from pathlib import Path
from models import Listing
from storage import load_seen, save_seen, filter_new


def test_listing_id_is_sha1_of_url():
    listing = Listing(titulo="Test", url="https://example.com/1", fuente="TEST", fecha="2026-04-19")
    import hashlib
    expected = hashlib.sha1("https://example.com/1".encode()).hexdigest()
    assert listing.id == expected


def test_listing_to_dict():
    listing = Listing(titulo="Test", url="https://example.com/1", fuente="TEST", fecha="2026-04-19")
    d = listing.to_dict()
    assert d["titulo"] == "Test"
    assert d["url"] == "https://example.com/1"
    assert d["fuente"] == "TEST"
    assert d["fecha"] == "2026-04-19"
    assert "id" in d


def test_load_seen_returns_empty_set_for_empty_file(tmp_path):
    seen_file = tmp_path / "seen.json"
    seen_file.write_text("[]")
    result = load_seen(seen_file)
    assert result == set()


def test_load_seen_returns_ids(tmp_path):
    seen_file = tmp_path / "seen.json"
    seen_file.write_text('["abc123", "def456"]')
    result = load_seen(seen_file)
    assert result == {"abc123", "def456"}


def test_save_seen_writes_sorted_list(tmp_path):
    seen_file = tmp_path / "seen.json"
    save_seen({"zzz", "aaa", "mmm"}, seen_file)
    data = json.loads(seen_file.read_text())
    assert data == ["aaa", "mmm", "zzz"]


def test_filter_new_returns_only_new_listings():
    listings = [
        Listing(titulo="A", url="https://example.com/1", fuente="X", fecha="2026-04-19"),
        Listing(titulo="B", url="https://example.com/2", fuente="X", fecha="2026-04-19"),
    ]
    import hashlib
    existing_id = hashlib.sha1("https://example.com/1".encode()).hexdigest()
    seen = {existing_id}
    result = filter_new(listings, seen)
    assert len(result) == 1
    assert result[0].url == "https://example.com/2"
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/test_storage.py -v
```

Expected: `ImportError` or `ModuleNotFoundError` — models/storage don't exist yet.

- [ ] **Step 3: Create models.py**

```python
import hashlib
from dataclasses import dataclass


@dataclass
class Listing:
    titulo: str
    url: str
    fuente: str
    fecha: str

    @property
    def id(self) -> str:
        return hashlib.sha1(self.url.encode()).hexdigest()

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "titulo": self.titulo,
            "url": self.url,
            "fuente": self.fuente,
            "fecha": self.fecha,
        }
```

- [ ] **Step 4: Create storage.py**

```python
import json
from pathlib import Path
from typing import Set, List
from models import Listing

DEFAULT_SEEN_FILE = Path(__file__).parent / "seen.json"


def load_seen(path: Path = DEFAULT_SEEN_FILE) -> Set[str]:
    if not path.exists():
        return set()
    with open(path) as f:
        return set(json.load(f))


def save_seen(seen: Set[str], path: Path = DEFAULT_SEEN_FILE) -> None:
    with open(path, "w") as f:
        json.dump(sorted(seen), f, indent=2)


def filter_new(listings: List[Listing], seen: Set[str]) -> List[Listing]:
    return [l for l in listings if l.id not in seen]
```

- [ ] **Step 5: Run tests to verify they pass**

```bash
pytest tests/test_storage.py -v
```

Expected: all 6 tests PASS.

- [ ] **Step 6: Commit**

```bash
git add models.py storage.py tests/test_storage.py
git commit -m "feat: listing model and storage utils"
```

---

### Task 3: BOCM scraper

**Files:**
- Create: `scrapers/bocm.py`
- Create: `tests/test_bocm.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/test_bocm.py
from unittest.mock import patch, MagicMock
from scrapers.bocm import scrape


SAMPLE_FEED = {
    "entries": [
        {
            "title": "Convocatoria sorteo vivienda protección oficial Vallecas",
            "link": "https://www.bocm.es/boletin/1234",
            "published": "Sat, 19 Apr 2026 00:00:00 +0000",
        },
        {
            "title": "Resolución sobre impuesto municipal",
            "link": "https://www.bocm.es/boletin/5678",
            "published": "Sat, 19 Apr 2026 00:00:00 +0000",
        },
        {
            "title": "Adjudicación vivienda precio tasado VPP Madrid",
            "link": "https://www.bocm.es/boletin/9999",
            "published": "Sat, 19 Apr 2026 00:00:00 +0000",
        },
    ]
}


def test_scrape_returns_only_matching_entries():
    with patch("scrapers.bocm.feedparser.parse", return_value=SAMPLE_FEED):
        results = scrape()
    assert len(results) == 2
    urls = [r.url for r in results]
    assert "https://www.bocm.es/boletin/1234" in urls
    assert "https://www.bocm.es/boletin/9999" in urls
    assert "https://www.bocm.es/boletin/5678" not in urls


def test_scrape_sets_fuente_bocm():
    with patch("scrapers.bocm.feedparser.parse", return_value=SAMPLE_FEED):
        results = scrape()
    assert all(r.fuente == "BOCM" for r in results)


def test_scrape_returns_empty_on_feed_error():
    with patch("scrapers.bocm.feedparser.parse", side_effect=Exception("network error")):
        results = scrape()
    assert results == []
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/test_bocm.py -v
```

Expected: `ImportError` — scrapers.bocm doesn't exist.

- [ ] **Step 3: Create scrapers/bocm.py**

```python
import feedparser
import logging
from datetime import datetime
from models import Listing

logger = logging.getLogger(__name__)

FEED_URL = "https://www.bocm.es/boletin/boletin_hoy.rss"

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
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest tests/test_bocm.py -v
```

Expected: all 3 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add scrapers/bocm.py tests/test_bocm.py
git commit -m "feat: BOCM RSS scraper"
```

---

### Task 4: AVS scraper

**Files:**
- Create: `scrapers/avs.py`
- Create: `tests/test_avs.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/test_avs.py
from unittest.mock import patch, MagicMock
from scrapers.avs import scrape

SAMPLE_HTML = """
<html><body>
  <ul class="listado-noticias">
    <li>
      <a href="/convocatorias/sorteo-vpo-2026">Sorteo vivienda protección oficial 2026</a>
      <span class="fecha">19/04/2026</span>
    </li>
    <li>
      <a href="/convocatorias/renovacion-contrato">Renovación contratos alquiler social</a>
      <span class="fecha">18/04/2026</span>
    </li>
    <li>
      <a href="/convocatorias/alquiler-opcion-compra-vallecas">Alquiler con opción a compra Vallecas VPP</a>
      <span class="fecha">17/04/2026</span>
    </li>
  </ul>
</body></html>
"""


def _mock_response(html):
    mock = MagicMock()
    mock.status_code = 200
    mock.text = html
    mock.raise_for_status = MagicMock()
    return mock


def test_scrape_returns_matching_listings():
    with patch("scrapers.avs.requests.get", return_value=_mock_response(SAMPLE_HTML)):
        results = scrape()
    assert len(results) == 2
    titles = [r.titulo for r in results]
    assert any("protección oficial" in t.lower() for t in titles)
    assert any("alquiler con opción a compra" in t.lower() for t in titles)


def test_scrape_sets_fuente_avs():
    with patch("scrapers.avs.requests.get", return_value=_mock_response(SAMPLE_HTML)):
        results = scrape()
    assert all(r.fuente == "AVS" for r in results)


def test_scrape_builds_full_url():
    with patch("scrapers.avs.requests.get", return_value=_mock_response(SAMPLE_HTML)):
        results = scrape()
    assert all(r.url.startswith("https://") for r in results)


def test_scrape_returns_empty_on_request_error():
    with patch("scrapers.avs.requests.get", side_effect=Exception("timeout")):
        results = scrape()
    assert results == []
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/test_avs.py -v
```

Expected: `ImportError`.

- [ ] **Step 3: Create scrapers/avs.py**

```python
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
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest tests/test_avs.py -v
```

Expected: all 4 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add scrapers/avs.py tests/test_avs.py
git commit -m "feat: AVS Madrid scraper"
```

---

### Task 5: EMVS scraper

**Files:**
- Create: `scrapers/emvs.py`
- Create: `tests/test_emvs.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/test_emvs.py
from unittest.mock import patch, MagicMock
from scrapers.emvs import scrape

SAMPLE_HTML = """
<html><body>
  <div class="listado-viviendas">
    <div class="vivienda-item">
      <a href="/Viviendas/vivienda-proteccion-oficial-carabanchel">VPO Carabanchel - Promoción 2026</a>
    </div>
    <div class="vivienda-item">
      <a href="/Viviendas/vivienda-libre-centro">Vivienda libre Centro Madrid</a>
    </div>
    <div class="vivienda-item">
      <a href="/Viviendas/alquiler-opcion-compra-vallecas">Alquiler con opción a compra Vallecas</a>
    </div>
  </div>
</body></html>
"""


def _mock_response(html):
    mock = MagicMock()
    mock.status_code = 200
    mock.text = html
    mock.raise_for_status = MagicMock()
    return mock


def test_scrape_returns_matching_listings():
    with patch("scrapers.emvs.requests.get", return_value=_mock_response(SAMPLE_HTML)):
        results = scrape()
    assert len(results) == 2
    titles = [r.titulo for r in results]
    assert any("vpo" in t.lower() for t in titles)
    assert any("alquiler con opción a compra" in t.lower() for t in titles)


def test_scrape_sets_fuente_emvs():
    with patch("scrapers.emvs.requests.get", return_value=_mock_response(SAMPLE_HTML)):
        results = scrape()
    assert all(r.fuente == "EMVS" for r in results)


def test_scrape_builds_full_url():
    with patch("scrapers.emvs.requests.get", return_value=_mock_response(SAMPLE_HTML)):
        results = scrape()
    assert all(r.url.startswith("https://") for r in results)


def test_scrape_returns_empty_on_error():
    with patch("scrapers.emvs.requests.get", side_effect=Exception("connection refused")):
        results = scrape()
    assert results == []
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/test_emvs.py -v
```

Expected: `ImportError`.

- [ ] **Step 3: Create scrapers/emvs.py**

```python
import requests
import logging
from bs4 import BeautifulSoup
from datetime import datetime
from models import Listing

logger = logging.getLogger(__name__)

BASE_URL = "https://www.emvs.es"
URL = f"{BASE_URL}/Viviendas/Paginas/viviendas.aspx"

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
            results.append(Listing(
                titulo=title,
                url=url,
                fuente="EMVS",
                fecha=datetime.today().strftime("%Y-%m-%d"),
            ))
        return results
    except Exception as e:
        logger.warning(f"EMVS scraper failed: {e}")
        return []
```

- [ ] **Step 4: Run tests**

```bash
pytest tests/test_emvs.py -v
```

Expected: all 4 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add scrapers/emvs.py tests/test_emvs.py
git commit -m "feat: EMVS scraper"
```

---

### Task 6: Idealista scraper

**Files:**
- Create: `scrapers/idealista.py`
- Create: `tests/test_idealista.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/test_idealista.py
from unittest.mock import patch, MagicMock
from scrapers.idealista import scrape

SAMPLE_HTML_VPO = """
<html><body>
  <article class="item">
    <a href="/inmueble/123456/" class="item-link">
      <span class="item-title">Piso VPO 3 habitaciones Vallecas</span>
    </a>
    <span class="item-price">150.000 €</span>
  </article>
  <article class="item">
    <a href="/inmueble/789012/" class="item-link">
      <span class="item-title">Piso libre centro Madrid</span>
    </a>
  </article>
</body></html>
"""

SAMPLE_HTML_ALQUILER = """
<html><body>
  <article class="item">
    <a href="/inmueble/555555/" class="item-link">
      <span class="item-title">Piso alquiler con opción a compra Carabanchel</span>
    </a>
    <span class="item-price">800 €/mes</span>
  </article>
</body></html>
"""


def _mock_response(html):
    mock = MagicMock()
    mock.status_code = 200
    mock.text = html
    mock.raise_for_status = MagicMock()
    return mock


def test_scrape_returns_listings_from_both_urls():
    with patch("scrapers.idealista.requests.get") as mock_get:
        mock_get.side_effect = [
            _mock_response(SAMPLE_HTML_VPO),
            _mock_response(SAMPLE_HTML_ALQUILER),
        ]
        results = scrape()
    assert len(results) == 2


def test_scrape_builds_full_idealista_urls():
    with patch("scrapers.idealista.requests.get") as mock_get:
        mock_get.side_effect = [
            _mock_response(SAMPLE_HTML_VPO),
            _mock_response(SAMPLE_HTML_ALQUILER),
        ]
        results = scrape()
    assert all(r.url.startswith("https://www.idealista.com") for r in results)


def test_scrape_sets_fuente_idealista():
    with patch("scrapers.idealista.requests.get") as mock_get:
        mock_get.side_effect = [
            _mock_response(SAMPLE_HTML_VPO),
            _mock_response(SAMPLE_HTML_ALQUILER),
        ]
        results = scrape()
    assert all(r.fuente == "Idealista" for r in results)


def test_scrape_deduplicates_same_url():
    with patch("scrapers.idealista.requests.get") as mock_get:
        mock_get.side_effect = [
            _mock_response(SAMPLE_HTML_VPO),
            _mock_response(SAMPLE_HTML_VPO),
        ]
        results = scrape()
    urls = [r.url for r in results]
    assert len(urls) == len(set(urls))


def test_scrape_returns_empty_on_error():
    with patch("scrapers.idealista.requests.get", side_effect=Exception("blocked")):
        results = scrape()
    assert results == []
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/test_idealista.py -v
```

Expected: `ImportError`.

- [ ] **Step 3: Create scrapers/idealista.py**

```python
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
```

- [ ] **Step 4: Run tests**

```bash
pytest tests/test_idealista.py -v
```

Expected: all 5 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add scrapers/idealista.py tests/test_idealista.py
git commit -m "feat: Idealista scraper"
```

---

### Task 7: Fotocasa scraper

**Files:**
- Create: `scrapers/fotocasa.py`
- Create: `tests/test_fotocasa.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/test_fotocasa.py
from unittest.mock import patch, MagicMock
from scrapers.fotocasa import scrape

SAMPLE_HTML_VPO = """
<html><body>
  <article data-testid="re-CardPackPremium">
    <a href="/es/comprar/vivienda/madrid/piso-vpo-2hab/34/2345678" class="re-CardPackPremium-thumbnail">
      Piso VPO 2 habitaciones Getafe
    </a>
  </article>
  <article data-testid="re-CardPackPremium">
    <a href="/es/comprar/vivienda/madrid/piso-libre/34/9999999" class="re-CardPackPremium-thumbnail">
      Piso libre lujo centro
    </a>
  </article>
</body></html>
"""

SAMPLE_HTML_ALQUILER = """
<html><body>
  <article data-testid="re-CardPackPremium">
    <a href="/es/alquiler/vivienda/madrid/piso-opcion-compra/34/1111111" class="re-CardPackPremium-thumbnail">
      Alquiler con opción a compra Leganés VPP
    </a>
  </article>
</body></html>
"""


def _mock_response(html):
    mock = MagicMock()
    mock.status_code = 200
    mock.text = html
    mock.raise_for_status = MagicMock()
    return mock


def test_scrape_returns_listings_from_both_urls():
    with patch("scrapers.fotocasa.requests.get") as mock_get:
        mock_get.side_effect = [
            _mock_response(SAMPLE_HTML_VPO),
            _mock_response(SAMPLE_HTML_ALQUILER),
        ]
        results = scrape()
    assert len(results) == 2


def test_scrape_sets_fuente_fotocasa():
    with patch("scrapers.fotocasa.requests.get") as mock_get:
        mock_get.side_effect = [
            _mock_response(SAMPLE_HTML_VPO),
            _mock_response(SAMPLE_HTML_ALQUILER),
        ]
        results = scrape()
    assert all(r.fuente == "Fotocasa" for r in results)


def test_scrape_builds_full_fotocasa_urls():
    with patch("scrapers.fotocasa.requests.get") as mock_get:
        mock_get.side_effect = [
            _mock_response(SAMPLE_HTML_VPO),
            _mock_response(SAMPLE_HTML_ALQUILER),
        ]
        results = scrape()
    assert all(r.url.startswith("https://www.fotocasa.es") for r in results)


def test_scrape_returns_empty_on_error():
    with patch("scrapers.fotocasa.requests.get", side_effect=Exception("timeout")):
        results = scrape()
    assert results == []
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/test_fotocasa.py -v
```

Expected: `ImportError`.

- [ ] **Step 3: Create scrapers/fotocasa.py**

```python
import requests
import logging
from bs4 import BeautifulSoup
from datetime import datetime
from models import Listing

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

KEYWORDS = [
    "vpo", "vpp", "vppl",
    "protección oficial",
    "precio tasado",
    "vivienda protegida",
    "alquiler con opción a compra",
    "alquiler opción compra",
]


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
```

- [ ] **Step 4: Run tests**

```bash
pytest tests/test_fotocasa.py -v
```

Expected: all 4 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add scrapers/fotocasa.py tests/test_fotocasa.py
git commit -m "feat: Fotocasa scraper"
```

---

### Task 8: CallMeBot notifier

**Files:**
- Create: `notifier.py`
- Create: `tests/test_notifier.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/test_notifier.py
from unittest.mock import patch, MagicMock, call
from models import Listing
from notifier import send_listing, send_warning, _format_message


def test_format_message():
    listing = Listing(
        titulo="Sorteo VPO Vallecas 2026",
        url="https://bocm.es/1234",
        fuente="BOCM",
        fecha="2026-04-19",
    )
    msg = _format_message(listing)
    assert "VPO" in msg
    assert "BOCM" in msg
    assert "https://bocm.es/1234" in msg
    assert "Sorteo VPO Vallecas 2026" in msg


def test_send_listing_calls_callmebot_api():
    listing = Listing(titulo="Test VPO", url="https://example.com", fuente="TEST", fecha="2026-04-19")
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    with patch("notifier.requests.get", return_value=mock_resp) as mock_get:
        send_listing(listing, phone="34600000000", apikey="testkey")
    assert mock_get.called
    args, kwargs = mock_get.call_args
    assert "api.callmebot.com" in args[0]
    assert "34600000000" in args[0]
    assert "testkey" in args[0]


def test_send_listing_retries_on_failure():
    listing = Listing(titulo="Test VPO", url="https://example.com", fuente="TEST", fecha="2026-04-19")
    mock_resp_fail = MagicMock()
    mock_resp_fail.status_code = 500
    mock_resp_ok = MagicMock()
    mock_resp_ok.status_code = 200
    with patch("notifier.requests.get", side_effect=[mock_resp_fail, mock_resp_ok]) as mock_get:
        send_listing(listing, phone="34600000000", apikey="testkey")
    assert mock_get.call_count == 2


def test_send_warning_calls_callmebot_api():
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    with patch("notifier.requests.get", return_value=mock_resp) as mock_get:
        send_warning("⚠️ Error scrapers", phone="34600000000", apikey="testkey")
    assert mock_get.called
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/test_notifier.py -v
```

Expected: `ImportError`.

- [ ] **Step 3: Create notifier.py**

```python
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
```

- [ ] **Step 4: Run tests**

```bash
pytest tests/test_notifier.py -v
```

Expected: all 4 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add notifier.py tests/test_notifier.py
git commit -m "feat: CallMeBot WhatsApp notifier"
```

---

### Task 9: Main orchestrator

**Files:**
- Create: `main.py`
- Create: `tests/test_main.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/test_main.py
from unittest.mock import patch, MagicMock, call
from pathlib import Path
from models import Listing
from main import run


def _listing(url: str, fuente: str = "TEST") -> Listing:
    return Listing(titulo=f"Test {url}", url=url, fuente=fuente, fecha="2026-04-19")


def test_run_sends_notification_for_new_listings(tmp_path):
    seen_file = tmp_path / "seen.json"
    seen_file.write_text('[]')
    new_listing = _listing("https://bocm.es/1")

    with patch("main.bocm.scrape", return_value=[new_listing]), \
         patch("main.avs.scrape", return_value=[]), \
         patch("main.emvs.scrape", return_value=[]), \
         patch("main.idealista.scrape", return_value=[]), \
         patch("main.fotocasa.scrape", return_value=[]), \
         patch("main.send_listing") as mock_send, \
         patch("main.send_warning"), \
         patch.dict("os.environ", {"CALLMEBOT_PHONE": "34600000000", "CALLMEBOT_APIKEY": "key"}):
        run(seen_file=seen_file)

    mock_send.assert_called_once_with(new_listing, phone="34600000000", apikey="key")


def test_run_does_not_notify_seen_listings(tmp_path):
    import hashlib
    url = "https://bocm.es/1"
    existing_id = hashlib.sha1(url.encode()).hexdigest()
    seen_file = tmp_path / "seen.json"
    seen_file.write_text(f'["{existing_id}"]')
    seen_listing = _listing(url)

    with patch("main.bocm.scrape", return_value=[seen_listing]), \
         patch("main.avs.scrape", return_value=[]), \
         patch("main.emvs.scrape", return_value=[]), \
         patch("main.idealista.scrape", return_value=[]), \
         patch("main.fotocasa.scrape", return_value=[]), \
         patch("main.send_listing") as mock_send, \
         patch("main.send_warning"), \
         patch.dict("os.environ", {"CALLMEBOT_PHONE": "34600000000", "CALLMEBOT_APIKEY": "key"}):
        run(seen_file=seen_file)

    mock_send.assert_not_called()


def test_run_updates_seen_json(tmp_path):
    import json
    seen_file = tmp_path / "seen.json"
    seen_file.write_text('[]')
    new_listing = _listing("https://bocm.es/1")

    with patch("main.bocm.scrape", return_value=[new_listing]), \
         patch("main.avs.scrape", return_value=[]), \
         patch("main.emvs.scrape", return_value=[]), \
         patch("main.idealista.scrape", return_value=[]), \
         patch("main.fotocasa.scrape", return_value=[]), \
         patch("main.send_listing"), \
         patch("main.send_warning"), \
         patch.dict("os.environ", {"CALLMEBOT_PHONE": "34600000000", "CALLMEBOT_APIKEY": "key"}):
        run(seen_file=seen_file)

    saved = json.loads(seen_file.read_text())
    assert new_listing.id in saved


def test_run_sends_warning_when_all_scrapers_return_empty(tmp_path):
    seen_file = tmp_path / "seen.json"
    seen_file.write_text('[]')

    with patch("main.bocm.scrape", return_value=[]), \
         patch("main.avs.scrape", return_value=[]), \
         patch("main.emvs.scrape", return_value=[]), \
         patch("main.idealista.scrape", return_value=[]), \
         patch("main.fotocasa.scrape", return_value=[]), \
         patch("main.send_listing") as mock_send, \
         patch("main.send_warning") as mock_warn, \
         patch.dict("os.environ", {"CALLMEBOT_PHONE": "34600000000", "CALLMEBOT_APIKEY": "key"}):
        run(seen_file=seen_file)

    mock_send.assert_not_called()
    mock_warn.assert_called_once()
    assert "Error" in mock_warn.call_args[0][0]
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/test_main.py -v
```

Expected: `ImportError`.

- [ ] **Step 3: Create main.py**

```python
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
```

- [ ] **Step 4: Run tests**

```bash
pytest tests/test_main.py -v
```

Expected: all 4 tests PASS.

- [ ] **Step 5: Run full test suite**

```bash
pytest -v
```

Expected: all tests PASS.

- [ ] **Step 6: Commit**

```bash
git add main.py tests/test_main.py
git commit -m "feat: main orchestrator"
```

---

### Task 10: GitHub Actions workflow

**Files:**
- Create: `.github/workflows/check.yml`

- [ ] **Step 1: Create workflow file**

```yaml
# .github/workflows/check.yml
name: VPO Check

on:
  schedule:
    - cron: '0 7 * * *'  # 07:00 UTC = 08:00/09:00 Madrid
  workflow_dispatch:      # allow manual trigger

permissions:
  contents: write

jobs:
  check:
    runs-on: ubuntu-latest

    steps:
      - name: Checkout
        uses: actions/checkout@v4
        with:
          token: ${{ secrets.GITHUB_TOKEN }}

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: pip install -r requirements.txt

      - name: Run scraper
        env:
          CALLMEBOT_PHONE: ${{ secrets.CALLMEBOT_PHONE }}
          CALLMEBOT_APIKEY: ${{ secrets.CALLMEBOT_APIKEY }}
        run: python main.py

      - name: Commit updated seen.json
        run: |
          git config user.name "github-actions[bot]"
          git config user.email "github-actions[bot]@users.noreply.github.com"
          git add seen.json
          git diff --staged --quiet || git commit -m "chore: update seen listings [skip ci]"
          git push
```

- [ ] **Step 2: Create .gitignore**

```
__pycache__/
*.pyc
.env
*.egg-info/
.pytest_cache/
```

- [ ] **Step 3: Commit**

```bash
git add .github/workflows/check.yml .gitignore
git commit -m "feat: GitHub Actions daily cron workflow"
```

---

### Task 11: Setup instructions

- [ ] **Step 1: Activate CallMeBot**

Send this exact message from your WhatsApp to `+34 644 59 72 64`:
```
I allow callmebot to send me messages
```
You will receive an API key in reply. Save it.

- [ ] **Step 2: Add GitHub Secrets**

After repo is created on GitHub, go to:
`Settings → Secrets and variables → Actions → New repository secret`

Add:
- `CALLMEBOT_PHONE` → your phone with country code, no `+` (e.g. `34612345678`)
- `CALLMEBOT_APIKEY` → key received from CallMeBot

- [ ] **Step 3: Test manual trigger**

In GitHub repo → Actions → VPO Check → Run workflow

Verify:
1. Workflow runs green
2. You receive WhatsApp message (or "no new listings" means scrapers worked but nothing new)
3. `seen.json` updated with a new commit

- [ ] **Step 4: Verify BOCM RSS URL**

If BOCM scraper returns 0 results consistently, the RSS URL may be wrong. Check actual URL at `bocm.es` and update `BOCM_FEED_URL` in `scrapers/bocm.py`.

---

## Self-Review Notes

- All scraper tests use mocked HTTP — no real network calls in CI
- `seen.json` path is injectable via `run(seen_file=...)` for testability
- Warning sent only when ALL scrapers return empty (not when one fails)
- `[skip ci]` in auto-commit message prevents infinite workflow loops
- BOCM RSS URL needs real-world verification on first run
