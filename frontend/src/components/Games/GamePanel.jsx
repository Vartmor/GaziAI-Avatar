import useAppStore from '../../stores/appStore';
import MathGame from './MathGame';
import RPSGame from './RPSGame';

export default function GamePanel() {
  const activeGame = useAppStore((s) => s.activeGame);
  const setActiveGame = useAppStore((s) => s.setActiveGame);

  const handleClose = () => setActiveGame('none');

  return (
    <div className="game-panel">
      <div className="game-panel-header">
        <div className="game-title">
          {activeGame === 'math' ? 'Matematik Oyunu' : activeGame === 'rps' ? 'Taş Kağıt Makas' : 'Oyun Seçilmedi'}
        </div>
        {activeGame !== 'none' && (
          <button className="game-close-btn" onClick={handleClose}>×</button>
        )}
      </div>
      <div className="game-panel-body">
        {activeGame === 'math' && <MathGame />}
        {activeGame === 'rps' && <RPSGame />}
        {activeGame === 'none' && (
          <div className="game-empty">Bir oyun seçin.</div>
        )}
      </div>
    </div>
  );
}

