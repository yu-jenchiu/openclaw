"""Input parsing utilities for the calendar assistant."""
from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass
from datetime import date, datetime, time
from typing import Iterable, List, Literal, Optional

from config import settings

try:
    from openai import OpenAI
except ImportError:  # pragma: no cover - optional dependency during linting
    OpenAI = None  # type: ignore


FixedOrNatural = Literal["fixed", "natural"]

TIMED_EVENT_PATTERN = re.compile(
    r"^\s*(?P<date>\d{4}-\d{2}-\d{2})\s+"
    r"(?P<start>\d{2}:\d{2})\s*~\s*(?P<end>\d{2}:\d{2})\s*\|\s*(?P<title>.+)$"
)
ALL_DAY_PATTERN = re.compile(
    r"^\s*(?P<date>\d{4}-\d{2}-\d{2})\s*\|\s*(?P<title>.+)$"
)


@dataclass(slots=True)
class EventRequest:
    date: date
    title: str
    start_time: Optional[time] = None
    end_time: Optional[time] = None
    all_day: bool = False

    def to_dict(self) -> dict:
        return {
            "date": self.date.isoformat(),
            "title": self.title,
            "start_time": self.start_time.isoformat(timespec="minutes")
            if self.start_time
            else None,
            "end_time": self.end_time.isoformat(timespec="minutes") if self.end_time else None,
            "all_day": self.all_day,
        }


def detect_mode(text: str) -> FixedOrNatural:
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        if TIMED_EVENT_PATTERN.match(stripped) or (
            ALL_DAY_PATTERN.match(stripped) and "~" not in stripped
        ):
            return "fixed"
        break
    return "natural"


def parse_fixed_format(text: str) -> List[EventRequest]:
    events: List[EventRequest] = []
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        match = TIMED_EVENT_PATTERN.match(line)
        if match:
            date_val = datetime.strptime(match.group("date"), "%Y-%m-%d").date()
            start = datetime.strptime(match.group("start"), "%H:%M").time()
            end = datetime.strptime(match.group("end"), "%H:%M").time()
            if end <= start:
                raise ValueError(f"結束時間必須晚於開始時間：{line}")
            events.append(
                EventRequest(
                    date=date_val,
                    title=match.group("title").strip(),
                    start_time=start,
                    end_time=end,
                )
            )
            continue
        all_day = ALL_DAY_PATTERN.match(line)
        if all_day:
            date_val = datetime.strptime(all_day.group("date"), "%Y-%m-%d").date()
            events.append(
                EventRequest(
                    date=date_val,
                    title=all_day.group("title").strip(),
                    all_day=True,
                )
            )
            continue
        raise ValueError(f"無法解析固定格式這一行：{line}")
    if not events:
        raise ValueError("沒有任何有效的固定格式事件")
    return events


def parse_natural_language(text: str) -> List[EventRequest]:
    if not settings.llm_enabled():
        raise RuntimeError(
            "尚未設定 OPENAI_API_KEY，無法使用自然語言模式；"
            "請改用固定格式或設定 API key。"
        )
    if OpenAI is None:
        raise RuntimeError("openai 套件未安裝，請確認 requirements 已安裝完成。")

    client = OpenAI(api_key=settings.openai_api_key, base_url=settings.openai_base_url or None)
    prompt = (
        "你是一個行事曆助手，請將輸入的一段自然語言轉成 JSON 陣列。"
        "JSON 結構必須是 [{\"date\": \"YYYY-MM-DD\", \"title\": \"...\","
        " \"start_time\": \"HH:MM\" 或 null, \"end_time\": \"HH:MM\" 或 null,"
        " \"all_day\": 布林值}]。若無法解析，回傳空陣列。"
    )

    response = client.responses.create(
        model=settings.llm_model,
        input=[
            {
                "role": "system",
                "content": prompt,
            },
            {
                "role": "user",
                "content": text,
            },
        ],
        response_format={"type": "json_object"},
    )

    raw = response.output[0].content[0].text  # type: ignore[attr-defined]
    data = json.loads(raw)
    if isinstance(data, dict) and "events" in data:
        items = data["events"]
    else:
        items = data

    events: List[EventRequest] = []
    for item in items:
        parsed_date = datetime.strptime(item["date"], "%Y-%m-%d").date()
        start_time = (
            datetime.strptime(item["start_time"], "%H:%M").time()
            if item.get("start_time")
            else None
        )
        end_time = (
            datetime.strptime(item["end_time"], "%H:%M").time()
            if item.get("end_time")
            else None
        )
        all_day = bool(item.get("all_day")) or (start_time is None and end_time is None)
        events.append(
            EventRequest(
                date=parsed_date,
                title=item["title"].strip(),
                start_time=start_time,
                end_time=end_time,
                all_day=all_day,
            )
        )
    if not events:
        raise ValueError("LLM 無法解析出任何事件，請再試一次或改用固定格式。")
    return events
