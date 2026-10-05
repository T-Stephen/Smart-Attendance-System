# Biometric Model Registry & Privacy Architecture

This directory serves as the local runtime store for facial feature embeddings and identity encoding artifacts utilized by the Smart Campus AI Attendance System.

---

## 1. Biometric Privacy & Public Repository Notice

In compliance with student privacy regulations (FERPA), biometric data security policies, and ethical AI development guidelines:

- **No real student facial embeddings are included in this public repository.**
- All production embedding galleries (`student_embeddings.pkl`, `embeddings.pkl`) and identity mappings (`student_label_encoder.pkl`) are intentionally excluded via `.gitignore`.
- No raw face images, student identities, or personal identifiable biometric vectors are hosted publicly.

---

## 2. Embedding Architecture

The system utilizes deep convolutional metric learning based on the **Inception-ResNet-v1 (FaceNet)** architecture:

- **Dimensionality:** 512-dimensional continuous feature representation per face.
- **Normalization:** Vectors are $L_2$-normalized prior to gallery storage and comparison:
  $$\|v\|_2 = 1.0$$
- **Metric Space:** Pairwise distances are computed via standard Euclidean distance ($L_2$ norm):
  $$d(u, v) = \sqrt{\sum_{i=1}^{512} (u_i - v_i)^2}$$
- **Threshold Calibration:** A strict threshold of $d \le 0.65$ with an ambiguity margin of $\Delta d \ge 0.04$ is enforced for identity confirmation.

---

## 3. Provisioning Authorized Embeddings Locally

To deploy the system in an authorized campus environment with participating students:

1. **Acquire Authorized Images:**
   Capture facial training samples using the built-in registration flow:
   ```bash
   python src/register_student.py
   ```
   *Note: Ensure formal institutional consent is acquired prior to image capture.*

2. **Generate Embedding Gallery:**
   Execute the automated embedding extraction script:
   ```bash
   python src/extract_student_embeddings.py
   ```
   This script will:
   - Detect faces using MTCNN.
   - Extract normalized 512-dimensional embeddings via FaceNet.
   - Save the serialized gallery to `models/student_embeddings.pkl` and mapping to `models/student_label_encoder.pkl`.

3. **Verify Deployment:**
   Run the regression validation suite to confirm embedding gallery integrity:
   ```bash
   python tests/test_dashboard_regression.py
   ```

---

## 4. Ethical & Institutional Deployment Guidelines

Biometric attendance systems handle sensitive personal representations. Institutional deployments must ensure:
- Local database and embedding storage encryption at rest.
- Strict physical and network access controls to server nodes hosting `.pkl` and `.db` files.
- Clear data retention and deletion policies upon student graduation or consent revocation.
