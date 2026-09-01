def update_reliability(alpha: float, beta: float, reward: float) -> tuple[float, float]:
    """Conjugate Beta-Bernoulli update. `reward` in [0, 1] is treated as a
    (possibly fractional) Bernoulli outcome — full success=1.0 fully credits alpha,
    full failure=0.0 fully credits beta, partial reward splits proportionally."""
    if not 0.0 <= reward <= 1.0:
        raise ValueError(f"reward must be in [0, 1], got {reward}")
    return alpha + reward, beta + (1.0 - reward)
