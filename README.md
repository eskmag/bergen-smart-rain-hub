# Bergen Beredskap
### Regnvannsoppsamling som beredskapsressurs

Bergen er en av Europas mest nedbørsrike byer, med over 2 200 mm nedbør i året. Bergen Beredskap analyserer ekte nedbørsdata for å kartlegge potensialet for regnvannsoppsamling som **beredskapsressurs** — for enkeltpersoner, lokalsamfunn og kommunale beredskapsplaner.

Ved vannkrise, forurensning eller infrastruktursvikt kan oppsamlet regnvann utgjøre forskjellen mellom trygg vannforsyning og krise. Dette verktøyet viser hvor mye vann som kan samles opp fra bygningstak, og hvor lenge det rekker.

---

### Hovedfunksjoner

**Beredskapskalkulator** (`/beregn`) — velg bygningstype, antall personer og tankstørrelse:

- **Beredskapssimulering** — simulerer tanknivå dag for dag gjennom et helt år med ekte nedbørsdata.
- **Sårbare perioder** — identifiserer de lengste tørkeperiodene der nedbøren uteblir.
- **Anbefalt tankstørrelse** — foreslår tankstørrelse basert på ønsket beredskapshorisont.
- **WHO-standarder** — beregninger basert på 13 liter/person/dag (kriseminimum).
- **Kostnadsoverslag** — indikativt anslag for investering og årlig drift.

**Takkart** (`/takkart`) — mål takflaten direkte på kartet:

- **Adressesøk** — søk opp adressen din og få bygningens takfotavtrykk automatisk fra OpenStreetMap (Overpass API). Kartverket FKB-Bygning planlegges som kilde i produksjon.
- **Manuell oppmåling** — tegn et polygon på kartet for å måle taket nøyaktig (geodesisk areal via Turf.js).
- **Direkte beregning** — årsoppsamling, beredskapsdager og tankanbefaling oppdateres umiddelbart fra det målte arealet.
- **Kartunderlag** — Kartverket topografisk kart med OpenStreetMap som fallback.

---

### Datakilder

Nedbørsdata hentes fra **Meteorologisk Institutt** sitt [Frost API](https://frost.met.no/), med målestasjon SN50540 (Bergen Florida). Systemet henter og lagrer det siste året med daglige nedbørs- og temperaturmålinger.

---

### Arkitektur

Tre lag: ren beregning i `backend/`, et tynt FastAPI-lag i `api/`, og en React + TypeScript-frontend i `frontend-react/`.

```
bergen-smart-rain-hub/
│
├── backend/                  # Ren beregningslogikk (ingen web-avhengigheter)
│   ├── analysis.py           # Vannoppsamling, lagringssimulering, tørkeperioder, WHO-behov
│   ├── scales.py             # Skala-definisjoner (husholdning → kritisk infrastruktur)
│   ├── economics.py          # Kapital- og livsløpskostnader
│   ├── climate.py            # Klimascenarier på historiske nedbørsserier
│   ├── database.py           # SQLite-lagring av observasjoner
│   ├── frost_client.py       # Henter nedbørsdata fra Frost API
│   ├── pipeline.py           # Orkestrering: hent data → lagre i database
│   └── config.py             # Stier, Frost-nøkler, DB_PATH
│
├── api/                      # FastAPI — kun serialisering og DB-lesing
│   ├── main.py               # App-fabrikk, CORS, router-registrering
│   ├── schemas.py            # Pydantic request/response-modeller
│   └── routers/              # config · observations · simulate/beredskap · costs
│
├── frontend-react/           # Vite + React + TypeScript
│   └── src/
│       ├── pages/            # Home · Beregn (kalkulator) · Takkart (kartmåling)
│       ├── components/       # Landing*-seksjoner + beregn/ + takkart/
│       ├── context/          # BeredskapsContext · TakkartContext
│       ├── lib/rainwater.ts  # Klientside-beregninger (årsoppsamling, beredskapsdager)
│       └── api/client.ts     # Typede fetch-wrappere
│
├── data/rain.db              # SQLite-database med nedbørsdata
├── tests/                    # pytest (112 tester)
└── docs/                     # Kildedokument + fase-rapporter
```

---

### Teknisk stack

- **Backend:** Python 3.11+, pandas, numpy
- **API:** FastAPI + Pydantic + Uvicorn
- **Frontend:** React + TypeScript + Vite, TanStack Query, Recharts, React Router, React-Leaflet, Turf.js
- **Database:** SQLite
- **Datakilde:** Frost API (Meteorologisk Institutt)

---

### Kom i gang

Krever Python 3.11+ og Node.js. Avhengigheter er pinnet i `pyproject.toml`.

```bash
# 1. Backend-avhengigheter (fra et aktivert .venv)
pip install -e ".[dev]"

# 2. Hent nedbørsdata (krever CLIENT_ID, CLIENT_SECRET, FROST_API_ENDPOINT i .env)
python -m backend.pipeline

# 3. Start API-serveren
uvicorn api.main:app --reload

# 4. Start React-frontenden (i et eget terminalvindu)
cd frontend-react && npm install && npm run dev
```

Åpne `http://localhost:5173` — Vite proxyer `/api` til FastAPI på port 8000.

Kjør testene med `python -m pytest tests/`.

---

### Eksempeldata fra Bergen (siste år, enebolig 120 m²)

| Nøkkeltall | Verdi |
|---|---|
| Total nedbør | ~2 200 mm |
| Lengste tørkeperiode | 24 dager |
| Årlig oppsamling (120 m² tak) | ~217 000 liter |
| Beredskapsforsyning (4 pers. familie) | ~4 170 dager |

_Verdiene er illustrative og avhenger av takareal, tankstørrelse og forbruksnivå._

---

### Lisens

Apache 2.0 — se [LICENSE](LICENSE).
