import BeregnNav from '../components/beregn/BeregnNav'
import InputPanel from '../components/beregn/InputPanel'
import ResultPanel from '../components/beregn/ResultPanel'
import '../kalkulator.css'

// Two-pane Beredskapskalkulator. Has its own nav (escapes the AppShell);
// both panels read/write the shared BeredskapsContext provided by the
// parent layout route, so state carries over to /beredskap.
export default function Beregn() {
  return (
    <div className="k-shell">
      <BeregnNav />
      <div className="k-layout">
        <InputPanel />
        <ResultPanel />
      </div>
    </div>
  )
}
