import cv2
import threading
import time
from .object_detector import ObjectDetector

class UnifiedDetectionSystem:
    def __init__(self):
        self.object_detector = ObjectDetector()
        self.current_frame = None
        self.processed_frame = None
        self.is_running = False
        self.cap = None
        self.detection_results = {
            'objects': [],
            'hands': 0,
            'faces': 0,
            'pose_detection': False,
            'fps': 0
        }
        # Kamera ayarları için değişkenler
        self.camera_index = 0
        self.frame_width = 640  # Düşük çözünürlük için
        self.frame_height = 480

    def start_camera(self, camera_index=0):
        """Kamerayı başlat ve işleme thread'ini başlat"""
        # Eğer kamera zaten çalışıyorsa, tekrar başlatma
        if self.is_running:
            print("Kamera zaten çalışıyor.")
            return True

        try:
            self.cap = cv2.VideoCapture(camera_index)
            if not self.cap.isOpened():
                raise Exception("Kamera açılamadı")

            # Kamera ayarlarını yap (performans için)
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.frame_width)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.frame_height)
            self.cap.set(cv2.CAP_PROP_FPS, 30)  # FPS'i sınırla

            self.is_running = True

            # Frame okuma thread'ini başlat
            self.read_thread = threading.Thread(target=self._read_frames)
            self.read_thread.daemon = True
            self.read_thread.start()

            # İşleme thread'ini başlat
            self.process_thread = threading.Thread(target=self._process_frames)
            self.process_thread.daemon = True
            self.process_thread.start()

            print("Kamera başarıyla başlatıldı")
            return True

        except Exception as e:
            print(f"Kamera başlatma hatası: {e}")
            return False

    def _read_frames(self):
        """Sürekli frame okuma - MÜMKÜN OLDUĞUNCA HIZLI"""
        while self.is_running:
            ret, frame = self.cap.read()
            if ret:
                self.current_frame = frame
            # Sleep SÜRESİNİ AZALT veya KALDIR for maximum reading speed
            # time.sleep(0.001) # Çok kısa bir bekleme

    def _process_frames(self):
        """Sürekli frame işleme - İŞLEME HIZINI AYARLA"""
        while self.is_running:
            if self.current_frame is not None:
                try:
                    # Frame'i kopyala
                    frame = self.current_frame.copy()

                    # Nesne tespiti (Bu işlem CPU yoğun, onu yavaşlatıyor)
                    processed_frame, results = self.object_detector.detect_objects(frame)
                    self.processed_frame = processed_frame

                    # Sonuçları güncelle
                    self.detection_results = results
                    self.detection_results['fps'] = self.object_detector.get_fps()

                except Exception as e:
                    print(f"Frame işleme hatası: {e}")

            # İŞLEME HIZINI AYARLA: MediaPipe çok ağır, bu yüzden bekleme süresini ARTIRABİLİRSİN
            time.sleep(0.1)  # Saniyede ~10 frame işle (10 FPS)

    def get_processed_frame(self):
        """İşlenmiş frame'i döndür"""
        return self.processed_frame

    def get_detection_results(self):
        """Tespit sonuçlarını döndür"""
        return self.detection_results

    def stop_camera(self):
        """Kamerayı durdur"""
        self.is_running = False
        if self.cap:
            self.cap.release()
        cv2.destroyAllWindows()
        print("Kamera durduruldu.")