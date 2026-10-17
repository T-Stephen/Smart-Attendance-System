"""
src/core/quality_diagnostics.py

Explainable Face-Image Quality Assessment (X-FIQA) Diagnostic Engine
======================================================================
Provides standalone, deterministic, and explainable face-image quality
diagnostics and actionable remediation guidance for facial crops.

DESIGN CONSTRAINTS & PRINCIPLES:
- Additive-only, standalone component with zero operational side effects.
- Operates strictly on image pixel geometry and luminance statistics.
- Never mutates the input image array.
- Never accesses cameras, graphical interfaces, databases, student PII,
  or operational file systems.
- Does not import or instantiate RecognitionEngine.
- Component scores (0-100) are heuristic indicators inspired by general
  facial image quality assessment principles (e.g. ISO/IEC 29794-5 concepts).
  They do NOT constitute formal ISO certification or guaranteed recognition
  probabilities.

ALGORITHMIC CHARACTERISTICS & KNOWN LIMITATIONS (F-02):
- Laplacian-based sharpness measures discrete second-order spatial derivative
  energy across the image. Consequently, it measures high-frequency intensity
  transitions indiscriminately and cannot distinguish between semantic facial
  contours (such as eye, nose, and mouth boundaries) and high-frequency sensor
  noise, grain, or artificial geometric patterns (e.g., checkerboard textures).
- In operational deployment, this limitation is mitigated by structural gating:
  crops are only analyzed after prior face detection and landmark alignment
  (e.g., via MTCNN).
- X-FIQA scores must NEVER be treated as proof of face presence, biometric
  confidence, verification accuracy, or anti-spoof liveness.
"""

import math
from typing import Any, Dict, List
import cv2
import numpy as np


class FaceQualityDiagnostics:
    """Evaluates facial crop quality across five distinct dimensions and

    provides deterministic scores and explainable remediation advice.

    Note on Noise Sensitivity (F-02):
    Sharpness evaluation utilizes discrete Laplacian variance. High-frequency
    random noise, sensor noise, or artificial textures will produce high
    Laplacian variance. This engine evaluates optical and signal properties
    of the supplied array and relies on upstream detectors for semantic face
    verification.
    """

    # Supported array data types
    SUPPORTED_DTYPES = (np.uint8, np.float32, np.float64)

    # Nominal threshold constants
    MIN_FACE_WIDTH = 40
    MIN_FACE_HEIGHT = 40
    OPTIMAL_MIN_DIMENSION = 160.0

    # Weight distribution for composite score (sum = 1.0)
    WEIGHT_SHARPNESS = 0.35
    WEIGHT_ILLUMINATION = 0.30
    WEIGHT_CONTRAST = 0.20
    WEIGHT_RESOLUTION = 0.15

    @classmethod
    def analyze_crop(cls, crop: np.ndarray, color_order: str = "BGR") -> Dict[str, Any]:
        """Analyzes a facial crop array and computes five bounded 0-100 quality scores

        along with diagnostic labels and remediation guidance.

        Parameters
        ----------
        crop : np.ndarray
            Input image array representing a cropped facial region.
            Supported shapes: (H, W, 3), (H, W, 1), or (H, W).
            Supported dtypes: uint8, float32, float64.
        color_order : str, optional
            Color channel ordering for 3-channel images: "BGR" (default) or "RGB".

        Returns
        -------
        dict
            Deterministic JSON-serializable dictionary containing:
            - "composite_score": Overall quality score (0.0 to 100.0)
            - "quality_tier": "OPTIMAL", "ACCEPTABLE", "SUBOPTIMAL", or "REJECT"
            - "is_acceptable": Boolean threshold determination
            - "metrics": Dictionary of sub-scores and raw measurements
            - "defects": List of identified quality defects
            - "remediation_advice": Actionable user advice strings

        Raises
        ------
        TypeError
            If crop is not a numpy.ndarray or has an unsupported dtype.
        ValueError
            If crop is empty, has invalid dimensions, channel counts, non-finite values,
            or an unsupported color_order.
        """
        # 1. Strict Input Validation (F-03: Validate dtype before operations)
        if not isinstance(crop, np.ndarray):
            raise TypeError(f"Input 'crop' must be a numpy.ndarray, got {type(crop).__name__}.")

        # Enforce exact supported dtype allowlist
        if crop.dtype not in cls.SUPPORTED_DTYPES:
            raise TypeError(
                f"Unsupported array dtype '{crop.dtype}'. Supported dtypes are uint8, float32, float64."
            )

        if crop.size == 0:
            raise ValueError("Input 'crop' array is empty (zero elements).")

        if crop.ndim not in (2, 3):
            raise ValueError(
                f"Input 'crop' must be 2D (grayscale) or 3D (channels), got {crop.ndim} dimensions."
            )

        # Validate channel count for 3D arrays
        if crop.ndim == 3:
            num_channels = crop.shape[2]
            if num_channels not in (1, 3):
                raise ValueError(
                    f"Unsupported channel count {num_channels}. Only 1-channel or 3-channel crops are supported."
                )

        h, w = crop.shape[:2]
        if h <= 0 or w <= 0:
            raise ValueError(f"Invalid image dimensions: height={h}, width={w}.")

        # Check for non-finite values (NaN / Inf) in floating point inputs
        if np.issubdtype(crop.dtype, np.floating):
            if not np.all(np.isfinite(crop)):
                raise ValueError("Input 'crop' contains non-finite values (NaN or Inf).")

        # Validate color order
        normalized_color_order = str(color_order).strip().upper()
        if normalized_color_order not in ("BGR", "RGB"):
            raise ValueError(
                f"Invalid color_order '{color_order}'. Supported color orders are 'BGR' or 'RGB'."
            )

        # 2. Safe Grayscale Conversion (F-01: Correct dtype conversion for float32/float64)
        # Never mutate the caller's input array
        if crop.ndim == 2:
            gray_work = crop.astype(np.float64)
        elif crop.shape[2] == 1:
            gray_work = crop[:, :, 0].astype(np.float64)
        else:
            # 3-channel image
            code = cv2.COLOR_BGR2GRAY if normalized_color_order == "BGR" else cv2.COLOR_RGB2GRAY
            if crop.dtype == np.float64:
                # OpenCV cvtColor does not support CV_64F; cast working copy to float32
                work_crop = crop.astype(np.float32)
                gray_work = cv2.cvtColor(work_crop, code).astype(np.float64)
            else:
                gray_work = cv2.cvtColor(crop, code).astype(np.float64)

        # Normalize floating-point representations to standard range [0.0, 255.0]
        if np.issubdtype(crop.dtype, np.floating):
            max_val = float(np.max(gray_work)) if gray_work.size > 0 else 1.0
            if 0.0 < max_val <= 1.05:
                # Scale nominal [0.0, 1.0] float image to [0.0, 255.0]
                gray_work = gray_work * 255.0
            gray_work = np.clip(gray_work, 0.0, 255.0)

        # Guarantee working grayscale array is float64 before cv2.Laplacian (F-01)
        gray_work = gray_work.astype(np.float64)

        # 3. Dimension 1: Sharpness (Bounded Logarithmic Laplacian Variance)
        # Raw Laplacian second-order spatial derivative variance
        lap = cv2.Laplacian(gray_work, cv2.CV_64F)
        raw_lap_var = float(lap.var())

        # Bounded logarithmic mapping:
        # lap_var = 0.0 -> score 0.0
        # lap_var = 4.0 (baseline blur cutoff) -> score ~29.1
        # lap_var = 50.0 (clean focus) -> score ~71.1
        # lap_var >= 250.0 (high frequency detail) -> score 100.0
        s_sharp = float(
            np.clip(
                (math.log10(1.0 + max(0.0, raw_lap_var)) / math.log10(1.0 + 250.0)) * 100.0,
                0.0,
                100.0,
            )
        )

        # 4. Dimension 2: Illumination & Exposure Bounded Metric
        mean_lum = float(np.mean(gray_work))
        total_pixels = float(gray_work.size)

        # Symmetrical penalty from nominal midpoint (128.0)
        lum_deviation = abs(mean_lum - 128.0) / 128.0
        base_illum = 100.0 - (lum_deviation ** 1.35) * 100.0

        # Clipping penalties for extreme saturation or pitch-black pixels
        dark_pixels = float(np.count_nonzero(gray_work < 10.0))
        bright_pixels = float(np.count_nonzero(gray_work > 245.0))
        f_dark = dark_pixels / total_pixels
        f_bright = bright_pixels / total_pixels
        clipping_penalty = min(40.0, (f_dark + f_bright) * 50.0)

        s_illum = float(np.clip(base_illum - clipping_penalty, 0.0, 100.0))

        # 5. Dimension 3: Contrast (Dynamic Range Dispersion)
        std_dev = float(np.std(gray_work))
        # Optimal facial contrast is typically around std in [35.0, 65.0]
        # std < 8.0 represents severe featureless washed out or dark crop
        if std_dev <= 45.0:
            s_contrast = (std_dev / 45.0) * 100.0
        else:
            # Gentle penalty if contrast is excessively harsh (> 75.0)
            excess_penalty = max(0.0, std_dev - 75.0) * 1.5
            s_contrast = max(50.0, 100.0 - excess_penalty)
        s_contrast = float(np.clip(s_contrast, 0.0, 100.0))

        # 6. Dimension 4: Resolution & Scale (Conservative Pixel Density Metric)
        min_dim = float(min(h, w))
        # Note: Resolution measures available pixel grid size relative to
        # typical neural embedding input (160x160). It does not guarantee biometric accuracy.
        if min_dim < cls.MIN_FACE_WIDTH:
            s_resol = (min_dim / float(cls.MIN_FACE_WIDTH)) * 30.0
        elif min_dim <= cls.OPTIMAL_MIN_DIMENSION:
            # Linear scaling from 30.0 at 40px to 95.0 at 160px
            ratio = (min_dim - cls.MIN_FACE_WIDTH) / (cls.OPTIMAL_MIN_DIMENSION - cls.MIN_FACE_WIDTH)
            s_resol = 30.0 + (ratio * 65.0)
        else:
            # Diminishing returns beyond 160px up to 320px
            extra_ratio = min(1.0, (min_dim - 160.0) / 160.0)
            s_resol = 95.0 + (extra_ratio * 5.0)
        s_resol = float(np.clip(s_resol, 0.0, 100.0))

        # 7. Dimension 5: Composite Quality Score with Bottleneck Guard
        # Weighted arithmetic base
        s_base = (
            cls.WEIGHT_SHARPNESS * s_sharp
            + cls.WEIGHT_ILLUMINATION * s_illum
            + cls.WEIGHT_CONTRAST * s_contrast
            + cls.WEIGHT_RESOLUTION * s_resol
        )

        # Bottleneck attenuation: if any single critical metric falls below 30.0,
        # attenuate the composite score so a severe defect is not masked.
        min_component = min(s_sharp, s_illum, s_contrast, s_resol)
        if min_component < 30.0:
            attenuation = 0.50 + (0.50 * (min_component / 30.0))
            composite_score = float(np.clip(s_base * attenuation, 0.0, 100.0))
        else:
            composite_score = float(np.clip(s_base, 0.0, 100.0))

        # 8. Identify Specific Quality Defects
        defects: List[str] = []
        if s_sharp < 30.0 or raw_lap_var < 4.0:
            defects.append("LOW_SHARPNESS")
        if mean_lum < 40.0:
            defects.append("UNDEREXPOSURE")
        elif mean_lum > 215.0:
            defects.append("OVEREXPOSURE")
        if s_contrast < 20.0 or std_dev < 8.0:
            defects.append("LOW_CONTRAST")
        if min_dim < cls.MIN_FACE_WIDTH:
            defects.append("INSUFFICIENT_RESOLUTION")

        # 9. Quality Tier Classification
        if composite_score >= 75.0 and not defects:
            quality_tier = "OPTIMAL"
        elif composite_score >= 50.0 and len(defects) <= 1:
            quality_tier = "ACCEPTABLE"
        elif composite_score >= 30.0:
            quality_tier = "SUBOPTIMAL"
        else:
            quality_tier = "REJECT"

        is_acceptable = bool(composite_score >= 50.0 and len(defects) == 0)

        # 10. Assemble Diagnostic Dictionary
        diagnostics = {
            "composite_score": round(composite_score, 2),
            "quality_tier": quality_tier,
            "is_acceptable": is_acceptable,
            "metrics": {
                "sharpness": {
                    "score": round(s_sharp, 2),
                    "raw_laplacian_variance": round(raw_lap_var, 4),
                },
                "illumination": {
                    "score": round(s_illum, 2),
                    "mean_luminance": round(mean_lum, 2),
                    "dark_clipping_pct": round(f_dark * 100.0, 2),
                    "bright_clipping_pct": round(f_bright * 100.0, 2),
                },
                "contrast": {
                    "score": round(s_contrast, 2),
                    "std_deviation": round(std_dev, 2),
                },
                "resolution": {
                    "score": round(s_resol, 2),
                    "dimensions": [int(w), int(h)],
                    "min_dimension": int(min_dim),
                },
            },
            "defects": defects,
        }

        # Attach remediation advice
        diagnostics["remediation_advice"] = cls.get_remediation_advice(diagnostics)

        return diagnostics

    @classmethod
    def get_remediation_advice(cls, diagnostics: Dict[str, Any]) -> List[str]:
        """Generates concise, non-contradictory actionable advice

        based on computed diagnostic scores and detected defects.

        Parameters
        ----------
        diagnostics : dict
            Dictionary produced by analyze_crop().

        Returns
        -------
        list of str
            Actionable user instructions for remediation.
        """
        advice: List[str] = []
        defects = diagnostics.get("defects", [])
        metrics = diagnostics.get("metrics", {})

        illum_data = metrics.get("illumination", {})
        sharp_data = metrics.get("sharpness", {})
        resol_data = metrics.get("resolution", {})
        contrast_data = metrics.get("contrast", {})

        # Illumination advice (strictly mutually exclusive)
        if "UNDEREXPOSURE" in defects or illum_data.get("score", 100.0) < 35.0:
            if illum_data.get("mean_luminance", 128.0) < 100.0:
                advice.append("Improve frontal lighting on the face and avoid strong backlighting.")
        elif "OVEREXPOSURE" in defects or illum_data.get("score", 100.0) < 35.0:
            if illum_data.get("mean_luminance", 128.0) > 160.0:
                advice.append("Reduce direct glare, harsh overhead lighting, or camera exposure.")

        # Sharpness advice
        if "LOW_SHARPNESS" in defects or sharp_data.get("score", 100.0) < 35.0:
            advice.append("Keep the camera steady, remain still during capture, and ensure the lens is clean.")

        # Resolution advice
        if "INSUFFICIENT_RESOLUTION" in defects or resol_data.get("score", 100.0) < 35.0:
            advice.append("Move closer to the camera to ensure the face occupies sufficient pixel area.")

        # Contrast advice
        if "LOW_CONTRAST" in defects or contrast_data.get("score", 100.0) < 25.0:
            advice.append("Adjust ambient lighting to enhance contrast between the subject and the background.")

        # If no specific defects, provide positive guidance
        if not advice:
            comp = diagnostics.get("composite_score", 0.0)
            if comp >= 75.0:
                advice.append("Image quality is optimal for biometric processing.")
            else:
                advice.append("Image quality is acceptable; minor lighting or stability adjustments may improve consistency.")

        return advice
