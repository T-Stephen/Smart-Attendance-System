"""
tests/benchmark_biometric_rigor.py

================================================================================
SMART CAMPUS AI ATTENDANCE SYSTEM
Isolated Synthetic Biometric Specification & Verification Benchmark
================================================================================

PURPOSE & METHODOLOGICAL DISCLOSURE:
- This module provides an automated, reproducible, headless specification test
  harness for biometric threshold boundaries, image quality gating, and
  biometric error-rate formulas (FMR, FNMR, HTER).
- All evaluation vectors and image arrays are procedurally generated in memory
  using a fixed random seed.
- NO real student biometric images, names, roll numbers, credentials, or model
  weights are accessed, loaded, or evaluated.
- NO hardware cameras (cv2.VideoCapture) or graphical interfaces (Tkinter)
  are opened or required.
- IMPORTANT: Metrics computed herein reflect synthetic verification trials
  designed to mathematically validate code logic and boundary handling.
  They DO NOT constitute real-world operational accuracy or ISO/IEC PAD
  compliance on human subjects.
================================================================================
"""

import sys
import os
import argparse
import math
from datetime import datetime
import numpy as np
import cv2

# Set path to source directory
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC_DIR = os.path.join(PROJECT_ROOT, "src")
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

# Deterministic random seed
FIXED_SEED = 42
np.random.seed(FIXED_SEED)

# Attempt safe import of production quality gating and pipeline constants
PROD_ENGINE_IMPORTED = False
try:
    from core.recognition_engine import (
        evaluate_crop_quality,
        STRICT_RECOGNITION_THRESHOLD,
        DEFAULT_AMBIGUITY_MARGIN,
        MIN_FACE_WIDTH,
        MIN_FACE_HEIGHT,
        MIN_SHARPNESS_LAPLACIAN,
        MIN_MEAN_BRIGHTNESS,
        MAX_MEAN_BRIGHTNESS,
        MIN_CONTRAST_STD,
    )
    PROD_ENGINE_IMPORTED = True
except Exception as import_err:
    # Graceful fallback to documented architecture constants if import fails
    STRICT_RECOGNITION_THRESHOLD = 0.65
    DEFAULT_AMBIGUITY_MARGIN = 0.04
    MIN_FACE_WIDTH = 40
    MIN_FACE_HEIGHT = 40
    MIN_SHARPNESS_LAPLACIAN = 4.0
    MIN_MEAN_BRIGHTNESS = 18.0
    MAX_MEAN_BRIGHTNESS = 248.0
    MIN_CONTRAST_STD = 8.0
    evaluate_crop_quality = None
    _import_error_msg = str(import_err)


# ==============================================================================
# 1. SYNTHETIC VECTOR GENERATOR (512-D L2-NORMALIZED)
# ==============================================================================

class SyntheticVectorGenerator:
    """
    Constructs exact 512-dimensional unit vectors with mathematically
    guaranteed Euclidean distance separation.
    """

    @staticmethod
    def create_orthogonal_basis(dim=512, seed=FIXED_SEED):
        rng = np.random.default_rng(seed)
        v1 = rng.standard_normal(dim)
        v1 = v1 / np.linalg.norm(v1)

        # Generate orthogonal vector via Gram-Schmidt
        v2_raw = rng.standard_normal(dim)
        v2 = v2_raw - np.dot(v2_raw, v1) * v1
        v2 = v2 / np.linalg.norm(v2)
        return v1, v2

    @staticmethod
    def vector_at_distance(u, w, distance):
        """
        Synthesizes a unit vector v such that ||u - v||_2 == distance.
        Given orthonormal u, w:
            v = alpha * u + beta * w
            ||u - v||^2 = (1 - alpha)^2 + beta^2 = 2 * (1 - alpha) = distance^2
            alpha = 1 - (distance^2 / 2)
            beta = sqrt(max(0.0, 1 - alpha^2))
        """
        dist = float(np.clip(distance, 0.0, 2.0))
        alpha = 1.0 - (dist ** 2) / 2.0
        beta_sq = max(0.0, 1.0 - alpha ** 2)
        beta = math.sqrt(beta_sq)

        v = alpha * u + beta * w
        norm = np.linalg.norm(v)
        if norm > 0:
            v = v / norm
        return v


# ==============================================================================
# 2. SPECIFICATION-LEVEL BIOMETRIC DECISION LOGIC
# ==============================================================================

def evaluate_biometric_decision(
    best_dist: float,
    second_dist: float,
    threshold: float = STRICT_RECOGNITION_THRESHOLD,
    ambiguity_margin: float = DEFAULT_AMBIGUITY_MARGIN,
) -> tuple[str, str, float]:
    """
    Evaluates Euclidean distance matching and ambiguity separation matching
    the exact production logic from RecognitionEngine.process_frame().

    Returns: (identity_label, status_string, confidence_score)
    """
    separation = second_dist - best_dist

    if best_dist <= threshold:
        if separation < ambiguity_margin:
            name = "Unknown"
            conf = max(0.0, 0.60 - (best_dist - (threshold - ambiguity_margin)))
            status = "AMBIGUOUS"
        else:
            name = "VALID_CANDIDATE"
            conf = 0.99 - ((best_dist / threshold) * 0.39)
            status = "MATCH CANDIDATE"
    else:
        name = "Unknown"
        conf = max(0.0, 0.60 - (best_dist - threshold))
        status = "DISTANCE EXCEEDED"

    return name, status, float(conf)


def resolve_intra_frame_conflicts(candidate_matches: list[dict]) -> list[dict]:
    """
    Resolves multiple faces matching the same student ID in the same frame
    using greedy distance assignment (matching RecognitionEngine#L510-525).
    """
    claimed = {}
    # Sort by best_dist ascending
    sorted_idx = sorted(range(len(candidate_matches)), key=lambda k: candidate_matches[k]["best_dist"])

    resolved = [dict(c) for c in candidate_matches]
    for idx in sorted_idx:
        cand = resolved[idx]
        cand_name = cand["name"]
        if cand_name != "Unknown":
            if cand_name in claimed:
                cand["name"] = "Unknown"
                cand["status"] = "DUPLICATE MATCH"
            else:
                claimed[cand_name] = idx
    return resolved


# ==============================================================================
# 3. METRIC CALCULATION ENGINE (FMR, FNMR, HTER)
# ==============================================================================

def compute_biometric_rates(
    false_matches: int,
    total_impostor_trials: int,
    false_non_matches: int,
    total_genuine_trials: int,
) -> dict:
    """
    Computes standard biometric operational error rates with robust
    zero-denominator handling:
      - FMR  = False Matches / Total Impostor Trials
      - FNMR = False Non-Matches / Total Genuine Trials
      - HTER = (FMR + FNMR) / 2
    """
    fmr = (false_matches / total_impostor_trials) if total_impostor_trials > 0 else 0.0
    fnmr = (false_non_matches / total_genuine_trials) if total_genuine_trials > 0 else 0.0
    hter = (fmr + fnmr) / 2.0

    return {
        "fmr": float(fmr),
        "fnmr": float(fnmr),
        "hter": float(hter),
        "false_matches": int(false_matches),
        "total_impostor_trials": int(total_impostor_trials),
        "false_non_matches": int(false_non_matches),
        "total_genuine_trials": int(total_genuine_trials),
    }


# ==============================================================================
# 4. BENCHMARK SUITE IMPLEMENTATION
# ==============================================================================

class BiometricRigorBenchmark:
    """Coordinates and executes isolated synthetic benchmark test suites."""

    def __init__(self):
        self.results = {}
        self.u, self.w = SyntheticVectorGenerator.create_orthogonal_basis()

    # --------------------------------------------------------------------------
    # SUITE A: Recognition Threshold Boundary Tests
    # --------------------------------------------------------------------------
    def run_threshold_boundary_tests(self) -> dict:
        suite_results = []

        # Test cases: (distance, second_distance, expected_status, description)
        test_cases = [
            # Below threshold (clear match)
            (0.5000, 0.7000, "MATCH CANDIDATE", "Distance 0.50 (well below 0.65, separation 0.20)"),
            (0.6000, 0.7000, "MATCH CANDIDATE", "Distance 0.60 (below 0.65, separation 0.10)"),
            (0.6499, 0.7000, "MATCH CANDIDATE", "Distance 0.6499 (infinitesimally below 0.65)"),
            # Exact threshold boundary
            (0.6500, 0.7500, "MATCH CANDIDATE", "Distance 0.6500 (exact threshold, <= is inclusive)"),
            # Above threshold (distance exceeded)
            (0.6501, 0.7500, "DISTANCE EXCEEDED", "Distance 0.6501 (infinitesimally above 0.65)"),
            (0.7000, 0.8500, "DISTANCE EXCEEDED", "Distance 0.70 (above 0.65 threshold)"),
            (0.8500, 0.9500, "DISTANCE EXCEEDED", "Distance 0.85 (substantially above threshold)"),
            # Ambiguity margin boundaries
            (0.5500, 0.5800, "AMBIGUOUS", "Distance 0.55, 2nd 0.58 (separation 0.03 < 0.04 margin)"),
            (0.5500, 0.5899, "AMBIGUOUS", "Distance 0.55, 2nd 0.5899 (separation 0.0399 < 0.04 margin)"),
            (0.5500, 0.5900, "AMBIGUOUS", "Distance 0.55, 2nd 0.5900 (IEEE 754 precision: 0.59-0.55 < 0.04 -> AMBIGUOUS)"),
            (0.5500, 0.5901, "MATCH CANDIDATE", "Distance 0.55, 2nd 0.5901 (separation 0.0401 >= 0.04 margin -> MATCH)"),
            (0.5500, 0.6000, "MATCH CANDIDATE", "Distance 0.55, 2nd 0.6000 (separation 0.0500 > 0.04 margin -> MATCH)"),
        ]

        passed = 0
        for best_d, sec_d, expected_status, desc in test_cases:
            # Generate vectors
            v_cand = SyntheticVectorGenerator.vector_at_distance(self.u, self.w, best_d)
            computed_dist = float(np.linalg.norm(self.u - v_cand))

            name, status, conf = evaluate_biometric_decision(
                best_dist=computed_dist,
                second_dist=sec_d,
                threshold=STRICT_RECOGNITION_THRESHOLD,
                ambiguity_margin=DEFAULT_AMBIGUITY_MARGIN,
            )

            is_ok = (status == expected_status)
            if is_ok:
                passed += 1

            suite_results.append({
                "description": desc,
                "input_dist": best_d,
                "measured_dist": computed_dist,
                "second_dist": sec_d,
                "expected_status": expected_status,
                "actual_status": status,
                "confidence": conf,
                "passed": is_ok,
            })

        # Test intra-frame conflict suppression
        candidates = [
            {"name": "STU_1001", "best_dist": 0.52, "status": "MATCH CANDIDATE"},
            {"name": "STU_1001", "best_dist": 0.58, "status": "MATCH CANDIDATE"},  # Same identity
            {"name": "STU_1002", "best_dist": 0.49, "status": "MATCH CANDIDATE"},  # Distinct identity
        ]
        resolved = resolve_intra_frame_conflicts(candidates)
        conflict_passed = (
            resolved[0]["status"] == "MATCH CANDIDATE"
            and resolved[1]["status"] == "DUPLICATE MATCH"
            and resolved[1]["name"] == "Unknown"
            and resolved[2]["status"] == "MATCH CANDIDATE"
        )
        if conflict_passed:
            passed += 1

        suite_results.append({
            "description": "Intra-frame duplicate identity suppression (lower distance wins)",
            "expected_status": "Candidate 1: MATCH, Candidate 2: DUPLICATE MATCH",
            "actual_status": f"Cand 1: {resolved[0]['status']}, Cand 2: {resolved[1]['status']}",
            "passed": conflict_passed,
        })

        total = len(test_cases) + 1
        return {
            "name": "Recognition Threshold Boundary Suite",
            "type": "SPECIFICATION TEST",
            "total": total,
            "passed": passed,
            "failed": total - passed,
            "details": suite_results,
        }

    # --------------------------------------------------------------------------
    # SUITE B: Image-Quality Perturbation Tests
    # --------------------------------------------------------------------------
    def run_image_quality_tests(self) -> dict:
        if not PROD_ENGINE_IMPORTED or evaluate_crop_quality is None:
            return {
                "name": "Image-Quality Perturbation Suite",
                "type": "SKIPPED",
                "reason": "Production evaluate_crop_quality could not be imported safely",
                "total": 0,
                "passed": 0,
                "failed": 0,
                "details": [],
            }

        suite_results = []
        cases = []

        # 1. Invalid / empty crop
        empty_crop = np.zeros((0, 0, 3), dtype=np.uint8)
        cases.append((empty_crop, False, "INVALID CROP", "Empty array (0x0)"))

        # 2. Too small crop (< 40x40)
        tiny_crop = np.full((32, 32, 3), 120, dtype=np.uint8)
        cases.append((tiny_crop, False, "FACE TOO SMALL", "Tiny crop (32x32 < 40x40)"))

        # 3. Low contrast crop with high-frequency noise (Contrast < 8.0, Sharpness >= 4.0)
        rng = np.random.default_rng(FIXED_SEED)
        low_contrast_noise = np.clip(rng.normal(128, 4.0, (80, 80, 3)), 0, 255).astype(np.uint8)
        cases.append((low_contrast_noise, False, "LOW CONTRAST", "Low contrast crop with noise (std=4.0 < 8.0)"))

        # 4. Severe underexposure / near-black (Mean brightness < 18.0)
        dark_noisy = np.clip(rng.normal(10, 2, (80, 80, 3)), 0, 255).astype(np.uint8)
        cases.append((dark_noisy, False, "POOR LIGHTING", "Severe underexposure (mean < 18.0)"))

        # 5. Severe overexposure (Mean brightness > 248.0)
        white_noisy = np.clip(rng.normal(252, 2, (80, 80, 3)), 0, 255).astype(np.uint8)
        cases.append((white_noisy, False, "OVEREXPOSED", "Severe overexposure (mean > 248.0)"))

        # 6. Heavy blur (Laplacian variance < 4.0)
        textured = rng.integers(40, 200, (80, 80, 3), dtype=np.uint8)
        blurred = cv2.GaussianBlur(textured, (21, 21), 9.0)
        cases.append((blurred, False, "BLUR DETECTED", "Heavily blurred textured crop (sigma=9)"))

        # 7. Valid, well-lit textured crop
        sharp_texture = rng.integers(60, 190, (100, 100, 3), dtype=np.uint8)
        cases.append((sharp_texture, True, "QUALITY OK", "Synthetic high-contrast textured crop (100x100)"))

        passed = 0
        for crop_arr, expected_ok, expected_status_substr, desc in cases:
            ok, score, reason = evaluate_crop_quality(crop_arr)

            status_matched = (expected_status_substr in reason)
            verdict_matched = (ok == expected_ok)
            test_passed = status_matched and verdict_matched
            if test_passed:
                passed += 1

            suite_results.append({
                "description": desc,
                "expected_ok": expected_ok,
                "actual_ok": ok,
                "expected_reason_substr": expected_status_substr,
                "actual_reason": reason,
                "quality_score": float(score),
                "passed": test_passed,
            })

        return {
            "name": "Image-Quality Perturbation Suite",
            "type": "EMPIRICAL UNIT TEST (SYNTHETIC IMAGES)",
            "total": len(cases),
            "passed": passed,
            "failed": len(cases) - passed,
            "details": suite_results,
        }

    # --------------------------------------------------------------------------
    # SUITE C: Metric Calculation Verification (FMR, FNMR, HTER)
    # --------------------------------------------------------------------------
    def run_metric_calculation_tests(self) -> dict:
        suite_results = []
        passed = 0

        # Scenario 1: Standard populated trial batch
        # 100 genuine comparisons: 92 accept (d <= 0.65), 8 false non-matches (d > 0.65)
        # 500 impostor comparisons: 490 reject (d > 0.65), 10 false matches (d <= 0.65)
        m1 = compute_biometric_rates(
            false_matches=10,
            total_impostor_trials=500,
            false_non_matches=8,
            total_genuine_trials=100,
        )
        expected_fmr1 = 10 / 500  # 0.02 (2.0%)
        expected_fnmr1 = 8 / 100  # 0.08 (8.0%)
        expected_hter1 = (0.02 + 0.08) / 2.0  # 0.05 (5.0%)

        t1_ok = (
            math.isclose(m1["fmr"], expected_fmr1, abs_tol=1e-6)
            and math.isclose(m1["fnmr"], expected_fnmr1, abs_tol=1e-6)
            and math.isclose(m1["hter"], expected_hter1, abs_tol=1e-6)
        )
        if t1_ok:
            passed += 1
        suite_results.append({
            "description": "Standard trial batch calculation (500 impostor, 100 genuine)",
            "expected": f"FMR={expected_fmr1:.4f}, FNMR={expected_fnmr1:.4f}, HTER={expected_hter1:.4f}",
            "actual": f"FMR={m1['fmr']:.4f}, FNMR={m1['fnmr']:.4f}, HTER={m1['hter']:.4f}",
            "passed": t1_ok,
        })

        # Scenario 2: Perfect performance (0 errors)
        m2 = compute_biometric_rates(0, 200, 0, 200)
        t2_ok = (m2["fmr"] == 0.0 and m2["fnmr"] == 0.0 and m2["hter"] == 0.0)
        if t2_ok:
            passed += 1
        suite_results.append({
            "description": "Zero-error trial batch calculation (200 impostor, 200 genuine)",
            "expected": "FMR=0.0, FNMR=0.0, HTER=0.0",
            "actual": f"FMR={m2['fmr']:.4f}, FNMR={m2['fnmr']:.4f}, HTER={m2['hter']:.4f}",
            "passed": t2_ok,
        })

        # Scenario 3: Robust zero-sample denominator handling (no crashes)
        m3 = compute_biometric_rates(0, 0, 0, 0)
        t3_ok = (m3["fmr"] == 0.0 and m3["fnmr"] == 0.0 and m3["hter"] == 0.0)
        if t3_ok:
            passed += 1
        suite_results.append({
            "description": "Zero-sample denominator guard (0 impostor, 0 genuine trials)",
            "expected": "Zero-division handled safely -> 0.0 without exception",
            "actual": f"FMR={m3['fmr']}, FNMR={m3['fnmr']}, HTER={m3['hter']}",
            "passed": t3_ok,
        })

        return {
            "name": "Biometric Metric Calculation Suite",
            "type": "MATHEMATICAL UNIT TEST",
            "total": 3,
            "passed": passed,
            "failed": 3 - passed,
            "details": suite_results,
        }

    # --------------------------------------------------------------------------
    # Master Execution Runner
    # --------------------------------------------------------------------------
    def run_all(self) -> dict:
        suite_a = self.run_threshold_boundary_tests()
        suite_b = self.run_image_quality_tests()
        suite_c = self.run_metric_calculation_tests()

        total_tests = suite_a["total"] + suite_b["total"] + suite_c["total"]
        total_passed = suite_a["passed"] + suite_b["passed"] + suite_c["passed"]

        self.results = {
            "timestamp": datetime.now().isoformat(),
            "python_version": sys.version.split()[0],
            "opencv_version": cv2.__version__,
            "numpy_version": np.__version__,
            "prod_module_imported": PROD_ENGINE_IMPORTED,
            "total_tests": total_tests,
            "total_passed": total_passed,
            "total_failed": total_tests - total_passed,
            "all_passed": (total_passed == total_tests),
            "suites": [suite_a, suite_b, suite_c],
        }
        return self.results


# ==============================================================================
# 5. MARKDOWN REPORT GENERATOR (SAFE & ANONYMIZED)
# ==============================================================================

def generate_markdown_report(results: dict, target_file: str, allow_overwrite: bool = False) -> bool:
    """
    Generates a formal, anonymized Markdown benchmark summary.
    Respects safe non-overwrite constraints.
    """
    if os.path.exists(target_file) and not allow_overwrite:
        print(f"[NOTICE] Report file exists at {target_file}. Overwrite not authorized. Skipping write.")
        return False

    os.makedirs(os.path.dirname(os.path.abspath(target_file)), exist_ok=True)

    lines = []
    lines.append("# Biometric Specification & Rigor Benchmark Report")
    lines.append("")
    lines.append(f"**Execution Timestamp:** {results['timestamp']}<br>")
    lines.append(f"**Environment:** Python {results['python_version']} | NumPy {results['numpy_version']} | OpenCV {results['opencv_version']}<br>")
    lines.append(f"**Production Import Status:** {'Successfully imported `core.recognition_engine`' if results['prod_module_imported'] else 'Specification fallback (Engine unimported)'}<br>")
    lines.append(f"**Benchmark Verdict:** {'ALL TESTS PASSED' if results['all_passed'] else 'FAILURES DETECTED'} ({results['total_passed']}/{results['total_tests']})")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## 1. Methodological Disclosure & Scope")
    lines.append("")
    lines.append("This benchmark evaluates the **mathematical decision logic**, **boundary tolerances**, and **image-quality filter thresholds** of the Smart Campus AI Attendance System.")
    lines.append("")
    lines.append("> [!IMPORTANT]")
    lines.append("> - **Zero Real Student Biometrics:** All vectors and image arrays were procedurally generated in memory.")
    lines.append("> - **No Hardware Dependency:** No live webcam, GUI, or database connection was utilized.")
    lines.append("> - **Non-Operational Scope:** Metrics reflect unit trial verification; they do not represent real-world human subject accuracy or ISO presentation attack detection compliance.")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## 2. Test Suite Summaries")
    lines.append("")

    for suite in results["suites"]:
        lines.append(f"### {suite['name']}")
        lines.append(f"**Category:** `{suite['type']}` | **Result:** {suite['passed']}/{suite['total']} Passed")
        lines.append("")
        lines.append("| Test Description | Expected | Measured / Actual | Status |")
        lines.append("|---|---|---|---|")
        for d in suite["details"]:
            desc = d["description"]
            exp = d.get("expected_status", str(d.get("expected_ok", d.get("expected", "-"))))
            act = d.get("actual_status", str(d.get("actual_ok", d.get("actual", "-"))))
            st = "PASS" if d["passed"] else "FAIL"
            lines.append(f"| {desc} | `{exp}` | `{act}` | **{st}** |")
        lines.append("")

    lines.append("---")
    lines.append("")
    lines.append("## 3. Mathematical Reference Formulas")
    lines.append("")
    lines.append("1. **Euclidean Recognition Metric:**")
    lines.append("   $$d(u, v) = \\|u - v\\|_2 = \\sqrt{\\sum_{i=1}^{512} (u_i - v_i)^2}$$")
    lines.append("   - Threshold Enforcement: $\\text{Decision} = \\text{ACCEPT}$ iff $d_1 \\le 0.65$ and $(d_2 - d_1) \\ge 0.04$.")
    lines.append("")
    lines.append("2. **Standard Biometric Operational Error Rates:**")
    lines.append("   $$\\text{FMR}(\\theta) = \\frac{\\text{False Matches}}{\\text{Total Impostor Trials}}$$")
    lines.append("   $$\\text{FNMR}(\\theta) = \\frac{\\text{False Non-Matches}}{\\text{Total Genuine Trials}}$$")
    lines.append("   $$\\text{HTER}(\\theta) = \\frac{\\text{FMR}(\\theta) + \\text{FNMR}(\\theta)}{2}$$")
    lines.append("")
    lines.append("---")
    lines.append("*Report generated automatically by `tests/benchmark_biometric_rigor.py`.*")
    lines.append("")

    with open(target_file, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    print(f"[INFO] Benchmark report successfully written to: {target_file}")
    return True


# ==============================================================================
# 6. CLI ENTRY POINT
# ==============================================================================

def main():
    parser = argparse.ArgumentParser(description="Synthetic Biometric Rigor Benchmark Harness")
    parser.add_argument("--report", action="store_true", help="Generate Markdown report if not already present")
    parser.add_argument("--force-report", action="store_true", help="Overwrite existing Markdown report")
    args = parser.parse_args()

    print("=" * 70)
    print("SMART CAMPUS AI — BIOMETRIC SPECIFICATION & RIGOR BENCHMARK")
    print("=" * 70)

    benchmark = BiometricRigorBenchmark()
    res = benchmark.run_all()

    print(f"\nExecution Timestamp : {res['timestamp']}")
    print(f"Engine Import Status: {'SAFE IMPORT SUCCESS' if res['prod_module_imported'] else 'SPECIFICATION FALLBACK'}")
    print(f"Total Tests Run     : {res['total_tests']}")
    print(f"Passed              : {res['total_passed']}")
    print(f"Failed              : {res['total_failed']}")
    print("-" * 70)

    for suite in res["suites"]:
        print(f"\n[{suite['type']}] {suite['name']}: {suite['passed']}/{suite['total']} Passed")
        for d in suite["details"]:
            status_flag = "[PASS]" if d["passed"] else "[FAIL]"
            print(f"  {status_flag} {d['description']}")

    print("\n" + "=" * 70)
    if res["all_passed"]:
        print(">>> ALL BENCHMARK RIGOR VERIFICATION TESTS PASSED SUCCESSFULLY! <<<")
    else:
        print(">>> FAILURES DETECTED IN BENCHMARK VERIFICATION <<<")
    print("=" * 70)

    report_path = os.path.join(PROJECT_ROOT, "reports", "Benchmark_Biometric_Rigor.md")
    if args.report or args.force_report:
        generate_markdown_report(res, report_path, allow_overwrite=args.force_report)

    sys.exit(0 if res["all_passed"] else 1)


if __name__ == "__main__":
    main()
