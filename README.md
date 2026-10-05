# Smart Campus AI Attendance System

An enterprise-grade, edge-deployable multi-face recognition and attendance intelligence platform engineered for academic institutions and campus facilities. The system integrates deep convolutional face detection, 512-dimensional metric embedding matching, single-pass facial mesh anti-spoofing, and multi-target tracking into an asynchronous, thread-decoupled Tkinter operations console.

---

## 1. Overview

Traditional single-subject attendance systems suffer from severe throughput bottlenecks when handling student arrival rushes at classroom doorways and access gates. The Smart Campus AI Attendance System resolves this challenge by providing concurrent multi-face tracking and recognition for up to **4 simultaneous targets** in real time, backed by strict mathematical distance gating, per-subject liveness verification, and cryptographic database transaction logging.

---

## 2. Key Capabilities

- **Multi-Target Detection:** Deep cascaded MTCNN detection operating with scaled-resolution optimization ($0.5\times$ input) to minimize CPU inference latency while maintaining small-face recall.
- **Metric Face Embeddings:** Inception-ResNet-v1 (FaceNet) extracting $L_2$-normalized 512-dimensional feature representations.
- **Strict Metric Matching:** Euclidean nearest-neighbor distance computation against registered student vector galleries.
- **Anti-Ambiguity Protection:** Enforces minimum mathematical separation between the closest identity candidate and competing candidates to prevent misidentification.
- **Greedy Identity Deduplication:** Prevents single identities from being simultaneously assigned to multiple physical subjects in the same video frame.
- **Multi-Target Facial Tracking:** Centroid distance and spatial IoU tracking preserving temporal identity continuity across frames.
- **Isolated Per-Face Liveness:** Single-pass MediaPipe FaceMesh computing independent Eye Aspect Ratio (EAR) state machines for each tracked individual, defeating static photo presentations.
- **Dynamic Quality & Contrast Gating:** Laplacian blur variance checks, luminance bounds gating, and selective LAB-space CLAHE illumination enhancement on underexposed faces.
- **Forensic Threat Monitoring:** Automated session clustering (`GHOST-XXX`) and forensic capture logging for unidentified individuals.
- **Asynchronous GUI Decoupling:** Main camera preview loop executes at $30\text{--}33\text{ FPS}$ on the primary UI thread while AI inference executes asynchronously in background worker threads.
- **Executive Reporting & Analytics:** Native Excel (`openpyxl`) and PDF (`reportlab`) export with historical attendance analytics.

---

## 3. Pipeline Architecture

```
                          [ Real-Time Video Stream (640x480 @ 30 FPS) ]
                                                │
                                                ▼
                                    [ Frame Downscale (0.5x) ]
                                                │
                                                ▼
                                    [ MTCNN Face Detection ]
                                                │
                                                ▼
                                 [ Spatial Deduplication (IoU >= 0.45) ]
                                                │
                                                ▼
                               [ Multi-Target Tracker (IoU + Centroid) ]
                                                │
                                                ▼
                         [ Collision-Safe Crop (Full-Res Pristine Canvas) ]
                                                │
                                                ▼
                       [ Quality Gating (Laplacian >= 4.0, 18 <= Mean <= 248) ]
                                                │
                                                ▼
                         [ Illumination Normalization (Selective CLAHE) ]
                                                │
                                                ▼
                                   [ Batched FaceNet (512-d) ]
                                                │
                                                ▼
                                 [ Euclidean Distance vs Gallery ]
                                                │
                   ┌────────────────────────────┴────────────────────────────┐
                   ▼                                                         ▼
       [ d1 > 0.65 or d2 - d1 < 0.04 ]                            [ d1 <= 0.65 and d2 - d1 >= 0.04 ]
                   │                                                         │
                   ▼                                                         ▼
         [ Flagged as UNKNOWN ]                                     [ Identity Verified ]
                   │                                                         │
                   ▼                                                         ▼
       [ Threat Clustering & Log ]                                [ Isolated Per-Track Liveness ]
                                                                             │
                                                                             ▼
                                                                 [ Temporal Confirmation (5 Frames) ]
                                                                             │
                                                                             ▼
                                                                [ Attendance Committed (DB & CSV) ]
```

---

## 4. Security Design & Calibration

The system prioritizes identity security and fraud prevention over superficial recognition throughput:

- **Strict Recognition Threshold ($d \le 0.65$):** Normalized 512-d FaceNet embeddings operate on an $L_2$ Euclidean metric. Matches with distance $> 0.65$ are rejected as unrecognized, preventing unauthorized access.
- **Ambiguity Separation Margin ($\Delta d \ge 0.04$):** Requires that the Euclidean distance between the best candidate identity and the second-closest *distinct* student candidate differs by at least $0.04$. Ambiguous candidates are flagged for security review.
- **Duplicate Spatial IoU Gate ($\text{IoU} \ge 0.45$):** Suppresses redundant multi-scale detection boxes around the same physical face.
- **Target Concurrency Cap ($\le 4\text{ Faces}$):** Binds peak computational load to four priority subjects sorted by bounding box area.
- **Temporal Confirmation ($\ge 5\text{ Consecutive Frames}$):** Requires 5 consecutive verified detections on an active track ID before committing attendance to the ledger.
- **Isolated Per-Track Liveness:** Passive Eye Aspect Ratio (EAR) state tracking isolates each face. If a static photograph is presented adjacent to a real blinking person, the photograph remains blocked at `BLINK REQUIRED` while the live student is confirmed.

> **Notice:** The system does not claim 100% accuracy or total resistance to sophisticated physical spoofing attacks (e.g., high-definition video playback with natural blinks or 3D synthetic masks).

---

## 5. Performance Telemetry

Empirical benchmarks measured on a standard multi-core x86_64 CPU workstation without GPU acceleration:

| Active Faces | MTCNN Detection | Batched FaceNet | Matching & Tracker | Total AI Latency | AI Inference FPS | Camera / UI FPS |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **1 Face** | $270.8\text{ ms}$ | $273.5\text{ ms}$ | $11.6\text{ ms}$ | $596.7\text{ ms}$ | **$1.9\text{ FPS}$** | **$30\text{--}33\text{ FPS}$** |
| **2 Faces** | $269.1\text{ ms}$ | $289.9\text{ ms}$ | $5.8\text{ ms}$ | $629.7\text{ ms}$ | **$1.8\text{ FPS}$** | **$30\text{--}33\text{ FPS}$** |
| **3 Faces** | $284.2\text{ ms}$ | $390.8\text{ ms}$ | $4.9\text{ ms}$ | $827.1\text{ ms}$ | **$1.4\text{ FPS}$** | **$30\text{--}33\text{ FPS}$** |
| **4 Faces** | $318.5\text{ ms}$ | $417.2\text{ ms}$ | $5.0\text{ ms}$ | $902.3\text{ ms}$ | **$1.3\text{ FPS}$** | **$30\text{--}33\text{ FPS}$** |

*Hardware Optimization Note:* Because video capture and UI rendering run on an asynchronous event loop decoupled from AI inference, the camera HUD brackets and video feed remain responsive at $30\text{+ FPS}$. Inference throughput can be accelerated to $\ge 30\text{ FPS}$ on GPU-enabled edge hardware using ONNX Runtime FP16, TensorRT, or OpenVINO.

---

## 6. Documented Limitations

1. **CPU Inference Latency:** Native CPU inference throughput is bounded between $1.3\text{ and }1.9\text{ FPS}$. This throughput is well-suited for stationary turnstiles and classroom doorways, but not for unconstrained high-speed transit gates.
2. **Pose Tolerance:** Moderate head turns ($\pm 15^\circ$ to $\pm 25^\circ$ yaw/pitch) are normalized by landmark alignment. Extreme profile angles ($> 35^\circ$) cause feature degradation and safe rejection.
3. **Lighting Extrema:** Frames with mean intensity below $18.0$ (near-pitch black) or contrast standard deviation below $8.0$ are gated out to prevent noise-based false positives.
4. **Passive Blink Liveness:** Eye Aspect Ratio verification prevents printed and digital 2D static photos, but does not prevent video replay attacks featuring pre-recorded blinks.
5. **Fixed Camera Interface:** Default video acquisition is bound to camera index `0` via DirectShow.

---

## 7. Installation & Setup

### Prerequisites
- Python 3.10 or 3.11 (64-bit)
- USB / Integrated Webcam

### Environment Configuration
```bash
# 1. Clone the repository
git clone https://github.com/your-username/smart-campus-ai-attendance.git
cd smart-campus-ai-attendance

# 2. Create and activate a clean virtual environment
python -m venv .venv

# On Windows:
.venv\Scripts\activate

# On Linux/macOS:
source .venv/bin/activate

# 3. Install verified production dependencies
pip install -r requirements.txt
```

### Database Initialization
New installations must initialize the local database schema prior to first execution:
```bash
# Windows PowerShell
python -c "import sqlite3, os; os.makedirs('database', exist_ok=True); conn = sqlite3.connect('database/attendance.db'); conn.executescript(open('database/schema.sql').read()); conn.close(); print('Database initialized cleanly.')"
```

---

## 8. Launching the System

Execute the official enterprise dashboard entry point:

```bash
python src/admin_dashboard.py
```

- **Default Administrative Access:** Default administrative credentials can be provisioned directly via the registration modal or database seed.
- **Navigation:**
  - **Live Face Recognition:** Real-time multi-target tracking, liveness evaluation, and automatic attendance commits.
  - **Student Database:** Search, filter, and inspect enrolled student profiles.
  - **Attendance Database:** Daily and historical attendance logs.
  - **Attendance Reports:** One-click export to formatted Excel spreadsheets and PDF documents.
  - **Security Operations Center (SOC):** Forensic audit logs and threat capture inspection.

---

## 9. Verification & Automated Test Suites

The repository contains three standardized validation suites in the `tests/` directory:

```bash
# 1. Run full 18-scenario multi-face pipeline suite
python tests/test_comprehensive_suite.py

# 2. Run GUI regression & tab transition suite
python tests/test_dashboard_regression.py

# 3. Run targeted UI color, atomic buffer, and teardown stress suite
python tests/test_targeted_maintenance.py
```

---

## 10. Repository Structure

```
smart-campus-ai-attendance/
├── .gitignore                          # Excludes credentials, biometric photos & runtime databases
├── README.md                           # Technical documentation & usage instructions
├── requirements.txt                    # Pinned Python dependencies
├── config.json                         # Operational vision configuration
├── database/
│   └── schema.sql                      # Sanitized DDL schema for clean deployment
├── docs/                               # Formal architectural documentation & audit reports
│   ├── Completed_Project_Technical_Audit.md
│   ├── Completed_Project_Technical_Audit.html
│   └── Completed_Project_Technical_Audit.pdf
├── models/
│   ├── student_embeddings.pkl          # Reference FaceNet embeddings (512-d gallery)
│   ├── student_label_encoder.pkl       # LabelEncoder mapping IDs to categorical targets
│   └── embeddings.pkl                  # Normalized reference vector collection
├── tests/                              # Automated integration & regression test suites
│   ├── test_comprehensive_suite.py
│   ├── test_dashboard_regression.py
│   └── test_targeted_maintenance.py
└── src/                                # Production application code
    ├── core/
    │   ├── recognition_engine.py       # Phase-2 MTCNN + FaceNet + Tracking pipeline
    │   └── liveness_detector.py        # Multi-Target MediaPipe EAR liveness engine
    ├── utils/
    │   ├── __init__.py
    │   └── face_verifier.py            # Pairwise biometric distance verification
    ├── admin_dashboard.py              # Primary Tkinter operations dashboard
    ├── attendance_manager.py           # Attendance transaction logic
    ├── database_manager.py             # SQLite helper and table setup
    ├── dashboard_analytics.py          # Executive analytics charts engine
    ├── face_detection.py               # Face detection helpers
    ├── main.py                         # Startup launcher
    ├── main_login.py                   # Role-based access control login dialog
    ├── register_student.py             # Biometric student enrollment module
    ├── report_generator.py             # Excel & PDF generation utility
    ├── splash.py                       # Splash screen loader
    ├── student_database.py             # Student record management interface
    └── student_info.py                 # Student metadata container
```

---

## 11. Privacy & Security Notice

To comply with institutional privacy policies, FERPA guidelines, and biometric data regulations:
- **No live personal student data, biometric facial photographs, actual user passwords, or operational attendance logs are committed to this repository.**
- The `database/attendance.db` file, `registered_faces/` directory, `reports/threat_captures/`, and exported spreadsheets are strictly excluded via `.gitignore`.
- Production instances must safeguard local database storage and obtain explicit consent from participating students before capturing facial biometric data.

---

## 12. Disclaimer

This platform was developed as an academic computer vision engineering project demonstrating real-time multi-target biometrics, anti-spoofing heuristics, and software reliability. Production deployment in high-security environments should be accompanied by institutionally approved access control hardware, network security audits, and compliance reviews.
