import VolunteerMap from "./components/VolunteerMap.jsx";

function App() {
  return (
    <div className="app-shell">
      <header className="app-header">
        <h1>Buffalo to the rescue</h1>
        <p>Pins highlight open elder requests prioritized by current conditions.</p>
      </header>
      <main>
        <VolunteerMap />
      </main>
    </div>
  );
}

export default App;

