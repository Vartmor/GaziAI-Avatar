import cv2
import mediapipe as mp
import time


class ObjectDetector:
    def __init__(self):
        # MediaPipe çözümlerini başlat
        self.mp_hands = mp.solutions.hands
        self.mp_pose = mp.solutions.pose
        self.mp_face = mp.solutions.face_detection
        self.mp_face_mesh = mp.solutions.face_mesh
        self.mp_drawing = mp.solutions.drawing_utils
        self.mp_drawing_styles = mp.solutions.drawing_styles

        # Modeller
        self.hands = self.mp_hands.Hands(
            max_num_hands=2,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5
        )

        self.pose = self.mp_pose.Pose(
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5
        )

        self.face_detection = self.mp_face.FaceDetection(
            min_detection_confidence=0.5
        )

        self.face_mesh = self.mp_face_mesh.FaceMesh(
            max_num_faces=1,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5
        )

        self.fps = 0
        self.detection_results = {
            'objects': [],
            'hands': 0,
            'faces': 0,
            'pose_detected': False,
            'fingers': 0,
            'gesture': None,
        }

    def _count_fingers(self, landmarks_px, handedness_label="Right"):
        """Count extended fingers using pixel landmarks and handedness.
        landmarks_px: list of (x, y) in pixels for 21 landmarks
        handedness_label: "Right" or "Left"
        Returns count [0..10] for two hands caller-summed, here one hand count.
        """
        # Indices based on MediaPipe Hands
        THUMB_TIP = 4
        THUMB_IP = 3
        # Tip/PIP pairs for other fingers
        pairs = [(8, 6), (12, 10), (16, 14), (20, 18)]

        finger_count = 0
        # Thumb: check horizontal direction depending on handedness
        thumb_tip_x, thumb_ip_x = landmarks_px[THUMB_TIP][0], landmarks_px[THUMB_IP][0]
        if handedness_label == "Right":
            if thumb_tip_x > thumb_ip_x:
                finger_count += 1
        else:
            if thumb_tip_x < thumb_ip_x:
                finger_count += 1

        # Other four fingers: tip is above PIP (smaller y) when extended
        for tip_idx, pip_idx in pairs:
            tip_y, pip_y = landmarks_px[tip_idx][1], landmarks_px[pip_idx][1]
            if tip_y < pip_y:
                finger_count += 1

        return finger_count

    def _recognize_rps(self, fingers_state, two_finger_indices=(1, 2)):
        """Recognize Rock/Paper/Scissors gesture from fingers_state list.
        fingers_state: list of 5 ints [thumb, index, middle, ring, pinky]
        Returns a string: "Tas" (Rock), "Kagit" (Paper), "Makas" (Scissors) or None.
        """
        total = sum(fingers_state)
        # Rock: 0 or 1 finger up
        if total <= 1:
            return "Tas"
        # Scissors: exactly index and middle up
        if total == 2 and fingers_state[1] == 1 and fingers_state[2] == 1:
            return "Makas"
        # Paper: 4 or 5 up
        if total >= 4:
            return "Kagit"
        return None

    def detect_objects(self, frame):
        """Frame'deki nesneleri, elleri, yüzleri ve pozları tespit et"""
        try:
            start_time = time.time()

            # Convert BGR to RGB
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            rgb_frame.flags.writeable = False

            # Process hands, pose, face detection and face mesh
            hands_results = self.hands.process(rgb_frame)
            pose_results = self.pose.process(rgb_frame)
            face_results = self.face_detection.process(rgb_frame)
            face_mesh_results = self.face_mesh.process(rgb_frame)

            # Convert back to BGR for drawing
            rgb_frame.flags.writeable = True
            frame = cv2.cvtColor(rgb_frame, cv2.COLOR_RGB2BGR)

            # Reset detection results
            self.detection_results = {
                'objects': [],
                'hands': 0,
                'faces': 0,
                'pose_detected': False,
                'fingers': 0,
                'gesture': None,
            }

            # Draw hands and count
            if hands_results.multi_hand_landmarks:
                self.detection_results['hands'] = len(hands_results.multi_hand_landmarks)
                fingers_total = 0
                recognized_gesture = None
                h, w, _ = frame.shape
                # Iterate with handedness labels when available
                handedness_list = getattr(hands_results, 'multi_handedness', [])
                for idx, hand_landmarks in enumerate(hands_results.multi_hand_landmarks):
                    self.mp_drawing.draw_landmarks(
                        frame, hand_landmarks, self.mp_hands.HAND_CONNECTIONS,
                        self.mp_drawing_styles.get_default_hand_landmarks_style(),
                        self.mp_drawing_styles.get_default_hand_connections_style()
                    )
                    landmarks_px = [(int(lm.x * w), int(lm.y * h)) for lm in hand_landmarks.landmark]
                    hand_label = None
                    try:
                        hand_label = handedness_list[idx].classification[0].label
                    except Exception:
                        hand_label = "Right"

                    # Per-finger state vector for gesture recognition
                    # Thumb state as horizontal test
                    thumb_up = 1 if ((hand_label == "Right" and landmarks_px[4][0] > landmarks_px[3][0]) or
                                       (hand_label != "Right" and landmarks_px[4][0] < landmarks_px[3][0])) else 0
                    # Index, middle, ring, pinky: vertical
                    other_states = []
                    for tip, pip in [(8, 6), (12, 10), (16, 14), (20, 18)]:
                        other_states.append(1 if landmarks_px[tip][1] < landmarks_px[pip][1] else 0)
                    fingers_state = [thumb_up] + other_states

                    fingers_count = self._count_fingers(landmarks_px, hand_label)
                    fingers_total += fingers_count

                    # Use the first hand's gesture for simplicity
                    if recognized_gesture is None:
                        recognized_gesture = self._recognize_rps(fingers_state)

                self.detection_results['fingers'] = fingers_total
                self.detection_results['gesture'] = recognized_gesture

            # Draw pose
            if pose_results.pose_landmarks:
                self.detection_results['pose_detected'] = True
                self.mp_drawing.draw_landmarks(
                    frame, pose_results.pose_landmarks, self.mp_pose.POSE_CONNECTIONS,
                    self.mp_drawing_styles.get_default_pose_landmarks_style()
                )

            # Draw face detection
            if face_results.detections:
                self.detection_results['faces'] = len(face_results.detections)
                for detection in face_results.detections:
                    self.mp_drawing.draw_detection(frame, detection)

            # Draw face mesh
            if face_mesh_results.multi_face_landmarks:
                for face_landmarks in face_mesh_results.multi_face_landmarks:
                    self.mp_drawing.draw_landmarks(
                        image=frame,
                        landmark_list=face_landmarks,
                        connections=self.mp_face_mesh.FACEMESH_TESSELATION,
                        landmark_drawing_spec=None,
                        connection_drawing_spec=self.mp_drawing_styles
                        .get_default_face_mesh_tesselation_style()
                    )

            # FPS calculation
            self.fps = 1 / (time.time() - start_time)
            # [KAPALI] Fps'i ekrana yazdır
            #cv2.putText(frame, f'FPS: {int(self.fps)}', (20, 70),
                        #cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0, 255, 0), 2)

            # [KAPALI] Bilgileri ekrana yazdır
            #cv2.putText(frame, f'Eller: {self.detection_results["hands"]}', (20, 110),
                        #cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            #cv2.putText(frame, f'Yuzler: {self.detection_results["faces"]}', (20, 140),
                        #cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            #cv2.putText(frame, f'Poz: {"Var" if self.detection_results["pose_detected"] else "Yok"}', (20, 170),
                        #cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

            return frame, self.detection_results

        except Exception as e:
            print(f"Nesne tespit hatası: {e}")
            return frame, self.detection_results

    def get_detection_results(self):
        """Tespit sonuçlarını döndür"""
        return self.detection_results

    def get_fps(self):
        """Mevcut FPS'i döndür"""
        return self.fps
