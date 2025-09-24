import './App.css';
import Scene from './components/Scene';
import CameraFeed from './components/CameraFeed';
import ControlPanel from './components/UI/ControlPanel';
import GamePanel from './components/Games/GamePanel';

function App() {
  return (
    <div className="app">
      <div className="main-container">
        <div className="left-panel">
          <h2>GaziAI Avatar</h2>
          <Scene />
        </div>
        
        <div className="right-panel">
          <ControlPanel />
          <CameraFeed />
          <GamePanel />
        </div>
      </div>
    </div>
  );
}

export default App;
