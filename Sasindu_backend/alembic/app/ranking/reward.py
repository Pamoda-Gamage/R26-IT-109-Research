TOP_K_FULL_REWARD = 3
MAX_RANK_CONSIDERED = 25  # matches SearchAgent's normal top_n (Phase 3) -- beyond this, reward floors at 0


def compute_reward(selected_rank: int | None) -> float:
    """srs.md §3.2.6: full reward for top-3 selection, partial for lower ranks, zero for abandonment."""
    if selected_rank is None:
        return 0.0
    if selected_rank <= TOP_K_FULL_REWARD:
        return 1.0
    if selected_rank >= MAX_RANK_CONSIDERED:
        return 0.0
    span = MAX_RANK_CONSIDERED - TOP_K_FULL_REWARD
    return round(1.0 - (selected_rank - TOP_K_FULL_REWARD) / span, 4)
