from __future__ import annotations

import json
from typing import Any

import pandas as pd
from openai import OpenAI
from tqdm import tqdm

from app.core.config import settings


SENTIMENT_SYSTEM_PROMPT = (
    "Bạn là chuyên gia phân tích cảm xúc văn bản tiếng Việt từ đánh giá sinh viên về "
    "giảng viên/môn học/phương pháp dạy. Nhiệm vụ: phân tích sentiment của text, rồi "
    "gán nhãn: negative, neutral hoặc positive. Chỉ output nhãn duy nhất "
    "(ví dụ: 'positive'), không giải thích trừ khi yêu cầu."
)

VALID_SENTIMENT_LABELS = {"negative", "neutral", "positive"}
BATCH_SENTIMENT_SYSTEM_PROMPT = (
    "Bạn là chuyên gia phân tích cảm xúc văn bản tiếng Việt từ đánh giá sinh viên về "
    "giảng viên, môn học và phương pháp dạy học. Bạn sẽ nhận một danh sách text. "
    "Hãy gán cho mỗi text đúng một nhãn trong tập: negative, neutral, positive. "
    "Bắt buộc chỉ trả về JSON array các nhãn theo đúng thứ tự đầu vào, ví dụ: "
    "[\"positive\", \"neutral\", \"negative\"]. Không giải thích."
)


def _parse_sentiment_label(raw_value: Any) -> str:
    value = str(raw_value or "").replace('"', "").strip().lower()
    if value not in VALID_SENTIMENT_LABELS:
        return "neutral"
    return value


def _strip_code_fences(raw_value: str) -> str:
    value = raw_value.strip()
    if value.startswith("```"):
        lines = value.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        return "\n".join(lines).strip()
    return value


def _label_single_text(client: OpenAI, text: str) -> str:
    response = client.chat.completions.create(
        model=settings.openai_sentiment_model,
        messages=[
            {"role": "system", "content": SENTIMENT_SYSTEM_PROMPT},
            {"role": "user", "content": f"Text: {text}"},
        ],
        temperature=0,
        timeout=settings.openai_request_timeout_seconds,
    )
    return _parse_sentiment_label(response.choices[0].message.content)


def _label_text_batch(client: OpenAI, texts: list[str]) -> list[str] | None:
    response = client.chat.completions.create(
        model=settings.openai_sentiment_model,
        messages=[
            {"role": "system", "content": BATCH_SENTIMENT_SYSTEM_PROMPT},
            {
                "role": "user",
                "content": json.dumps({"texts": texts}, ensure_ascii=False),
            },
        ],
        temperature=0,
        timeout=settings.openai_request_timeout_seconds,
    )
    raw_content = response.choices[0].message.content or ""
    normalized_content = _strip_code_fences(raw_content)

    try:
        parsed = json.loads(normalized_content)
    except json.JSONDecodeError:
        return None

    if not isinstance(parsed, list) or len(parsed) != len(texts):
        return None

    return [_parse_sentiment_label(item) for item in parsed]


def label_vietnamese_sentiment_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    if "sentence" in df.columns:
        text_column = "sentence"
    elif "text" in df.columns:
        text_column = "text"
    else:
        raise ValueError("DataFrame must contain either a 'sentence' or 'text' column.")

    if not settings.openai_api_key:
        raise RuntimeError(
            "OPENAI_API_KEY is not configured. Set OPENAI_API_KEY or switch SENTIMENT_PROVIDER=rule_based."
        )

    client = OpenAI(api_key=settings.openai_api_key)
    texts = df[text_column].fillna("").astype(str).tolist()
    batch_size = max(1, settings.openai_sentiment_batch_size)

    labels: list[str] = []
    progress_bar = tqdm(
        range(0, len(texts), batch_size),
        desc="Labeling sentiments with OpenAI",
        disable=not settings.show_label_progress,
    )

    for start_index in progress_bar:
        batch_texts = texts[start_index : start_index + batch_size]
        batch_labels = ["neutral"] * len(batch_texts)
        non_empty_indexes = [index for index, text in enumerate(batch_texts) if text.strip()]

        if not non_empty_indexes:
            labels.extend(batch_labels)
            continue

        try:
            active_texts = [batch_texts[index] for index in non_empty_indexes]
            predicted_labels = _label_text_batch(client, active_texts)
            if predicted_labels is None:
                raise ValueError("Batch labeling did not return a valid JSON label list.")
            for offset, label in zip(non_empty_indexes, predicted_labels, strict=False):
                batch_labels[offset] = label
        except Exception:
            for offset in non_empty_indexes:
                try:
                    batch_labels[offset] = _label_single_text(client, batch_texts[offset])
                except Exception:
                    batch_labels[offset] = "neutral"

        labels.extend(batch_labels)

    labeled_df = df.copy()
    labeled_df["label"] = labels
    return labeled_df
