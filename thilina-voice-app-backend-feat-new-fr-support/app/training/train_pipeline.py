"""
Full pipeline : dataset -> embedding -> train classifiers -> save models

Install requirements first:
    pip install sentence-transformers scikit-learn joblib pandas openpyxl

Run this on first build, or whenever retraining. Key properties (see the
"everything comes out HIGH urgency" investigation):

- Each head (intent / service / urgency) gets its OWN train/test split,
  stratified on that head's labels — the old code stratified on intent only,
  so urgency class balance across train/test was left to chance.
- The urgency head is wrapped in CalibratedClassifierCV so predict_proba is
  meaningful and the confidence gate in dispatch_service actually works.
- Urgency is trained on the single `transcript` column (one short utterance),
  which is the contract the serving code now honours: dispatch_service scores
  urgency on the latest message only, never the whole concatenated case.
- Writes ../models/model_card.json (date, row counts, held-out metrics) so a
  stale/mis-saved artifact is detectable at serve time via _model_info().
"""
import datetime as dt
import json
import os

import numpy as np
import pandas as pd
from sentence_transformers import SentenceTransformer
from sklearn.calibration import CalibratedClassifierCV
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import classification_report, confusion_matrix

import joblib

HERE = os.path.dirname(__file__)
MODELS_DIR = os.path.abspath(os.path.join(HERE, "..", "models"))
XLSX_PATH = os.path.join(HERE, "Intent_Classification_Dataset_V2_labeled.xlsx")
CSV_PATH = os.path.join(HERE, "dataset_with_index.csv")

REQUIRED_COLS = ["transcript", "intent", "service_type", "urgency_level"]
EMBEDDER_NAME = "all-MiniLM-L6-v2"
RANDOM_STATE = 42


# STEP 1 : Load labeled dataset  (prefer the source .xlsx, fall back to the
# csv snapshot a previous run wrote next to this script)
def load_dataset() -> pd.DataFrame:
    if os.path.exists(XLSX_PATH):
        df = pd.read_excel(XLSX_PATH)
        src = XLSX_PATH
    elif os.path.exists(CSV_PATH):
        df = pd.read_csv(CSV_PATH)
        src = CSV_PATH
    else:
        raise FileNotFoundError(
            f"No dataset found. Put the labelled file at {XLSX_PATH} "
            f"(or a snapshot csv at {CSV_PATH})."
        )
    df.columns = [c.strip() for c in df.columns]
    missing = [c for c in REQUIRED_COLS if c not in df.columns]
    if missing:
        raise ValueError(f"{src} is missing required columns: {missing}")
    df = df.dropna(subset=REQUIRED_COLS)
    print(f"Loaded {len(df)} rows from {os.path.basename(src)}")
    return df


def audit(df: pd.DataFrame) -> dict:
    print("\n=== LABEL BALANCE ===")
    counts = {}
    for col in ("intent", "service_type", "urgency_level"):
        vc = df[col].value_counts()
        counts[col] = vc.to_dict()
        print(f"\n{col}:")
        print(vc)
    print("\nurgency_level x intent crosstab:")
    print(pd.crosstab(df["intent"], df["urgency_level"]))
    return counts


def train_head(name: str, X, y, encoder: LabelEncoder, calibrate: bool = False):
    """One stratified split + fit + report for a single classifier head."""
    X_tr, X_te, y_tr, y_te = train_test_split(
        X, y, test_size=0.2, random_state=RANDOM_STATE, stratify=y
    )
    base = LogisticRegression(max_iter=1000, class_weight="balanced")
    if calibrate:
        # sigmoid (Platt) — robust for the modest per-class counts here.
        clf = CalibratedClassifierCV(base, method="sigmoid", cv=3)
    else:
        clf = base
    clf.fit(X_tr, y_tr)

    y_pred = clf.predict(X_te)
    report = classification_report(
        y_te, y_pred, target_names=list(encoder.classes_), output_dict=True, zero_division=0
    )
    print(f"\n=== {name.upper()} CLASSIFICATION REPORT ===")
    print(classification_report(y_te, y_pred, target_names=list(encoder.classes_), zero_division=0))
    print("confusion matrix (rows=true, cols=pred):", list(encoder.classes_))
    print(confusion_matrix(y_te, y_pred))
    return clf, report


def main() -> None:
    os.makedirs(MODELS_DIR, exist_ok=True)
    df = load_dataset()
    counts = audit(df)

    print(f"\nEmbedding {len(df)} transcripts with {EMBEDDER_NAME} ...")
    embedder = SentenceTransformer(EMBEDDER_NAME)
    X = embedder.encode(
        df["transcript"].tolist(), batch_size=64, show_progress_bar=True, convert_to_numpy=True
    )
    print("Embedding shape:", X.shape)

    intent_encoder = LabelEncoder()
    service_encoder = LabelEncoder()
    urgency_encoder = LabelEncoder()
    y_intent = intent_encoder.fit_transform(df["intent"])
    y_service = service_encoder.fit_transform(df["service_type"])
    y_urgency = urgency_encoder.fit_transform(df["urgency_level"])

    intent_clf, intent_report = train_head("intent", X, y_intent, intent_encoder)
    service_clf, service_report = train_head("service", X, y_service, service_encoder)
    urgency_clf, urgency_report = train_head(
        "urgency", X, y_urgency, urgency_encoder, calibrate=True
    )

    # STEP 7 : save
    joblib.dump(intent_clf, os.path.join(MODELS_DIR, "intent_classifier_lr.joblib"))
    joblib.dump(service_clf, os.path.join(MODELS_DIR, "service_classifier_lr.joblib"))
    joblib.dump(urgency_clf, os.path.join(MODELS_DIR, "urgency_classifier_lr.joblib"))
    joblib.dump(intent_encoder, os.path.join(MODELS_DIR, "intent_encoder_lr.joblib"))
    joblib.dump(service_encoder, os.path.join(MODELS_DIR, "service_encoder_lr.joblib"))
    joblib.dump(urgency_encoder, os.path.join(MODELS_DIR, "urgency_encoder_lr.joblib"))

    card = {
        "trained_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "embedder": EMBEDDER_NAME,
        "rows": int(len(df)),
        "label_counts": counts,
        "urgency_calibrated": True,
        "urgency_trained_on": "single transcript (per-message, not per-case)",
        "metrics": {
            "intent": {"macro_f1": intent_report["macro avg"]["f1-score"]},
            "service": {"macro_f1": service_report["macro avg"]["f1-score"]},
            "urgency": {
                "macro_f1": urgency_report["macro avg"]["f1-score"],
                "per_class": {
                    k: {"precision": v["precision"], "recall": v["recall"], "f1": v["f1-score"]}
                    for k, v in urgency_report.items()
                    if k in set(map(str, urgency_encoder.classes_))
                },
            },
        },
    }
    with open(os.path.join(MODELS_DIR, "model_card.json"), "w", encoding="utf-8") as f:
        json.dump(card, f, indent=2)

    print("\nSaved 6 .joblib artifacts + model_card.json to", MODELS_DIR)
    print("urgency macro-F1:", card["metrics"]["urgency"]["macro_f1"])
    print("Re-run app.training.diagnose_urgency to sanity-check before shipping.")


if __name__ == "__main__":
    main()
