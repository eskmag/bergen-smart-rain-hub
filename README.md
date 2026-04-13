# Bergen Smart Rain Hub
### Regnvannsoppsamling som beredskapsressurs

Bergen er en av Europas mest nedbørsrike byer, med over 2 200 mm nedbør i året. Bergen Smart Rain Hub analyserer ekte nedbørsdata for å kartlegge potensialet for regnvannsoppsamling som **beredskapsressurs** — for enkeltpersoner, lokalsamfunn og kommunale beredskapsplaner.

Ved vannkrise, forurensning eller infrastruktursvikt kan oppsamlet regnvann utgjøre forskjellen mellom trygg vannforsyning og krise. Dette verktøyet viser hvor mye vann som kan samles opp fra bygningstak, og hvor lenge det rekker.

---

### Hovedfunksjoner

- **Beredskapssimulering** — Simuler tanknivå dag for dag gjennom et helt år med ekte nedbørsdata. Se når tanken fylles opp, når den tømmes, og når vannforsyningen er kritisk.
- **Tørkeperiode-analyse** — Identifiser de mest sårbare periodene der nedbøren uteblir og man er avhengig av lagret vann.
- **Skalerbare scenarier** — Modeller alt fra én husholdning til et helt nabolag med justerbare parametere for takareal, tankkapasitet, befolkning og forbruksnivå.
- **WHO-standarder** — Beregninger basert på Verdens helseorganisasjons minimumsforbruk ved krise (13 liter/person/dag).
- **Energipotensial** — Sekundær analyse av teoretisk energi fra vannets fall (E = mgh), med CO₂-besparelser og praktiske sammenligninger.

---

### Datakilder

Nedbørsdata hentes fra **Meteorologisk Institutt** sitt [Frost API](https://frost.met.no/), med målestasjon SN50540 (Bergen Florida). Systemet henter og lagrer det siste året med daglige nedbørsmålinger.

---

### Prosjektstruktur

```
bergen-smart-rain-hub/
│
├── backend/
│   ├── frost_client.py      # Henter nedbørsdata fra Frost API (1 år)
│   ├── analysis.py          # Beredskapsberegninger, vannoppsamling, energipotensial
│   ├── database.py          # SQLite-lagring av observasjoner
│   └── pipeline.py          # Orkestrering: hent data → lagre i database
│
├── frontend/
│   ├── app.py               # Hovedside — oversikt og nøkkeltall
│   └── pages/
│       ├── 1_vannberedskap.py    # Beredskapssimulering og tørkeanalyse
│       └── 2_energipotensial.py  # Energiberegning (sekundær)
│
├── data/
│   └── rain.db              # SQLite-database med nedbørsdata
│
└── docs/                    # Dokumentasjon
```

---

### Teknisk stack

- **Språk:** Python
- **Frontend:** Streamlit
- **API:** Frost API (Meteorologisk Institutt)
- **Database:** SQLite
- **Analyse:** pandas, numpy
- **Visualisering:** Altair

---

### Eksempeldata fra Bergen (siste år)

| Nøkkeltall | Verdi |
|---|---|
| Total nedbør | 2 213 mm |
| Lengste tørkeperiode | 25 dager |
| Vann fra ett hustak (150 m²) | 282 000 liter |
| Beredskapsforsyning (1 person) | 21 700 dager |
| Beredskapsforsyning (4 pers. familie) | 5 400 dager |

---

### Lisens

Apache 2.0 — se [LICENSE](LICENSE).
