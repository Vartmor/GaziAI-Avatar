import cv2
import mediapipe as mp
import time


class ObjectDetector:
    def __init__(self, *, enable_pose=True, enable_face_detection=True, enable_face_mesh=True):
        # MediaPipe ??z?mlerini ba?lat
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
            min_tracking_confidence=0.5,
        )

        self.pose = self.mp_pose.Pose(
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5,
        ) if enable_pose else None

        self.face_detection = self.mp_face.FaceDetection(
            min_detection_confidence=0.5,
        ) if enable_face_detection else None

        self.face_mesh = self.mp_face_mesh.FaceMesh(
            max_num_faces=1,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5,
        ) if enable_face_mesh else None

        self.enable_pose = enable_pose
        self.enable_face_detection = enable_face_detection
        self.enable_face_mesh = enable_face_mesh

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
        """Count extended fingers using pixel landmarks and handedness."""
        thumb_tip_x, thumb_ip_x = landmarks_px[4][0], landmarks_px[3][0]
        finger_pairs = [(8, 6), (12, 10), (16, 14), (20, 18)]

        finger_count = 0
        if handedness_label == "Right":
            if thumb_tip_x > thumb_ip_x:
                finger_count += 1
        else:
            if thumb_tip_x < thumb_ip_x:
                finger_count += 1

        for tip_idx, pip_idx in finger_pairs:
            tip_y, pip_y = landmarks_px[tip_idx][1], landmarks_px[pip_idx][1]
            if tip_y < pip_y:
                finger_count += 1

        return finger_count

    def _recognize_rps(self, fingers_state):
        """Recognize Rock/Paper/Scissors gesture from finger state list."""
        total = sum(fingers_state)
        if total <= 1:
            return "Tas"
        if total == 2 and fingers_state[1] == 1 and fingers_state[2] == 1:
            return "Makas"
        if total >= 4:
            return "Kagit"
        return None

    def detect_objects(self, frame):
        """Frame'deki nesneleri, elleri, y?zleri ve pozlar? tespit et."""
        try:
            start_time = time.time()

            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            rgb_frame.flags.writeable = False

            hands_results = self.hands.process(rgb_frame) if self.hands else None
            pose_results = self.pose.process(rgb_frame) if self.pose else None
            face_results = self.face_detection.process(rgb_frame) if self.face_detection else None
            face_mesh_results = self.face_mesh.process(rgb_frame) if self.face_mesh else None

            rgb_frame.flags.writeable = True
            frame = cv2.cvtColor(rgb_frame, cv2.COLOR_RGB2BGR)

            self.detection_results = {
                'objects': [],
                'hands': 0,
                'faces': 0,
                'pose_detected': False,
                'fingers': 0,
                'gesture': None,
            }

            if hands_results and hands_results.multi_hand_landmarks:
                self.detection_results['hands'] = len(hands_results.multi_hand_landmarks)
                fingers_total = 0
                recognized_gesture = None
                h, w, _ = frame.shape
                handedness_list = getattr(hands_results, 'multi_handedness', [])

                for idx, hand_landmarks in enumerate(hands_results.multi_hand_landmarks):
                    self.mp_drawing.draw_landmarks(
                        frame,
                        hand_landmarks,
                        self.mp_hands.HAND_CONNECTIONS,
                        self.mp_drawing_styles.get_default_hand_landmarks_style(),
                        self.mp_drawing_styles.get_default_hand_connections_style(),
                    )

                    landmarks_px = [(int(lm.x * w), int(lm.y * h)) for lm in hand_landmarks.landmark]
                    try:
                        hand_label = handedness_list[idx].classification[0].label
                    except Exception:
                        hand_label = "Right"

                    thumb_up = 1 if ((hand_label == "Right" and landmarks_px[4][0] > landmarks_px[3][0]) or
                                      (hand_label != "Right" and landmarks_px[4][0] < landmarks_px[3][0])) else 0
                    other_states = [1 if landmarks_px[tip][1] < landmarks_px[pip][1] else 0
                                    for tip, pip in [(8, 6), (12, 10), (16, 14), (20, 18)]]
                    fingers_state = [thumb_up] + other_states

                    fingers_total += self._count_fingers(landmarks_px, hand_label)
                    if recognized_gesture is None:
                        recognized_gesture = self._recognize_rps(fingers_state)

                self.detection_results['fingers'] = fingers_total
                self.detection_results['gesture'] = recognized_gesture

            if pose_results and pose_results.pose_landmarks:
                self.detection_results['pose_detected'] = True
                self.mp_drawing.draw_landmarks(
                    frame,
                    pose_results.pose_landmarks,
                    self.mp_pose.POSE_CONNECTIONS,
                    self.mp_drawing_styles.get_default_pose_landmarks_style(),
                )

            if face_results and face_results.detections:
                self.detection_results['faces'] = len(face_results.detections)
                for detection in face_results.detections:
                    self.mp_drawing.draw_detection(frame, detection)

            if face_mesh_results and face_mesh_results.multi_face_landmarks:
                for face_landmarks in face_mesh_results.multi_face_landmarks:
                    self.mp_drawing.draw_landmarks(
                        image=frame,
                        landmark_list=face_landmarks,
                        connections=self.mp_face_mesh.FACEMESH_TESSELATION,
                        landmark_drawing_spec=None,
                        connection_drawing_spec=self.mp_drawing_styles.get_default_face_mesh_tesselation_style(),
                    )

            elapsed = max(time.time() - start_time, 1e-6)
            self.fps = 1.0 / elapsed

            return frame, self.detection_results

        except Exception as exc:
            print(f"Nesne tespit hatas?: {exc}")
            return frame, self.detection_results

    def get_detection_results(self):
        return self.detection_results

    def get_fps(self):
        return self.fps
