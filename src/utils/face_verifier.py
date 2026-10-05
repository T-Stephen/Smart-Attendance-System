import os
import pickle
import numpy as np


# ============================================================
# CONFIGURATION
# ============================================================

EMBEDDINGS_FILE = "models/student_embeddings.pkl"

# Cosine-distance threshold.
#
# Lower = stricter verification
# Higher = more tolerant verification
#
# Start with 0.55 and adjust after testing.
VERIFICATION_THRESHOLD = 0.55


# ============================================================
# LOAD STUDENT EMBEDDINGS
# ============================================================

_student_embeddings = None
_student_labels = None


def load_embeddings():

    global _student_embeddings
    global _student_labels

    if _student_embeddings is not None:
        return

    if not os.path.exists(EMBEDDINGS_FILE):

        raise FileNotFoundError(
            f"Student embeddings file not found: "
            f"{EMBEDDINGS_FILE}"
        )

    with open(
        EMBEDDINGS_FILE,
        "rb"
    ) as file:

        data = pickle.load(file)

    _student_embeddings = np.asarray(
        data["embeddings"],
        dtype=np.float32
    )

    _student_labels = np.asarray(
        data["labels"]
    )

    print("=" * 60)
    print("FACE VERIFIER")
    print("=" * 60)

    print(
        "Embeddings loaded :",
        len(_student_embeddings)
    )

    print(
        "Students loaded   :",
        len(set(_student_labels))
    )

    print(
        "Verification threshold :",
        VERIFICATION_THRESHOLD
    )

    print("=" * 60)


# ============================================================
# COSINE DISTANCE
# ============================================================

def cosine_distance(
    embedding1,
    embedding2
):

    embedding1 = np.asarray(
        embedding1,
        dtype=np.float32
    )

    embedding2 = np.asarray(
        embedding2,
        dtype=np.float32
    )

    norm1 = np.linalg.norm(
        embedding1
    )

    norm2 = np.linalg.norm(
        embedding2
    )

    if norm1 == 0 or norm2 == 0:

        return 1.0

    similarity = np.dot(
        embedding1,
        embedding2
    ) / (
        norm1 * norm2
    )

    similarity = np.clip(
        similarity,
        -1.0,
        1.0
    )

    return float(
        1.0 - similarity
    )


# ============================================================
# VERIFY FACE
# ============================================================

def verify_face(
    embedding
):

    load_embeddings()

    if (
        _student_embeddings is None
        or len(_student_embeddings) == 0
    ):

        return (
            False,
            None,
            None
        )

    embedding = np.asarray(
        embedding,
        dtype=np.float32
    )

    # --------------------------------------------------------
    # Calculate distance against every registered face
    # --------------------------------------------------------

    distances = []

    for stored_embedding in _student_embeddings:

        distance = cosine_distance(
            embedding,
            stored_embedding
        )

        distances.append(
            distance
        )

    distances = np.asarray(
        distances
    )

    # --------------------------------------------------------
    # Find closest registered face
    # --------------------------------------------------------

    best_index = int(
        np.argmin(distances)
    )

    best_distance = float(
        distances[best_index]
    )

    best_student_id = str(
        _student_labels[best_index]
    )

    # --------------------------------------------------------
    # Verification decision
    # --------------------------------------------------------

    verified = (
        best_distance
        <= VERIFICATION_THRESHOLD
    )

    if not verified:

        return (
            False,
            None,
            best_distance
        )

    return (
        True,
        best_student_id,
        best_distance
    )