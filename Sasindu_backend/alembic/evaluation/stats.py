import numpy as np


def bootstrap_ci(
    samples: list[float], n_resamples: int = 2000, confidence: float = 0.95, seed: int = 42
) -> tuple[float, float, float]:
    arr = np.array(samples)
    rng = np.random.default_rng(seed)
    means = np.empty(n_resamples)
    for i in range(n_resamples):
        resample = rng.choice(arr, size=len(arr), replace=True)
        means[i] = resample.mean()

    alpha = 1 - confidence
    lo, hi = np.quantile(means, [alpha / 2, 1 - alpha / 2])
    return float(arr.mean()), float(lo), float(hi)
