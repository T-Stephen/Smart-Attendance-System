# Contributing to Smart Campus AI Attendance System

Thank you for your interest in contributing to the **Smart Campus AI Attendance System**.

This platform is an academic research and engineering portfolio project developed to demonstrate concurrent multi-face tracking, 512-dimensional metric embedding matching, single-pass facial mesh anti-spoofing, and thread-decoupled graphical operations.

---

## 1. Important Project Scope & Deployment Notice

- **Project Status:** This repository represents an academic research and portfolio project. It is not an enterprise-certified commercial appliance or legally certified security system.
- **Biometric Governance:** Deploying facial recognition technology in real-world facilities requires institutional authorization, clear stakeholder consent, data protection reviews, and strict privacy controls.
- **Accuracy & Security Disclaimers:** The system does not claim 100% recognition accuracy, guaranteed anti-spoofing resistance against all presentation attacks (e.g., high-definition video replays), or guaranteed 10 FPS CPU inference. On standard x86_64 CPUs, AI inference throughput is approximately $1.3\text{--}1.9\text{ FPS}$ across 1–4 active targets, while the asynchronous user interface runs at $30\text{--}33\text{ FPS}$.

---

## 2. Environment Setup

### Prerequisites
- **Operating System:** Windows, Linux, or macOS
- **Python Version:** Python 3.10 or 3.11 (64-bit required)
- **Hardware:** Standard webcam or USB video input device

### Installation
```bash
# 1. Clone the repository
git clone https://github.com/T-Stephen/Smart-Attendance-System.git
cd Smart-Attendance-System

# 2. Create and activate a virtual environment
python -m venv .venv

# Windows:
.venv\Scripts\activate

# Linux/macOS:
source .venv/bin/activate

# 3. Install verified dependencies
pip install -r requirements.txt

# 4. Initialize the local database schema
python -c "import sqlite3, os; os.makedirs('database', exist_ok=True); conn = sqlite3.connect('database/attendance.db'); conn.executescript(open('database/schema.sql').read()); conn.close(); print('Database initialized cleanly.')"
```

---

## 3. Running the Application

Launch the operations console via the primary administrative entry point:

```bash
python src/admin_dashboard.py
```

---

## 4. Running Validation & Automated Tests

Before proposing any changes, verify that the existing validation suites execute cleanly:

```bash
# 1. Targeted maintenance validation (status colors, atomic buffer, rapid teardown)
python tests/test_targeted_maintenance.py

# 2. Dashboard regression suite (page transitions, engine initialization)
python tests/test_dashboard_regression.py

# 3. Comprehensive multi-face pipeline suite (18 operational scenarios)
python tests/test_comprehensive_suite.py
```

All tests must pass with 100% success prior to submission.

---

## 5. Strict Biometric Privacy & Security Policy

> [!CAUTION]
> **NEVER COMMIT SENSITIVE BIOMETRIC OR PRIVATE DATA TO GIT**

Contributions that violate this policy will be rejected immediately. Do **NOT** stage or commit:
- Real facial photographs or training datasets (`registered_faces/`, custom images)
- Serialized biometric embeddings (`models/*.pkl`, `models/student_embeddings.pkl`)
- Local SQLite databases or student records (`database/*.db`)
- Attendance operational logs or exports (`attendance/*.csv`, Excel/PDF reports)
- Threat captures or forensic surveillance snapshots (`reports/threat_captures/*.jpg`)
- System passwords, API tokens, or private credentials

Always verify your changes before staging with `git status` and `git diff`.

---

## 6. Contribution Workflow

1. **Create an Issue:** For bugs or feature requests, open an issue using the appropriate template.
2. **Branch Naming:** Create a focused feature branch from `main`:
   ```bash
   git checkout -b fix/issue-description
   # or
   git checkout -b feature/improvement-name
   ```
3. **Scope Your Changes:** Keep pull requests tightly focused. Do not combine unrelated refactors, formatting sweeps, and functional edits.
4. **Preserve System Baselines:** Do not alter validated recognition decision thresholds ($0.65$ Euclidean distance), ambiguity margins ($0.04$), or liveness state machines without prior consensus.
5. **Submit a Pull Request:** Open a PR against `main` using the provided [Pull Request Template](.github/PULL_REQUEST_TEMPLATE.md). Complete the full verification checklist.

---

## 7. Code Quality Expectations

- Adhere to standard PEP 8 styling where applicable.
- Maintain existing docstrings and comments.
- Ensure new functions contain appropriate error handling and type annotations where helpful.
- Keep UI operations thread-safe and non-blocking for background inference.
