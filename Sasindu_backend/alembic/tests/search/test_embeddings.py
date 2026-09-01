import numpy as np

from app.search.embeddings import Embedder


def test_encode_returns_normalized_vectors():
    embedder = Embedder()
    vectors = embedder.encode(["fast plumbing repair", "24/7 emergency plumber"])
    assert vectors.shape == (2, 384)
    norms = np.linalg.norm(vectors, axis=1)
    assert np.allclose(norms, 1.0, atol=1e-5)


def test_similar_sentences_are_closer_than_dissimilar_ones():
    embedder = Embedder()
    a, b, c = embedder.encode(
        [
            "emergency plumbing service available 24 hours",
            "urgent plumber needed right now",
            "professional wedding photography services",
        ]
    )
    assert np.dot(a, b) > np.dot(a, c)
