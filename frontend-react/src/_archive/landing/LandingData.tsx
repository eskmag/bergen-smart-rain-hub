export default function LandingData() {
  return (
    <section className="l-data-section" id="data">
      <div>
        <p className="l-section-eyebrow">Datagrunnlag</p>
        <h2 className="l-data-title">Ekte data. Reelle tall. Ingen gjetning.</h2>
        <p className="l-data-body">
          Alle beregninger er basert på daglige nedbørsmålinger fra Meteorologisk Institutts
          målestasjon på Bergen Florida (SN50540) — en av de mest kontinuerlige
          nedbørsstasjonene i Bergensregionen. Modellene følger WHO sine beredskapsstandarder
          og norske tekniske retningslinjer for regnvannsoppsamling.
        </p>
      </div>
      <div className="l-data-facts">
        <div className="l-data-fact">
          <div className="l-df-num">365 d</div>
          <div className="l-df-label">Daglige målinger simulert per analyse</div>
        </div>
        <div className="l-data-fact">
          <div className="l-df-num">85%</div>
          <div className="l-df-label">Standard oppsamlingseffektivitet — realistisk, ikke optimistisk</div>
        </div>
        <div className="l-data-fact">
          <div className="l-df-num">13 L</div>
          <div className="l-df-label">WHO-minimum per person per dag i krisesituasjon</div>
        </div>
        <div className="l-data-fact">
          <div className="l-df-num">SN50540</div>
          <div className="l-df-label">Bergen Florida — primær målestasjon, Frost API</div>
        </div>
      </div>
    </section>
  )
}
