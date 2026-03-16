# Bergen Smart-Rain Hub: 
### IoT-løsning for urban energiberegning.

Dette prosjektet er lagd for å samle inn og analysere data fra regnsensorer i Bergen, for å gi en oversikt over nedbørsmønstre og gi en forståelse av hvordan regn kan påvirke energiforbruket i byen, og hvordan nedbør kan utnyttes som en ressurs for å redusere energiforbruket til næringsbygg og boliger.

---
### Målsetning:
- Samle inn data om nedbør i Bergen ved hjelp av regnsensorer koblet til Raspberry Pi Pico.
- Analysere dataene for å beregne potensiell energi som kan utnyttes fra regnvann (E = mgh).
- Gi innsikt i hvordan regn kan påvirke energiforbruket i urbane områder og hvordan det kan utnyttes for å redusere energiforbruket i næringsbygg og boliger

---

### Projsektoversikt:
```
bergen-rain-hub/
│
├── hardware/                # Programvare som kjører på Raspberry Pi Pico
│   ├── main.py              # Hovedprogrammet som starter når Pico får strøm
│   ├── boot.py              # Oppsett av Wi-Fi og nettverkstilkobling
│   └── sensors.py           # Logikk for å lese av regnsensor og temperatur
│
├── backend/                 # Programvare som kjører på server
│   ├── frost_client.py      # Skriptet som henter data fra Frost API
│   ├── analysis.py          # Funksjoner for energiutregning (E = mgh)
│   └── database.py          # Lagring av data
│
├── docs/                    # Dokumentasjon
│   ├── circuit_diagram.png  # Bilde/skisse av koblingsskjemaet for regnsensoren
│   └── hardware_list.md     # Liste over komponenter
│
```
---
### Current Tech-Stack
- Python
- Frost_API