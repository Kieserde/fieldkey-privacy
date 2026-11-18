"""
title: Google Calendar (read/write)
description: Lets the local AI list, create, update and delete Google Calendar events.
version: 0.2.0
requirements: google-api-python-client, google-auth
"""
# Setup is described in scripts/calendar/README.md.
# Install: Open WebUI -> Workspace -> Tools -> "+" -> paste this file -> Save,
# then open the tool's gear icon and fill in TOKEN_JSON (from calendar_auth.py).

import json
from datetime import datetime, timedelta

from pydantic import BaseModel, Field

SCOPES = ["https://www.googleapis.com/auth/calendar.events"]


def _service(token_json: str):
    from google.oauth2.credentials import Credentials
    from googleapiclient.discovery import build

    creds = Credentials.from_authorized_user_info(json.loads(token_json), SCOPES)
    return build("calendar", "v3", credentials=creds, cache_discovery=False)


def _when(e: dict) -> str:
    s = e.get("start", {})
    if "dateTime" in s:
        return datetime.fromisoformat(s["dateTime"]).strftime("%a %d %b %H:%M")
    return f"{s.get('date', '?')} (all day)"


def _line(e: dict) -> str:
    out = f"- [{e['id']}] {_when(e)}: {e.get('summary', '(no title)')}"
    if e.get("location"):
        out += f" @ {e['location']}"
    return out


class Tools:
    class Valves(BaseModel):
        TOKEN_JSON: str = Field(default="", description="Token JSON printed by calendar_auth.py")
        CALENDAR_ID: str = Field(default="primary", description="Calendar to use")
        TIMEZONE: str = Field(default="", description="IANA zone, e.g. Europe/Berlin. Required for timed events.")

    def __init__(self):
        self.valves = self.Valves()

    def _svc(self):
        if not self.valves.TOKEN_JSON:
            raise RuntimeError("Calendar is not configured: set TOKEN_JSON in this tool's settings.")
        return _service(self.valves.TOKEN_JSON)

    def list_events(self, days: int = 7) -> str:
        """
        List upcoming calendar events with their IDs (IDs are needed to update or delete).
        :param days: How many days ahead to look (1-90). Use 1 for today.
        """
        try:
            days = max(1, min(days, 90))
            now = datetime.now().astimezone()
            res = self._svc().events().list(
                calendarId=self.valves.CALENDAR_ID,
                timeMin=now.isoformat(),
                timeMax=(now + timedelta(days=days)).isoformat(),
                singleEvents=True,
                orderBy="startTime",
                maxResults=100,
            ).execute()
            items = res.get("items", [])
            return "\n".join(_line(e) for e in items) or f"No events in the next {days} days."
        except Exception as exc:
            return f"Could not read calendar: {exc}"

    def create_event(self, title: str, start: str, end: str = "", location: str = "", description: str = "") -> str:
        """
        Create a calendar event.
        :param title: Event title.
        :param start: Start as ISO 8601 local time like 2026-11-20T15:00:00, or a date like 2026-11-20 for an all-day event.
        :param end: End in the same format. Optional; defaults to one hour later (timed) or the same day (all-day).
        :param location: Optional location.
        :param description: Optional notes.
        """
        try:
            body = {"summary": title}
            if location:
                body["location"] = location
            if description:
                body["description"] = description
            if "T" in start:
                if not self.valves.TIMEZONE:
                    return "Set TIMEZONE (e.g. Europe/Berlin) in this tool's settings first."
                end = end or (datetime.fromisoformat(start) + timedelta(hours=1)).isoformat()
                body["start"] = {"dateTime": start, "timeZone": self.valves.TIMEZONE}
                body["end"] = {"dateTime": end, "timeZone": self.valves.TIMEZONE}
            else:
                end_date = end or (datetime.fromisoformat(start) + timedelta(days=1)).date().isoformat()
                body["start"] = {"date": start}
                body["end"] = {"date": end_date}
            e = self._svc().events().insert(calendarId=self.valves.CALENDAR_ID, body=body).execute()
            return f"Created: {_line(e)}"
        except Exception as exc:
            return f"Could not create event: {exc}"

    def update_event(self, event_id: str, title: str = "", start: str = "", end: str = "", location: str = "") -> str:
        """
        Change an existing event. Only the fields you pass are changed. Get event_id from list_events.
        :param event_id: ID of the event.
        :param title: New title (optional).
        :param start: New start, ISO 8601 local time (optional). Pass end too when moving an event.
        :param end: New end (optional).
        :param location: New location (optional).
        """
        try:
            patch = {}
            if title:
                patch["summary"] = title
            if location:
                patch["location"] = location
            if start or end:
                if (start and "T" not in start) or (end and "T" not in end):
                    return "Only timed changes (with a T time) are supported here."
                if not self.valves.TIMEZONE:
                    return "Set TIMEZONE in this tool's settings first."
                if start:
                    patch["start"] = {"dateTime": start, "timeZone": self.valves.TIMEZONE}
                if end:
                    patch["end"] = {"dateTime": end, "timeZone": self.valves.TIMEZONE}
            if not patch:
                return "Nothing to change."
            e = self._svc().events().patch(calendarId=self.valves.CALENDAR_ID, eventId=event_id, body=patch).execute()
            return f"Updated: {_line(e)}"
        except Exception as exc:
            return f"Could not update event: {exc}"

    def delete_event(self, event_id: str, confirmed: bool = False) -> str:
        """
        Delete an event. FIRST call with confirmed=False to preview, show the user the event and
        ask them to confirm. Only call again with confirmed=True after the user says yes.
        :param event_id: ID of the event (from list_events).
        :param confirmed: True only after the user explicitly approved this deletion.
        """
        try:
            svc = self._svc()
            e = svc.events().get(calendarId=self.valves.CALENDAR_ID, eventId=event_id).execute()
            if not confirmed:
                return f"NOT deleted yet. Ask the user to confirm deleting: {_line(e)}"
            svc.events().delete(calendarId=self.valves.CALENDAR_ID, eventId=event_id).execute()
            return f"Deleted: {_line(e)}"
        except Exception as exc:
            return f"Could not delete event: {exc}"
