import { useEffect, useMemo, useRef, useState } from 'react';
import useAppStore from '../../stores/appStore';

function genQuestion() {
  let a = Math.floor(Math.random() * 6);
  let b = Math.floor(Math.random() * 6);
  while (a + b > 10) {
    a = Math.floor(Math.random() * 6);
    b = Math.floor(Math.random() * 6);
  }
  return { a, b, sum: a + b };
}

export default function MathGame() {
  const cv = useAppStore((s) => s.cvResults);
  const [question, setQuestion] = useState(genQuestion());
  const [score, setScore] = useState(0);
  const target = 5;
  const [feedback, setFeedback] = useState('');
  const [answered, setAnswered] = useState(false);
  const timerRef = useRef(null);

  // User's current number from fingers
  const userNumber = useMemo(() => {
    const f = typeof cv?.fingers === 'number' ? cv.fingers : 0;
    // Clamp to [0..10]
    return Math.max(0, Math.min(10, f));
  }, [cv?.fingers]);

  useEffect(() => {
    // Evaluate only if not already answered
    if (answered) return;
    if (userNumber == null) return;

    if (userNumber === question.sum) {
      setFeedback('DOĞRU!');
      setAnswered(true);
      setScore((s) => s + 1);
      clearTimeout(timerRef.current);
      timerRef.current = setTimeout(() => {
        if (score + 1 < target) {
          setQuestion(genQuestion());
          setFeedback('');
          setAnswered(false);
        }
      }, 1500);
    } else if (userNumber > 0) {
      setFeedback('YANLIŞ');
      clearTimeout(timerRef.current);
      timerRef.current = setTimeout(() => setFeedback(''), 1200);
    }
  }, [userNumber, question, answered, score]);

  useEffect(() => () => clearTimeout(timerRef.current), []);

  const won = score >= target;

  return (
    <div className="math-game">
      {!won ? (
        <>
          <div className="math-line">{question.a} + {question.b} = ?</div>
          <div className="math-sub">Puan: {score}/{target}</div>
          <div className="math-sub">Gösterdiğiniz sayı: {userNumber}</div>
          {feedback && <div className={`math-feedback ${feedback === 'DOĞRU!' ? 'ok' : 'bad'}`}>{feedback}</div>}
          <div className="math-hint">Parmaklarınla sonucu göster</div>
        </>
      ) : (
        <div className="math-win">Tebrikler!</div>
      )}
    </div>
  );
}

