"""
tests/test_quality_diagnostics.py

Unit Test Suite for Explainable Face-Image Quality Diagnostics (X-FIQA)
=======================================================================
Validates FaceQualityDiagnostics using strictly synthetic procedurally
generated NumPy arrays.

SAFETY GUARANTEES:
- NO real student photos or enrollment assets accessed.
- NO hardware cameras initialized.
- NO database or CSV operations.
- NO operational side effects.
"""

import os
import sys
import unittest
import numpy as np
import cv2

# Ensure project src is in sys.path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC_DIR = os.path.join(PROJECT_ROOT, "src")
CORE_DIR = os.path.join(SRC_DIR, "core")
for p in [PROJECT_ROOT, SRC_DIR, CORE_DIR]:
    if p not in sys.path:
        sys.path.insert(0, p)

from quality_diagnostics import FaceQualityDiagnostics


class TestFaceQualityDiagnostics(unittest.TestCase):

    def setUp(self):
        # Set deterministic seed for synthetic test array generation
        self.rng = np.random.default_rng(42)

    def _create_synthetic_texture(self, height=160, width=160, dtype=np.uint8):
        """Generates a synthetic high-contrast textured image array."""
        canvas = np.zeros((height, width, 3), dtype=np.float64 if dtype != np.uint8 else np.uint8)
        block_size = 8
        for r in range(0, height, block_size):
            for c in range(0, width, block_size):
                if ((r // block_size) + (c // block_size)) % 2 == 0:
                    canvas[r : r + block_size, c : c + block_size] = (200.0, 200.0, 200.0)
                else:
                    canvas[r : r + block_size, c : c + block_size] = (50.0, 50.0, 50.0)

        if dtype == np.uint8:
            return canvas.astype(np.uint8)
        elif dtype == np.float32:
            return canvas.astype(np.float32)
        elif dtype == np.float64:
            return canvas.astype(np.float64)
        return canvas

    def test_valid_bgr_and_rgb_inputs(self):
        """Verify both BGR and RGB color order specifications execute cleanly."""
        img = self._create_synthetic_texture()
        diag_bgr = FaceQualityDiagnostics.analyze_crop(img, color_order="BGR")
        diag_rgb = FaceQualityDiagnostics.analyze_crop(img, color_order="RGB")

        self.assertIsInstance(diag_bgr, dict)
        self.assertIsInstance(diag_rgb, dict)
        self.assertIn("composite_score", diag_bgr)
        self.assertIn("composite_score", diag_rgb)

    def test_deterministic_repeatability(self):
        """Verify repeated calls on the identical array produce identical results."""
        img = self._create_synthetic_texture()
        res1 = FaceQualityDiagnostics.analyze_crop(img)
        res2 = FaceQualityDiagnostics.analyze_crop(img)
        self.assertEqual(res1, res2)

    def test_score_bounds_and_structure(self):
        """Verify all returned component and composite scores are bounded in [0.0, 100.0]."""
        img = self._create_synthetic_texture()
        res = FaceQualityDiagnostics.analyze_crop(img)

        self.assertGreaterEqual(res["composite_score"], 0.0)
        self.assertLessEqual(res["composite_score"], 100.0)

        for name, data in res["metrics"].items():
            score = data["score"]
            self.assertGreaterEqual(score, 0.0, f"Metric '{name}' score < 0.0")
            self.assertLessEqual(score, 100.0, f"Metric '{name}' score > 100.0")

        self.assertIn(res["quality_tier"], ["OPTIMAL", "ACCEPTABLE", "SUBOPTIMAL", "REJECT"])
        self.assertIsInstance(res["is_acceptable"], bool)
        self.assertIsInstance(res["defects"], list)
        self.assertIsInstance(res["remediation_advice"], list)

    def test_input_immutability_uint8_and_float(self):
        """Verify the diagnostic analysis does not mutate uint8 or float input arrays."""
        # Test uint8 immutability
        img_uint8 = self._create_synthetic_texture(dtype=np.uint8)
        original_uint8 = img_uint8.copy()
        _ = FaceQualityDiagnostics.analyze_crop(img_uint8)
        self.assertTrue(np.array_equal(img_uint8, original_uint8))

        # Test float32 immutability
        img_float32 = self._create_synthetic_texture(dtype=np.float32) / 255.0
        original_float32 = img_float32.copy()
        _ = FaceQualityDiagnostics.analyze_crop(img_float32)
        self.assertTrue(np.array_equal(img_float32, original_float32))

    def test_floating_point_inputs_support(self):
        """Verify float32 in [0, 1], float32 in [0, 255], and float64 inputs execute cleanly (F-01)."""
        # 1. float32 normalized in [0.0, 1.0]
        f32_norm = (self._create_synthetic_texture(dtype=np.float32) / 255.0).astype(np.float32)
        res_norm = FaceQualityDiagnostics.analyze_crop(f32_norm)
        self.assertIsInstance(res_norm, dict)
        self.assertGreaterEqual(res_norm["composite_score"], 0.0)
        self.assertLessEqual(res_norm["composite_score"], 100.0)

        # 2. float32 in [0.0, 255.0]
        f32_255 = self._create_synthetic_texture(dtype=np.float32)
        res_255 = FaceQualityDiagnostics.analyze_crop(f32_255)
        self.assertIsInstance(res_255, dict)
        self.assertGreaterEqual(res_255["composite_score"], 0.0)
        self.assertLessEqual(res_255["composite_score"], 100.0)

        # 3. float64 in [0.0, 1.0]
        f64_img = (self._create_synthetic_texture(dtype=np.float64) / 255.0).astype(np.float64)
        res_f64 = FaceQualityDiagnostics.analyze_crop(f64_img)
        self.assertIsInstance(res_f64, dict)
        self.assertGreaterEqual(res_f64["composite_score"], 0.0)
        self.assertLessEqual(res_f64["composite_score"], 100.0)

    def test_single_channel_and_2d_grayscale_inputs(self):
        """Verify 2D grayscale arrays and (H, W, 1) single-channel inputs execute cleanly."""
        # 2D grayscale array
        gray_2d = np.full((160, 160), 128, dtype=np.uint8)
        res_2d = FaceQualityDiagnostics.analyze_crop(gray_2d)
        self.assertIsInstance(res_2d, dict)
        self.assertGreaterEqual(res_2d["composite_score"], 0.0)

        # Single-channel 3D array (H, W, 1)
        gray_1ch = np.full((160, 160, 1), 128, dtype=np.uint8)
        res_1ch = FaceQualityDiagnostics.analyze_crop(gray_1ch)
        self.assertIsInstance(res_1ch, dict)
        self.assertGreaterEqual(res_1ch["composite_score"], 0.0)

    def test_explicit_dtype_validation(self):
        """Verify unsupported array data types raise TypeError safely before OpenCV calls (F-03)."""
        # Boolean array
        with self.assertRaises(TypeError) as ctx_bool:
            FaceQualityDiagnostics.analyze_crop(np.zeros((100, 100, 3), dtype=bool))
        self.assertIn("Unsupported array dtype", str(ctx_bool.exception))

        # int32 array
        with self.assertRaises(TypeError) as ctx_int32:
            FaceQualityDiagnostics.analyze_crop(np.zeros((100, 100, 3), dtype=np.int32))
        self.assertIn("Unsupported array dtype", str(ctx_int32.exception))

        # int16 array
        with self.assertRaises(TypeError) as ctx_int16:
            FaceQualityDiagnostics.analyze_crop(np.zeros((100, 100, 3), dtype=np.int16))
        self.assertIn("Unsupported array dtype", str(ctx_int16.exception))

        # Object array
        with self.assertRaises(TypeError) as ctx_obj:
            FaceQualityDiagnostics.analyze_crop(np.array(["a", "b", "c"], dtype=object))
        self.assertIn("Unsupported array dtype", str(ctx_obj.exception))

    def test_underexposure_penalty(self):
        """Verify dark synthetic image receives a low illumination score and defect."""
        dark_img = np.full((160, 160, 3), 15, dtype=np.uint8)
        res = FaceQualityDiagnostics.analyze_crop(dark_img)

        self.assertLess(res["metrics"]["illumination"]["score"], 30.0)
        self.assertIn("UNDEREXPOSURE", res["defects"])
        self.assertNotIn("OVEREXPOSURE", res["defects"])

        # Advice should recommend improving front lighting
        advice_text = " ".join(res["remediation_advice"]).lower()
        self.assertIn("lighting", advice_text)
        self.assertNotIn("glare", advice_text)

    def test_overexposure_penalty(self):
        """Verify overexposed synthetic image receives a low illumination score and defect."""
        bright_img = np.full((160, 160, 3), 250, dtype=np.uint8)
        res = FaceQualityDiagnostics.analyze_crop(bright_img)

        self.assertLess(res["metrics"]["illumination"]["score"], 30.0)
        self.assertIn("OVEREXPOSURE", res["defects"])
        self.assertNotIn("UNDEREXPOSURE", res["defects"])

        # Advice should recommend reducing glare/exposure
        advice_text = " ".join(res["remediation_advice"]).lower()
        self.assertTrue("glare" in advice_text or "exposure" in advice_text or "lighting" in advice_text)
        self.assertNotIn("frontal lighting", advice_text)

    def test_sharp_versus_blurred_relative_ordering(self):
        """Verify sharp texture strictly outscores its blurred counterpart and detects severe blur."""
        sharp_img = self._create_synthetic_texture()
        # Heavy Gaussian blur (sigma=9, kernel=25) matching benchmark rigor perturbation
        blurred_img = cv2.GaussianBlur(sharp_img, (25, 25), 9.0)

        res_sharp = FaceQualityDiagnostics.analyze_crop(sharp_img)
        res_blurred = FaceQualityDiagnostics.analyze_crop(blurred_img)

        sharp_score = res_sharp["metrics"]["sharpness"]["score"]
        blurred_score = res_blurred["metrics"]["sharpness"]["score"]

        self.assertGreater(
            sharp_score,
            blurred_score,
            f"Sharp score ({sharp_score}) not strictly greater than blurred score ({blurred_score}).",
        )
        self.assertIn("LOW_SHARPNESS", res_blurred["defects"])

    def test_resolution_relative_ordering(self):
        """Verify low-resolution input scores lower than optimal resolution input."""
        low_res = np.full((30, 30, 3), 128, dtype=np.uint8)
        high_res = np.full((160, 160, 3), 128, dtype=np.uint8)

        res_low = FaceQualityDiagnostics.analyze_crop(low_res)
        res_high = FaceQualityDiagnostics.analyze_crop(high_res)

        resol_low = res_low["metrics"]["resolution"]["score"]
        resol_high = res_high["metrics"]["resolution"]["score"]

        self.assertLess(resol_low, resol_high)
        self.assertIn("INSUFFICIENT_RESOLUTION", res_low["defects"])
        self.assertNotIn("INSUFFICIENT_RESOLUTION", res_high["defects"])

    def test_constant_and_empty_inputs(self):
        """Verify constant image exhibits zero sharpness and zero contrast."""
        constant_img = np.full((100, 100, 3), 128, dtype=np.uint8)
        res = FaceQualityDiagnostics.analyze_crop(constant_img)

        self.assertEqual(res["metrics"]["sharpness"]["raw_laplacian_variance"], 0.0)
        self.assertEqual(res["metrics"]["sharpness"]["score"], 0.0)
        self.assertEqual(res["metrics"]["contrast"]["score"], 0.0)
        self.assertIn("LOW_SHARPNESS", res["defects"])
        self.assertIn("LOW_CONTRAST", res["defects"])

        # Empty array must raise ValueError
        empty_img = np.array([], dtype=np.uint8)
        with self.assertRaises(ValueError):
            FaceQualityDiagnostics.analyze_crop(empty_img)

    def test_invalid_input_types_and_dimensions(self):
        """Verify invalid inputs raise documented exceptions safely."""
        # Non-array input
        with self.assertRaises(TypeError):
            FaceQualityDiagnostics.analyze_crop("not_an_array")  # type: ignore

        with self.assertRaises(TypeError):
            FaceQualityDiagnostics.analyze_crop([1, 2, 3])  # type: ignore

        # 1D array
        with self.assertRaises(ValueError):
            FaceQualityDiagnostics.analyze_crop(np.zeros(100, dtype=np.uint8))

        # 4D array
        with self.assertRaises(ValueError):
            FaceQualityDiagnostics.analyze_crop(np.zeros((1, 50, 50, 3), dtype=np.uint8))

        # Unsupported channel count (2 channels)
        with self.assertRaises(ValueError):
            FaceQualityDiagnostics.analyze_crop(np.zeros((50, 50, 2), dtype=np.uint8))

        # Unsupported channel count (4 channels)
        with self.assertRaises(ValueError):
            FaceQualityDiagnostics.analyze_crop(np.zeros((50, 50, 4), dtype=np.uint8))

        # Invalid color order
        with self.assertRaises(ValueError):
            FaceQualityDiagnostics.analyze_crop(np.zeros((50, 50, 3), dtype=np.uint8), color_order="CMYK")

        # Non-finite inputs (NaN / Inf)
        nan_img = np.zeros((50, 50, 3), dtype=np.float32)
        nan_img[10, 10, 0] = np.nan
        with self.assertRaises(ValueError):
            FaceQualityDiagnostics.analyze_crop(nan_img)

        inf_img = np.zeros((50, 50, 3), dtype=np.float32)
        inf_img[10, 10, 0] = np.inf
        with self.assertRaises(ValueError):
            FaceQualityDiagnostics.analyze_crop(inf_img)

    def test_high_frequency_noise_sensitivity_documentation(self):
        """Documents F-02: verify discrete Laplacian variance sensitivity to high-frequency noise.

        This test verifies that pure unstructured Gaussian noise produces high Laplacian
        variance without raising exceptions, and documents this algorithmic characteristic
        without asserting an uncalibrated quality tier.
        """
        noise = self.rng.normal(128.0, 40.0, (160, 160, 3)).clip(0, 255).astype(np.uint8)
        res = FaceQualityDiagnostics.analyze_crop(noise)

        # Confirm execution is finite and bounded
        self.assertGreaterEqual(res["composite_score"], 0.0)
        self.assertLessEqual(res["composite_score"], 100.0)
        self.assertIsInstance(res["metrics"]["sharpness"]["raw_laplacian_variance"], float)

        # Document characteristic: high-frequency noise generates non-trivial Laplacian variance
        self.assertGreater(res["metrics"]["sharpness"]["raw_laplacian_variance"], 100.0)

    def test_remediation_advice_generation(self):
        """Verify remediation advice generator produces concise, actionable strings."""
        mock_diag = {
            "composite_score": 25.0,
            "defects": ["UNDEREXPOSURE", "LOW_SHARPNESS"],
            "metrics": {
                "illumination": {"score": 20.0, "mean_luminance": 25.0},
                "sharpness": {"score": 15.0},
                "resolution": {"score": 80.0},
                "contrast": {"score": 40.0},
            },
        }
        advice = FaceQualityDiagnostics.get_remediation_advice(mock_diag)
        self.assertIsInstance(advice, list)
        self.assertGreaterEqual(len(advice), 2)
        joined = " ".join(advice).lower()
        self.assertIn("lighting", joined)
        self.assertIn("steady", joined)


if __name__ == "__main__":
    unittest.main()
