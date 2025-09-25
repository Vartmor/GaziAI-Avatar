import { useEffect, useRef, useState } from 'react';
import { apiUrl } from '../../config/api';
import useAppStore from '../../stores/appStore';

export default function CameraFeed() {
  const videoRef = useRef(null);
  const canvasRef = useRef(null);
  const lowResCanvasRef = useRef(null);
  const [stream, setStream] = useState(null);
  const [cvData, setCvData] = useState({ hands: 0, faces: 0, fingers: 0, gesture: null });
  const [cvMode, setCvMode] = useState('full');
  const setCvResults = useAppStore((s) => s.setCvResults);
  const [isLoading, setIsLoading] = useState(true);
  const [fps, setFps] = useState(0);
  const isProcessingRef = useRef(false);
  const lastTimeRef = useRef(0);
  const rafIdRef = useRef(null);

  useEffect(() => {
    const videoElement = videoRef.current;
    const canvasElement = canvasRef.current;
    const lowResCanvasElement = lowResCanvasRef.current;

    if (!videoElement || !canvasElement || !lowResCanvasElement) return;

    const getVideo = async () => {
      try {
        if (stream) {
          stream.getTracks().forEach(track => track.stop());
        }

        const mediaStream = await navigator.mediaDevices.getUserMedia({
          video: {
            width: { ideal: 640, max: 640 },
            height: { ideal: 480, max: 480 },
            frameRate: { ideal: 24, max: 30 }
          }
        });

        setStream(mediaStream);
        videoElement.srcObject = mediaStream;

        videoElement.onloadedmetadata = () => {
          videoElement.play();
          setIsLoading(false);
        };

        videoElement.onerror = (e) => {
          console.error('Video error:', e);
          setIsLoading(false);
        };
      } catch (error) {
        console.error('Kamera erişim hatası:', error);
        setIsLoading(false);

        // Fallback placeholder
        const processedImg = document.getElementById('processed-frame');
        if (processedImg) {
          processedImg.src = "data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMzIwIiBoZWlnaHQ9IjI0MCIgdmlld0JveD0iMCAwIDMyMCAyNDAiIGZpbGw9Im5vbmUiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI+CjxyZWN0IHdpZHRoPSIzMjAiIGhlaWdodD0iMjQwIiBmaWxsPSIjNGE1NTY4Ii8+Cjx0ZXh0IHg9IjUwJSIgeT0iNTAlIiBkb21pbmFudC1iYXNlbGluZT0ibWlkZGxlIiB0ZXh0LWFuY2hvcj0ibWlkZGxlIiBmaWxsPSIjZmZmIiBmb250LXNpemU9IjE2cHgiPkthbWVyYSBVlaşılamadı</text></svg>";
        }
      }
    };

    getVideo();

    return () => {
      if (stream) stream.getTracks().forEach(track => track.stop());
      if (rafIdRef.current) cancelAnimationFrame(rafIdRef.current);
    };
  }, []);

  useEffect(() => {
    const calculateFps = (currentTime) => {
      if (!lastTimeRef.current) lastTimeRef.current = currentTime;
      const delta = currentTime - lastTimeRef.current;
      if (delta >= 1000) {
        setFps(1000 / delta);
        lastTimeRef.current = currentTime;
      }
      rafIdRef.current = requestAnimationFrame(calculateFps);
    };
    rafIdRef.current = requestAnimationFrame(calculateFps);
    return () => rafIdRef.current && cancelAnimationFrame(rafIdRef.current);
  }, []);

  const processFrame = async () => {
    if (isProcessingRef.current) return;

    const videoElement = videoRef.current;
    const canvasElement = canvasRef.current;
    const lowResCanvasElement = lowResCanvasRef.current;

    if (!videoElement || !canvasElement || !lowResCanvasElement || videoElement.readyState !== 4) return;

    isProcessingRef.current = true;

    try {
      const HIGH_WIDTH = 640;
      const HIGH_HEIGHT = 480;
      canvasElement.width = HIGH_WIDTH;
      canvasElement.height = HIGH_HEIGHT;
      const highCtx = canvasElement.getContext('2d');
      highCtx.drawImage(videoElement, 0, 0, HIGH_WIDTH, HIGH_HEIGHT);

      let frameData;
      if (cvMode === 'lite') {
        const LOW_WIDTH = 320;
        const LOW_HEIGHT = 240;
        const lowResCtx = lowResCanvasElement.getContext('2d');
        lowResCanvasElement.width = LOW_WIDTH;
        lowResCanvasElement.height = LOW_HEIGHT;
        lowResCtx.drawImage(videoElement, 0, 0, LOW_WIDTH, LOW_HEIGHT);
        frameData = lowResCanvasElement.toDataURL('image/jpeg', 0.2);
      } else {
        frameData = canvasElement.toDataURL('image/jpeg', 0.55);
      }

      const response = await fetch(apiUrl('/api/process_frame'), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ frame: frameData })
      });

      if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);

      const result = await response.json();
      setCvMode(result.cv_mode || 'full');
      if (result.success) {
        const processedImg = document.getElementById('processed-frame');
        if (processedImg) {
          processedImg.src = result.processed_frame;
          processedImg.loading = 'lazy';
        }
        const newCv = {
          hands: result.hands || 0,
          faces: result.faces || 0,
          fingers: result.fingers ?? 0,
          gesture: result.gesture ?? null,
          fps: result.fps || 0,
        };
        setCvData(newCv);
        try { setCvResults(newCv); } catch {}
      }
    } catch (error) {
      console.error('Frame i?leme hatas?:', error);
      await new Promise(resolve => setTimeout(resolve, 3000));
    } finally {
      isProcessingRef.current = false;
    }
  };

  useEffect(() => {
    const delay = cvMode === 'lite' ? 120 : 190;
    const interval = setInterval(processFrame, delay);
    return () => clearInterval(interval);
  }, [cvMode, stream]);

  return (
    <div className="camera-container">
      <h2>Kamera Görüntüsü</h2>
      <div className="camera-feed">
        <video
          ref={videoRef}
          autoPlay
          playsInline
          muted
          style={{ display: 'none' }}
        />
        {isLoading ? (
          <div style={{
            width: '100%',
            height: '300px',
            background: '#4a5568',
            display: 'flex',
            justifyContent: 'center',
            alignItems: 'center',
            borderRadius: '8px',
            color: 'white'
          }}>
            Kamera yükleniyor...
          </div>
        ) : (
          <img
            id="processed-frame"
            alt="İşlenmiş Kamera Görüntüsü"
            style={{ width: '100%', height: '300px', objectFit: 'cover', borderRadius: '8px', transform: 'scaleX(-1)' }}
            src="data:image/gif;base64,R0lGODlhAQABAIAAAAAAAP///ywAAAAAAQABAAACAUwAOw=="
          />
        )}
        <canvas ref={canvasRef} width="320" height="240" style={{ display: 'none' }} />
        <canvas ref={lowResCanvasRef} width="320" height="240" style={{ display: 'none' }} />
      </div>

      <div className="cv-results">
        {cvMode === 'lite' ? (
          <div style={{ color: '#63b3ed' }}>Info: Lite mode streams the camera only.</div>
        ) : (
          <>
            <div>Eller: {cvData.hands}</div>
            <div>Yuzler: {cvData.faces}</div>
            <div>Parmaklar: {cvData.fingers ?? 0}</div>
            <div>Isaret: {cvData.gesture || '-'} </div>
          </>
        )}
      </div>
    </div>
  );
}
