import useAppStore from '../../stores/appStore';
import useRecording from '../../hooks/useRecording';

export default function ControlPanel() {
  const { isRecording, loading } = useAppStore();
  const { startRecording, stopRecording } = useRecording();
  const setActiveGame = useAppStore((s) => s.setActiveGame);

  const handleRecord = async () => {
    if (isRecording) {
      stopRecording();
    } else {
      try {
        await startRecording();
      } catch (error) {
        console.error('Recording failed:', error);
      }
    }
  };

  return (
    <div className="controls-container">
      <div className="control-buttons">
        <button
          onClick={handleRecord}
          disabled={loading}
          className={`record-btn ${isRecording ? 'recording' : ''} ${loading ? 'processing' : ''}`}
        >
          {isRecording ? 'Durdur' : loading ? 'Yükleniyor...' : 'Konuş'}
        </button>

        <button
          onClick={() => setActiveGame('rps')}
          className="games-btn"
        >
          Taş Kağıt Makas Oyna
        </button>

        <button
          onClick={() => setActiveGame('math')}
          className="games-btn alt"
        >
          Matematik Oyunu Oyna
        </button>
      </div>
    </div>
  );
}

