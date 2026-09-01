from evaluation.experiments.exp1_adaptive_vs_static import run_experiment


def test_run_experiment_returns_expected_columns():
    df = run_experiment(n_rounds=50, seed=42)
    assert set(df.columns) == {"round", "condition", "context", "reward", "cumulative_regret"}
    assert set(df["condition"].unique()) == {"adaptive", "static_baseline"}


def test_adaptive_condition_achieves_lower_final_regret_than_static():
    df = run_experiment(n_rounds=400, seed=42)
    final_adaptive_regret = df[df.condition == "adaptive"]["cumulative_regret"].iloc[-1]
    final_static_regret = df[df.condition == "static_baseline"]["cumulative_regret"].iloc[-1]
    assert final_adaptive_regret < final_static_regret


def test_run_experiment_is_reproducible_given_same_seed():
    df_a = run_experiment(n_rounds=100, seed=42)
    df_b = run_experiment(n_rounds=100, seed=42)
    assert df_a["reward"].tolist() == df_b["reward"].tolist()
