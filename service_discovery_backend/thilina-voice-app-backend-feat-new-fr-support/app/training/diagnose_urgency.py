"""Diagnostic for the "everything comes out HIGH urgency" bug.

Run from the backend dir:
    ./.venv/Scripts/python.exe -m app.training.diagnose_urgency

It does three things:
1. Sanity-checks the live urgency artifact (classes, that it's really the
   urgency head and not a mis-saved copy of another classifier).
2. Scores a small labelled set of single utterances and prints the predicted
   label / confidence / full candidate ranking.
3. Reproduces the train/serve skew: scores the SAME utterances again after
   concatenating them into one multi-line blob (what build_case_context used
   to feed the model) and shows how the distribution shifts toward "high".
"""
from __future__ import annotations

from collections import Counter

from app.services.predict_service import (
    predict, urgency_clf, urgency_encoder, intent_encoder, embedder, EMBEDDER_NAME,
)

# (text, expected urgency) - deliberately mundane cases first.
SAMPLES = [
    ("i want to schedule a garden cleanup sometime next week", "low"),
    ("can someone come paint the spare room, no rush", "low"),
    ("my tv remote stopped working, need a replacement sometime", "low"),
    ("the kitchen tap drips a bit, please send a plumber this week", "medium"),
    ("ac is not cooling well, would like it looked at in the next day or two", "medium"),
    ("fridge making noise, want a technician soon", "medium"),
    ("water is flooding the bathroom right now, need a plumber immediately", "high"),
    ("someone has collapsed and is not breathing, send help now", "high"),
    ("i can smell gas in the kitchen, come right away", "high"),
]


def _print_artifact_sanity() -> None:
    print("=" * 70)
    print("ARTIFACT SANITY")
    print(f"  embedder            : {EMBEDDER_NAME}")
    print(f"  urgency classes     : {list(urgency_encoder.classes_)}")
    print(f"  urgency clf n_class : {len(urgency_clf.classes_)}")
    print(f"  urgency clf n_feat  : {getattr(urgency_clf, 'n_features_in_', '?')}")
    print(f"  intent classes      : {list(intent_encoder.classes_)}")
    overlap = set(map(str, urgency_encoder.classes_)) & set(map(str, intent_encoder.classes_))
    if overlap:
        print(f"  !! urgency/intent encoder classes overlap: {overlap} "
              f"(possible mis-saved artifact)")
    print()


def _score(text: str) -> dict:
    return predict(text, urgency_text=text)


def _run(label: str, texts: list[str]) -> Counter:
    print("=" * 70)
    print(label)
    dist: Counter = Counter()
    for t in texts:
        p = _score(t)
        dist[p["urgency"]] += 1
        cands = ", ".join(f'{c["label"]}={c["confidence"]:.2f}' for c in p["urgency_candidates"])
        ov = f'  [override: {p["urgency_override"]}]' if p.get("urgency_override") else ""
        print(f'  {p["urgency"]:>6}  conf={p["urgency_confidence"]:.2f}  ({cands}){ov}')
        print(f'         <- {t[:80]}')
    print(f"  distribution: {dict(dist)}")
    print()
    return dist


def main() -> None:
    _print_artifact_sanity()

    exp = Counter(u for _, u in SAMPLES)
    print(f"expected distribution: {dict(exp)}\n")

    per_message = _run("PER-MESSAGE (each utterance scored alone - the fix)",
                       [t for t, _ in SAMPLES])

    blob = "\n".join(t for t, _ in SAMPLES)
    _run("CONCATENATED (whole blob scored once - the old build_case_context path)",
         [blob])

    # Also: score each sample prefixed with the growing history, mimicking a
    # multi-turn chat where the model saw the full narrative every turn.
    growing = ["\n".join(t for t, _ in SAMPLES[: i + 1]) for i in range(len(SAMPLES))]
    _run("GROWING HISTORY (message i scored with messages 0..i concatenated)",
         growing)

    print("=" * 70)
    print("READ: if PER-MESSAGE tracks the expected distribution but the "
          "CONCATENATED / GROWING runs skew to 'high', the bug is train/serve "
          "skew and the dispatch_service fix (score urgency on the latest "
          "message only) addresses it. If PER-MESSAGE is itself all 'high', "
          "the artifact/threshold needs retraining (see train_pipeline.py).")


if __name__ == "__main__":
    main()
