import { useEffect, useState } from "react";

function App() {
  const [nightly, setNightly] = useState(null);
  const [trade, setTrade] = useState(null);
  const [season, setSeason] = useState(null);

  useEffect(() => {
    fetch("/api/run/nightly")
      .then((res) => res.json())
      .then((d) => setNightly(d));

    fetch("/api/run/trade")
      .then((res) => res.json())
      .then((d) => setTrade(d));

    fetch("/api/season")
      .then((res) => res.json())
      .then((d) => setSeason(d));
  }, []);

  return (
    <div style={{ padding: "2rem", fontFamily: "sans-serif" }}>
      <h1>FantasyCPU Dashboard</h1>
      <h2>Nightly Logic</h2>
      <pre>{JSON.stringify(nightly, null, 2)}</pre>
      <h2>Trade Logic</h2>
      <pre>{JSON.stringify(trade, null, 2)}</pre>
      <h2>Season Outlook</h2>
      <pre>{JSON.stringify(season, null, 2)}</pre>
    </div>
  );
}

export default App;
