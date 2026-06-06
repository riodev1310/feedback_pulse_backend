from __future__ import annotations

import pickle
from functools import lru_cache
from pathlib import Path
from typing import Any

import pandas as pd

from app.core.config import settings


VALID_SENTIMENT_LABELS = {"negative", "neutral", "positive"}
TRAINED_MODEL_LABEL_MAP = {
    0: "negative",
    1: "neutral",
    2: "positive",
    "0": "negative",
    "1": "neutral",
    "2": "positive",
    "negative": "negative",
    "neutral": "neutral",
    "positive": "positive",
}


def _normalize_predicted_label(raw_value: Any) -> str:
    normalized = TRAINED_MODEL_LABEL_MAP.get(raw_value)
    if normalized in VALID_SENTIMENT_LABELS:
        return normalized

    lowered = str(raw_value or "").strip().lower()
    if lowered in VALID_SENTIMENT_LABELS:
        return lowered
    return "neutral"


@lru_cache(maxsize=1)
def _load_trained_model_pipeline():
    model_path = Path(settings.trained_model_sentiment_model_path)
    if not model_path.exists():
        raise FileNotFoundError(f"Trained-model sentiment file not found: {model_path}")

    try:
        with model_path.open("rb") as model_file:
            return pickle.load(model_file)
    except ModuleNotFoundError as exc:
        raise RuntimeError(
            "Trained-model sentiment requires scikit-learn to be installed. "
            "Run `pip install -r requirements.txt` in backend/.venv."
        ) from exc


def label_vietnamese_sentiment_dataframe_with_trained_model(df: pd.DataFrame) -> pd.DataFrame:
    if "sentence" in df.columns:
        text_column = "sentence"
    elif "text" in df.columns:
        text_column = "text"
    else:
        raise ValueError("DataFrame must contain either a 'sentence' or 'text' column.")

    pipeline = _load_trained_model_pipeline()
    texts = df[text_column].fillna("").astype(str).tolist()
    labels = ["neutral"] * len(texts)
    non_empty_indexes = [index for index, text in enumerate(texts) if text.strip()]

    if non_empty_indexes:
        active_texts = [texts[index] for index in non_empty_indexes]
        raw_predictions = pipeline.predict(active_texts)
        for offset, prediction in zip(non_empty_indexes, raw_predictions, strict=False):
            labels[offset] = _normalize_predicted_label(prediction)

    labeled_df = df.copy()
    labeled_df["label"] = labels
    return labeled_df
