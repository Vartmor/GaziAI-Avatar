// frontend/src/components/UI/StatusPanel.jsx
import { useEffect } from 'react';
import useAppStore from '../../stores/appStore';

export default function StatusPanel() {
  const { cvResults, fetchCvResults } = useAppStore();

  useEffect(() => {
    // CV sonuçlarını periyodik olarak al
    const interval = setInterval(fetchCvResults, 1000);
    return () => clearInterval(interval);
  }, [fetchCvResults]);

  return (
    <div style={{
      background: '#fff',
      padding: '10px',
      borderRadius: '5px',
      border: '1px solid #ccc'
    }}>
      <h2>Durum Bilgisi</h2>
      <div>
        <p>Eller: {cvResults.hands || 0}</p>
        <p>Yüzler: {cvResults.faces || 0}</p>
        <p>Poz: {cvResults.pose_detected ? 'Algılandı' : 'Yok'}</p>
        <p>FPS: {cvResults.fps || 0}</p>
        {cvResults.objects && cvResults.objects.length > 0 && (
          <p>Nesneler: {cvResults.objects.join(', ')}</p>
        )}
      </div>
    </div>
  );
}