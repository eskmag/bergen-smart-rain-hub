export default function LandingNarrative() {
  return (
    <section className="l-narrative" id="bakgrunn">
      <p className="l-section-eyebrow">Hvordan det henger sammen</p>
      <div className="l-narrative-steps">
        <div className="l-narrative-step">
          <div className="l-step-index">01</div>
          <h3 className="l-step-title">Nedbøren finnes allerede</h3>
          <p className="l-step-body">
            Bergen er en av Europas mest nedbørsrike byer. Over 2 200 mm faller hvert år —
            mer enn nok til å dekke et krisebehov for alle som bor i bygget ditt.
          </p>
          <a className="l-step-link" href="#data">
            Hydrologiske data
            <svg className="l-icon-sm" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
              <path d="M5 12h14M12 5l7 7-7 7" />
            </svg>
          </a>
        </div>
        <div className="l-narrative-step">
          <div className="l-step-index">02</div>
          <h3 className="l-step-title">Systemet er sårbart</h3>
          <p className="l-step-body">
            Forurensning, ledningsbrudd og ekstremvær kan kutte vanntilgangen. Uten
            oppsamlingssystem finnes ingen buffer — vi er avhengige av ett enkelt nett.
          </p>
          <a className="l-step-link" href="#verktoy">
            Risikoscenarier
            <svg className="l-icon-sm" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
              <path d="M5 12h14M12 5l7 7-7 7" />
            </svg>
          </a>
        </div>
        <div className="l-narrative-step">
          <div className="l-step-index">03</div>
          <h3 className="l-step-title">Løsningen er lokal</h3>
          <p className="l-step-body">
            Regnvannsoppsamling fra eksisterende tak kan gi bygg-nivå beredskap. Beregn hva
            som er mulig — fra hustak til kommunal infrastruktur.
          </p>
          <a className="l-step-link" href="#verktoy">
            Start kalkulator
            <svg className="l-icon-sm" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
              <path d="M5 12h14M12 5l7 7-7 7" />
            </svg>
          </a>
        </div>
      </div>
    </section>
  )
}
