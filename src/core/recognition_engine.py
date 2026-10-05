import cv2
import joblib
import numpy as np
import sqlite3
import os
import time
import math
from datetime import datetime

from mtcnn import MTCNN
from keras_facenet import FaceNet
from student_info import STUDENT_INFO
from attendance_manager import mark_attendance

try:
    from core.liveness_detector import BlinkDetector
except ImportError:
    from liveness_detector import BlinkDetector

# ============================================================
# CONFIGURABLE PIPELINE CONSTANTS (GROUNDED IN EMPIRICAL AUDIT)
# ============================================================
DEFAULT_DETECTION_CONFIDENCE = 0.75  # MTCNN confidence threshold
MIN_FACE_WIDTH = 40                  # Minimum face width in pixels
MIN_FACE_HEIGHT = 40                 # Minimum face height in pixels
DUPLICATE_IOU_THRESHOLD = 0.45       # IoU above which overlapping candidate boxes are suppressed
MAX_TARGET_FACES = 4                 # Maximum simultaneous targets

# Crop Margin & Preprocessing
# Bounded collision margin keeps live crop aligned with reference embeddings (which used MTCNN tight crop)
DEFAULT_MARGIN_RATIO = 0.02          # Subtle 2% margin with inter-face collision bounding
DEFAULT_DETECTOR_SCALE = 0.50        # Scaled detector input (320x240) provides ~2x MTCNN speedup without accuracy loss

# Quality Gating (calibrated against measured dataset percentiles)
MIN_SHARPNESS_LAPLACIAN = 4.0        # Laplacian variance threshold to detect heavy blur
MIN_MEAN_BRIGHTNESS = 18.0           # Reject near pitch-black frames
MAX_MEAN_BRIGHTNESS = 248.0          # Reject severe overexposure / washout
MIN_CONTRAST_STD = 8.0               # Reject featureless / flat crops

# Recognition & Matching Security
STRICT_RECOGNITION_THRESHOLD = 0.65  # Intentional strict L2 recognition threshold
DEFAULT_AMBIGUITY_MARGIN = 0.04      # Minimum separation between best and 2nd-best candidate identities
CONFIRMATION_FRAMES = 5              # Temporal confirmation frames required before marking attendance

# Liveness & Tracking
DEFAULT_EAR_THRESHOLD = 0.20         # Eye Aspect Ratio threshold
DEFAULT_CONSECUTIVE_BLINK_FRAMES = 1 # Consecutive frames closed for blink
LIVENESS_EXPIRATION_SECONDS = 60.0   # Live status TTL before re-verification
MAX_TRACK_MISSES = 10                # Frames missed before tracking state is purged


class TrackedFace:
    """Maintains persistent state for a physical face target across frames."""
    def __init__(self, track_id, box):
        self.track_id = track_id
        self.box = box  # (x, y, w, h)
        self.consecutive_misses = 0
        self.temporal_frames = 0
        self.last_identity = "Unknown"
        self.last_seen = time.time()


class SimpleFaceTracker:
    """Lightweight spatial tracker associating detections across frames using IoU and centroid proximity."""
    def __init__(self, iou_thresh=0.25, max_misses=MAX_TRACK_MISSES):
        self.iou_thresh = iou_thresh
        self.max_misses = max_misses
        self.next_track_id = 1
        self.tracks = {}  # track_id -> TrackedFace

    def update(self, detected_boxes):
        now = time.time()
        matched = {}
        used_tracks = set()

        for d_idx, d_box in enumerate(detected_boxes):
            dx, dy, dw, dh = d_box
            dcx, dcy = dx + dw / 2.0, dy + dh / 2.0
            best_tid = None
            best_score = -1.0

            for tid, track in self.tracks.items():
                if tid in used_tracks:
                    continue
                tx, ty, tw, th = track.box
                tcx, tcy = tx + tw / 2.0, ty + th / 2.0

                xA = max(dx, tx)
                yA = max(dy, ty)
                xB = min(dx + dw, tx + tw)
                yB = min(dy + dh, ty + th)
                inter = max(0, xB - xA) * max(0, yB - yA)
                union = dw * dh + tw * th - inter
                iou = inter / union if union > 0 else 0.0

                dist = math.hypot(dcx - tcx, dcy - tcy)
                if iou >= self.iou_thresh or dist <= min(dw, dh) * 0.75:
                    score = iou * 100.0 - dist
                    if score > best_score:
                        best_score = score
                        best_tid = tid

            if best_tid is not None:
                matched[d_idx] = best_tid
                used_tracks.add(best_tid)
                self.tracks[best_tid].box = d_box
                self.tracks[best_tid].consecutive_misses = 0
                self.tracks[best_tid].last_seen = now

        for d_idx, d_box in enumerate(detected_boxes):
            if d_idx not in matched:
                new_tid = self.next_track_id
                self.next_track_id += 1
                new_track = TrackedFace(new_tid, d_box)
                self.tracks[new_tid] = new_track
                matched[d_idx] = new_tid

        dead_tracks = []
        for tid, track in self.tracks.items():
            if tid not in used_tracks and tid not in matched.values():
                track.consecutive_misses += 1
                if track.consecutive_misses > self.max_misses:
                    dead_tracks.append(tid)

        for tid in dead_tracks:
            del self.tracks[tid]

        results = []
        for d_idx, d_box in enumerate(detected_boxes):
            tid = matched[d_idx]
            results.append((self.tracks[tid], d_box))

        return results


def compute_box_iou(boxA, boxB):
    xA = max(boxA[0], boxB[0])
    yA = max(boxA[1], boxB[1])
    xB = min(boxA[0] + boxA[2], boxB[0] + boxB[2])
    yB = min(boxA[1] + boxA[3], boxB[1] + boxB[3])
    inter = max(0, xB - xA) * max(0, yB - yA)
    areaA = boxA[2] * boxA[3]
    areaB = boxB[2] * boxB[3]
    union = areaA + areaB - inter
    return inter / union if union > 0 else 0.0


def deduplicate_detections(detections, iou_thresh=DUPLICATE_IOU_THRESHOLD):
    if len(detections) <= 1:
        return detections
    sorted_dets = sorted(detections, key=lambda d: d.get("confidence", 0.0), reverse=True)
    kept = []
    for d in sorted_dets:
        box = d["box"]
        is_dup = False
        for k in kept:
            if compute_box_iou(box, k["box"]) >= iou_thresh:
                is_dup = True
                break
        if not is_dup:
            kept.append(d)
    return kept


def sanitize_and_crop_face(frame_rgb, box, all_boxes, margin_ratio=DEFAULT_MARGIN_RATIO):
    fh, fw = frame_rgb.shape[:2]
    x, y, w, h = box
    x = max(0, min(x, fw - 1))
    y = max(0, min(y, fh - 1))
    w = max(1, min(w, fw - x))
    h = max(1, min(h, fh - y))

    mx = int(w * margin_ratio)
    my = int(h * margin_ratio)
    x1 = max(0, x - mx)
    y1 = max(0, y - my)
    x2 = min(fw, x + w + mx)
    y2 = min(fh, y + h + my)

    # Collision-aware clipping against all neighboring boxes
    for other in all_boxes:
        if other == box:
            continue
        ox, oy, ow, oh = other
        if ox >= x + w and (oy < y + h and oy + oh > y):
            x2 = min(x2, ox)
        if ox + ow <= x and (oy < y + h and oy + oh > y):
            x1 = max(x1, ox + ow)
        if oy >= y + h and (ox < x + w and ox + ow > x):
            y2 = min(y2, oy)
        if oy + oh <= y and (ox < x + w and ox + ow > x):
            y1 = max(y1, oy + oh)

    raw_crop = frame_rgb[y1:y2, x1:x2]
    return (x, y, w, h), raw_crop


def evaluate_crop_quality(crop):
    if crop is None or crop.size == 0:
        return False, 0.0, "INVALID CROP"
    h, w = crop.shape[:2]
    if w < MIN_FACE_WIDTH or h < MIN_FACE_HEIGHT:
        return False, 30.0, "FACE TOO SMALL"

    try:
        gray = cv2.cvtColor(crop, cv2.COLOR_RGB2GRAY)
        sharpness = float(cv2.Laplacian(gray, cv2.CV_64F).var())
        mean_bright = float(np.mean(gray))
        contrast = float(np.std(gray))

        if sharpness < MIN_SHARPNESS_LAPLACIAN:
            return False, 35.0, "BLUR DETECTED"
        if mean_bright < MIN_MEAN_BRIGHTNESS:
            return False, 25.0, "POOR LIGHTING"
        if mean_bright > MAX_MEAN_BRIGHTNESS:
            return False, 25.0, "OVEREXPOSED"
        if contrast < MIN_CONTRAST_STD:
            return False, 30.0, "LOW CONTRAST"

        res_factor = min(1.0, (w * h) / (160.0 * 160.0))
        sharp_factor = min(1.0, sharpness / 50.0)
        quality_score = min(99.4, 40.0 + 30.0 * res_factor + 29.4 * sharp_factor)
        return True, quality_score, "QUALITY OK"
    except Exception:
        return False, 0.0, "QUALITY CHECK ERROR"


class RecognitionEngine:

    def __init__(self):
        print("=" * 60)
        print("Loading Enterprise-grade Identity Intelligence Platform...")
        print("=" * 60)

        self.detector = MTCNN()
        self.embedder = FaceNet()

        try:
            emb_data = joblib.load("models/student_embeddings.pkl")
            self.db_embeddings = np.array(emb_data["embeddings"], dtype=np.float32)
            self.db_labels = np.array(emb_data["labels"])
            norms = np.linalg.norm(self.db_embeddings, axis=1, keepdims=True)
            self.db_embeddings = self.db_embeddings / np.maximum(norms, 1e-12)
            print(f"Engine Online: Loaded {len(self.db_labels)} reference face prints.")
        except Exception as e:
            self.db_embeddings = None
            self.db_labels = None
            print(f"Warning: Could not load reference embeddings: {e}")

        self.liveness = BlinkDetector(ear_threshold=DEFAULT_EAR_THRESHOLD, consecutive_frames=DEFAULT_CONSECUTIVE_BLINK_FRAMES)
        self.live_students = set()
        self.tracker = SimpleFaceTracker(iou_thresh=0.25, max_misses=MAX_TRACK_MISSES)

        self.cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
        if not self.cap.isOpened():
            self.cap = cv2.VideoCapture(0)

        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

        import json
        try:
            if os.path.exists("config.json"):
                with open("config.json", "r") as f:
                    config = json.load(f)
                    self.face_detection_threshold = config.get("detection_confidence", 75) / 100.0
        except Exception:
            self.face_detection_threshold = DEFAULT_DETECTION_CONFIDENCE
        self.detector_scale = DEFAULT_DETECTOR_SCALE

        self.process_every_n_frames = 3
        self.frame_counter = 0
        self.confirmation_frames = CONFIRMATION_FRAMES
        self.recognition_counter = {}
        self.attendance_marked = set()

        self.current_faces = []
        self.telemetry = {"detect_ms": 0, "embed_ms": 0, "match_ms": 0, "total_ms": 0, "fps": 0}

        self.session_threats = []
        self.threat_counter = 1

        self.base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        self.threat_dir = os.path.join(self.base_dir, "reports", "threat_captures")
        os.makedirs(self.threat_dir, exist_ok=True)
        self.threat_cooldown = 0

        self.last_name = "Unknown"
        self.last_student_name = "Unknown"
        self.last_department = "-"
        self.last_year = "-"
        self.last_confidence = 0.0
        self.last_status = "WAITING..."
        self.last_box = None
        self.unknown_tolerance = 12
        self.unknown_counter = 0

    def start(self):
        if not self.cap.isOpened():
            return
        while True:
            ret, frame = self.cap.read()
            if not ret:
                break
            frame = cv2.flip(frame, 1)
            self.frame_counter += 1
            if self.frame_counter % self.process_every_n_frames == 0:
                self.process_frame(frame)
            key = cv2.waitKey(1) & 0xFF
            if key == 27 or key == ord("q"):
                break
        self.cap.release()

    def process_frame(self, frame):
        t_start_total = time.time()
        if frame is None or frame.size == 0:
            self.reset_display()
            return

        # 1. Detection Phase (Standard RGB with configurable detector scaling)
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        t_det = time.time()
        try:
            if self.detector_scale < 0.99:
                det_input = cv2.resize(rgb, (0, 0), fx=self.detector_scale, fy=self.detector_scale, interpolation=cv2.INTER_LINEAR)
                scale_inv = 1.0 / self.detector_scale
                raw_faces_scaled = self.detector.detect_faces(det_input)
                raw_faces = []
                for rf in raw_faces_scaled:
                    rf_box = rf.get("box", [0, 0, 0, 0])
                    scaled_box = [
                        int(round(rf_box[0] * scale_inv)),
                        int(round(rf_box[1] * scale_inv)),
                        int(round(rf_box[2] * scale_inv)),
                        int(round(rf_box[3] * scale_inv))
                    ]
                    rf_copy = dict(rf)
                    rf_copy["box"] = scaled_box
                    if "keypoints" in rf:
                        scaled_kp = {}
                        for k, (kx, ky) in rf["keypoints"].items():
                            scaled_kp[k] = (int(round(kx * scale_inv)), int(round(ky * scale_inv)))
                        rf_copy["keypoints"] = scaled_kp
                    raw_faces.append(rf_copy)
            else:
                raw_faces = self.detector.detect_faces(rgb)
        except Exception:
            raw_faces = []
        det_ms = (time.time() - t_det) * 1000

        # Filter by confidence and deduplicate overlapping boxes
        valid_faces = [f for f in raw_faces if f.get("confidence", 0) >= self.face_detection_threshold]
        valid_faces = deduplicate_detections(valid_faces, iou_thresh=DUPLICATE_IOU_THRESHOLD)

        # Deterministic spatial ordering: left-to-right (by x coordinate)
        valid_faces = sorted(valid_faces, key=lambda item: item["box"][0])[:MAX_TARGET_FACES]

        if not valid_faces:
            self.current_faces = []
            self.unknown_counter += 1
            if self.unknown_counter > self.unknown_tolerance:
                self.reset_display()
            self._update_telemetry(det_ms, 0, 0, t_start_total)
            return

        self.unknown_counter = 0

        # 2. Tracking Phase
        raw_boxes = [f["box"] for f in valid_faces]
        tracked_pairs = self.tracker.update(raw_boxes)

        # 3. Independent Multi-Target Liveness Extraction (Single FaceMesh pass)
        box_coords = [b for (_, b) in tracked_pairs]
        box_ears = self.liveness.extract_face_ears(frame, box_coords)

        # 4. Per-Face Cropping, Collision Bounding & Quality Gating
        prepared_faces = []
        crops_to_embed = []
        crops_index_map = []

        for i, (track, raw_box) in enumerate(tracked_pairs):
            try:
                sanitized_box, raw_crop = sanitize_and_crop_face(rgb, raw_box, box_coords, margin_ratio=DEFAULT_MARGIN_RATIO)
                is_quality_ok, quality_score, quality_reason = evaluate_crop_quality(raw_crop)

                rec = {
                    "index": i,
                    "track": track,
                    "box": sanitized_box,
                    "raw_crop": raw_crop,
                    "is_quality_ok": is_quality_ok,
                    "quality_score": quality_score,
                    "quality_reason": quality_reason,
                    "ear": box_ears.get(i),
                    "embedding": None
                }
                prepared_faces.append(rec)

                if is_quality_ok and raw_crop.size > 0:
                    # Independent per-crop lighting normalization (only if crop is genuinely dim)
                    crop_for_embed = raw_crop
                    try:
                        gray_crop = cv2.cvtColor(raw_crop, cv2.COLOR_RGB2GRAY)
                        if np.mean(gray_crop) < 60.0:
                            lab_c = cv2.cvtColor(raw_crop, cv2.COLOR_RGB2LAB)
                            l_c, a_c, b_c = cv2.split(lab_c)
                            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(4, 4))
                            crop_for_embed = cv2.cvtColor(cv2.merge((clahe.apply(l_c), a_c, b_c)), cv2.COLOR_LAB2RGB)
                    except Exception:
                        crop_for_embed = raw_crop

                    resized_crop = cv2.resize(crop_for_embed, (160, 160), interpolation=cv2.INTER_LINEAR)
                    crops_to_embed.append(resized_crop)
                    crops_index_map.append(i)

            except Exception:
                # Per-face isolation for cropping errors
                rec = {
                    "index": i,
                    "track": track,
                    "box": raw_box,
                    "raw_crop": None,
                    "is_quality_ok": False,
                    "quality_score": 0.0,
                    "quality_reason": "CROP ERROR",
                    "ear": None,
                    "embedding": None
                }
                prepared_faces.append(rec)

        # 5. Batched FaceNet Inference with Safe Per-Crop Fallback
        t_emb = time.time()
        if crops_to_embed:
            try:
                raw_embeddings = self.embedder.embeddings(crops_to_embed)
                for crop_idx, mapped_face_idx in enumerate(crops_index_map):
                    prepared_faces[mapped_face_idx]["embedding"] = raw_embeddings[crop_idx]
            except Exception:
                # Fallback to serial inference so one corrupted crop does not drop other faces
                for crop_idx, mapped_face_idx in enumerate(crops_index_map):
                    try:
                        single_emb = self.embedder.embeddings([crops_to_embed[crop_idx]])[0]
                        prepared_faces[mapped_face_idx]["embedding"] = single_emb
                    except Exception:
                        prepared_faces[mapped_face_idx]["embedding"] = None
        emb_ms = (time.time() - t_emb) * 1000

        # 6. Matching & Candidate Identification with Ambiguity Guard
        t_match = time.time()
        candidate_matches = []
        self._faces_buffer = []

        for face_rec in prepared_faces:
            emb = face_rec["embedding"]
            name, conf, best_dist = "Unknown", 0.0, 1.0
            second_dist, second_name = 999.0, "None"
            status = "WAITING..."

            if not face_rec["is_quality_ok"]:
                status = face_rec["quality_reason"]
            elif emb is None or np.isnan(emb).any() or np.isinf(emb).any():
                status = "EMBEDDING ERROR"
            elif self.db_embeddings is not None and len(self.db_embeddings) > 0:
                norm = np.linalg.norm(emb)
                if norm > 1e-6:
                    norm_emb = emb / norm
                    distances = np.linalg.norm(self.db_embeddings - norm_emb, axis=1)
                    min_idx = np.argmin(distances)
                    best_dist = float(distances[min_idx])
                    cand_id = str(self.db_labels[min_idx])

                    # Find second-best candidate belonging to a DIFFERENT student identity
                    other_mask = (self.db_labels != cand_id)
                    if np.any(other_mask):
                        other_dists = distances[other_mask]
                        min_other_idx = np.argmin(other_dists)
                        second_dist = float(other_dists[min_other_idx])
                        second_name = str(self.db_labels[other_mask][min_other_idx])

                    separation = second_dist - best_dist

                    # Strict enterprise thresholding (0.65) + Ambiguity Guard
                    if best_dist <= STRICT_RECOGNITION_THRESHOLD:
                        if separation < DEFAULT_AMBIGUITY_MARGIN:
                            name = "Unknown"
                            conf = max(0.0, 0.60 - (best_dist - (STRICT_RECOGNITION_THRESHOLD - DEFAULT_AMBIGUITY_MARGIN)))
                            status = "AMBIGUOUS"
                        else:
                            name = cand_id
                            conf = 0.99 - ((best_dist / STRICT_RECOGNITION_THRESHOLD) * 0.39)
                            status = "MATCH CANDIDATE"
                    else:
                        name = "Unknown"
                        conf = max(0.0, 0.60 - (best_dist - STRICT_RECOGNITION_THRESHOLD))
                        status = "DISTANCE EXCEEDED"
            else:
                status = "DATABASE UNAVAILABLE"

            candidate_matches.append({
                "face_rec": face_rec,
                "name": name,
                "conf": conf,
                "best_dist": best_dist,
                "second_dist": second_dist,
                "second_name": second_name,
                "status": status
            })

        # 7. Intra-Frame Duplicate Identity Conflict Suppression
        # If two faces match the same student, assign it only to the face with the lowest distance
        claimed_identities = {}
        # Sort candidate matches by best_dist ascending
        sorted_indices = sorted(range(len(candidate_matches)), key=lambda k: candidate_matches[k]["best_dist"])
        for k in sorted_indices:
            cand = candidate_matches[k]
            cand_name = cand["name"]
            if cand_name != "Unknown":
                if cand_name in claimed_identities:
                    # Duplicate identity in same frame: mark as duplicate/review rather than guessing
                    cand["name"] = "Unknown"
                    cand["status"] = "DUPLICATE MATCH"
                else:
                    claimed_identities[cand_name] = k

        # 8. Independent Per-Face Liveness & Attendance Decision
        for cand in candidate_matches:
            face_rec = cand["face_rec"]
            track = face_rec["track"]
            x, y, w, h = face_rec["box"]
            quality_score = face_rec["quality_score"]
            raw_crop = face_rec["raw_crop"]
            name = cand["name"]
            conf = cand["conf"]
            min_dist = cand["best_dist"]
            status = cand["status"]
            ear = face_rec["ear"]

            # Independent per-track liveness check
            is_live, liveness_status, _ = self.liveness.update_track_liveness(
                track.track_id, ear, ttl_seconds=LIVENESS_EXPIRATION_SECONDS
            )

            student_name, dept, year = "Unknown", "-", "-"

            if name != "Unknown":
                student = STUDENT_INFO.get(name)
                student_name = student["name"] if student else "Unknown"
                dept = student["department"] if student else "-"
                year = student["year"] if student else "-"

                # ATTENDANCE SECURITY GATE:
                # 1. Quality Valid
                # 2. Liveness Valid (Must be independently confirmed live via blink)
                # 3. Distance <= 0.65 (satisfied)
                # 4. Temporal Confirmation (5 frames)
                if not is_live:
                    status = liveness_status  # e.g., "PLEASE BLINK" or "EYES CLOSED"
                    # Liveness pending: DO NOT increment attendance temporal counter
                else:
                    self.live_students.add(name)
                    track.temporal_frames += 1
                    temporal_count = track.temporal_frames

                    if temporal_count >= self.confirmation_frames and name not in self.attendance_marked:
                        try:
                            mark_attendance(name, conf * 100)
                            self.attendance_marked.add(name)
                            status = "VERIFIED"
                        except Exception:
                            status = "DATABASE ERROR"
                    elif name in self.attendance_marked:
                        status = "ALREADY LOGGED"
                    else:
                        status = "TEMPORAL VERIFY"
            else:
                # Unknown / Threat face handling
                threat_id = None
                emb = face_rec["embedding"]
                if emb is not None and self.session_threats:
                    try:
                        norm_emb = emb / max(np.linalg.norm(emb), 1e-12)
                        threat_embs = np.array([t["embedding"] for t in self.session_threats])
                        t_distances = np.linalg.norm(threat_embs - norm_emb, axis=1)
                        t_min_idx = np.argmin(t_distances)
                        if t_distances[t_min_idx] <= STRICT_RECOGNITION_THRESHOLD:
                            threat_id = self.session_threats[t_min_idx]["id"]
                    except Exception:
                        pass

                if not threat_id:
                    threat_id = f"GHOST-{self.threat_counter:03d}"
                    self.threat_counter += 1
                    if emb is not None:
                        norm_emb = emb / max(np.linalg.norm(emb), 1e-12)
                        self.session_threats.append({"id": threat_id, "embedding": norm_emb, "captured": False})

                student_name = threat_id
                if status in ["WAITING...", "MATCH CANDIDATE", "DISTANCE EXCEEDED"]:
                    status = "THREAT DETECTED"

                is_new_threat = False
                for t in self.session_threats:
                    if t["id"] == threat_id and not t["captured"]:
                        is_new_threat = True
                        t["captured"] = True
                        break

                if is_new_threat and getattr(self, 'threat_cooldown', 0) <= 0 and raw_crop is not None and raw_crop.size > 0:
                    try:
                        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
                        filename = f"{threat_id}_{ts}.jpg"
                        cv2.imwrite(os.path.join(self.threat_dir, filename), cv2.cvtColor(raw_crop, cv2.COLOR_RGB2BGR))

                        conn = sqlite3.connect(os.path.join(self.base_dir, "database", "attendance.db"))
                        cursor = conn.cursor()
                        cursor.execute("CREATE TABLE IF NOT EXISTS audit_logs (timestamp TEXT, event_type TEXT, description TEXT)")
                        cursor.execute("INSERT INTO audit_logs (timestamp, event_type, description) VALUES (?, ?, ?)",
                                      (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "INTRUDER_CAPTURED", f"UNAUTHORIZED ENTITY [{threat_id}]. Image captured: {filename}"))
                        conn.commit()
                        conn.close()
                    except Exception:
                        pass

            self._store_face(
                index=face_rec["index"], x=x, y=y, w=w, h=h,
                name=name, student_name=student_name, dept=dept, year=year,
                conf=conf, status=status, dist=min_dist,
                temporal=min(5, track.temporal_frames), quality=quality_score
            )

        if hasattr(self, '_faces_buffer'):
            self.current_faces = list(self._faces_buffer)

        match_ms = (time.time() - t_match) * 1000
        self._update_telemetry(det_ms, emb_ms, match_ms, t_start_total)

    def _update_telemetry(self, det, emb, match, start_time):
        tot = (time.time() - start_time) * 1000
        fps = 1000 / tot if tot > 0 else 0

        if not hasattr(self, 'smoothed_tel'):
            self.smoothed_tel = {"detect_ms": det, "embed_ms": emb, "match_ms": match, "total_ms": tot, "fps": fps}

        alpha = 0.15
        self.smoothed_tel["detect_ms"] = (alpha * det) + ((1 - alpha) * self.smoothed_tel["detect_ms"])
        self.smoothed_tel["embed_ms"] = (alpha * emb) + ((1 - alpha) * self.smoothed_tel["embed_ms"])
        self.smoothed_tel["match_ms"] = (alpha * match) + ((1 - alpha) * self.smoothed_tel["match_ms"])
        self.smoothed_tel["total_ms"] = (alpha * tot) + ((1 - alpha) * self.smoothed_tel["total_ms"])
        self.smoothed_tel["fps"] = (alpha * fps) + ((1 - alpha) * self.smoothed_tel["fps"])

        self.telemetry = self.smoothed_tel

    def _store_face(self, index, x, y, w, h, name, student_name, dept, year, conf, status, dist, temporal, quality):
        face_record = {
            "box": (x, y, w, h), "name": name, "student_name": student_name, "dept": dept, "year": year,
            "confidence": conf, "status": status, "distance": dist, "temporal": temporal, "quality": quality
        }
        if not hasattr(self, '_faces_buffer'):
            self._faces_buffer = []
        self._faces_buffer.append(face_record)
        if index == 0:
            self.last_name = name
            self.last_student_name = student_name
            self.last_department = dept
            self.last_year = year
            self.last_confidence = conf
            self.last_status = status
            self.last_box = (x, y, w, h)

    def reset_display(self):
        self.last_name = "Unknown"
        self.last_student_name = "Unknown"
        self.last_department = "-"
        self.last_year = "-"
        self.last_confidence = 0.0
        self.last_status = "WAITING..."
        self.last_box = None
        self.current_faces = []
        self.recognition_counter.clear()
        self.unknown_counter = 0

    def draw_interface(self, frame):
        pass