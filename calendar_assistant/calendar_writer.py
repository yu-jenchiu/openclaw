"""Google Calendar interaction layer."""
from __future__ import annotations

from datetime import datetime, timedelta
from typing import Dict, List

import pytz
from google.oauth2 import service_account
from googleapiclient.discovery import build

from config import settings
from parser import EventRequest

SCOPES = ["https://www.googleapis.com/auth/calendar"]


class CalendarWriter:
    def __init__(self) -> None:
        self._timezone = pytz.timezone(settings.timezone)
        credentials = self._build_credentials()
        self._service = build("calendar", "v3", credentials=credentials)

    @staticmethod
    def _build_credentials():
        info = settings.service_account_info()
        if info:
            return service_account.Credentials.from_service_account_info(info, scopes=SCOPES)
        return service_account.Credentials.from_service_account_file(
            str(settings.service_account_file()), scopes=SCOPES
        )

    @property
    def calendar_id(self) -> str:
        if not settings.calendar_id:
            raise RuntimeError("尚未設定 CALENDAR_ID，無法與 Google Calendar 溝通")
        return settings.calendar_id

    def create_event(self, request: EventRequest) -> Dict:
        body = self._build_event_body(request)
        return (
            self._service.events()
            .insert(calendarId=self.calendar_id, body=body, supportsAttachments=False)
            .execute()
        )

    def update_event(self, event_id: str, request: EventRequest) -> Dict:
        body = self._build_event_body(request)
        return (
            self._service.events()
            .patch(calendarId=self.calendar_id, eventId=event_id, body=body)
            .execute()
        )

    def find_matching_events(self, request: EventRequest) -> List[Dict]:
        start_dt, end_dt = self._event_window(request)
        events_result = (
            self._service.events()
            .list(
                calendarId=self.calendar_id,
                timeMin=start_dt.isoformat(),
                timeMax=end_dt.isoformat(),
                q=request.title,
                singleEvents=True,
                orderBy="startTime",
            )
            .execute()
        )
        candidates = []
        for event in events_result.get("items", []):
            summary = event.get("summary", "")
            if summary.strip() != request.title.strip():
                continue
            candidates.append(event)
        return candidates

    def _build_event_body(self, request: EventRequest) -> Dict:
        if request.all_day:
            return {
                "summary": request.title,
                "start": {"date": request.date.isoformat(), "timeZone": settings.timezone},
                "end": {
                    "date": (request.date + timedelta(days=1)).isoformat(),
                    "timeZone": settings.timezone,
                },
            }
        start_dt = datetime.combine(request.date, request.start_time)
        end_dt = datetime.combine(request.date, request.end_time)
        start_dt = self._timezone.localize(start_dt)
        end_dt = self._timezone.localize(end_dt)
        return {
            "summary": request.title,
            "start": {"dateTime": start_dt.isoformat()},
            "end": {"dateTime": end_dt.isoformat()},
        }

    def _event_window(self, request: EventRequest):
        if request.all_day:
            start = self._timezone.localize(datetime.combine(request.date, datetime.min.time()))
            end = start + timedelta(days=1)
        else:
            start = self._timezone.localize(datetime.combine(request.date, request.start_time))
            end = start + timedelta(days=1)
        return start, end
