import { useMemo, useState } from 'react';
import useAppStore from '../../stores/appStore';

const MOVES = ['Tas', 'Kagit', 'Makas'];

function decideWinner(player, ai) {
  if (player === ai) return 'tie';
  if ((player === 'Tas' && ai === 'Makas') ||
      (player === 'Kagit' && ai === 'Tas') ||
      (player === 'Makas' && ai === 'Kagit')) return 'player';
  return 'ai';
}

export default function RPSGame() {
  const cv = useAppStore((s) => s.cvResults);
  const [playerScore, setPlayerScore] = useState(0);
  const [aiScore, setAiScore] = useState(0);
  const [lastMoves, setLastMoves] = useState({ player: '-', ai: '-' });
  const [result, setResult] = useState('');
  const maxScore = 3;

  const playerMove = useMemo(() => {
    const g = cv?.gesture;
    if (g === 'Tas' || g === 'Kagit' || g === 'Makas') return g;
    return 'Tas'; // default if unknown
  }, [cv?.gesture]);

  const makeMove = () => {
    const ai = MOVES[Math.floor(Math.random() * MOVES.length)];
    const outcome = decideWinner(playerMove, ai);
    setLastMoves({ player: playerMove, ai });
    if (outcome === 'player') setPlayerScore((s) => s + 1);
    if (outcome === 'ai') setAiScore((s) => s + 1);
    setResult(outcome === 'tie' ? 'Berabere' : outcome === 'player' ? 'Kazandınız!' : 'Kaybettiniz!');
  };

  const reset = () => {
    setPlayerScore(0);
    setAiScore(0);
    setLastMoves({ player: '-', ai: '-' });
    setResult('');
  };

  const gameOver = playerScore >= maxScore || aiScore >= maxScore;
  const winner = playerScore >= maxScore ? 'Oyuncu' : aiScore >= maxScore ? 'Yapay Zeka' : null;

  return (
    <div className="rps-game">
      <div className="rps-score">Oyuncu: {playerScore} - Yapay Zeka: {aiScore}</div>
      <div className="rps-moves">Oyuncu: {lastMoves.player} | Yapay Zeka: {lastMoves.ai}</div>
      <div className="rps-current">Gözlenen el: {playerMove}</div>
      <div className="rps-actions">
        <button className="btn-primary" onClick={makeMove} disabled={gameOver}>Hamle Yap</button>
        <button className="btn-secondary" onClick={reset}>Reset</button>
      </div>
      {result && <div className="rps-result">{result}</div>}
      {gameOver && <div className="rps-over">Oyun bitti: {winner} kazandı</div>}
    </div>
  );
}

