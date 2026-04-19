# VPO Alertas Madrid — Design Spec
_Date: 2026-04-19_

## Overview

Daily scraper that monitors multiple sources for new VPO, VPP, and rent-to-buy (alquiler con opción a compra) listings in the Comunidad de Madrid, sending WhatsApp notifications via CallMeBot when new items are detected.

## Architecture

```
GitHub Actions (cron daily 08:00 Europe/Madrid)
    │
    ▼
main.py
    ├── bocm_scraper()      → BOCM RSS feed
    ├── avs_scraper()       → agenciavivienda.comunidad.madrid
    ├── emvs_scraper()      → emvs.es
    ├── idealista_scraper() → idealista.com (VPO + VPP + alquiler opción compra)
    └── fotocasa_scraper()  → fotocasa.es (VPO + VPP + alquiler opción compra)
    │
    ▼
compare against seen.json (persisted in repo via git commit)
    │
    ▼ new items only
notifier.py → CallMeBot API → WhatsApp
    │
    ▼
update seen.json + auto git commit
```

## Project Structure

```
vpo-alertas/
├── .github/workflows/check.yml
├── scrapers/
│   ├── bocm.py
│   ├── avs.py
│   ├── emvs.py
│   ├── idealista.py
│   └── fotocasa.py
├── notifier.py
├── main.py
├── seen.json
└── requirements.txt
```

## Sources

| Scraper | URL | Type |
|---------|-----|------|
| BOCM | `bocm.es` RSS + keyword filter | Official gazette |
| AVS | `agenciavivienda.comunidad.madrid/convocatorias` | Public agency |
| EMVS | `emvs.es/viviendas` | Municipal agency |
| Idealista VPO/VPP | `idealista.com/venta-viviendas/madrid-provincia/vpo/` | Private portal |
| Idealista alquiler opción | `idealista.com/alquiler-viviendas/madrid-provincia/con-opcion-a-compra/` | Private portal |
| Fotocasa VPO/VPP | `fotocasa.es/comprar/vivienda/madrid-provincia/vpo/` | Private portal |
| Fotocasa alquiler opción | `fotocasa.es/alquiler/vivienda/madrid-provincia/alquiler-con-opcion-a-compra/` | Private portal |

## Keywords Filter

```python
KEYWORDS = [
    "VPO", "VPP", "VPPL",
    "vivienda protección oficial",
    "vivienda precio tasado",
    "vivienda protección pública",
    "vivienda protegida",
    "alquiler con opción a compra",
    "alquiler opción compra",
]
```

## Data Model

Each scraped item:
```json
{
  "id": "<sha1 of url>",
  "titulo": "Convocatoria VPO Vallecas 2026",
  "url": "https://...",
  "fuente": "BOCM",
  "fecha": "2026-04-19"
}
```

`seen.json` stores a list of all previously seen IDs. New = ID not in list.

## Notifications

WhatsApp message format via CallMeBot:
```
🏠 NUEVA VPO/VPP MADRID
Fuente: BOCM
Titulo: Convocatoria sorteo VPO Vallecas
URL: https://bocm.es/...
```

GitHub Secrets required:
- `CALLMEBOT_PHONE` — phone number with country code
- `CALLMEBOT_APIKEY` — CallMeBot API key

## Error Handling

- Single scraper failure → log warning, continue with remaining scrapers
- CallMeBot failure → retry x2, then log error
- All scrapers return 0 items → send WhatsApp warning: "⚠️ Error scrapers VPO, revisar logs"

## Scheduling

GitHub Actions cron: `0 7 * * *` (07:00 UTC = 08:00/09:00 Madrid depending on DST).
Free tier: 2000 min/month — daily run costs ~2 min/day = ~60 min/month, well within limits.

## GitHub Setup (post-implementation)

1. Create repo via GitHub MCP
2. Push code
3. Add secrets: `CALLMEBOT_PHONE`, `CALLMEBOT_APIKEY`
4. Activate CallMeBot: send WhatsApp message to +34 644 59 72 64 saying `I allow callmebot to send me messages`
