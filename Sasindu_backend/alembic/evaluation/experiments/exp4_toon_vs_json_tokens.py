import json
import random
from pathlib import Path

import pandas as pd

from app.context.toon_serializer import to_toon
from evaluation.stats import bootstrap_ci


def _estimate_tokens(text: str) -> int:
    # Whitespace/punctuation-based ~4-chars/token heuristic; swap in the exact
    # Anthropic tokenizer via messages.count_tokens for provider-exact figures.
    return max(1, len(text) // 4)


def generate_sample_requests(n: int, seed: int) -> list[dict]:
    rng = random.Random(seed)
    service_types = ["plumbing", "electrical", "cleaning", "locksmith"]
    time_slots = ["morning_peak", "midday", "evening_peak", "night"]
    samples = []
    for i in range(n):
        samples.append(
            {
                "raw_text": f"sample request {i} about {rng.choice(service_types)} issue",
                "region": rng.choice(["colombo-01", "colombo-02", "dehiwala"]),
                "time_slot": rng.choice(time_slots),
            }
        )
    return samples


def run_experiment(sample_requests: list[dict], seed: int) -> pd.DataFrame:
    rows = []
    for i, sample in enumerate(sample_requests):
        rows_for_toon = [
            {"field": "raw_text", "value": sample["raw_text"]},
            {"field": "region", "value": sample["region"]},
            {"field": "time_slot", "value": sample["time_slot"]},
        ]
        toon_text = to_toon(rows_for_toon)
        json_text = json.dumps(sample)

        rows.append(
            {
                "request_id": i,
                "format": "toon",
                "char_count": len(toon_text),
                "token_count_estimate": _estimate_tokens(toon_text),
            }
        )
        rows.append(
            {
                "request_id": i,
                "format": "json",
                "char_count": len(json_text),
                "token_count_estimate": _estimate_tokens(json_text),
            }
        )
    return pd.DataFrame(rows)


def main(n: int = 100, seed: int = 42) -> None:
    samples = generate_sample_requests(n, seed)
    df = run_experiment(samples, seed)
    out_dir = Path(__file__).parent.parent / "results"
    out_dir.mkdir(exist_ok=True)
    df.to_csv(out_dir / "exp4_toon_vs_json_tokens.csv", index=False)

    for fmt in ["toon", "json"]:
        tokens = df[df["format"] == fmt]["token_count_estimate"].tolist()
        mean, lo, hi = bootstrap_ci(tokens, seed=seed)
        print(f"{fmt}: mean_tokens={mean:.1f} CI=[{lo:.1f},{hi:.1f}]")


if __name__ == "__main__":
    main()
