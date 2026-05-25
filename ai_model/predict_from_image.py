import json
import re

import torch
import easyocr
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM

from calendar_schema import build_prompt


MODEL_DIR = "./calendar_json_model"
MAX_INPUT_LEN = 1024
MAX_TARGET_LEN = 512
DEFAULT_TIMEZONE = "Asia/Seoul"


def empty_calendar_json() -> dict:
    return {
        "summary": "",
        "description": "",
        "location": "",
        "start": {
            "date": "",
            "time": "",
            "timeZone": DEFAULT_TIMEZONE,
        },
        "end": {
            "date": "",
            "time": "",
            "timeZone": DEFAULT_TIMEZONE,
        },
    }


def normalize_calendar_json(data: dict) -> dict:
    result = empty_calendar_json()

    if not isinstance(data, dict):
        return result

    result["summary"] = data.get("summary") or ""
    result["description"] = data.get("description") or ""
    result["location"] = data.get("location") or ""

    start = data.get("start") or {}
    end = data.get("end") or {}

    if isinstance(start, dict):
        result["start"]["date"] = start.get("date") or ""
        result["start"]["time"] = start.get("time") or ""
        result["start"]["timeZone"] = start.get("timeZone") or DEFAULT_TIMEZONE

    if isinstance(end, dict):
        result["end"]["date"] = end.get("date") or ""
        result["end"]["time"] = end.get("time") or ""
        result["end"]["timeZone"] = end.get("timeZone") or DEFAULT_TIMEZONE

    return result


def extract_json_from_text(text: str) -> dict:
    if not text:
        return empty_calendar_json()

    text = text.strip()

    try:
        data = json.loads(text)
        return normalize_calendar_json(data)
    except Exception:
        pass

    match = re.search(r"\{.*\}", text, re.DOTALL)

    if not match:
        return empty_calendar_json()

    try:
        data = json.loads(match.group())
        return normalize_calendar_json(data)
    except Exception:
        return empty_calendar_json()


def ocr_image_to_text(image_path: str) -> str:
    reader = easyocr.Reader(
        ["ko", "en"],
        gpu=torch.cuda.is_available(),
    )

    results = reader.readtext(
        image_path,
        detail=0,
        paragraph=True,
    )

    return "\n".join(results)


def generate_calendar_json(raw_text: str, max_retry: int = 3) -> dict:
    tokenizer = AutoTokenizer.from_pretrained(MODEL_DIR)
    model = AutoModelForSeq2SeqLM.from_pretrained(MODEL_DIR)

    device = "cuda" if torch.cuda.is_available() else "cpu"
    model.to(device)
    model.eval()

    prompt = build_prompt(raw_text)

    generation_settings = [
        {"num_beams": 4, "do_sample": False},
        {"num_beams": 8, "do_sample": False},
        {"num_beams": 4, "do_sample": True, "temperature": 0.3, "top_p": 0.9},
    ]

    last_result = empty_calendar_json()

    for attempt in range(max_retry):
        settings = generation_settings[min(attempt, len(generation_settings) - 1)]

        inputs = tokenizer(
            prompt,
            return_tensors="pt",
            max_length=MAX_INPUT_LEN,
            truncation=True,
        ).to(device)

        with torch.no_grad():
            output_ids = model.generate(
                **inputs,
                max_new_tokens=MAX_TARGET_LEN,
                **settings,
            )

        decoded = tokenizer.decode(
            output_ids[0],
            skip_special_tokens=True,
        )

        parsed = extract_json_from_text(decoded)
        last_result = parsed

        has_any_value = (
            parsed["summary"]
            or parsed["description"]
            or parsed["location"]
            or parsed["start"]["date"]
            or parsed["start"]["time"]
            or parsed["end"]["date"]
            or parsed["end"]["time"]
        )

        if has_any_value:
            return parsed

    return last_result


def predict_from_image(image_path: str) -> dict:
    ocr_text = ocr_image_to_text(image_path)

    print("===== OCR 결과 =====")
    print(ocr_text)
    print("===================")

    return generate_calendar_json(ocr_text)


if __name__ == "__main__":
    image_path = "test4.png"

    result = predict_from_image(image_path)

    print("===== 최종 결과 =====")
    print(json.dumps(result, ensure_ascii=False, indent=2))