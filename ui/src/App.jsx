import React, { useEffect, useState } from "react";

function App() {
  const [headCoach, setHeadCoach] = useState(null);
  const [gm, setGm] = useState(null);
  const [scout, setScout] = useState(null);
  const [defense, setDefense] = useState(null);
  const [psycho, setPsycho] = useState(null);
  const [decree, setDecree] = useState(null);

  useEffect(() => {
    fetch("/api/run/head_coach").then(r => r.json()).then(setHeadCoach);
    fetch("/api/run/general_manager").then(r => r.json()).then(setGm);
    fetch("/api/run/scout").then(r => r.json()).then(setScout);
    fetch("/api/run/defense").then(r => r.json()).then(setDefense);
    fetch("/api/run/psycho").then(r => r.json()).then(setPsycho);
    fetch("/api/decree").then(r => r.json()).then(setDecree);
  }, []);

  return (
    <div className="newspaper">
      <header>
        <h1>FantasyCPU Times</h1>
        <p>{new Date().toLocaleDateString()}</p>
      </header>

      <section>
        <h2>Head Coach Report</h2>
        <pre>{JSON.stringify(headCoach, null, 2)}</pre>
      </section>

      <section>
        <h2>General Manager Memo</h2>
        <pre>{JSON.stringify(gm, null, 2)}</pre>
      </section>

      <section>
        <h2>Scout’s Notes</h2>
        <pre>{JSON.stringify(scout, null, 2)}</pre>
      </section>

      <section>
        <h2>Defensive Coordinator</h2>
        <pre>{JSON.stringify(defense, null, 2)}</pre>
      </section>

      <section>
        <h2>Opponent Psychoanalyst</h2>
        <pre>{JSON.stringify(psycho, null, 2)}</pre>
      </section>

      <section className="council">
        <h2>⚖️ Council Ruling</h2>
        <pre>{JSON.stringify(decree, null, 2)}</pre>
      </section>
    </div>
  );
}

export default App;
