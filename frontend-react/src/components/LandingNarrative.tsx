export default function LandingNarrative() {
  return (
    <section className="l-narrative" id="bakgrunn">
      <p className="l-section-eyebrow">Hvorfor regnvann</p>
      <div className="l-narrative-steps">
        <div className="l-narrative-step">
          <h3 className="l-step-title">Vannet finnes allerede</h3>
          <p className="l-step-body">
            Bergen er en av Europas regnrikeste byer. Det faller mer enn nok til å dekke
            krisebehovet for alle som bor i bygget ditt.
          </p>
        </div>
        <div className="l-narrative-step">
          <h3 className="l-step-title">Vannforsyningen er sårbar</h3>
          <p className="l-step-body">
            Forurensning, ledningsbrudd og ekstremvær kan kutte vannet fra springen.
            Uten egen oppsamling har du ingen buffer.
          </p>
        </div>
        <div className="l-narrative-step">
          <h3 className="l-step-title">Løsningen er på taket</h3>
          <p className="l-step-body">
            En tank koblet til taket gir bygget sitt eget nødvann. Kalkulatoren viser
            hvor lenge det holder.
          </p>
        </div>
      </div>
    </section>
  )
}
