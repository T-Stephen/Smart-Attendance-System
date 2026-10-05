import cv2
import mediapipe as mp
import math
import time

class BlinkDetector:
    def __init__(self, ear_threshold=0.20, consecutive_frames=2):
        """
        Initializes the Anti-Spoofing Blink Detector.
        ear_threshold: The Eye Aspect Ratio below which an eye is considered closed.
        consecutive_frames: How many frames the eye must be closed to count as a deliberate blink.
        """
        self.mp_face_mesh = mp.solutions.face_mesh
        # Initialize Mediapipe Face Mesh safely with support for up to 4 simultaneous targets
        self.face_mesh = self.mp_face_mesh.FaceMesh(
            max_num_faces=4,
            refine_landmarks=True,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5
        )
        self.ear_threshold = ear_threshold
        self.consecutive_frames = consecutive_frames
        self.blink_counter = 0
        self.blink_detected = False

        # Independent multi-target liveness tracking state:
        # track_id -> {"blink_counter": int, "blink_detected": bool, "live_confirmed": bool, "live_timestamp": float, "last_seen": float}
        self.track_states = {}

        # Exact facial landmark mapping for left and right eyes
        self.LEFT_EYE = [33, 160, 158, 133, 153, 144]
        self.RIGHT_EYE = [362, 385, 387, 263, 373, 380]

    def euclidean_distance(self, p1, p2):
        """Calculates distance between two 2D points safely."""
        return math.dist([p1.x, p1.y], [p2.x, p2.y])

    def calculate_ear(self, landmarks, eye_indices):
        """Calculates the Eye Aspect Ratio (EAR) using Euclidean math."""
        p1, p2, p3, p4, p5, p6 = [landmarks[i] for i in eye_indices]
        
        # Calculate vertical distances
        vertical1 = self.euclidean_distance(p2, p6)
        vertical2 = self.euclidean_distance(p3, p5)
        
        # Calculate horizontal distance
        horizontal = self.euclidean_distance(p1, p4)
        
        if horizontal == 0:
            return 0.0
            
        # Standard EAR formula
        ear = (vertical1 + vertical2) / (2.0 * horizontal)
        return ear

    def extract_face_ears(self, frame, face_boxes):
        """
        Processes frame once for up to 4 faces with spatial matching to bounding boxes.
        Returns a dictionary mapping {box_index: ear_value or None}.
        """
        box_ears = {i: None for i in range(len(face_boxes))}
        if not face_boxes or frame is None or frame.size == 0:
            return box_ears

        try:
            h, w = frame.shape[:2]
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = self.face_mesh.process(rgb_frame)

            if not results.multi_face_landmarks:
                return box_ears

            mesh_data = []
            for face_landmarks in results.multi_face_landmarks:
                landmarks = face_landmarks.landmark
                lear = self.calculate_ear(landmarks, self.LEFT_EYE)
                rear = self.calculate_ear(landmarks, self.RIGHT_EYE)
                avg_ear = (lear + rear) / 2.0
                
                # Face center from nose tip (1) and eye corners (33, 263)
                cx = (landmarks[1].x + landmarks[33].x + landmarks[263].x) / 3.0 * w
                cy = (landmarks[1].y + landmarks[33].y + landmarks[263].y) / 3.0 * h
                mesh_data.append({"center": (cx, cy), "ear": avg_ear})

            # Match each mesh center to the enclosing or nearest face box
            used_meshes = set()
            for box_idx, (bx, by, bw, bh) in enumerate(face_boxes):
                best_mesh_idx = None
                best_dist = float('inf')
                for m_idx, m in enumerate(mesh_data):
                    if m_idx in used_meshes:
                        continue
                    mx, my = m["center"]
                    # Check if center falls inside the bounding box (with slight 10% tolerance)
                    pad_w = bw * 0.1
                    pad_h = bh * 0.1
                    if (bx - pad_w <= mx <= bx + bw + pad_w) and (by - pad_h <= my <= by + bh + pad_h):
                        d = math.hypot(mx - (bx + bw / 2.0), my - (by + bh / 2.0))
                        if d < best_dist:
                            best_dist = d
                            best_mesh_idx = m_idx

                if best_mesh_idx is not None:
                    box_ears[box_idx] = mesh_data[best_mesh_idx]["ear"]
                    used_meshes.add(best_mesh_idx)

        except Exception:
            pass

        return box_ears

    def update_track_liveness(self, track_id, ear, ttl_seconds=60.0):
        """
        Updates the independent blink state machine for a specific track.
        Returns: (is_live: bool, status_str: str, ear: float or None)
        """
        now = time.time()
        if track_id not in self.track_states:
            self.track_states[track_id] = {
                "blink_counter": 0,
                "blink_detected": False,
                "live_confirmed": False,
                "live_timestamp": 0.0,
                "last_seen": now
            }

        state = self.track_states[track_id]
        state["last_seen"] = now

        # Enforce expiration of previously confirmed liveness
        if state["live_confirmed"] and (now - state["live_timestamp"] > ttl_seconds):
            state["live_confirmed"] = False
            state["blink_detected"] = False
            state["blink_counter"] = 0

        if ear is None:
            status = "VERIFIED LIVE" if state["live_confirmed"] else "PLEASE BLINK"
            return state["live_confirmed"], status, None

        if ear < self.ear_threshold:
            state["blink_counter"] += 1
            status = "EYES CLOSED"
        else:
            if state["blink_counter"] >= self.consecutive_frames:
                state["blink_detected"] = True
                state["live_confirmed"] = True
                state["live_timestamp"] = now
            state["blink_counter"] = 0
            status = "VERIFIED LIVE" if state["live_confirmed"] else "PLEASE BLINK"

        return state["live_confirmed"], status, ear

    def detect_blink(self, frame):
        """Processes a frame to detect if a live human blink occurred (legacy single-target)."""
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self.face_mesh.process(rgb_frame)

        if results.multi_face_landmarks:
            for face_landmarks in results.multi_face_landmarks:
                landmarks = face_landmarks.landmark
                left_ear = self.calculate_ear(landmarks, self.LEFT_EYE)
                right_ear = self.calculate_ear(landmarks, self.RIGHT_EYE)
                avg_ear = (left_ear + right_ear) / 2.0

                if avg_ear < self.ear_threshold:
                    self.blink_counter += 1
                else:
                    if self.blink_counter >= self.consecutive_frames:
                        self.blink_detected = True
                    self.blink_counter = 0

        return self.blink_detected

    def reset(self, track_id=None):
        """Resets the state after a successful spoof-check or when a track expires."""
        if track_id is not None:
            self.track_states.pop(track_id, None)
        else:
            self.blink_detected = False
            self.blink_counter = 0
            self.track_states.clear()