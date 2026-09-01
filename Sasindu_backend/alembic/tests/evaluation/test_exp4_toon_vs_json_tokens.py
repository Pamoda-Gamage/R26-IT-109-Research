from evaluation.experiments.exp4_toon_vs_json_tokens import generate_sample_requests, run_experiment


def test_toon_uses_fewer_tokens_than_json_on_average():
    samples = generate_sample_requests(n=100, seed=42)
    df = run_experiment(samples, seed=42)
    toon_mean = df[df["format"] == "toon"]["token_count_estimate"].mean()
    json_mean = df[df["format"] == "json"]["token_count_estimate"].mean()
    assert toon_mean < json_mean


def test_run_experiment_is_reproducible():
    samples_a = generate_sample_requests(n=20, seed=7)
    samples_b = generate_sample_requests(n=20, seed=7)
    assert samples_a == samples_b
