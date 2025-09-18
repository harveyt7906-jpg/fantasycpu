import React from "react";

function App() {
  return (
    <div style={{ fontFamily: "Arial, sans-serif", padding: "2rem" }}>
      <h1>⚡ Thanos Fantasy Dashboard ⚡</h1>
      <p>Welcome to your AI-powered Fantasy Football system.</p>

      <ul>
        <li><a href="/api/run/head_coach" target="_blank">Run Head Coach</a></li>
        <li><a href="/api/run/gm" target="_blank">Run General Manager</a></li>
        <li><a href="/api/run/waiver" target="_blank">Run Waiver Logic</a></li>
        <li><a href="/api/run/scout" target="_blank">Run Scout Logic</a></li>
        <li><a href="/api/run/learning" target="_blank">Run Learning</a></li>
        <li><a href="/api/decree" target="_blank">Council Decree</a></li>
        <li><a href="/api/season" target="_blank">Season Outlook</a></li>
      </ul>
    </div>
  );
}

export default App;
