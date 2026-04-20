"""Entry point and interaction handlers for the calendar assistant."""
from __future__ import annotations

import argparse
import json
import sys
from typing import Dict, List, Optional

from calendar_writer import CalendarWriter
from parser import EventRequest, detect_mode, parse_fixed_format, parse_natural_language

try:
    from telegram import Update
    from telegram.ext import (
        Application,
        CommandHandler,
        ContextTypes,
        MessageHandler,
        filters,
    )
except ImportError:  # pragma: no cover - optional dependency
    Update = ContextTypes = Application = None  # type: ignore


class AssistantApp:
    def __init__(self) -> None:
        self.writer = CalendarWriter()

    def process_text(self, text: str, preferred_mode: Optional[str] = None) -> dict:
        mode = preferred_mode or detect_mode(text)
        events = self._parse_by_mode(text, mode)
        results = []
        for event in events:
            output = self.writer.create_event(event)
            results.append({"request": event.to_dict(), "google_event_id": output.get("id")})
        return {"mode": mode, "action": "create", "events": results}

    def process_update(
        self, text: str, preferred_mode: Optional[str] = None, selection_index: Optional[int] = None
    ) -> dict:
        mode = preferred_mode or detect_mode(text)
        events = self._parse_by_mode(text, mode)
        if len(events) != 1:
            raise ValueError("修改事件一次僅支援一筆，請縮小輸入內容。")
        event = events[0]
        matches = self.writer.find_matching_events(event)
        if not matches:
            return {"mode": mode, "action": "update", "matches": [], "status": "not_found"}
        if len(matches) > 1 and selection_index is None:
            return {
                "mode": mode,
                "action": "update",
                "status": "needs_selection",
                "candidates": self._format_candidates(matches),
            }
        target_index = selection_index or 0
        if target_index < 0 or target_index >= len(matches):
            raise ValueError("selection_index 超出範圍。")
        event_id = matches[target_index]["id"]
        updated = self.writer.update_event(event_id, event)
        return {
            "mode": mode,
            "action": "update",
            "status": "updated",
            "updated_event": {
                "request": event.to_dict(),
                "google_event_id": updated.get("id"),
            },
        }

    def _parse_by_mode(self, text: str, mode: str) -> List[EventRequest]:
        if mode == "fixed":
            return parse_fixed_format(text)
        return parse_natural_language(text)

    @staticmethod
    def _format_candidates(matches: List[Dict]) -> List[Dict]:
        formatted = []
        for item in matches:
            start = item.get("start", {})
            end = item.get("end", {})
            formatted.append(
                {
                    "id": item.get("id"),
                    "summary": item.get("summary"),
                    "start": start.get("dateTime") or start.get("date"),
                    "end": end.get("dateTime") or end.get("date"),
                }
            )
        return formatted


async def handle_telegram_message(update: Update, context: ContextTypes.DEFAULT_TYPE):  # type: ignore
    app = context.application.bot_data.setdefault("app", AssistantApp())
    text = (update.message.text or "").strip()
    try:
        if text.lower().startswith("update:"):
            query = text.split(":", 1)[1].strip()
            result = app.process_update(query)
        else:
            result = app.process_text(text)
        response = json.dumps(result, ensure_ascii=False, indent=2)
    except Exception as exc:  # pylint: disable=broad-except
        response = f"發生錯誤：{exc}"
    await update.message.reply_text(response)


def build_cli_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Google Calendar assistant tester")
    parser.add_argument("text", help="輸入一句要解析的文字")
    parser.add_argument(
        "--mode",
        choices=["auto", "fixed", "natural"],
        default="auto",
        help="指定解析模式（預設自動偵測）",
    )
    parser.add_argument(
        "--update",
        action="store_true",
        help="啟用修改模式（預設為新增事件）",
    )
    parser.add_argument(
        "--select",
        type=int,
        help="當存在多筆待修改事件時，指定要選擇的候選索引（從 0 開始）",
    )
    parser.add_argument(
        "--telegram",
        action="store_true",
        help="改為啟動 Telegram Bot，TOKEN 從 TELEGRAM_BOT_TOKEN 讀取",
    )
    return parser


def run_cli() -> None:
    parser = build_cli_parser()
    args = parser.parse_args()

    if args.telegram:
        token = settings.__dict__.get("telegram_bot_token") or SystemExit(
            "請在環境變數 TELEGRAM_BOT_TOKEN 中設定 Bot Token"
        )
        run_telegram_bot(str(token))
        return

    app = AssistantApp()
    preferred = None if args.mode == "auto" else args.mode
    try:
        if args.update:
            result = app.process_update(args.text, preferred_mode=preferred, selection_index=args.select)
        else:
            result = app.process_text(args.text, preferred_mode=preferred)
    except Exception as exc:  # pylint: disable=broad-except
        print(f"錯誤：{exc}")
        sys.exit(1)

    print(json.dumps(result, ensure_ascii=False, indent=2))


def run_telegram_bot(token: str) -> None:
    if Application is None:
        raise RuntimeError("尚未安裝 python-telegram-bot，無法啟動 Telegram handler。")
    application = Application.builder().token(token).build()
    application.add_handler(
        CommandHandler("start", lambda update, _: update.message.reply_text("嗨！把行程丟給我。"))
    )
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_telegram_message))
    application.bot_data["app"] = AssistantApp()
    application.run_polling()


if __name__ == "__main__":
    run_cli()
