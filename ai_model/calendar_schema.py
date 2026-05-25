import json
import re
from datetime import datetime
from jsonschema import validate


TIME_ZONE = "Asia/Seoul"

CALENDAR_JSON_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "required": ["summary", "description", "location", "start", "end"],
    "properties": {
        "summary": {"type": "string", "minLength": 1},
        "description": {"type": "string", "minLength": 1},
        "location": {"type": "string", "minLength": 1},
        "start": {
            "type": "object",
            "additionalProperties": False,
            "required": ["date", "time", "timeZone"],
            "properties": {
                "date": {"type": "string", "pattern": r"^\d{4}-\d{2}-\d{2}$"},
                "time": {"type": "string", "pattern": r"^(?:[01]\d|2[0-3]):[0-5]\d$"},
                "timeZone": {"const": TIME_ZONE},
            },
        },
        "end": {
            "type": "object",
            "additionalProperties": False,
            "required": ["date", "time", "timeZone"],
            "properties": {
                "date": {"type": "string", "pattern": r"^\d{4}-\d{2}-\d{2}$"},
                "time": {"type": "string", "pattern": r"^(?:[01]\d|2[0-3]):[0-5]\d$"},
                "timeZone": {"const": TIME_ZONE},
            },
        },
    },
}


FORMAT_INSTRUCTION = """
다음 원문에서 일정 정보를 추출하여 반드시 아래 JSON 형식 하나만 출력하시오.

출력 규칙:
- JSON 객체만 출력한다.
- 설명 문장, markdown, ```json 코드블록은 출력하지 않는다.
- key 이름은 반드시 summary, description, location, start, end만 사용한다.
- start와 end에는 date, time, timeZone만 사용한다.
- date는 YYYY-MM-DD 형식이다.
- time은 HH:MM 24시간 형식이다.
- timeZone은 반드시 Asia/Seoul이다.

출력 형식:
{
  "summary": "일정 제목",
  "description": "일정 설명",
  "location": "일정 장소",
  "start": {
    "date": "YYYY-MM-DD",
    "time": "HH:MM",
    "timeZone": "Asia/Seoul"
  },
  "end": {
    "date": "YYYY-MM-DD",
    "time": "HH:MM",
    "timeZone": "Asia/Seoul"
  }
}
""".strip()


def build_prompt(raw_text: str) -> str:
    return f"{FORMAT_INSTRUCTION}\n\n원문:\n{normalize_text(raw_text)}"


def normalize_text(text: str) -> str:
    text = str(text)
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    return "\n".join(line.strip() for line in text.split("\n") if line.strip())


def canonicalize_calendar_json(obj: dict) -> dict:
    """
    key 순서를 고정하고, 불필요한 key를 제거합니다.
    """
    fixed = {
        "summary": str(obj["summary"]).strip(),
        "description": str(obj["description"]).strip(),
        "location": str(obj["location"]).strip(),
        "start": {
            "date": str(obj["start"]["date"]).strip(),
            "time": str(obj["start"]["time"]).strip(),
            "timeZone": TIME_ZONE,
        },
        "end": {
            "date": str(obj["end"]["date"]).strip(),
            "time": str(obj["end"]["time"]).strip(),
            "timeZone": TIME_ZONE,
        },
    }
    validate_calendar_json(fixed)
    return fixed


def validate_calendar_json(obj: dict) -> None:
    validate(instance=obj, schema=CALENDAR_JSON_SCHEMA)

    start_dt = datetime.fromisoformat(
        f'{obj["start"]["date"]}T{obj["start"]["time"]}:00'
    )
    end_dt = datetime.fromisoformat(
        f'{obj["end"]["date"]}T{obj["end"]["time"]}:00'
    )

    if end_dt <= start_dt:
        raise ValueError("end 시간이 start 시간보다 늦어야 합니다.")


def to_compact_json(obj: dict) -> str:
    fixed = canonicalize_calendar_json(obj)
    return json.dumps(fixed, ensure_ascii=False, separators=(",", ":"))


def parse_model_json(text: str) -> dict:
    """
    모델 출력에서 JSON 객체만 추출하고 schema로 검증합니다.
    """
    text = text.strip()
    text = text.replace("```json", "").replace("```", "").strip()

    try:
        obj = json.loads(text)
        return canonicalize_calendar_json(obj)
    except Exception:
        pass

    match = re.search(r"\{.*\}", text, flags=re.DOTALL)
    if not match:
        raise ValueError(f"JSON 객체를 찾지 못했습니다.\n모델 출력:\n{text}")

    obj = json.loads(match.group(0))
    return canonicalize_calendar_json(obj)