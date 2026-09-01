from evaluation.stats import bootstrap_ci


def test_bootstrap_ci_bounds_contain_the_sample_mean():
    samples = [1.0, 2.0, 3.0, 4.0, 5.0] * 20
    mean, lo, hi = bootstrap_ci(samples, seed=42)
    assert lo <= mean <= hi


def test_bootstrap_ci_is_deterministic_given_same_seed():
    samples = [1.0, 5.0, 3.0, 8.0, 2.0] * 10
    result_a = bootstrap_ci(samples, seed=7)
    result_b = bootstrap_ci(samples, seed=7)
    assert result_a == result_b


def test_bootstrap_ci_width_is_nonzero_for_varied_data():
    samples = [1.0] * 50 + [10.0] * 50
    mean, lo, hi = bootstrap_ci(samples, seed=1)
    assert hi > lo
    assert lo < mean < hi
