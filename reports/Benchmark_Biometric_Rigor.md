# Biometric Specification & Rigor Benchmark Report

**Execution Timestamp:** 2026-10-16T13:59:54.872996<br>
**Environment:** Python 3.11.0 | NumPy 1.26.4 | OpenCV 4.9.0<br>
**Production Import Status:** Successfully imported `core.recognition_engine`<br>
**Benchmark Verdict:** ALL TESTS PASSED (23/23)

---

## 1. Methodological Disclosure & Scope

This benchmark evaluates the **mathematical decision logic**, **boundary tolerances**, and **image-quality filter thresholds** of the Smart Campus AI Attendance System.

> [!IMPORTANT]
> - **Zero Real Student Biometrics:** All vectors and image arrays were procedurally generated in memory.
> - **No Hardware Dependency:** No live webcam, GUI, or database connection was utilized.
> - **Non-Operational Scope:** Metrics reflect unit trial verification; they do not represent real-world human subject accuracy or ISO presentation attack detection compliance.

---

## 2. Test Suite Summaries

### Recognition Threshold Boundary Suite
**Category:** `SPECIFICATION TEST` | **Result:** 13/13 Passed

| Test Description | Expected | Measured / Actual | Status |
|---|---|---|---|
| Distance 0.50 (well below 0.65, separation 0.20) | `MATCH CANDIDATE` | `MATCH CANDIDATE` | **PASS** |
| Distance 0.60 (below 0.65, separation 0.10) | `MATCH CANDIDATE` | `MATCH CANDIDATE` | **PASS** |
| Distance 0.6499 (infinitesimally below 0.65) | `MATCH CANDIDATE` | `MATCH CANDIDATE` | **PASS** |
| Distance 0.6500 (exact threshold, <= is inclusive) | `MATCH CANDIDATE` | `MATCH CANDIDATE` | **PASS** |
| Distance 0.6501 (infinitesimally above 0.65) | `DISTANCE EXCEEDED` | `DISTANCE EXCEEDED` | **PASS** |
| Distance 0.70 (above 0.65 threshold) | `DISTANCE EXCEEDED` | `DISTANCE EXCEEDED` | **PASS** |
| Distance 0.85 (substantially above threshold) | `DISTANCE EXCEEDED` | `DISTANCE EXCEEDED` | **PASS** |
| Distance 0.55, 2nd 0.58 (separation 0.03 < 0.04 margin) | `AMBIGUOUS` | `AMBIGUOUS` | **PASS** |
| Distance 0.55, 2nd 0.5899 (separation 0.0399 < 0.04 margin) | `AMBIGUOUS` | `AMBIGUOUS` | **PASS** |
| Distance 0.55, 2nd 0.5900 (IEEE 754 precision: 0.59-0.55 < 0.04 -> AMBIGUOUS) | `AMBIGUOUS` | `AMBIGUOUS` | **PASS** |
| Distance 0.55, 2nd 0.5901 (separation 0.0401 >= 0.04 margin -> MATCH) | `MATCH CANDIDATE` | `MATCH CANDIDATE` | **PASS** |
| Distance 0.55, 2nd 0.6000 (separation 0.0500 > 0.04 margin -> MATCH) | `MATCH CANDIDATE` | `MATCH CANDIDATE` | **PASS** |
| Intra-frame duplicate identity suppression (lower distance wins) | `Candidate 1: MATCH, Candidate 2: DUPLICATE MATCH` | `Cand 1: MATCH CANDIDATE, Cand 2: DUPLICATE MATCH` | **PASS** |

### Image-Quality Perturbation Suite
**Category:** `EMPIRICAL UNIT TEST (SYNTHETIC IMAGES)` | **Result:** 7/7 Passed

| Test Description | Expected | Measured / Actual | Status |
|---|---|---|---|
| Empty array (0x0) | `False` | `False` | **PASS** |
| Tiny crop (32x32 < 40x40) | `False` | `False` | **PASS** |
| Low contrast crop with noise (std=4.0 < 8.0) | `False` | `False` | **PASS** |
| Severe underexposure (mean < 18.0) | `False` | `False` | **PASS** |
| Severe overexposure (mean > 248.0) | `False` | `False` | **PASS** |
| Heavily blurred textured crop (sigma=9) | `False` | `False` | **PASS** |
| Synthetic high-contrast textured crop (100x100) | `True` | `True` | **PASS** |

### Biometric Metric Calculation Suite
**Category:** `MATHEMATICAL UNIT TEST` | **Result:** 3/3 Passed

| Test Description | Expected | Measured / Actual | Status |
|---|---|---|---|
| Standard trial batch calculation (500 impostor, 100 genuine) | `FMR=0.0200, FNMR=0.0800, HTER=0.0500` | `FMR=0.0200, FNMR=0.0800, HTER=0.0500` | **PASS** |
| Zero-error trial batch calculation (200 impostor, 200 genuine) | `FMR=0.0, FNMR=0.0, HTER=0.0` | `FMR=0.0000, FNMR=0.0000, HTER=0.0000` | **PASS** |
| Zero-sample denominator guard (0 impostor, 0 genuine trials) | `Zero-division handled safely -> 0.0 without exception` | `FMR=0.0, FNMR=0.0, HTER=0.0` | **PASS** |

---

## 3. Mathematical Reference Formulas

1. **Euclidean Recognition Metric:**
   $$d(u, v) = \|u - v\|_2 = \sqrt{\sum_{i=1}^{512} (u_i - v_i)^2}$$
   - Threshold Enforcement: $\text{Decision} = \text{ACCEPT}$ iff $d_1 \le 0.65$ and $(d_2 - d_1) \ge 0.04$.

2. **Standard Biometric Operational Error Rates:**
   $$\text{FMR}(\theta) = \frac{\text{False Matches}}{\text{Total Impostor Trials}}$$
   $$\text{FNMR}(\theta) = \frac{\text{False Non-Matches}}{\text{Total Genuine Trials}}$$
   $$\text{HTER}(\theta) = \frac{\text{FMR}(\theta) + \text{FNMR}(\theta)}{2}$$

---
*Report generated automatically by `tests/benchmark_biometric_rigor.py`.*
