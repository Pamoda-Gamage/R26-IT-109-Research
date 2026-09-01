import argparse

from evaluation.experiments import (
    exp1_adaptive_vs_static,
    exp2_routing_benchmark,
    exp3_retrieval_recall,
    exp4_toon_vs_json_tokens,
)


def main():
    parser = argparse.ArgumentParser(description="Run all thesis evaluation experiments from a single seed.")
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    print("=== Experiment 1: Adaptive vs Static Baseline ===")
    exp1_adaptive_vs_static.main(seed=args.seed)

    print("\n=== Experiment 2: Dijkstra vs A* Routing Benchmark ===")
    exp2_routing_benchmark.main(seed=args.seed)

    print("\n=== Experiment 3: Retrieval Recall@N ===")
    exp3_retrieval_recall.main()

    print("\n=== Experiment 4: TOON vs JSON Token Efficiency ===")
    exp4_toon_vs_json_tokens.main(seed=args.seed)

    print("\nAll experiments complete. CSVs written to evaluation/results/")


if __name__ == "__main__":
    main()
