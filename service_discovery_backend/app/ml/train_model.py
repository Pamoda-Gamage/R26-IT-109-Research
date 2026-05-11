"""Train lightweight text classifiers used by the FastAPI backend.

The training data intentionally includes Sinhala-English, Tamil-English, and
fragmented urgent phrases so the prototype can demonstrate the Objective 1
capability from the uploaded research component without requiring a cloud model.
"""
from __future__ import annotations

from pathlib import Path
from typing import List, Dict
import csv
import random

import joblib
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, accuracy_score

ROOT = Path(__file__).resolve().parents[1]
MODELS_DIR = ROOT / "models_store"
DATA_DIR = ROOT / "data"
MODELS_DIR.mkdir(exist_ok=True)
DATA_DIR.mkdir(exist_ok=True)

INTENTS = ["hospital", "plumber", "electrician", "mechanic", "taxi", "police", "fire", "cleaning"]

BASE_EXAMPLES: Dict[str, List[str]] = {
    "hospital": [
        "hospital ekak near me urgent", "doctor kenek ikmanata one", "amma asaneepa hospital now",
        "nearby clinic emergency", "medicine ganna place langama", "ambulance needed now",
        "podi accident hospital", "fever high doctor urgent", "hospital yanna ona", "maruthuvamanai venum urgent",
        "doctor please fast", "injury help hospital", "accident ikmanata hospital", "sick person help"
    ],
    "plumber": [
        "pipe leak wenawa plumber one", "bathroom water leak ikmanata", "tap kadila repair karanna",
        "plumber near me", "water line burst urgent", "sink block wela", "bathroom issue plumber",
        "drainage blocked service", "pipe ekak pupurala", "water problem house", "plumber ayya urgent",
        "toilet block repair", "leak leak kitchen", "nal plumber venum"
    ],
    "electrician": [
        "current na electrician one", "light trip wenawa", "electric repair urgent",
        "power cut in house", "switch board smoke", "wire problem", "fan not working electrician",
        "plug point repair", "mains trip karanawa", "electrician near me", "voltage issue help",
        "light ekak hadanna", "electric shock danger", "wire sparking urgent"
    ],
    "mechanic": [
        "car breakdown mechanic one", "bike start wenne na", "vehicle stopped road side",
        "tyre puncture help", "engine issue urgent", "mechanic near me", "car battery dead",
        "threewheel repair", "brake problem", "vehicle smoke coming", "bike mechanic venum",
        "garage support now", "accident vehicle repair", "car key stuck"
    ],
    "taxi": [
        "taxi near me", "cab ekak ikmanata one", "airport yanna cab", "ride needed now",
        "hire ekak call karanna", "taxi urgent", "vehicle to hospital", "colombo yanna car",
        "drop one now", "uber wage taxi", "van needed family", "school pickup taxi",
        "train station yanna", "cab venum fast"
    ],
    "police": [
        "police help urgent", "robbery happening", "fight outside house", "thief came now",
        "accident police report", "security issue", "violence near me", "police station number",
        "harassment complaint", "emergency police please", "dangerous person", "lost child police",
        "traffic police needed", "thief catch help"
    ],
    "fire": [
        "fire fire help", "gas leak fire brigade", "house burning", "smoke coming kitchen",
        "electrical fire urgent", "fire service now", "burning smell danger", "flame in shop",
        "fire brigade call", "building smoke", "cylinder leak urgent", "kitchen fire",
        "car fire road", "factory fire help"
    ],
    "cleaning": [
        "cleaning service one", "house clean karanna kenek", "garden cleaning near me",
        "office cleaning needed", "washroom cleaning", "after party clean", "deep cleaning service",
        "room clean karanna", "sweep mop service", "carpet cleaning", "maid service request",
        "cleaner near me", "home cleaning tomorrow", "window cleaning"
    ],
}

URGENCY_PHRASES = {
    "high": ["urgent", "ikmanata", "now", "emergency", "danger", "fast", "help", "asap", "immediately"],
    "moderate": ["today", "soon", "quick", "within hour", "need service", "please come", "important"],
    "normal": ["tomorrow", "this week", "book", "schedule", "normal", "later", "appointment"]
}


def build_rows() -> List[Dict[str, str]]:
    rows: List[Dict[str, str]] = []
    for intent, examples in BASE_EXAMPLES.items():
        for text in examples:
            lowered = text.lower()
            if any(w in lowered for w in URGENCY_PHRASES["high"]):
                urgency = "high"
            elif any(w in lowered for w in URGENCY_PHRASES["moderate"]):
                urgency = "moderate"
            else:
                urgency = "normal"
            rows.append({"transcript": text, "intent": intent, "urgency": urgency})
            rows.append({"transcript": f"{text} near me", "intent": intent, "urgency": urgency})
            rows.append({"transcript": f"{text} sri lanka", "intent": intent, "urgency": urgency})
    # Fragmented phrases deliberately included for incomplete-speech handling.
    fragments = [
        ("accident... hospital... ikmanata", "hospital", "high"),
        ("pipe... leak... water... urgent", "plumber", "high"),
        ("current... spark... danger", "electrician", "high"),
        ("car... road... stopped", "mechanic", "moderate"),
        ("cab... airport... now", "taxi", "high"),
        ("thief... police... help", "police", "high"),
        ("fire... smoke... kitchen", "fire", "high"),
        ("clean... house... tomorrow", "cleaning", "normal"),
    ]
    for text, intent, urgency in fragments:
        rows.append({"transcript": text, "intent": intent, "urgency": urgency})
    # Add controlled templates to make model more stable.
    suburbs = ["Maharagama", "Colombo", "Kandy", "Galle", "Negombo", "Jaffna"]
    for intent in INTENTS:
        for suburb in suburbs:
            rows.append({"transcript": f"need {intent} service in {suburb} today", "intent": intent, "urgency": "moderate"})
            rows.append({"transcript": f"book {intent} service {suburb} tomorrow", "intent": intent, "urgency": "normal"})
            rows.append({"transcript": f"{intent} emergency {suburb} now", "intent": intent, "urgency": "high"})
    random.shuffle(rows)
    return rows


def save_dataset(rows: List[Dict[str, str]]) -> None:
    path = DATA_DIR / "multilingual_intent_urgency_training_data.csv"
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["transcript", "intent", "urgency"])
        writer.writeheader()
        writer.writerows(rows)


def train() -> None:
    rows = build_rows()
    save_dataset(rows)
    texts = [r["transcript"] for r in rows]
    intents = [r["intent"] for r in rows]
    urgencies = [r["urgency"] for r in rows]

    intent_model = Pipeline([
        ("tfidf", TfidfVectorizer(analyzer="char_wb", ngram_range=(3, 5), lowercase=True)),
        ("clf", LogisticRegression(max_iter=1000, class_weight="balanced")),
    ])
    urgency_model = Pipeline([
        ("tfidf", TfidfVectorizer(analyzer="word", ngram_range=(1, 2), lowercase=True)),
        ("clf", LogisticRegression(max_iter=1000, class_weight="balanced")),
    ])

    X_train, X_test, y_train, y_test = train_test_split(texts, intents, test_size=0.2, random_state=42, stratify=intents)
    intent_model.fit(X_train, y_train)
    pred = intent_model.predict(X_test)
    intent_acc = accuracy_score(y_test, pred)

    X_train_u, X_test_u, y_train_u, y_test_u = train_test_split(texts, urgencies, test_size=0.2, random_state=42, stratify=urgencies)
    urgency_model.fit(X_train_u, y_train_u)
    upred = urgency_model.predict(X_test_u)
    urgency_acc = accuracy_score(y_test_u, upred)

    joblib.dump(intent_model, MODELS_DIR / "intent_classifier.joblib")
    joblib.dump(urgency_model, MODELS_DIR / "urgency_classifier.joblib")

    report = {
        "intent_accuracy": round(float(intent_acc), 4),
        "urgency_accuracy": round(float(urgency_acc), 4),
        "records": len(rows),
        "intent_labels": sorted(set(intents)),
        "urgency_labels": sorted(set(urgencies)),
    }
    joblib.dump(report, MODELS_DIR / "training_report.joblib")
    print("Training complete:", report)
    print("Intent classification report:\n", classification_report(y_test, pred))
    print("Urgency classification report:\n", classification_report(y_test_u, upred))


if __name__ == "__main__":
    train()
