import { useEffect, useState } from "react";

function App() {
  const [health, setHealth] = useState(null);

  useEffect(() => {
    fetch("/api/health")
      .then((res) => res.json())
      .then((data) => setHealth(data))
      .catch((err) => setHealth({ error: err.toString() }));
  }, []);

  return (
    <div style={{ padding: "2rem", fontFamily: "sans-serif" }}>
      <h1>FantasyCPU Dashboard</h1>
      <pre>{JSON.stringify(health, null, 2)}</pre>
    </div>
  );
}

export default App;
